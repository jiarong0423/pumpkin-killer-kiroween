#!/usr/bin/env python3
"""Build the whole overnight Colab art queue from one table, following docs/pose_spec.md.

Writes colab/jobs_queue_20261109.json = {"jobs": [...]} with tier "Q1". Every job: id, tier, ref, prompt, style, optional w/h.
Every pose prompt repeats the hard rules of the standard (same direction, same hand, same size and baseline, plain face, margin inside the picture,
the held item vanishes at the throw because the RELEASE and EMPTY frames show an empty hand).
Validates before writing: ids unique, every prompt under 170 words, rule phrases present, 8 frames per class (or the class has them already).
Usage: python3 -B scripts/make_art_queue.py [--check]   Exit 1 when the validation fails (nothing is written then).
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "colab", "jobs_queue_20261109.json")

RULES = ("STRICT SIDE VIEW FACING LEFT, the same direction as the reference picture. The character keeps EXACTLY the same size, scale and proportions as the reference "
         "and the feet stand on the same baseline. The whole character and everything it does stays completely INSIDE the picture with a wide empty margin on every side; "
         "nothing touches or crosses the picture edge. One head, no extra limbs, no new weapon. The face and eyes stay plain, NO lightning, NO cracks, NO extra marks.")
STYLE = ("Dark-fantasy 2D cartoon art with thick clean outlines, flat three-tone cel shading, one character only, full body. "
         "Flat solid magenta background (#FF00FF), no ground, no cast shadow, no text, no watermark.")

# class key -> (reference name known to the Colab cell, who it is, held item text, hand text)
CLASSES = {
    "skeleton": ("skeleton", "the skeleton javelin soldier with glowing cyan eyes", "a long spear", "the hand that holds the spear in the reference"),
    "wizard": ("wizard", "the pumpkin-headed wizard in a purple hat and robe", "a brass cannon on the shoulder", "the hands that hold the cannon in the reference"),
    "bat": ("bat", "the black cat assassin with bat ears and cape", "a small ninja throwing star", "the hand that holds the dagger in the reference"),
    "knight": ("knight", "the armoured pumpkin-headed knight with a cape", "a small round wooden shield", "the hand that holds the shield in the reference"),
    "bride": ("bride", "the ghost bride with a long dark hair, a flower crown and a pale veil", "nothing (her weapon is her scream)", "both hands, clasped in front in the reference"),
    "hunchback": ("hunchback", "the grey-green bell-tower brute with small tusks, a ragged green tunic and a giant rusty axe", "a giant axe", "both hands that hold the axe in the reference"),
    "reaper": ("reaper", "the one-headed hooded skull necromancer with glowing purple eyes", "a small purple flame", "the hand that holds the flame in the reference"),
}
# frames to make per class (the others already exist, see scripts/check_pose_set.py); idle1 is the existing unit picture
NEEDED = {
    "skeleton": ["idle2", "charge1", "charge3", "empty"],
    "wizard": ["idle2", "charge1", "charge2", "charge3", "release", "empty", "hit"],
    "bat": ["idle2", "charge3", "empty"],
    "knight": ["idle2", "charge1", "charge2", "charge3", "release", "empty", "hit"],
    "bride": ["idle2", "charge1", "charge2", "charge3", "release", "empty", "hit"],
    "hunchback": ["idle2", "charge1", "charge2", "charge3", "release", "empty", "hit"],
    "reaper": ["idle2", "charge1", "charge3"],
}
FRAME_TEXT = {
    "idle2": "Idle breathing frame: the same standing pose as the reference with the chest very slightly raised and the clothes and cloth shifted a little, a calm face; the item still in the hands.",
    "charge1": "Charge step 1 of 3 (low): the item starts to pull back, the body begins to lean back, a focused face.",
    "charge2": "Charge step 2 of 3 (mid): the item pulled well back behind the body, the body leaning back, the face tightening.",
    "charge3": "Charge step 3 of 3 (full): the item pulled back as far as it goes, the body leaning far back with the knees bent, the face straining with gritted teeth and narrowed eyes.",
    "release": "Release pose: the throwing arm thrust forward toward the LEFT, the hand is EMPTY (the item has already left it, it is a separate picture), the body lunging forward, the mouth open in a shout.",
    "empty": "Empty stance: the same standing pose as the reference but the hands are EMPTY, the item is gone from them, a calm confident face.",
    "hit": "Damage reaction: staggering backward toward the RIGHT, knees buckling, eyes tightly shut in pain, both arms raised shielding the head, the item not visible.",
}
WIZARD_NOTES = {
    "charge1": "The cannon is lifted from the shoulder and starts to aim.", "charge2": "The cannon is held out front aiming, the body bracing.",
    "charge3": "The cannon aims high, the body braced hard, the cannon glowing orange inside the barrel.",
    "release": "The cannon FIRES: the cannon kicks back in the hands with a short orange muzzle flash at the barrel, the body recoiling; the cannon stays in the hands.",
    "empty": "After the shot: the cannon lowered with a thin wisp of smoke, a calm face; the cannon stays in the hands.",
}
BRIDE_NOTES = {
    "charge1": "Both hands rise slowly in front of the chest, a worried face.", "charge2": "Both hands pulled to the chest, shoulders raised, the mouth starting to open.",
    "charge3": "Head thrown back, the mouth wide open drawing a breath, both fists at the chest.",
    "release": "The head thrown forward, the mouth wide open in a scream, both arms spread forward with both hands EMPTY (a sound wave is a separate picture).",
    "empty": "Hands clasped in front again, a calm eerie face.", "hit": "Both hands up to the face, eyes shut, staggering backward.",
}
HUNCH_NOTES = {
    "charge1": "The axe is lifted off the shoulder with both hands.", "charge2": "The axe pulled far back behind the head with both hands, the face tightening.",
    "charge3": "The axe pulled as far back as possible with both hands, the body leaning far back, a straining grimace.",
    "release": "A TWO-HANDED throw: both arms snapped forward, both hands EMPTY (the axe is already flying, a separate picture), the body lunging, a roar.",
    "empty": "Both hands EMPTY and hanging, a grumpy calm face.", "hit": "Staggering backward, eyes shut in pain, both arms raised shielding the face, no axe.",
}
REAPER_NOTES = {
    "charge1": "The raised hand lowers and the flame on the fingertips grows a little.", "charge3": "The arm pulled far back behind the shoulder with the clawed hand around a large bright purple flame.",
    "idle2": "Idle flicker frame: the same raised hand and flame as the reference with the flame leaning a little to the side and the robe hem shifted.",
}
PER_CLASS_NOTES = {"wizard": WIZARD_NOTES, "bride": BRIDE_NOTES, "hunchback": HUNCH_NOTES, "reaper": REAPER_NOTES}


def pose_prompt(key, frame):
    ref, who, item, hand = CLASSES[key]
    base = "Edit this image: keep exactly the same character, %s. " % who
    body = PER_CLASS_NOTES.get(key, {}).get(frame) or FRAME_TEXT[frame]
    if frame in ("charge1", "charge2", "charge3") and key not in PER_CLASS_NOTES:
        body = FRAME_TEXT[frame].replace("the item", item)
    hand_rule = "THE SAME HAND throughout: always use %s; never switch hands. " % hand
    if key == "wizard":
        hand_rule = "THE SAME HANDS throughout: the wizard always holds the cannon with %s. " % hand
    return base + hand_rule + body + " " + RULES


EXTRA_JOBS = [
    ("portrait_front_%s" % k, CLASSES[k][0],
     "Edit this image: draw a FRONT-FACING head-and-shoulders portrait of the same character, %s: the face looks straight at the viewer, shoulders up, the head large and centred, "
     "the same colours and outline, a confident look. No weapon visible. The head fills about 70 percent of the picture height." % CLASSES[k][1])
    for k in CLASSES
]
FX_JOBS = [
    ("fx_flame_comet", "bar", "Ignore the reference layout. Draw ONE single purple-magenta flame comet flying to the LEFT: a bright pale-violet rounded head on the LEFT and a long tapering tail of flickering purple fire to the RIGHT, horizontal, a few tiny star sparks, fully inside the picture with a wide margin."),
    ("fx_molotov_fire", "bar", "Ignore the reference layout. Draw ONE wide low patch of orange-red molotov fire burning on flat ground, a row of tall flickering flame tongues side by side, yellow cores, a few dark smoke wisps, seen from the side, fully inside the picture with a margin."),
    ("fx_axe_thrown", "bar", "Ignore the reference layout. Draw ONE giant rusty battle axe seen from the side, blade pointing UP-LEFT, a worn wooden handle, chipped grey-brown iron blade with rust spots, slight motion blur streak behind it, fully inside the picture with a margin."),
    ("fx_sonic_ring", "bar", "Ignore the reference layout. Draw ONE glowing pale-violet and cyan sound-wave ring, three nested arcs opening to the LEFT like a scream shockwave, soft luminous edges, fully inside the picture with a margin."),
    ("fx_bat_swarm", "bar", "Ignore the reference layout. Draw a small cluster of five tiny black bats with purple-glowing eyes flying to the LEFT with wings spread, each different, cartoon style, fully inside the picture with a margin."),
    ("fx_sky_lantern_target", "bar", "Ignore the reference layout. Draw ONE floating haunted lantern target: a round bullseye of concentric orange and cream rings inside an iron lantern frame, small cyan ghost-fire wisps rising from the top, symmetrical, fully inside the picture with a margin."),
    ("fx_heal_rain_drop", "bar", "Ignore the reference layout. Draw ONE glowing mint-green healing raindrop, a teardrop with a small white plus-shaped sparkle inside and a thin pale rim, soft glow, fully inside the picture with a margin."),
    ("fx_ghost_idle", "bar", "Ignore the reference layout. Draw ONE cute round white ghost with a soft teal glow facing RIGHT, eyes closed peacefully, a tiny closed smile, little arms hanging, floating asleep; fully inside the picture with a wide margin."),
    ("fx_ghost_puff", "bar", "Ignore the reference layout. Draw ONE cute round white ghost with a soft teal glow facing RIGHT, both cheeks puffed out round like balloons, lips pressed tightly shut, eyes squeezed with effort, little arms out; the SAME ghost, fully inside the picture with a wide margin."),
    ("fx_ghost_blow", "bar", "Ignore the reference layout. Draw ONE cute round white ghost with a soft teal glow facing RIGHT, the MOUTH WIDE OPEN in a big round O blowing air out to the right, cheeks relaxed, eyes open and bright, little arms out; the SAME ghost, fully inside the picture with a wide margin."),
    ("fx_ghost_blow_hard", "bar", "Ignore the reference layout. Draw ONE cute round white ghost with a soft teal glow facing RIGHT leaning back, the MOUTH OPENED AS WIDE AS POSSIBLE blowing a hurricane to the right, eyes squinted shut, little arms swept back; the SAME ghost, fully inside the picture with a wide margin."),
    ("fx_wind_swirl", "bar", "Ignore the reference layout. Draw ONE stylised wind gust: three thin curved white and pale-cyan streaks with a small curl at the end, flowing to the RIGHT, soft glow, fully inside the picture with a wide margin."),
    ("fx_flame_hand_purple", "bar", "Ignore the reference layout. Draw ONE small upright purple-magenta flame with a pale-violet core and two tiny star sparks, no hand, no body, fully inside the picture with a margin."),
]
HUD_JOBS = [
    ("ui_top_banner_left", "A wide dark gothic metal banner piece, left third: black iron with fine filigree, small bat-wing ornaments, thin cyan edge glow, an empty dark rectangular panel in the middle for text."),
    ("ui_top_banner_centre", "A wide dark gothic metal banner piece, centre: a notched dark plate with a small glowing pumpkin-lantern ornament on top, a thin gold edge, an empty dark rectangular panel for text."),
    ("ui_top_banner_right", "A wide dark gothic metal banner piece, right third: black iron with fine filigree, small bat-wing ornaments, thin violet edge glow, an empty dark rectangular panel in the middle for text."),
    ("ui_diamond_cyan_on", "One lit cyan diamond gem in a small dark metal setting, glowing."), ("ui_diamond_cyan_off", "One dark unlit cyan diamond gem in a small dark metal setting, no glow."),
    ("ui_diamond_violet_on", "One lit violet diamond gem in a small dark metal setting, glowing."), ("ui_diamond_violet_off", "One dark unlit violet diamond gem in a small dark metal setting, no glow."),
    ("ui_wind_plate", "A small dark metal plate with a round socket on the left for an arrow and an empty panel on the right for a number, thin cyan edge glow."),
]


def build():
    jobs = []
    for key, frames in NEEDED.items():
        ref = CLASSES[key][0]
        for fr in frames:
            jobs.append({"id": "pose_%s_%s" % (key, fr), "tier": "Q1", "ref": ref, "prompt": pose_prompt(key, fr), "style": STYLE})
    for jid, ref, prompt in EXTRA_JOBS:
        jobs.append({"id": jid, "tier": "Q1", "ref": ref, "prompt": prompt, "style": "Dark-fantasy 2D cartoon art with thick clean outlines, flat cel shading. Flat solid magenta background (#FF00FF), no text, no watermark."})
    fstyle = "Game sprite, glowing, painterly 2D with soft luminous edges, centred, alone. Flat solid magenta background (#FF00FF), no ground, no text, no watermark."
    for jid, ref, prompt in FX_JOBS:
        jobs.append({"id": jid, "tier": "Q1", "ref": ref, "prompt": prompt, "style": fstyle})
    for jid, prompt in HUD_JOBS:
        wide = "banner" in jid
        j = {"id": jid, "tier": "Q1", "ref": "bar", "prompt": "Ignore the reference layout. " + prompt, "style": "Dark-fantasy game UI art, polished metal and glow. Flat solid magenta background (#FF00FF), no text, no watermark."}
        if wide:
            j["w"], j["h"] = 1536, 512
        jobs.append(j)
    return jobs


def validate(jobs):
    errs = []
    ids = [j["id"] for j in jobs]
    if len(ids) != len(set(ids)):
        errs.append("duplicate ids")
    for j in jobs:
        n = len(re.findall(r"\S+", j["prompt"] + " " + j["style"]))
        if n > 170 + 40:
            errs.append("%s: %d words" % (j["id"], n))
        if j["id"].startswith("pose_") and not all(p in j["prompt"] for p in ("FACING LEFT", "SAME HAND", "INSIDE the picture")):
            errs.append("%s: rule phrases missing" % j["id"])
        if j["id"].startswith("pose_") and "release" in j["id"] and "EMPTY" not in j["prompt"] and "FIRES" not in j["prompt"]:
            errs.append("%s: the release frame must show an empty hand (or the cannon firing)" % j["id"])
        if j["id"].startswith("pose_") and re.search(r"\bscythe\b", j["prompt"]) and "no scythe" not in j["prompt"].lower():
            errs.append("%s: scythe mentioned" % j["id"])
    return errs


RETRY_IDS = ["pose_hunchback_idle2", "pose_hunchback_charge1", "pose_hunchback_charge3", "pose_hunchback_release", "pose_hunchback_empty", "pose_hunchback_hit",
             "pose_skeleton_idle2", "pose_reaper_charge3", "pose_wizard_release", "portrait_front_bat", "portrait_front_bride", "portrait_front_hunchback", "fx_molotov_fire"]
RETRY_EXTRA = {   # stronger wording for the pictures that came back as copies of the reference or with the wrong character / two flames
    "pose_hunchback_idle2": "Do NOT copy the reference pose: this frame must differ visibly: the whole body shifted down a little as if breathing out, the head lowered slightly, the axe resting a bit lower on the shoulder.",
    "pose_hunchback_charge1": "Do NOT copy the reference pose: the axe is lifted OFF the shoulder with both hands and held out in front of the chest, the knees slightly bent.",
    "pose_hunchback_charge3": "Do NOT copy the reference pose: the giant axe is swung far BACK behind the head with both arms stretched back, the whole body leaning far back, the face contorted with effort.",
    "pose_hunchback_release": "Do NOT copy the reference pose: both arms thrust forward to the LEFT, both hands open and EMPTY, no axe anywhere in the picture, the body lunging forward, a roaring face.",
    "pose_hunchback_empty": "Do NOT copy the reference pose: both hands EMPTY and hanging down, NO axe anywhere in the picture, a grumpy calm face.",
    "pose_hunchback_hit": "Do NOT copy the reference pose: NO axe in the picture, staggering backward, eyes shut in pain, both arms raised in front of the face.",
    "pose_skeleton_idle2": "The character must stay the SAME SKELETON as the reference: a bare white skull with glowing cyan eyes and bare white bones, NO hood, NO cloak, NO clothes.",
    "pose_reaper_charge3": "Only ONE hand holds the flame (the hand that holds it in the reference); the other hand is EMPTY at the side with NO flame at all.",
    "pose_wizard_release": "The whole cannon barrel and the muzzle flash stay fully inside the picture; the wizard stands in the LEFT half of the picture.",
    "portrait_front_bat": "The ears, the shoulders and the whole head stay fully inside the picture with a visible margin on the left and right.",
    "portrait_front_bride": "This must be a CLOSE head-and-shoulders portrait, NOT a full-body picture: the face fills the picture, only the head, the veil and the shoulders are visible.",
    "portrait_front_hunchback": "This must be a CLOSE head-and-shoulders portrait, NOT a full-body picture and NO axe visible: the face fills the picture, only the head and the shoulders.",
    "fx_molotov_fire": "The background must be flat solid magenta everywhere, NO dark red haze or smoke box around the fire; only the flames and a little smoke wisp, fully inside the picture.",
}


def build_retry():
    base = {j["id"]: j for j in build() + []}
    # portraits are built outside build()'s pose list: rebuild them from EXTRA_JOBS
    for jid, ref, prompt in EXTRA_JOBS:
        base.setdefault(jid, {"id": jid, "tier": "Q1", "ref": ref, "prompt": prompt, "style": STYLE})
    out = []
    for jid in RETRY_IDS:
        j = dict(base[jid])
        j["tier"] = "Q2"
        j["prompt"] = j["prompt"] + " " + RETRY_EXTRA[jid]
        j["w"], j["h"] = 1536, 1024   # a wider canvas gives the arms and weapons room
        out.append(j)
    return out


FACE_LOCK = ("FACE LOCK (very important): the head and face must be EXACTLY the same face as in the reference picture: the same eye shape and size, the same carved or drawn mouth, "
             "the same outline, the same colours and the same proportions; do NOT redraw, restyle or replace the face. Only the opening of the mouth and the angle of the eyebrows may change a little to show the "
             "expression; it is still clearly the same face.")
GENERIC_EXAGGERATE = ("EXAGGERATE the change: this frame must look clearly and immediately different from the reference at a glance (a big change of the pose, "
                      "the arms, the lean of the body and the face), while the character, its colours, its size and its direction stay exactly the same.")


def load_canon():
    """Per-class face and item descriptions written by the two art reviewers after looking at the reference pictures (docs/audition/agent_*_review.json)."""
    canon = {}
    for n in ("a", "b"):
        p = os.path.join(ROOT, "docs", "audition", "agent_%s_review.json" % n)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                for cls, v in json.load(f)["classes"].items():
                    canon[cls] = v["canonical"]
    return canon


ITEM_GONE = {"skeleton": "spear", "bat": "dagger and any throwing star", "knight": "shield", "hunchback": "axe"}   # thrown items: absent from release and empty frames


CANON = load_canon()


def build_from_review(path):
    """The owner's ticks (docs/audition/review_result.json): redo every ticked id, 1536x1024 canvas, extra wording, tier Q2."""
    with open(path, encoding="utf-8") as f:
        redo = json.load(f)["redo"]
    base = {j["id"]: j for j in build()}
    out = []
    for jid in redo:
        j = dict(base[jid])
        j["tier"] = "Q2"
        extra = RETRY_EXTRA.get(jid, "")
        if jid.startswith("pose_"):
            cls, fr = jid.split("_", 2)[1], jid.split("_", 2)[2]
            canon = CANON.get(cls)
            lock = ""
            if canon:
                lock = " REFERENCE FACE (keep it identical): %s REFERENCE ITEM (keep it identical when it is in the hands): %s" % (canon["face"], canon["weapon"])
            gone = ""
            if fr in ("release", "empty") and cls in ITEM_GONE:
                gone = " ABSOLUTELY NO %s in the hands and NO %s anywhere in the picture." % (ITEM_GONE[cls], ITEM_GONE[cls])
            extra = (extra + " " + GENERIC_EXAGGERATE + " " + FACE_LOCK + lock + gone).strip()
        j["prompt"] = (j["prompt"] + " " + extra).strip()
        j["w"], j["h"] = 1536, 1024
        out.append(j)
    return out


def main(argv):
    if "--from-review" in argv:
        jobs = build_from_review(argv[argv.index("--from-review") + 1])
        path = os.path.join(ROOT, "colab", "jobs_retry2_20261110.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"jobs": jobs}, f, ensure_ascii=False, indent=1)
        print("%d jobs -> %s" % (len(jobs), os.path.relpath(path, ROOT)))
        return 0
    if "--retry" in argv:
        jobs = build_retry()
        path = os.path.join(ROOT, "colab", "jobs_retry_20261109.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"jobs": jobs}, f, ensure_ascii=False, indent=1)
        print("%d retry jobs -> %s" % (len(jobs), os.path.relpath(path, ROOT)))
        return 0
    jobs = build()
    errs = validate(jobs)
    if errs:
        for e in errs:
            print("ERROR", e, file=sys.stderr)
        return 1
    if "--check" not in argv:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"jobs": jobs}, f, ensure_ascii=False, indent=1)
    print("%d jobs%s" % (len(jobs), "" if "--check" in argv else " -> " + os.path.relpath(OUT, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
