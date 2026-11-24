#!/usr/bin/env python3
"""Pumpkin Killer — SVG Scene Generator & GIF Baker.

Features:
- Full 1920x1080 battlefield vector placeholders.
- 100% compliant with user's core directions:
  1. NO stray projectiles or magic balls floating in the air.
  2. True throwing kinematics (windup -> release at hand -> ballistic flight).
  3. Tactical Pumpkin Shield (<||>) with 4 technical prediction uses per match.
  4. Movable defense slider intercepts incoming projectiles.
  5. Cat vs Dog wind physics and central graveyard barrier.
- Converts SVG frames to animated GIF via headless Chrome rendering and PIL assembly.
"""
import os
import sys
import math
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

OUTPUT_DIR = os.environ.get("PK_GIF_OUTPUT_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "gifs"))
FRAMES_DIR = "/tmp/svg_scene_frames"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TOTAL_FRAMES = 32

def generate_svg_frame(frame_idx: int) -> str:
    # Trajectory parameters
    # Skeleton at (320, 848) throws spear to (1600, 840)
    # White Shield moves from 1440 to 1600 between frame 5 and 11
    
    # Shield animation
    if frame_idx < 5:
        white_shield_x = 1440.0
        white_shield_sliding = False
    elif frame_idx <= 11:
        prog = (frame_idx - 5) / 6.0
        white_shield_x = 1440.0 + (1600.0 - 1440.0) * prog
        white_shield_sliding = True
    else:
        white_shield_x = 1600.0
        white_shield_sliding = False

    white_shield_charges = 4 if frame_idx < 26 else 3

    # Skeleton Thrower animation
    # 0..10: Idle stance
    # 11..13: Windup / backswing (lean back, spear pulled back)
    # 14: Release apex (spear leaves hand)
    # 15..31: Follow-through & recovery
    
    skeleton_throw_prog = 0.0
    if frame_idx in (11, 12, 13):
        skeleton_throw_prog = -1.0 # Backswing
    elif frame_idx == 14:
        skeleton_throw_prog = 1.0  # Whiplash release
    elif frame_idx > 14:
        skeleton_throw_prog = 0.2  # Rest / recovery

    # Projectile flight: active from frame 14 to 26
    proj_active = False
    proj_x, proj_y, proj_rot = 0.0, 0.0, 0.0
    impact_active = False

    if 14 <= frame_idx <= 26:
        proj_active = True
        t = (frame_idx - 14) / 12.0  # 0.0 to 1.0
        # Ballistic trajectory: start (345, 785), apex around (970, 380), land at (1600, 825)
        # Parabolic interpolation
        x0, y0 = 345.0, 785.0
        x1, y1 = 1600.0, 825.0
        apex_h = 420.0 # Height of apex above baseline
        
        proj_x = x0 + (x1 - x0) * t
        # Standard parabola: 4 * h * t * (1 - t)
        proj_y = y0 + (y1 - y0) * t - 4.0 * apex_h * t * (1.0 - t)
        
        # Tangent angle for spear rotation
        # dx/dt = (x1 - x0)
        # dy/dt = (y1 - y0) - 4 * apex_h * (1 - 2t)
        dx = x1 - x0
        dy = (y1 - y0) - 4.0 * apex_h * (1.0 - 2.0 * t)
        proj_rot = math.degrees(math.atan2(dy, dx))

    if 26 <= frame_idx <= 29:
        impact_active = True
        impact_t = (frame_idx - 26) / 3.0

    # Build SVG content
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 1920 1080">
  <defs>
    <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0a0514"/>
      <stop offset="50%" stop-color="#140b24"/>
      <stop offset="100%" stop-color="#231338"/>
    </linearGradient>
    <linearGradient id="groundGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1b122c"/>
      <stop offset="100%" stop-color="#0d0818"/>
    </linearGradient>
    <linearGradient id="wallGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3d374d"/>
      <stop offset="50%" stop-color="#2b2638"/>
      <stop offset="100%" stop-color="#1b1724"/>
    </linearGradient>
    <linearGradient id="shieldGradRed" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#e67e22" stop-opacity="0.9"/>
      <stop offset="50%" stop-color="#f39c12" stop-opacity="0.7"/>
      <stop offset="100%" stop-color="#e67e22" stop-opacity="0.9"/>
    </linearGradient>
    <linearGradient id="shieldGradWhite" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#00cec9" stop-opacity="0.9"/>
      <stop offset="50%" stop-color="#81ecec" stop-opacity="0.7"/>
      <stop offset="100%" stop-color="#00cec9" stop-opacity="0.9"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <filter id="heavyGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="14" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>

  <!-- Sky Background -->
  <rect width="1920" height="1080" fill="url(#skyGrad)"/>

  <!-- Distant Spooky Elements -->
  <circle cx="960" cy="180" r="70" fill="#ffeaa7" opacity="0.35" filter="url(#heavyGlow)"/>
  <circle cx="960" cy="180" r="62" fill="#fff9d2" opacity="0.85"/>
  <circle cx="940" cy="165" r="14" fill="#fae89c" opacity="0.5"/>
  <circle cx="985" cy="195" r="18" fill="#fae89c" opacity="0.5"/>

  <!-- Mountain Silhouettes -->
  <path d="M0 880 L180 620 L400 750 L680 580 L900 720 L1150 560 L1400 700 L1680 590 L1920 730 L1920 880 Z" fill="#130921" opacity="0.6"/>

  <!-- Ground Line -->
  <rect x="0" y="880" width="1920" height="200" fill="url(#groundGrad)"/>
  <line x1="0" y1="880" x2="1920" y2="880" stroke="#7158e2" stroke-width="3" opacity="0.5"/>

  <!-- Central Graveyard Wall (x: 890 to 1030, y: 720 to 880, height: 160) -->
  <g transform="translate(890, 720)">
    <rect x="0" y="0" width="140" height="160" rx="8" fill="url(#wallGrad)" stroke="#4a415a" stroke-width="3"/>
    <!-- Stone brick lines -->
    <line x1="0" y1="40" x2="140" y2="40" stroke="#1d1926" stroke-width="2"/>
    <line x1="0" y1="80" x2="140" y2="80" stroke="#1d1926" stroke-width="2"/>
    <line x1="0" y1="120" x2="140" y2="120" stroke="#1d1926" stroke-width="2"/>
    <line x1="70" y1="0" x2="70" y2="40" stroke="#1d1926" stroke-width="2"/>
    <line x1="35" y1="40" x2="35" y2="80" stroke="#1d1926" stroke-width="2"/>
    <line x1="105" y1="40" x2="105" y2="80" stroke="#1d1926" stroke-width="2"/>
    <line x1="70" y1="80" x2="70" y2="120" stroke="#1d1926" stroke-width="2"/>
    <!-- Gothic Spikes on Top -->
    <polygon points="15,0 25,-25 35,0" fill="#2c2738" stroke="#4a415a" stroke-width="1.5"/>
    <polygon points="60,0 70,-35 80,0" fill="#2c2738" stroke="#4a415a" stroke-width="1.5"/>
    <polygon points="105,0 115,-25 125,0" fill="#2c2738" stroke="#4a415a" stroke-width="1.5"/>
    <!-- Pumpkin Lantern on Wall -->
    <circle cx="70" cy="-45" r="16" fill="#e67e22"/>
    <polygon points="65,-48 68,-45 62,-45" fill="#f1c40f"/>
    <polygon points="75,-48 78,-45 72,-45" fill="#f1c40f"/>
    <path d="M64 -40 Q70 -35 76 -40 Z" fill="#f1c40f"/>
    <!-- Wall HUD Label -->
    <rect x="-10" y="55" width="160" height="26" rx="6" fill="#100b1a" stroke="#ff7675" stroke-width="1.5"/>
    <text x="70" y="73" fill="#ff7675" font-size="12" font-weight="bold" text-anchor="middle">中央墓地障礙牆 (H:160)</text>
  </g>

  <!-- ================= TOP HUD ================= -->
  <rect x="0" y="0" width="1920" height="90" fill="#100a1c" stroke="#3d2358" stroke-width="3"/>
  
  <!-- Red Team HUD (Left) -->
  <g transform="translate(40, 16)">
    <text x="0" y="22" fill="#ff5252" font-size="20" font-weight="bold">🔴 RED TEAM (人類玩家)</text>
    <rect x="0" y="34" width="360" height="22" rx="5" fill="#2c1620"/>
    <rect x="0" y="34" width="360" height="22" rx="5" fill="#d63031"/>
    <text x="180" y="50" fill="#fff" font-size="13" font-weight="bold" text-anchor="middle">HP: 395 / 395 (4 員存活)</text>
    <rect x="0" y="60" width="220" height="22" rx="4" fill="#3a1c1c" stroke="#ff7675" stroke-width="1"/>
    <text x="110" y="76" fill="#ffb8b8" font-size="12" font-weight="bold" text-anchor="middle">🛡️ 戰術預判南瓜盾: [4/4] 次</text>
  </g>

  <!-- Cat vs Dog Center Wind Gauge -->
  <g transform="translate(760, 10)">
    <rect x="0" y="0" width="400" height="74" rx="10" fill="#1c102e" stroke="#ffd32a" stroke-width="2.5" filter="url(#glow)"/>
    <text x="200" y="24" fill="#ffd32a" font-size="15" font-weight="bold" text-anchor="middle">第 1 回合 ｜ 行動: 骷髏長矛兵</text>
    <rect x="50" y="36" width="300" height="22" rx="6" fill="#0d0717"/>
    <line x1="200" y1="36" x2="200" y2="58" stroke="#7158e2" stroke-width="2"/>
    <!-- Wind Indicator +2.8 to Right -->
    <rect x="200" y="38" width="80" height="18" rx="4" fill="#4deeea" filter="url(#glow)"/>
    <text x="200" y="52" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">風力: +2.8 東風 ➔</text>
  </g>

  <!-- White Team HUD (Right) -->
  <g transform="translate(1420, 16)">
    <text x="460" y="22" fill="#00cec9" font-size="20" font-weight="bold" text-anchor="end">⚪ WHITE TEAM (子代理 AI)</text>
    <rect x="100" y="34" width="360" height="22" rx="5" fill="#102528"/>
    <rect x="100" y="34" width="360" height="22" rx="5" fill="#00b894"/>
    <text x="280" y="50" fill="#fff" font-size="13" font-weight="bold" text-anchor="middle">HP: 395 / 395 (4 員存活)</text>
    <rect x="240" y="60" width="220" height="22" rx="4" fill="#123533" stroke="#00cec9" stroke-width="1"/>
    <text x="350" y="76" fill="#81ecec" font-size="12" font-weight="bold" text-anchor="middle">🛡️ 戰術預判南瓜盾: [{white_shield_charges}/4] 次</text>
  </g>

  <!-- ================= RED TEAM HEROES (Facing Right) ================= -->

  <!-- Red 1: Bat Scout (200, 840) -->
  <g transform="translate(170, 750)">
    <ellipse cx="30" cy="90" rx="35" ry="10" fill="#6c5ce7" opacity="0.3"/>
    <rect x="12" y="35" width="36" height="52" rx="8" fill="#2d3436" stroke="#9b59b6" stroke-width="2.5"/>
    <polygon points="12,35 22,12 28,35" fill="#2d3436"/>
    <polygon points="48,35 38,12 32,35" fill="#2d3436"/>
    <circle cx="30" cy="42" r="14" fill="#34495e"/>
    <circle cx="25" cy="40" r="3" fill="#f1c40f"/>
    <circle cx="35" cy="40" r="3" fill="#f1c40f"/>
    <rect x="-10" y="-8" width="80" height="20" rx="10" fill="#1b1430" stroke="#9b59b6" stroke-width="1.5"/>
    <text x="30" y="6" fill="#fff" font-size="11" font-weight="bold" text-anchor="middle">蝙蝠刺客</text>
  </g>

  <!-- Red 2: Skeleton Spearman (320, 848) - The Active Thrower! -->
  <g transform="translate(290, 758)">
    <ellipse cx="30" cy="90" rx="35" ry="10" fill="#00d2d3" opacity="0.4" filter="url(#glow)"/>
    <!-- Skeleton body with kinematic throw pose -->
    '''

    # Skeleton Pose dynamically transforms during throw
    if skeleton_throw_prog == -1.0:
        # Windup: lean back
        svg += f'''
    <g transform="rotate(-15 30 70)">
      <rect x="15" y="32" width="30" height="55" rx="6" fill="#2c3e50" stroke="#ecf0f1" stroke-width="2"/>
      <circle cx="30" cy="20" r="15" fill="#ecf0f1"/>
      <circle cx="26" cy="18" r="3" fill="#00cec9"/>
      <circle cx="34" cy="18" r="3" fill="#00cec9"/>
      <!-- Spear in hand pulled back -->
      <line x1="-15" y1="20" x2="35" y2="45" stroke="#00cec9" stroke-width="4" stroke-linecap="round"/>
      <polygon points="-22,16 -12,25 -10,15" fill="#81ecec"/>
    </g>
    <rect x="-15" y="-14" width="90" height="22" rx="11" fill="#00cec9"/>
    <text x="30" y="2" fill="#000" font-size="11" font-weight="bold" text-anchor="middle">投擲蓄力中</text>
        '''
    elif skeleton_throw_prog == 1.0:
        # Whiplash release: forward thrust
        svg += f'''
    <g transform="rotate(18 30 70)">
      <rect x="15" y="32" width="30" height="55" rx="6" fill="#2c3e50" stroke="#ecf0f1" stroke-width="2"/>
      <circle cx="30" cy="20" r="15" fill="#ecf0f1"/>
      <circle cx="26" cy="18" r="3" fill="#00cec9"/>
      <circle cx="34" cy="18" r="3" fill="#00cec9"/>
      <!-- Empty arm extended forward (spear released!) -->
      <line x1="30" y1="42" x2="55" y2="28" stroke="#ecf0f1" stroke-width="4" stroke-linecap="round"/>
    </g>
    <rect x="-15" y="-14" width="90" height="22" rx="11" fill="#ffeaa7"/>
    <text x="30" y="2" fill="#000" font-size="11" font-weight="bold" text-anchor="middle">標槍脫手！</text>
        '''
    else:
        # Normal stance
        svg += f'''
    <rect x="15" y="32" width="30" height="55" rx="6" fill="#2c3e50" stroke="#ecf0f1" stroke-width="2"/>
    <circle cx="30" cy="20" r="15" fill="#ecf0f1"/>
    <circle cx="26" cy="18" r="3" fill="#00cec9"/>
    <circle cx="34" cy="18" r="3" fill="#00cec9"/>
    <!-- Holding spear resting upright (only when before throw) -->
    ''' + ('''<line x1="35" y1="75" x2="35" y2="10" stroke="#00cec9" stroke-width="3.5" stroke-linecap="round"/>
    <polygon points="31,12 39,12 35,0" fill="#81ecec"/>''' if frame_idx < 11 else '''<line x1="28" y1="45" x2="42" y2="55" stroke="#ecf0f1" stroke-width="3"/>''') + f'''
    <rect x="-10" y="-8" width="80" height="20" rx="10" fill="#1b1430" stroke="#00cec9" stroke-width="1.5"/>
    <text x="30" y="6" fill="#81ecec" font-size="11" font-weight="bold" text-anchor="middle">骷髏長矛兵</text>
        '''

    svg += f'''
  </g>

  <!-- Red 3: Pumpkin Knight (440, 870) -->
  <g transform="translate(410, 780)">
    <ellipse cx="30" cy="90" rx="38" ry="10" fill="#e67e22" opacity="0.3"/>
    <rect x="10" y="25" width="45" height="65" rx="8" fill="#2c3e50" stroke="#e67e22" stroke-width="2.5"/>
    <circle cx="32" cy="18" r="18" fill="#e67e22"/>
    <polygon points="26,14 29,18 23,18" fill="#f1c40f"/>
    <polygon points="38,14 41,18 35,18" fill="#f1c40f"/>
    <path d="M26 24 Q32 28 38 24 Z" fill="#f1c40f"/>
    <rect x="-10" y="-10" width="85" height="20" rx="10" fill="#1b1430" stroke="#e67e22" stroke-width="1.5"/>
    <text x="32" y="4" fill="#e67e22" font-size="11" font-weight="bold" text-anchor="middle">南瓜盾衛</text>
  </g>

  <!-- Red 4: Pumpkin Wizard Mortar (560, 885) -->
  <!-- Note: EMPTY barrel muzzle! No floating magic ball! -->
  <g transform="translate(530, 795)">
    <ellipse cx="30" cy="90" rx="38" ry="10" fill="#ff7675" opacity="0.3"/>
    <rect x="10" y="30" width="42" height="60" rx="8" fill="#341f47" stroke="#ff7675" stroke-width="2"/>
    <polygon points="8,30 31, -2 54,30" fill="#2c163b"/>
    <ellipse cx="31" cy="30" rx="28" ry="7" fill="#4a2363"/>
    <!-- Brass Mortar Cannon (pointed cleanly forward, NO stray ball) -->
    <rect x="25" y="38" width="40" height="14" rx="4" fill="#d35400" transform="rotate(-35 30 45)"/>
    <rect x="-10" y="-12" width="85" height="20" rx="10" fill="#1b1430" stroke="#ff7675" stroke-width="1.5"/>
    <text x="32" y="2" fill="#ff7675" font-size="11" font-weight="bold" text-anchor="middle">巫師迫擊砲</text>
  </g>

  <!-- Red Team's Movable Pumpkin Shield <||> (Standby at x=380) -->
  <g transform="translate(380, 810)">
    <rect x="0" y="0" width="80" height="85" rx="14" fill="url(#shieldGradRed)" stroke="#ffffff" stroke-width="2.5" opacity="0.85"/>
    <circle cx="40" cy="36" r="18" fill="#e65100"/>
    <polygon points="34,32 37,36 31,36" fill="#f1c40f"/>
    <polygon points="46,32 49,36 43,36" fill="#f1c40f"/>
    <path d="M34 42 Q40 46 46 42 Z" fill="#f1c40f"/>
    <!-- Tactile Grips < || > -->
    <text x="12" y="44" fill="#ffffff" font-size="20" font-weight="bold">&lt;</text>
    <line x1="37" y1="62" x2="37" y2="74" stroke="#ffffff" stroke-width="2"/>
    <line x1="43" y1="62" x2="43" y2="74" stroke="#ffffff" stroke-width="2"/>
    <text x="68" y="44" fill="#ffffff" font-size="20" font-weight="bold">&gt;</text>
    <rect x="-10" y="90" width="100" height="18" rx="4" fill="#100a1c" stroke="#e67e22" stroke-width="1"/>
    <text x="40" y="103" fill="#ffb8b8" font-size="10" font-weight="bold" text-anchor="middle">紅隊防禦滑塊</text>
  </g>

  <!-- ================= WHITE TEAM HEROES (Facing Left) ================= -->

  <!-- White 1: Pumpkin Wizard Mortar (1360, 885) -->
  <g transform="translate(1330, 795)">
    <ellipse cx="30" cy="90" rx="38" ry="10" fill="#ff7675" opacity="0.3"/>
    <rect x="10" y="30" width="42" height="60" rx="8" fill="#341f47" stroke="#d2dae2" stroke-width="2"/>
    <polygon points="8,30 31, -2 54,30" fill="#2c163b"/>
    <ellipse cx="31" cy="30" rx="28" ry="7" fill="#4a2363"/>
    <!-- Cannon pointed left, NO stray magic ball -->
    <rect x="-5" y="38" width="40" height="14" rx="4" fill="#d35400" transform="rotate(35 30 45)"/>
    <rect x="-10" y="-12" width="85" height="20" rx="10" fill="#1b1430" stroke="#d2dae2" stroke-width="1.5"/>
    <text x="32" y="2" fill="#d2dae2" font-size="11" font-weight="bold" text-anchor="middle">敵方 AI 巫師</text>
  </g>

  <!-- White 2: Pumpkin Knight (1480, 870) -->
  <g transform="translate(1450, 780)">
    <ellipse cx="30" cy="90" rx="38" ry="10" fill="#d2dae2" opacity="0.3"/>
    <rect x="10" y="25" width="45" height="65" rx="8" fill="#2c3e50" stroke="#d2dae2" stroke-width="2"/>
    <circle cx="32" cy="18" r="18" fill="#d2dae2"/>
    <polygon points="26,14 29,18 23,18" fill="#2c3e50"/>
    <polygon points="38,14 41,18 35,18" fill="#2c3e50"/>
    <path d="M26 24 Q32 28 38 24 Z" fill="#2c3e50"/>
    <rect x="-10" y="-10" width="85" height="20" rx="10" fill="#1b1430" stroke="#d2dae2" stroke-width="1.5"/>
    <text x="32" y="4" fill="#d2dae2" font-size="11" font-weight="bold" text-anchor="middle">敵方 AI 盾衛</text>
  </g>

  <!-- White 3: Skeleton Spearman (1600, 848) - Target of the Spear! -->
  <g transform="translate(1570, 758)">
    <ellipse cx="30" cy="90" rx="35" ry="10" fill="#00d2d3" opacity="0.3"/>
    <rect x="15" y="32" width="30" height="55" rx="6" fill="#1e272e" stroke="#ecf0f1" stroke-width="2"/>
    <circle cx="30" cy="20" r="15" fill="#ecf0f1"/>
    <circle cx="26" cy="18" r="3" fill="#00cec9"/>
    <circle cx="34" cy="18" r="3" fill="#00cec9"/>
    <line x1="25" y1="75" x2="25" y2="10" stroke="#ecf0f1" stroke-width="3" stroke-linecap="round"/>
    <polygon points="21,12 29,12 25,0" fill="#81ecec"/>
    <rect x="-10" y="-8" width="80" height="20" rx="10" fill="#1b1430" stroke="#ecf0f1" stroke-width="1.5"/>
    <text x="30" y="6" fill="#d2dae2" font-size="11" font-weight="bold" text-anchor="middle">敵方 AI 骷髏</text>
  </g>

  <!-- White 4: Bat Scout (1720, 840) -->
  <g transform="translate(1690, 750)">
    <ellipse cx="30" cy="90" rx="35" ry="10" fill="#6c5ce7" opacity="0.3"/>
    <rect x="12" y="35" width="36" height="52" rx="8" fill="#2d3436" stroke="#d2dae2" stroke-width="2"/>
    <polygon points="12,35 22,12 28,35" fill="#2d3436"/>
    <polygon points="48,35 38,12 32,35" fill="#2d3436"/>
    <circle cx="30" cy="42" r="14" fill="#34495e"/>
    <circle cx="25" cy="40" r="3" fill="#f1c40f"/>
    <circle cx="35" cy="40" r="3" fill="#f1c40f"/>
    <rect x="-10" y="-8" width="80" height="20" rx="10" fill="#1b1430" stroke="#d2dae2" stroke-width="1.5"/>
    <text x="30" y="6" fill="#d2dae2" font-size="11" font-weight="bold" text-anchor="middle">敵方 AI 刺客</text>
  </g>

  <!-- ================= WHITE TEAM MOVABLE PUMPKIN SHIELD <||> ================= -->
  <!-- Moves to white_shield_x to predict the incoming landing! -->
  <g transform="translate({white_shield_x - 40}, 790)">
    <!-- Shield Main Barrier Body -->
    <rect x="0" y="0" width="80" height="95" rx="14" fill="url(#shieldGradWhite)" stroke="#ffffff" stroke-width="3" filter="url(#glow)"/>
    <!-- Pumpkin Carving on Shield -->
    <circle cx="40" cy="40" r="18" fill="#006266"/>
    <polygon points="34,36 37,40 31,40" fill="#81ecec"/>
    <polygon points="46,36 49,40 43,40" fill="#81ecec"/>
    <path d="M34 46 Q40 50 46 46 Z" fill="#81ecec"/>
    
    <!-- Tactile Prediction Slider Grips < || > (From user video) -->
    <text x="10" y="48" fill="#ffffff" font-size="22" font-weight="bold">&lt;</text>
    <line x1="37" y1="68" x2="37" y2="82" stroke="#ffffff" stroke-width="2.5"/>
    <line x1="43" y1="68" x2="43" y2="82" stroke="#ffffff" stroke-width="2.5"/>
    <text x="68" y="48" fill="#ffffff" font-size="22" font-weight="bold">&gt;</text>

    <!-- Floating HUD Pill -->
    <rect x="-35" y="-30" width="150" height="24" rx="12" fill="#0d1b2a" stroke="#4deeea" stroke-width="2"/>
    <text x="40" y="-14" fill="#4deeea" font-size="12" font-weight="bold" text-anchor="middle">🛡️ 預判滑塊 (x={int(white_shield_x)})</text>
  </g>
    '''

    # If White Shield is sliding, draw sliding motion dash line
    if white_shield_sliding:
        svg += f'''
  <line x1="1440" y1="840" x2="1600" y2="840" stroke="#4deeea" stroke-width="3" stroke-dasharray="6 4" filter="url(#glow)"/>
  <polygon points="1595,835 1605,840 1595,845" fill="#4deeea"/>
  <rect x="1450" y="855" width="140" height="20" rx="4" fill="#003b39" stroke="#4deeea" stroke-width="1"/>
  <text x="1520" y="869" fill="#e0fbfb" font-size="11" font-weight="bold" text-anchor="middle">技術性預判移動中...</text>
        '''

    # ================= PROJECTILE IN BALLISTIC FLIGHT =================
    if proj_active:
        svg += f'''
  <!-- Ballistic Trajectory Hint Path -->
  <path d="M 345 785 Q 970 0 1600 825" fill="none" stroke="#00cec9" stroke-width="3" stroke-dasharray="10 8" opacity="0.45"/>
  
  <!-- Flying Spear (Rotated along tangent) -->
  <g transform="translate({proj_x}, {proj_y}) rotate({proj_rot})">
    <!-- Motion streak / trail behind spear -->
    <line x1="-60" y1="0" x2="-10" y2="0" stroke="#00cec9" stroke-width="4" stroke-linecap="round" opacity="0.6" filter="url(#glow)"/>
    <line x1="-30" y1="-3" x2="-5" y2="-3" stroke="#81ecec" stroke-width="2" opacity="0.4"/>
    <line x1="-30" y1="3" x2="-5" y2="3" stroke="#81ecec" stroke-width="2" opacity="0.4"/>
    <!-- Spear Body -->
    <line x1="-25" y1="0" x2="25" y2="0" stroke="#ecf0f1" stroke-width="5" stroke-linecap="round"/>
    <line x1="-20" y1="0" x2="15" y2="0" stroke="#00cec9" stroke-width="3"/>
    <!-- Glowing Spearhead Tip -->
    <polygon points="18,-7 35,0 18,7" fill="#81ecec" filter="url(#glow)"/>
  </g>
        '''

    # ================= INTERCEPTION BURST AT SHIELD =================
    if impact_active:
        r_burst = 25.0 + impact_t * 35.0
        opacity_burst = max(0.0, 1.0 - impact_t)
        svg += f'''
  <g transform="translate(1600, 830)">
    <!-- Shockwave ring -->
    <circle cx="0" cy="0" r="{r_burst}" fill="none" stroke="#4deeea" stroke-width="5" opacity="{opacity_burst}" filter="url(#heavyGlow)"/>
    <circle cx="0" cy="0" r="{r_burst * 0.6}" fill="#ffffff" opacity="{opacity_burst}"/>
    <!-- Sparks -->
    <line x1="0" y1="0" x2="-45" y2="-30" stroke="#ffeaa7" stroke-width="3" opacity="{opacity_burst}"/>
    <line x1="0" y1="0" x2="-40" y2="25" stroke="#ffeaa7" stroke-width="3" opacity="{opacity_burst}"/>
    <line x1="0" y1="0" x2="35" y2="-35" stroke="#81ecec" stroke-width="3" opacity="{opacity_burst}"/>
    <line x1="0" y1="0" x2="40" y2="30" stroke="#81ecec" stroke-width="3" opacity="{opacity_burst}"/>
    <!-- Big Toast Callout -->
    <rect x="-180" y="-80" width="360" height="38" rx="19" fill="#003b39" stroke="#4deeea" stroke-width="2.5" filter="url(#glow)"/>
    <text x="0" y="-55" fill="#ffffff" font-size="14" font-weight="bold" text-anchor="middle">🛡️ 預判精準！南瓜盾成功格擋 (0 傷害)</text>
  </g>
        '''

    # Bottom Legend Banner
    svg += '''
  <g transform="translate(560, 1020)">
    <rect x="0" y="0" width="800" height="42" rx="21" fill="#140b24" stroke="#7158e2" stroke-width="2" opacity="0.95"/>
    <circle cx="30" cy="21" r="7" fill="#00cec9"/>
    <text x="45" y="26" fill="#fff" font-size="13" font-weight="bold">真實拋射脫手 (無空浮法球)</text>
    
    <circle cx="280" cy="21" r="7" fill="#4deeea"/>
    <text x="295" y="26" fill="#fff" font-size="13" font-weight="bold">南瓜盾牌技術預判 (4次機會)</text>
    
    <circle cx="560" cy="21" r="7" fill="#ffd32a"/>
    <text x="575" y="26" fill="#fff" font-size="13" font-weight="bold">貓狗大戰風向儀 + 障礙牆</text>
  </g>

</svg>'''
    return svg


def render_worker(i):
    svg_content = generate_svg_frame(i)
    svg_path = f"{FRAMES_DIR}/frame_{i:03d}.svg"
    png_path = f"{FRAMES_DIR}/frame_{i:03d}.png"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    cmd = [
        CHROME_BIN,
        "--headless=new",
        "--disable-gpu",
        "--window-size=960,540",
        f"--screenshot={png_path}",
        svg_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return png_path


def main():
    print(f"Generating {TOTAL_FRAMES} SVG frames in parallel...")
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(render_worker, i) for i in range(TOTAL_FRAMES)]
        for f in futures:
            f.result()
    print("All frames rendered to PNG. Assembling GIF...")

    frames = []
    for i in range(TOTAL_FRAMES):
        png_path = f"{FRAMES_DIR}/frame_{i:03d}.png"
        if os.path.exists(png_path):
            img = Image.open(png_path)
            # Duration per frame: 120ms (frame 14 and frame 26 hold slightly longer)
            frames.append(img.copy())
    
    if not frames:
        print("Error: No frames rendered!")
        sys.exit(1)

    durations = [120] * len(frames)
    durations[0] = 500   # Pause at start
    durations[13] = 220  # Windup pose hold
    durations[14] = 180  # Release apex hold
    durations[26] = 500  # Shield impact highlight
    durations[-1] = 800  # End pause

    gif_path = f"{OUTPUT_DIR}/svg_scene_gameplay_showcase.gif"
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"Successfully baked: {gif_path} ({os.path.getsize(gif_path) // 1024} KB)")

    # Also save frame 0 as the reference static SVG in docs/gameplay_mockup.svg
    ref_svg = generate_svg_frame(0)
    ref_svg_path = os.environ.get("PK_MOCKUP_OUTPUT", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "gameplay_mockup.svg"))
    with open(ref_svg_path, "w", encoding="utf-8") as f:
        f.write(ref_svg)
    print(f"Updated reference mockup: {ref_svg_path}")


if __name__ == "__main__":
    main()
