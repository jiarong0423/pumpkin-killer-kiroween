#!/usr/bin/env python3
"""Deterministic Python rules engine for Pumpkin Killer's fixed headless mode."""
import argparse
import json
import math
import os
import random
import sys
from typing import Any, Dict, List, Optional

import comeback_py as comeback
import team_tuning_py as tuning
from determinism_py import nun_stun_pick, start_x

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_ROOT, "shared", "constants.json"), encoding="utf-8") as handle:
    _SHARED = json.load(handle)
with open(os.path.join(_ROOT, "shared", "heroes.json"), encoding="utf-8") as handle:
    HERO_TEMPLATES = json.load(handle)

CANVAS_WIDTH = 1920
GROUND_Y = _SHARED["GROUND_Y"]
_WIND_TAIL = float(_SHARED["WIND_TAIL"])   # shared/constants.json: the same numbers as js/flight.js
_WIND_HEAD = float(_SHARED["WIND_HEAD"])

_HIT_MASKS = [False]
def _hit_masks():
    """The binary hit masks (shared/hit_masks.json), loaded once; None when the file is missing, so the box alone decides."""
    if _HIT_MASKS[0] is False:
        try:
            from hit_mask_py import HitMasks
            _HIT_MASKS[0] = HitMasks()
        except (OSError, ValueError, ImportError):
            _HIT_MASKS[0] = None
    return _HIT_MASKS[0]
GRAVITY = _SHARED["GRAVITY"]
V0_PER_POWER = _SHARED["V0_PER_POWER"]
WIND_MIN = _SHARED["WIND_MIN"]
WIND_MAX = _SHARED["WIND_MAX"]
WALL_HIT_DMG = _SHARED["WALL_HIT_DMG"]
KNIGHT_ZONE = _SHARED["KNIGHT_ZONE"]
SHIELD_WALL_COFFIN_HEIGHT = _SHARED["SHIELD_WALL_COFFIN_HEIGHT"]
SHIELD_WALL_EXPIRES_AFTER_ATTACKS = _SHARED["SHIELD_WALL_EXPIRES_AFTER_ATTACKS"]
START_X_RANGE = {"red": (220, 620), "white": (1280, 1680)}
# Drawn size (wLen, wThick) of each projectile, equal to HERO_PROFILES in index.html (checked by scripts/test_hit_radius.py)
PROJECTILE_SIZE = {"proj_spear": (210, 33), "cannonball": (40, 40), "proj_shuriken": (58, 58), "proj_flame": (150, 55),
                   "proj_cross": (118, 82), "proj_soundwave": (170, 170), "proj_axe": (130, 130), "proj_shield": (62, 92)}
MOVE_X_LIMITS = {"red": (110.0, 640.0), "white": (1280.0, 1810.0)}   # the retreat limits go back to the edge, 110 / 1810 (owner 2026-11-17), the forward limits stay
WALL_X_MIN = _SHARED["FENCE_X"] - _SHARED["FENCE_W"] / 2
WALL_X_MAX = _SHARED["FENCE_X"] + _SHARED["FENCE_W"] / 2
WALL_TOP_Y = GROUND_Y - _SHARED["FENCE_H"]
# Wizard ultimate (page: `ultBlast`): every living enemy unit within BLAST_RADIUS px of the impact point takes a flat 1.5 x normal damage
# (no distance steps, no crit, no status: poison comes only from the shell's own contact hit).
BLAST_RADIUS = 234.0
BLAST_MULTIPLIER = 1.5
# Bride wave (page: js/sound_wave.js): every living enemy unit within 105 px of the wave centre, stepped 100/75/50 percent by its own distance.
WAVE_STEPS = ((35.0, 1.0), (70.0, 0.75), (105.0, 0.5))   # cells of 35 px (owner 2026-11-18); twin of js/sound_wave.js
SWARM_PRECISE_RADIUS = None   # was 55.0: since 2026-11-18 ANY hit of the armed ultimate wave calls the bat swarm on every living enemy (page: p.ultSwarm && opp.hp > 0)
SWARM_MULTIPLIER = 1.3
MIN_TEAMMATE_GAP = 120.0      # page: a unit never stops within 120 px of a living teammate (moves and knockback)
HEAD_FRACTION = 0.25
HEAD_HALF_WIDTH = 35.0
CRIT_MULTIPLIER = 1.1   # owner 2026-11-17: was 1.25; the same number as CRIT_MULT in index.html
DICE_STEP_PX = 36.0
WAVE_BANDS = ((35.0, "100"), (70.0, "75"), (105.0, "50"))
STATUS_TICK_DAMAGE = {"bleed": 2.0, "poison": 2.0, "burn": 2.0}
DEFAULT_RED_HEROES = ("bat", "skeleton", "knight")
DEFAULT_WHITE_HEROES = ("wizard", "knight", "skeleton")


def hit_report(landing_x: float, target_x: float, hit_type: str, weapon: str) -> Dict[str, Any]:
    """Classify a resolved throw using the browser's public landing vocabulary."""
    landing = float(landing_x)
    target = float(target_x)
    distance = abs(landing - target)
    steps = int(math.floor(distance / DICE_STEP_PX + 0.5))
    if weapon == "proj_soundwave":
        band = next((name for limit, name in WAVE_BANDS if distance <= limit), "out")
        return {"kind": "wave", "key": "hitReport.wave" + band,
                "params": {"band": band}, "distance": distance, "steps": steps}
    if hit_type == "hero":
        return {"kind": "hit", "key": "hitReport.hit", "params": {}, "distance": distance, "steps": 0}
    if hit_type in ("wall", "central_wall"):
        return {"kind": "blocked", "key": "hitReport.fence", "params": {}, "distance": distance, "steps": 0}
    if hit_type in ("shield_blocked", "ultblock", "ultimate_blocked"):
        return {"kind": "blocked", "key": "hitReport.shield", "params": {}, "distance": distance, "steps": 0}
    return {"kind": "miss", "key": "hitReport.short" if landing < target else "hitReport.long",
            "params": {"steps": steps}, "distance": distance, "steps": steps}


def _round_tenth(value: float) -> float:
    return math.floor(value * 10 + 0.5) / 10


def wave_multiplier(distance: float) -> float:
    """Stepped bride-wave damage factor for a unit `distance` px from the wave centre (0.0 outside 105 px)."""
    for limit, factor in WAVE_STEPS:
        if distance <= limit:
            return factor
    return 0.0


def _status_words(unit: Dict[str, Any]) -> List[str]:
    statuses = unit.get("statuses", {})
    words = []
    for name in ("bleed", "poison", "burn", "weak", "slow", "stun"):
        value = statuses.get(name, 0)
        if name == "stun":
            if value:
                words.append("stun")
        elif value:
            words.append("%s:%d" % (name, int(value)))
    return sorted(words)


def set_status_words(unit: Dict[str, Any], words: List[str]) -> None:
    """Replace internal statuses with the public relay representation."""
    if not isinstance(words, list) or any(not isinstance(word, str) for word in words):
        return
    statuses: Dict[str, Any] = {}
    for word in words:
        if word == "stun":
            statuses["stun"] = True
            continue
        name, separator, count = word.partition(":")
        if separator and name in ("bleed", "poison", "burn", "weak", "slow"):
            try:
                value = int(count)
            except ValueError:
                continue
            if value > 0:
                statuses[name] = value
    unit["statuses"] = statuses


def first_team_of_round(round_num: int) -> str:
    """The team that acts first in a round. Fixed: red every round (owner 2026-11-17: with an alternating opener the team that ended round r also opened round r+1, two attacks in a row)."""
    return "red"


def resolution_order(units: Dict[str, Dict[str, Any]], round_num: int) -> List[str]:
    first_team = first_team_of_round(round_num)
    teams = (first_team, "white" if first_team == "red" else "red")
    return [uid for team in teams for uid in sorted(units) if units[uid]["team"] == team]


def _hero_choices(value: Any, defaults: tuple, units: int, side: str) -> tuple:
    """Validate one side's requested hero roster without silently repeating a hero."""
    if value is None:
        choices = tuple(defaults[:units])
    elif isinstance(value, str):
        if units != 1:
            raise ValueError("%s hero must be a list of exactly %d ids" % (side, units))
        choices = (value,)
    elif isinstance(value, list):
        if len(value) != units or not all(isinstance(hero, str) for hero in value):
            raise ValueError("%s hero list must contain exactly %d ids" % (side, units))
        choices = tuple(value)
    else:
        raise ValueError("%s hero must be a hero id for 1 unit or a list of ids" % side)
    if any(hero not in HERO_TEMPLATES for hero in choices):
        raise ValueError("hero choices must be known hero ids")
    return choices


TEAM_SLOT_X = {"red": (252.0, 612.0), "white": (1296.0, 1656.0)}   # js/team_battle.js slots(): first and last slot of a team, evenly spaced, slot i is unit i


def seeded_spawn_positions(seed: int, team: str, units: int) -> List[float]:
    """Start x of every unit of a team: the page's fixed formation (js/team_battle.js `slots`), so a room that mixes the page and this engine starts from the same positions.
    One unit keeps the seeded single start of the one-versus-one game."""
    if units == 1:
        return [float(start_x(seed, 0 if team == "red" else 1, 0))]
    first, last = TEAM_SLOT_X[team]
    spacing = (last - first) / (units - 1)
    return [first + spacing * index for index in range(units)]


class GameState:
    def __init__(self, mode: str = "human_vs_agent", seed: Optional[int] = None,
                 units: int = 3, hero_red: Any = None, hero_white: Any = None):
        if units not in (1, 2, 3):
            raise ValueError("units must be 1, 2 or 3")
        actual_seed = random.randint(100000, 999999) if seed is None else seed
        if isinstance(actual_seed, bool) or not isinstance(actual_seed, int) or not 0 <= actual_seed <= 0xffffffff:
            raise ValueError("seed must be an unsigned 32-bit integer")
        red_heroes = _hero_choices(hero_red, DEFAULT_RED_HEROES, units, "red")
        white_heroes = _hero_choices(hero_white, DEFAULT_WHITE_HEROES, units, "white")
        self.match_id = "pk_match_%04d" % random.randint(1000, 9999)
        self.mode = mode
        self.seed = actual_seed
        self.rng = random.Random(self.seed)
        self.units_per_side = units
        self.hero_red = red_heroes
        self.hero_white = white_heroes
        self.round_num = 1
        self.wind = round(self.rng.uniform(WIND_MIN, WIND_MAX), 1)
        self.central_wall_hp = 100
        self.history: List[Dict[str, Any]] = []
        self.throw_seq = 0
        # Comeback pack (team matches only, shared/comeback.json): per-team count of throws since the last direct hit.
        self.pity: Dict[str, int] = {"red": 0, "white": 0}
        self._pity_now = 0   # the attacking team's count at the start of the throw being resolved
        self._cb_lock: Optional[tuple] = None   # (own share, enemy share, pity) fixed by the FIRST hit of a throw and shared by every later hit of it (page: cbBegin, index.html)
        # Coordinates are game state but never emitted by GameState's public view.
        # Each wall answers at most three enemy throws, regardless of whether a
        # stored point was crossed. The counter is private with the points.
        self.knight_walls: Dict[str, List[Dict[str, float]]] = {"red": [], "white": []}
        self.knight_wall_attacks: Dict[str, int] = {"red": 0, "white": 0}
        self.weather: Optional[Dict[str, Any]] = None
        self._started_status_teams: set = set()
        self._slow_expiring: Dict[tuple, set] = {}
        self.shields = {
            "red": {"charges": 4, "x": 420.0, "y": 430.0, "width": 80.0, "height": 140.0,
                    "active": False, "duration_rounds": 0},
            "white": {"charges": 4, "x": 1440.0, "y": 430.0, "width": 80.0, "height": 140.0,
                      "active": False, "duration_rounds": 0},
        }
        self.units: Dict[str, Dict[str, Any]] = {}
        self._setup_teams()

    def _start_x(self, team: str) -> float:
        lo, hi = START_X_RANGE[team]
        return float(round(lo + self.rng.random() * (hi - lo)))

    def _controllers(self) -> List[str]:
        count = self.units_per_side
        if self.mode == "agent_vs_agent":
            return ["subagent"] * (count * 2)
        controllers = ["human"] * count + ["subagent"] * count
        if self.mode == "random_assignment":
            self.rng.shuffle(controllers)
        return controllers

    def _setup_teams(self) -> None:
        controllers = self._controllers()
        for team, heroes, offset, facing in (("red", self.hero_red, 0, 1),
                                             ("white", self.hero_white, len(self.hero_red), -1)):
            positions = seeded_spawn_positions(self.seed, team, self.units_per_side)
            for index, hero in enumerate(heroes, 1):
                template = HERO_TEMPLATES[hero]
                # Team matches (2 or 3 units) scale unit hp (shared/team_tuning.json); one unit per team keeps the hero table value.
                unit_hp = tuning.team_max_hp(template["hp"], template["dmg"], self.units_per_side)
                unit_id = "%s_%d" % (team, index)
                self.units[unit_id] = {
                    "id": unit_id, "team": team, "hero": hero, "name": hero,
                    "controller": controllers[offset + index - 1], "facing": facing,
                    "x": positions[index - 1], "y": float(GROUND_Y), "scale": 1.0,
                    "max_hp": unit_hp, "hp": float(unit_hp),
                    "dmg": float(template["dmg"]), "weapon": template["weapon"],
                    "launch": dict(template["launch"]), "hit_box": dict(template["hitBox"]),
                    "attack_hit_box": dict(template.get("attackHitBox", template["hitBox"])),
                    "status_on_hit": dict(template["statusOnHit"]),
                    "bounce": dict(template.get("bounce", {})), "statuses": {}, "alive": True,
                    "last_throw": None,
                }

    def get_public_state(self) -> Dict[str, Any]:
        units = {}
        for uid, unit in self.units.items():
            units[uid] = {key: unit[key] for key in ("team", "name", "controller", "x", "y", "hp",
                                                       "max_hp", "alive", "weapon", "hero")}
            units[uid]["statuses"] = _status_words(unit)
        return {
            "match_id": self.match_id, "mode": self.mode, "round": self.round_num, "wind": self.wind,
            "central_wall": {"x_range": [WALL_X_MIN, WALL_X_MAX], "top_y": WALL_TOP_Y,
                             "hp": self.central_wall_hp},
            "shields": {team: dict(shield) for team, shield in self.shields.items()},
            "units": units, "landing_history": self.history[-8:],
        }

    def begin_team_turn(self, team: str) -> Dict[str, Any]:
        """Tick DoTs once, at their owner's turn start, and consume one-turn stun."""
        token = (self.round_num, team)
        if token in self._started_status_teams:
            return {"stunned": False, "ticks": []}
        self._started_status_teams.add(token)
        ticks = []
        skipped = []
        stunned = False
        for unit in self.units.values():
            if unit["team"] != team or not unit["alive"]:
                continue
            statuses = unit["statuses"]
            for name, damage in STATUS_TICK_DAMAGE.items():
                if statuses.get(name, 0) > 0:
                    dealt = min(damage, max(0.0, unit["hp"] - 1.0))
                    unit["hp"] -= dealt
                    statuses[name] -= 1
                    if not statuses[name]:
                        statuses.pop(name)
                    ticks.append({"unit": unit["id"], "status": name, "damage": dealt})
            if statuses.pop("skip", 0):
                skipped.append(unit["id"])
            if statuses.pop("stun", False):
                stunned = True
            if statuses.get("slow", 0):
                self._slow_expiring.setdefault(token, set()).add(unit["id"])
        return {"stunned": stunned, "ticks": ticks, "skipped": skipped}

    def finish_team_turn(self, team: str) -> None:
        """Slow forbids the affected team's next move, then expires with that turn."""
        token = (self.round_num, team)
        for unit_id in self._slow_expiring.pop(token, set()):
            self.units[unit_id].get("statuses", {}).pop("slow", None)

    def submit_defend(self, unit_id: str, shield_x: float, shield_y: float = 430.0) -> Dict[str, Any]:
        unit = self.units.get(unit_id)
        if unit is None:
            return {"success": False, "error": "Unknown unit %s" % unit_id}
        if unit["hero"] != "knight":
            return {"success": False, "error": "Only the Pumpkin Guard can defend"}
        if not unit["alive"]:
            return {"success": False, "error": "Unit %s is already dead" % unit_id}
        team = unit["team"]
        if self.shields[team]["charges"] <= 0:
            return {"success": False, "error": "Team %s has exhausted all 4 tactical shield charges" % team}
        x_min, x_max = (180.0, 850.0) if team == "red" else (1070.0, 1780.0)
        shield_x = max(x_min, min(x_max, float(shield_x)))
        shield_y = max(220.0, min(680.0, float(shield_y)))
        unit["pending_action"] = {"type": "defend", "shield_x": shield_x, "shield_y": shield_y}
        unit["pending_throw"] = None
        self.shields[team].update({"x": shield_x, "y": shield_y, "active": True, "duration_rounds": 2})
        return {"success": True, "unit_id": unit_id, "action": "defend", "shield_x": shield_x,
                "shield_y": shield_y, "duration_rounds": 2,
                "remaining_charges": self.shields[team]["charges"]}

    def submit_throw(self, unit_id: str, angle: float, power: float,
                     special: Optional[str] = None, damage_scale: float = 1.0,
                     second_throw: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Queue one deterministic throw, optionally with a documented skill or ultimate."""
        unit = self.units.get(unit_id)
        if unit is None:
            return {"success": False, "error": "Unknown unit %s" % unit_id}
        if not unit["alive"]:
            return {"success": False, "error": "Unit %s is already dead" % unit_id}
        angle = max(0.0, min(90.0, float(angle)))
        power = max(0.0, min(115.0, float(power)))
        unit["pending_throw"] = {"angle": angle, "power": power, "special": special,
                                 "damage_scale": max(0.0, float(damage_scale)),
                                 "second_throw": second_throw}
        return {"success": True, "unit_id": unit_id, "controller": unit["controller"],
                "angle": angle, "power": power, "status": "recorded", "special": special}

    def set_knight_wall(self, team: str, points: List[Dict[str, float]]) -> None:
        """Keep Shield Wall coordinates internal; Session filters them per seat."""
        cleaned = []
        for point in points[:3]:
            if isinstance(point, dict) and isinstance(point.get("x"), (int, float)) and isinstance(point.get("y"), (int, float)):
                cleaned.append({"x": float(point["x"]), "y": float(point["y"])})
        self.knight_walls[team] = cleaned
        self.knight_wall_attacks[team] = 0

    def _record_shield_wall_attack(self, defending_team: str) -> None:
        """Consume one of Shield Wall's three enemy-throw opportunities."""
        if not self.knight_walls[defending_team]:
            return
        self.knight_wall_attacks[defending_team] += 1
        if self.knight_wall_attacks[defending_team] >= SHIELD_WALL_EXPIRES_AFTER_ATTACKS:
            self.knight_walls[defending_team] = []
            self.knight_wall_attacks[defending_team] = 0

    @staticmethod
    def _shield_wall_contains(point: Dict[str, float], x: float, y: float) -> bool:
        return (abs(x - point["x"]) <= KNIGHT_ZONE and
                abs(y - point["y"]) <= SHIELD_WALL_COFFIN_HEIGHT / 2)

    def compute_subagent_throw(self, unit_id: str) -> Dict[str, Any]:
        unit = self.units[unit_id]
        opponents = [candidate for candidate in self.units.values()
                     if candidate["team"] != unit["team"] and candidate["alive"]]
        if not opponents:
            return {"angle": 55.0, "power": 60.0}
        target = min(opponents, key=lambda candidate: abs(candidate["x"] - unit["x"]))
        distance = abs(target["x"] - unit["x"])
        angle = 55.0
        needed_v = math.sqrt(max(100.0, distance * GRAVITY / max(0.1, math.sin(math.radians(2 * angle)))))
        wind_comp = self.wind * unit["facing"] * (-3.7 if self.wind * unit["facing"] > 0 else -5.6)
        return {"angle": angle, "power": round(max(20.0, min(115.0, needed_v / 14.0 + wind_comp +
                                                               self.rng.uniform(-3.5, 3.5))), 1)}

    def effective_wind(self) -> float:
        """The page's effWind(): the storm makes the wind stronger, its sign stays."""
        bonus = float(self.weather.get("windBonus", 0)) if isinstance(self.weather, dict) else 0.0
        return self.wind + (math.copysign(bonus, self.wind) if self.wind else 0.0)

    @staticmethod
    def projectile_radius(weapon: str) -> float:
        """Collision radius of the drawn projectile beyond the 70 px box (same formula as the page's projHitRadius)."""
        size = PROJECTILE_SIZE.get(weapon)
        if size is None or weapon == "proj_soundwave":
            return 0.0
        return max(0.0, math.sqrt(size[0] * size[1]) / 2.0 - 20.0)

    @staticmethod
    def projectile_hits(attacker: Dict[str, Any], target: Dict[str, Any], x: float, y: float) -> bool:
        wave = attacker["weapon"] == "proj_soundwave"
        box = attacker["attack_hit_box"] if wave else target["hit_box"]
        reach = GameState.projectile_radius(attacker["weapon"])
        in_box = (abs(target["x"] - x) <= box["halfWidth"] + reach and
                  target["y"] - box["height"] - reach <= y <= target["y"] + (0.0 if wave else reach))
        if not in_box or wave:
            return in_box
        # the decided box AND the figure: the drawn shot disk must touch a visible pixel (binary mask, shared/hit_masks.json, twin of js/hit_masks.js)
        masks = _hit_masks(); hero = target.get("hero")
        return masks is None or hero is None or not masks.has(hero) or masks.touches(hero, x - target["x"], y - target["y"], reach, target.get("facing", 1) > 0, True)   # armed mask always: a target is shot at on the other team's turn, when it has long been re-armed (the page re-arms 0.55 s after a throw, index.html resupply); same on the page (red-team R3A-1)

    @staticmethod
    def is_head_hit(target: Dict[str, Any], x: float, y: float) -> bool:
        box = target["hit_box"]
        return (abs(target["x"] - x) <= HEAD_HALF_WIDTH and
                y <= target["y"] - box["height"] * (1.0 - HEAD_FRACTION))

    def team_share(self, team: str) -> float:
        """HP share of a team at this moment: sum of living hp over sum of max hp."""
        return comeback.hp_share([{"hp": unit["hp"], "maxHp": unit["max_hp"]}
                                  for unit in self.units.values() if unit["team"] == team])

    def underdog_bonus(self, team: str) -> float:
        """The extra damage fraction `team` gets right now for trailing in HP share (0.0 = none)."""
        other = "white" if team == "red" else "red"
        return round(comeback.underdog_multiplier(self.team_share(team), self.team_share(other)) - 1.0, 3)

    def hit_multiplier(self, team: str) -> float:
        """The real combined damage factor of `team`'s next direct hit: min(cap, underdog x (1 + pity)), shares as of now."""
        other = "white" if team == "red" else "red"
        factor = comeback.underdog_multiplier(self.team_share(team), self.team_share(other)) * (1 + comeback.pity_bonus(self.pity[team]))
        return round(min(comeback.MAX_TOTAL, factor), 3)

    def _near_miss(self, unit: Dict[str, Any], opponent_team: str, landing_x: float, base: float) -> Optional[Dict[str, Any]]:
        """B1: a ground landing within NEAR_REACH px of the nearest living enemy box edge hits that unit for near_miss_damage;
        no crit, no status, no ultimate pip (hit_type stays "ground")."""
        if not comeback.NEAR_ENABLED:   # shared/comeback.json near_miss.enabled (reach 120 px since 2026-11-18, owner)
            return None
        best = None
        for candidate in self.units.values():
            if candidate["team"] != opponent_team or not candidate["alive"]:
                continue
            edge = max(0.0, abs(candidate["x"] - landing_x) - candidate["hit_box"]["halfWidth"])
            if best is None or edge < best[0]:
                best = (edge, candidate)
        if best is None:
            return None
        edge, victim = best
        damage = comeback.near_miss_damage(base, edge)
        if damage <= 0:
            return None
        victim["hp"] = max(0.0, round(victim["hp"] - damage, 6))   # no floating-point residue such as 1.4e-14 (twin of index.html hpAfter, ledger N7)
        victim["alive"] = victim["hp"] > 0
        return {"target": victim["id"], "damage": damage, "edge": round(edge, 1)}

    def living_teammates(self, unit: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [other for other in self.units.values()
                if other is not unit and other["team"] == unit["team"] and other["alive"]]

    def step_back_move(self, unit: Dict[str, Any], start: float, target: float) -> float:
        """The page's move rule: try the target, then step back toward `start` in 20 slices until the spot is at
        least MIN_TEAMMATE_GAP px from every living teammate; if none is free the unit stays at `start`."""
        mates = self.living_teammates(unit)
        if not mates:
            return round(target, 1)
        for k in range(20, -1, -1):
            candidate = round(start + (target - start) * k / 20.0, 1)
            if not any(abs(candidate - mate["x"]) < MIN_TEAMMATE_GAP - 1e-6 for mate in mates):
                return candidate
        return round(start, 1)

    def clamp_knockback(self, unit: Dict[str, Any], wanted: float) -> float:
        """Stop a push at the first living teammate it would come within MIN_TEAMMATE_GAP px of (never past it, never
        backwards): the result is between the unit's current x and `wanted`."""
        start = unit["x"]
        if wanted == start:
            return wanted
        direction = 1.0 if wanted > start else -1.0
        for mate in self.living_teammates(unit):
            if (mate["x"] - start) * direction > 0:
                limit = mate["x"] - direction * MIN_TEAMMATE_GAP
                wanted = min(wanted, limit) if direction > 0 else max(wanted, limit)
        return max(wanted, start) if direction > 0 else min(wanted, start)

    def _weather_damage(self, damage: float) -> float:
        if self.weather is None:
            return damage
        multiplier = self.weather.get("attackMult", 1) if isinstance(self.weather, dict) else 1
        return max(1.0, _round_tenth(damage * float(multiplier)))

    def _apply_hit(self, attacker: Dict[str, Any], target: Dict[str, Any], x: float, y: float,
                   weak_active: Optional[bool] = None, damage_scale: float = 1.0,
                   no_crit: bool = False, apply_status: bool = True) -> Dict[str, Any]:
        if weak_active is None:
            weak_active = bool(attacker["statuses"].get("weak", 0))
            if weak_active:
                attacker["statuses"]["weak"] -= 1
                if not attacker["statuses"]["weak"]:
                    attacker["statuses"].pop("weak")
        damage = self._weather_damage(attacker["dmg"] * (0.85 if weak_active else 1.0) * max(0.0, damage_scale))
        critical = not no_crit and self.is_head_hit(target, x, y)
        if critical:
            damage = _round_tenth(damage * CRIT_MULTIPLIER)
        if self.units_per_side > 1:
            # Team matches: damage = base x weather x ramp x min(cap, underdog x (1 + pity)), rounded to 0.1 once at the end (comeback_py.final_damage).
            ramp = tuning.ramp_multiplier(self.round_num, self.units_per_side)
            # The page fixes the shares and the pity charge at the first damage of a projectile and every later hit of it (blast, wave splash, swarm) uses them:
            # the same here, otherwise the second victim of one wave took less than the page's number (red-team R11B-2).
            if self._cb_lock is None:
                self._cb_lock = (self.team_share(attacker["team"]), self.team_share(target["team"]), self._pity_now)
            own_share, enemy_share, pity_count = self._cb_lock
            damage = comeback.final_damage(damage * ramp, own_share, enemy_share, pity_count)
        collisions = 1
        bounce = attacker.get("bounce", {}).get("collisions")
        if bounce:
            collisions = self.rng.randint(int(bounce["min"]), int(bounce["max"]))
            damage = _round_tenth(damage / collisions) * collisions
        target_hp_after = max(0.0, round(target["hp"] - damage, 6))   # no floating-point residue such as 1.4e-14: that unit counted as alive with 0 hp (twin of index.html hpAfter, ledger N7)
        survives = target_hp_after > 0
        if survives and apply_status:
            for name, rule in attacker["status_on_hit"].items():
                if name == "knockback":
                    continue
                turns = rule.get("turns", rule.get("throws", 1))
                target["statuses"][name] = max(target["statuses"].get(name, 0), int(turns))
            if critical and not target["statuses"].get("stun"):
                target["statuses"]["stun"] = True
        target["hp"] = target_hp_after
        target["alive"] = survives
        knockback = 0
        rule = attacker["status_on_hit"].get("knockback")
        if survives and rule:
            knockback = int(rule["pixels"])
            direction = 1 if target["x"] > attacker["x"] else -1
            lo, hi = MOVE_X_LIMITS[target["team"]]
            pushed = max(lo, min(hi, target["x"] + direction * knockback))
            target["x"] = round(self.clamp_knockback(target, pushed), 1)
        return {"damage": damage, "critical": critical, "collisions": collisions,
                "statuses": _status_words(target), "knockback": knockback}

    def _resolve_throw(self, unit: Dict[str, Any], throw: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve one projectile. Ultimate follow-up contacts stay in one throw record."""
        team = unit["team"]
        special = throw.get("special")
        weak_active = bool(unit["statuses"].get("weak", 0))
        if weak_active:
            unit["statuses"]["weak"] -= 1
            if not unit["statuses"]["weak"]:
                unit["statuses"].pop("weak")
        angle = math.radians(throw["angle"])
        speed = throw["power"] * V0_PER_POWER
        vx, vy = speed * math.cos(angle) * unit["facing"], -speed * math.sin(angle)
        cur_x = float(unit["x"] + unit["launch"]["fwd"] * unit["facing"])
        cur_y = float(unit["y"] - unit["launch"]["up"])
        hit_type, hit_target = "ground", None
        landed = False
        self._pity_now = self.pity[team] if self.units_per_side > 1 else 0
        self._cb_lock = None
        outcome = {"damage": 0.0, "critical": False, "collisions": 0, "statuses": [], "knockback": 0}
        self.throw_seq += 1
        throw_id = self.throw_seq

        opponent_team = "white" if team == "red" else "red"
        # An enemy throw counts even if it misses, hits the central fence, or is
        # shield-bypassing. Expiry happens after this throw has had its chance
        # to cross one hidden point.
        shield_wall_was_active = bool(self.knight_walls[opponent_team])

        def apply(target: Dict[str, Any], scale: float = 1.0, no_crit: bool = False,
                  apply_status: bool = True) -> Dict[str, Any]:
            return self._apply_hit(unit, target, cur_x, cur_y, weak_active, scale * throw.get("damage_scale", 1.0),
                                   no_crit, apply_status)

        def blast_victims() -> List[Dict[str, Any]]:
            """Living enemy units inside the wizard blast, nearest to the impact point first (page rule, 234 px)."""
            near = [candidate for candidate in self.units.values()
                    if candidate["team"] == opponent_team and candidate["alive"] and
                    abs(candidate["x"] - cur_x) <= BLAST_RADIUS]
            return sorted(near, key=lambda candidate: abs(candidate["x"] - cur_x))

        eff_wind = self.effective_wind()
        for _step in range(300):
            # the page's flight step (js/flight.js, index.html): wind is a constant ACCELERATION on vx (tail 56, head 84 per wind unit, storm adds its bonus), then gravity, then the move
            vx += eff_wind * (_WIND_TAIL if eff_wind * unit["facing"] > 0 else _WIND_HEAD) / 60.0
            vy += GRAVITY / 60.0
            prev_x, prev_y = cur_x, cur_y
            cur_x += vx / 60.0
            cur_y += vy / 60.0
            if unit["weapon"] == "proj_soundwave" and prev_y < GROUND_Y < cur_y:   # twin of the page (index.html tCross, owner 2026-11-17 and 2026-11-19): the wave counts where it REALLY lands, the frame that crosses the ground is cut back to the crossing point
                t_cross = (GROUND_Y - prev_y) / (cur_y - prev_y)
                cur_x = prev_x + (cur_x - prev_x) * t_cross
                cur_y = float(GROUND_Y)
            if self.central_wall_hp > 0:   # swept like the page, for every weapon (the wave too): the first sub-point (every 3 px) of the step inside the fence is the hit point (a corner clip between two end points still hits)
                end_wx, end_wy = cur_x, cur_y
                n_wall = max(1, math.ceil(math.hypot(end_wx - prev_x, end_wy - prev_y) / 1.5))
                for k in range(1, n_wall):
                    qx, qy = prev_x + (end_wx - prev_x) * k / n_wall, prev_y + (end_wy - prev_y) * k / n_wall
                    if WALL_X_MIN <= qx <= WALL_X_MAX and qy >= WALL_TOP_Y:
                        cur_x, cur_y = qx, qy
                        break
            if self.central_wall_hp > 0 and WALL_X_MIN <= cur_x <= WALL_X_MAX and cur_y >= WALL_TOP_Y:
                hit_type = "central_wall"
                self.central_wall_hp = max(0, self.central_wall_hp - WALL_HIT_DMG)
                break
            # Shield Wall is an actual coffin-sized intercept, not a vertical
            # infinite line. Hunchback's boomerang is shield-bypassing before
            # this check, like the page's floating shield rule.
            wall = self.knight_walls[opponent_team]
            wall_index = (None if special == "hunchback" else next(
                (i for i, point in enumerate(wall)
                 if self._shield_wall_contains(point, cur_x, cur_y)), None))
            if wall_index is not None:
                wall.pop(wall_index)
                hit_type, hit_target = "ultimate_blocked", opponent_team + "_shield_wall"
                break
            shield = self.shields[opponent_team]
            if special != "hunchback" and shield["active"] and shield["charges"] > 0 and abs(cur_x - shield["x"]) <= shield["width"] / 2 and abs(cur_y - shield["y"]) <= shield["height"] / 2:
                hit_type, hit_target = "shield_blocked", opponent_team + "_shield"
                shield["charges"] -= 1
                break
            # SWEPT CONTACT (twin of the page, owner 2026-11-18: a fast shot must not fly through a unit): the shot is tested at points every 3 px along the step it just made (the bride's wave keeps one test);
            # the first touching point is where it hits
            end_x, end_y = cur_x, cur_y
            n_sub = 1 if unit["weapon"] == "proj_soundwave" else max(1, math.ceil(math.hypot(end_x - prev_x, end_y - prev_y) / 3.0))
            touched = []
            for k in range(1, n_sub + 1):
                if k < n_sub:
                    cur_x, cur_y = prev_x + (end_x - prev_x) * k / n_sub, prev_y + (end_y - prev_y) * k / n_sub
                else:
                    cur_x, cur_y = end_x, end_y
                touched = [candidate for candidate in self.units.values()
                           if candidate["team"] == opponent_team and candidate["alive"] and
                           self.projectile_hits(unit, candidate, cur_x, cur_y)]
                if touched:
                    break
            if not touched:
                cur_x, cur_y = end_x, end_y
            # two boxes touched in the same step: the one nearest to the projectile is hit first (same rule as the page, docs/TEAM_RULES_20261117.md rule 4)
            target = min(touched, key=lambda candidate: abs(cur_x - candidate["x"])) if touched else None
            if target is not None:
                hit_type, hit_target = "hero", target["id"]
                if special == "bat":
                    hits = [apply(target, 1.5 / 5) for _ in range(5) if target["alive"]]
                elif special == "skeleton":
                    hits = [apply(target, 1.5 / 3) for _ in range(3) if target["alive"]]
                elif special == "reaper":
                    hits = [apply(target, scale, True) for scale in (0.55, 0.65, 0.75) if target["alive"]]
                    if hits:
                        target["statuses"]["skip"] = 1
                elif special == "hag":
                    hits = [apply(target, 0.575, True) for _ in range(2) if target["alive"]]
                    touched = [target]
                    if hits and target["alive"]:
                        # The page's random-looking selection derives from the shared
                        # contract, never a fresh local RNG draw.
                        chosen = touched[nun_stun_pick(int(self.seed), self.round_num, throw_id, len(touched))]
                        chosen["statuses"]["stun"] = True
                elif special == "wizard":
                    # The shell deals its normal contact damage, then the blast (page `ultBlast`: flat
                    # 1.5 x normal, no crit) hits every living enemy unit within BLAST_RADIUS of that impact point.
                    hits = [apply(target)]
                    for candidate in blast_victims():
                        hits.append(apply(candidate, BLAST_MULTIPLIER, True, False))
                elif special == "hunchback":
                    hits = [apply(target, 1.0, True)]
                    if target["alive"]:
                        hits.append(apply(target, 1.5, True))
                elif special == "bride" or (special is None and unit["weapon"] == "proj_soundwave"):
                    # The wave is an area effect (page): the touched unit and every other living enemy unit
                    # within 105 px of the wave centre take the stepped 100/75/50 percent damage of their own distance.
                    hits = [apply(target, wave_multiplier(abs(target["x"] - cur_x)))]
                    for candidate in self.units.values():
                        if candidate is target or candidate["team"] != opponent_team or not candidate["alive"]:
                            continue
                        factor = wave_multiplier(abs(candidate["x"] - cur_x))
                        if factor:
                            hits.append(apply(candidate, factor, True))
                    if special == "bride" and target["alive"]:
                        # Ultimate: a precise hit calls the bat swarm on EVERY living enemy unit, at any distance, no status.
                        for candidate in self.units.values():
                            if candidate["team"] == opponent_team and candidate["alive"]:
                                hits.append(apply(candidate, SWARM_MULTIPLIER, True, False))
                else:
                    hits = [apply(target)]
                outcome["damage"] = _round_tenth(sum(item["damage"] for item in hits))
                outcome["critical"] = any(item["critical"] for item in hits)
                outcome["collisions"] = sum(item["collisions"] for item in hits)
                outcome["statuses"] = _status_words(target)
                outcome["knockback"] = sum(item["knockback"] for item in hits)
                break
            if cur_y >= GROUND_Y:
                cur_y = float(GROUND_Y)
                landed = True
                if special == "wizard":
                    victims = blast_victims()
                    hits = [apply(candidate, BLAST_MULTIPLIER, True, False) for candidate in victims]
                    if hits:
                        hit_type = "hero"
                        hit_target = ",".join(candidate["id"] for candidate in victims)
                        outcome["damage"] = _round_tenth(sum(item["damage"] for item in hits))
                        outcome["collisions"] = sum(item["collisions"] for item in hits)
                break
        if special == "wizard" and hit_type in ("central_wall", "shield_blocked", "ultimate_blocked"):
            # page: `hit && p.ultBlast` also fires when the shell stops on the fence or a shield; hit_type stays the blocking kind
            hits = [apply(candidate, BLAST_MULTIPLIER, True, False) for candidate in blast_victims()]
            if hits:
                outcome["damage"] = _round_tenth(sum(item["damage"] for item in hits))
                outcome["collisions"] = sum(item["collisions"] for item in hits)
        near_miss = None
        if self.units_per_side > 1:
            if landed and hit_type == "ground":
                base = unit["dmg"] * (0.85 if weak_active else 1.0) * max(0.0, throw.get("damage_scale", 1.0))
                near_miss = self._near_miss(unit, opponent_team, cur_x, base)
            # B3: a direct hit uses the pity charge and resets it; every other throw (near miss included) adds one
            self.pity[team] = 0 if hit_type == "hero" else self.pity[team] + 1
            self._pity_now = 0
        if shield_wall_was_active:
            self._record_shield_wall_attack(opponent_team)
        report_target = next((candidate for candidate in self.units.values()
                              if candidate["team"] == opponent_team), unit)
        if hit_target in self.units:
            report_target = self.units[hit_target]
        elif isinstance(hit_target, str) and hit_target.split(",")[0] in self.units:
            report_target = self.units[hit_target.split(",")[0]]   # blast list: the unit nearest to the impact point
        report = hit_report(cur_x, report_target["x"], hit_type, unit["weapon"])
        record = {"unit_id": unit["id"], "team": team, "controller": unit["controller"],
                "angle": throw["angle"], "power": throw["power"],
                "landing_x": round(cur_x, 1), "landing_y": round(cur_y, 1),
                "hit_type": hit_type, "hit_target": hit_target,
                "damage_dealt": outcome["damage"], "critical": outcome["critical"],
                "collision_count": outcome["collisions"], "statuses": outcome["statuses"],
                "knockback": outcome["knockback"], "hit_report": report, "throw_id": throw_id,
                "ultimate": special is not None,
                "_launch": {"x": unit["x"], "y": unit["y"], "facing": unit["facing"],
                            "launch": dict(unit["launch"])} }
        if near_miss is not None:
            record["near_miss"] = near_miss   # team matches only
        return record

    def resolve_round(self) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        for uid, unit in self.units.items():
            if unit["alive"] and unit.get("pending_throw") is None and unit["controller"] == "subagent":
                unit["pending_throw"] = self.compute_subagent_throw(uid)
        started = set()
        skipped_units = set()
        for uid in resolution_order(self.units, self.round_num):
            unit = self.units[uid]
            team = unit["team"]
            if team not in started:
                start_report = self.begin_team_turn(team)
                skipped_units.update(start_report.get("skipped", []))
                started.add(team)
            if uid in skipped_units or not unit["alive"] or not unit.get("pending_throw"):
                continue
            throw = unit["pending_throw"]
            results.append(self._resolve_throw(unit, throw))
            second = throw.get("second_throw")
            if unit["alive"] and isinstance(second, dict):
                results.append(self._resolve_throw(unit, second))
            self.history.extend(results[-(2 if unit["alive"] and isinstance(second, dict) else 1):])
            unit["pending_throw"] = None
        for team in ("red", "white"):
            if team in started:
                self.finish_team_turn(team)
        for uid, unit in self.units.items():
            action = unit.pop("pending_action", None)
            if action and unit["alive"] and action.get("type") == "defend":
                results.append({"unit_id": uid, "team": unit["team"], "controller": unit["controller"],
                                "action": "defend", "shield_x": action["shield_x"],
                                "remaining_charges": self.shields[unit["team"]]["charges"]})
        for shield in self.shields.values():
            if shield["active"]:
                shield["duration_rounds"] -= 1
                if shield["duration_rounds"] <= 0:
                    shield["active"] = False
        self.round_num += 1
        self._started_status_teams.clear()
        self.wind = round(self.rng.uniform(WIND_MIN, WIND_MAX), 1)
        red_alive = any(unit["alive"] for unit in self.units.values() if unit["team"] == "red")
        white_alive = any(unit["alive"] for unit in self.units.values() if unit["team"] == "white")
        winner = "draw" if not red_alive and not white_alive else ("white" if not red_alive else
                 ("red" if not white_alive else None))
        reason = None
        if winner is None and self.round_num > tuning.round_cap(self.units_per_side):
            # Team matches have a round limit: the round counter has passed the cap, the larger hp share wins (shared/team_tuning.json).
            sides = {"left": "red", "right": "white"}
            teams = {side: [{"hp": unit["hp"], "maxHp": unit["max_hp"]}
                            for unit in self.units.values() if unit["team"] == team]
                     for side, team in sides.items()}
            winner = sides[tuning.cap_winner(teams)]
            reason = "round_cap"
        result = {"round_resolved": self.round_num - 1, "next_round": self.round_num,
                  "new_wind": self.wind, "results": results, "winner": winner}
        if reason is not None:
            result["winner_reason"] = reason
        return result


GAME_INSTANCE = GameState(mode="human_vs_agent")


def handle_mcp_request(req: Dict[str, Any]) -> Dict[str, Any]:
    global GAME_INSTANCE
    method, params, req_id = req.get("method", ""), req.get("params", {}), req.get("id", 1)
    if method == "get_public_state":
        result = GAME_INSTANCE.get_public_state()
    elif method == "set_match_mode":
        GAME_INSTANCE = GameState(mode=params.get("mode", "human_vs_agent"), seed=params.get("seed"),
                                  units=params.get("units", 3), hero_red=params.get("hero_red"),
                                  hero_white=params.get("hero_white"))
        result = {"status": "ok", "mode": GAME_INSTANCE.mode, "match_id": GAME_INSTANCE.match_id}
    elif method == "submit_throw":
        result = GAME_INSTANCE.submit_throw(params.get("unit_id"), params.get("angle", 45), params.get("power", 50))
    elif method == "submit_defend":
        result = GAME_INSTANCE.submit_defend(params.get("unit_id"), params.get("shield_x", 380), params.get("shield_y", 430))
    elif method == "resolve_round":
        result = GAME_INSTANCE.resolve_round()
    else:
        return {"jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": "Method %s not found" % method}}
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", action="store_true", help="run a short local engine demonstration")
    parser.add_argument("--units", type=int, default=3)
    parser.add_argument("--hero-red", nargs="+", choices=sorted(HERO_TEMPLATES), default=None,
                        help="one hero id for --units 1, otherwise exactly one id per red unit")
    parser.add_argument("--hero-white", nargs="+", choices=sorted(HERO_TEMPLATES), default=None,
                        help="one hero id for --units 1, otherwise exactly one id per white unit")
    args = parser.parse_args(argv)
    if args.cli:
        game = GameState(seed=1, units=args.units, hero_red=args.hero_red, hero_white=args.hero_white)
        print(json.dumps(game.get_public_state(), ensure_ascii=False, indent=2))
        return 0
    for line in sys.stdin:
        try:
            request = json.loads(line)
            print(json.dumps(handle_mcp_request(request), ensure_ascii=False), flush=True)
        except (TypeError, ValueError) as exc:
            sys.stderr.write("Error handling request: %s\n" % exc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
