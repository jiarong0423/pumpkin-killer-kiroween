#!/usr/bin/env python3
"""Tests for scripts/postprocess_audio.py and colab/audio_jobs.json (numpy plus stdlib).

All signals are synthetic. Nothing here says how the real generated audio sounds.

Run with: ``python3 -B scripts/test_postprocess_audio.py``
Last line on success: ``test_postprocess_audio: <n> passed, 0 failed``
"""
import ast
import json
import os
import re
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import postprocess_audio as pp  # noqa: E402

SR = 8000
JOBS_PATH = os.path.join(ROOT, "colab", "audio_jobs.json")
EVENT_MAP_PATH = os.path.join(ROOT, "docs", "audio_event_map.json")
JOB_SCRIPT_PATH = os.path.join(ROOT, "colab", "audio_job.py")
POST_SCRIPT_PATH = os.path.join(HERE, "postprocess_audio.py")

MUSIC_IDS = ["music_bed", "music_tension_drone", "music_victory_sting", "music_defeat_sting"]
BANNED = [
    "zelda", "mario", "minecraft", "halo", "doom", "skyrim", "dark souls", "diablo", "warcraft",
    "pokemon", "nintendo", "playstation", "xbox", "disney", "pixar", "marvel", "star wars",
    "hans zimmer", "john williams", "beethoven", "mozart", "kenney", "freesound",
]


def sine(freq, seconds, amp=0.5, sr=SR):
    t = np.arange(int(round(sr * seconds))) / sr
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def block(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    begin = text.index("# --- BEGIN POSTPROCESS")
    end = text.index("# --- END POSTPROCESS ---") + len("# --- END POSTPROCESS ---")
    return text[begin:end].strip()


# ---- signal tests -----------------------------------------------------------

def test_trim_silence_cuts_both_ends():
    x = np.concatenate([np.zeros(2000), np.full(800, 0.5), np.zeros(2000)]).astype(np.float32)
    y = pp.trim_silence(x, SR, -45.0)
    # start = 2000 - 16 (2 ms), end = 2800 + 80 (10 ms)
    assert y.shape == (896, 1), y.shape
    assert np.all(y[:16] == 0.0)
    assert y[16, 0] == 0.5
    assert y[-1, 0] == 0.0


def test_trim_silence_uses_threshold_relative_to_peak():
    quiet = np.full(1000, 0.0003)           # about -64 dB under the 0.5 peak, below the -45 dB threshold
    x = np.concatenate([quiet, np.full(800, 0.5), quiet]).astype(np.float32)
    y = pp.trim_silence(x, SR, -45.0)
    assert y.shape[0] == 16 + 800 + 80, y.shape


def test_trim_silence_leaves_all_silent_clip_alone():
    x = np.zeros(1234, dtype=np.float32)
    y = pp.trim_silence(x, SR)
    assert y.shape == (1234, 1)


def test_fades_have_the_requested_length():
    x = np.ones(8000, dtype=np.float32)
    y = pp.apply_fades(x, SR, 5.0, 30.0)[:, 0]
    assert abs(y[0]) < 1e-6
    assert abs(y[39] - 1.0) < 1e-6            # 5 ms = 40 samples, the ramp ends at full level
    assert abs(y[4000] - 1.0) < 1e-6          # untouched middle
    assert abs(y[8000 - 240] - 1.0) < 1e-6    # 30 ms = 240 samples, the ramp starts at full level
    assert abs(y[-1]) < 1e-6
    assert np.all(np.diff(y[:40]) >= 0)
    assert np.all(np.diff(y[-240:]) <= 0)


def test_fades_on_a_clip_shorter_than_the_fades():
    x = np.ones(10, dtype=np.float32)
    y = pp.apply_fades(x, SR, 5.0, 30.0)
    assert y.shape == (10, 1)
    assert np.all(np.isfinite(y))


def test_fades_do_not_change_the_input():
    x = np.ones(1000, dtype=np.float32)
    pp.apply_fades(x, SR, 5.0, 30.0)
    assert np.all(x == 1.0)


def test_normalise_sets_peak_to_minus_3_dbfs():
    x = sine(440, 0.5, amp=0.1)
    x[100] = -0.2                              # the negative peak counts too
    y = pp.normalise_peak(x, -3.0)
    assert abs(float(np.max(np.abs(y))) - 10 ** (-3 / 20)) < 1e-4


def test_normalise_silent_clip_stays_silent():
    y = pp.normalise_peak(np.zeros(100, dtype=np.float32), -3.0)
    assert np.all(y == 0.0) and np.all(np.isfinite(y))


def test_loop_crossfade_length_is_n_minus_crossfade():
    x = sine(441, 3001 / SR)
    assert x.shape[0] == 3001
    y = pp.loop_crossfade(x, SR, 80.0)
    assert y.shape == (3001 - 640, 1), y.shape   # 80 ms at 8000 Hz = 640 samples


def test_loop_crossfade_removes_the_seam_jump():
    x = sine(441, 3001 / SR, amp=0.8)
    before = pp.loop_seam_ratio(x)
    y = pp.loop_crossfade(x, SR, 80.0)
    after = pp.loop_seam_ratio(y)
    assert before > 2.5, before
    assert after < before, (before, after)
    max_step = float(np.max(np.abs(np.diff(x))))
    assert abs(float(y[0, 0] - y[-1, 0])) <= max_step + 1e-4


def test_loop_crossfade_zero_ms_is_a_no_op():
    x = sine(441, 0.25)
    assert pp.loop_crossfade(x, SR, 0.0).shape == (x.shape[0], 1)


def test_loop_crossfade_rejects_a_clip_that_is_too_short():
    x = sine(441, 0.1)                           # 800 samples, crossfade needs 2 x 640
    try:
        pp.loop_crossfade(x, SR, 80.0)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_postprocess_one_shot():
    burst = sine(440, 1.0, amp=0.8)
    mono = np.concatenate([np.zeros(1000), burst, np.zeros(1000)]).astype(np.float32)
    stereo = np.stack([mono, mono], axis=1)
    y = pp.postprocess(stereo, SR, None, duration=0.5, loop=False)
    assert y.shape == (4000, 1), y.shape         # mono, cut to 0.5 s
    assert abs(float(np.max(np.abs(y))) - 10 ** (-3 / 20)) < 1e-4
    assert abs(y[0, 0]) < 1e-6 and abs(y[-1, 0]) < 1e-6


def test_postprocess_loop_uses_crossfade_and_no_fades():
    burst = sine(440, 1.5, amp=0.8)
    mono = np.concatenate([np.zeros(500), burst, np.zeros(500)]).astype(np.float32)
    post = {"mono": True, "fade_in_ms": 5, "fade_out_ms": 30, "loop_crossfade_ms": 80}
    y = pp.postprocess(mono, SR, post, duration=1.0, loop=True)
    assert y.shape == (8000 - 640, 1), y.shape
    # a fade-in would make the first sample 0; the crossfade keeps the tail's level there
    assert abs(float(np.max(np.abs(y))) - 10 ** (-3 / 20)) < 1e-4


def test_postprocess_keeps_stereo_when_mono_is_false():
    mono = sine(440, 0.5, amp=0.8)
    stereo = np.stack([mono, mono * 0.5], axis=1)
    y = pp.postprocess(stereo, SR, {"mono": False}, duration=None, loop=False)
    assert y.shape[1] == 2


def test_wav_round_trip_and_batch():
    spec = {"jobs": [{"id": "demo", "duration": 0.5, "loop": False,
                      "post": {"mono": True, "loop_crossfade_ms": 0}}]}
    tone = sine(440, 1.0, amp=0.6)
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = os.path.join(tmp, "raw"), os.path.join(tmp, "out")
        os.makedirs(src)
        pp.write_wav(os.path.join(src, "demo_v1.wav"), tone, SR)
        results = pp.run_batch(spec, src, dst)
        assert results == [("demo_v1.wav", "OK", None)], results
        data, sr = pp.read_wav(os.path.join(dst, "demo_v1.wav"))
        assert sr == SR
        assert data.shape == (4000, 1), data.shape
        assert abs(float(np.max(np.abs(data))) - 10 ** (-3 / 20)) < 1e-3   # 16-bit rounding


def test_batch_reports_a_bad_file_and_continues():
    spec = {"jobs": [{"id": "a", "duration": 0.5, "loop": False}, {"id": "b", "duration": 0.5, "loop": False}]}
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = os.path.join(tmp, "raw"), os.path.join(tmp, "out")
        os.makedirs(src)
        with open(os.path.join(src, "a_v1.wav"), "wb") as f:
            f.write(b"not a wav file")
        pp.write_wav(os.path.join(src, "b_v1.wav"), sine(440, 1.0), SR)
        results = pp.run_batch(spec, src, dst)
        status = {name: s for name, s, _ in results}
        assert status["a_v1.wav"].startswith("ERR"), status
        assert status["b_v1.wav"] == "OK", status


# ---- job file tests ---------------------------------------------------------

def test_jobs_cover_all_events_and_4_music_layers():   # 61 events + 4 music jobs = 65 (the old name said 35)
    jobs = load_json(JOBS_PATH)["jobs"]
    events = load_json(EVENT_MAP_PATH)["events"]
    ids = [j["id"] for j in jobs]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(events) == 61, len(events)   # 48 + ult_bat_hit, ult_reaper_hit, ult_hunchback_hit, ult_hag_hit + status_stun, status_slow, status_shock, status_frost (2026-11-22)
    assert set(events) <= set(ids), sorted(set(events) - set(ids))
    assert set(MUSIC_IDS) <= set(ids)
    assert len(jobs) == 65, len(jobs)


def test_jobs_match_the_event_map():
    jobs = {j["id"]: j for j in load_json(JOBS_PATH)["jobs"]}
    for name, ev in load_json(EVENT_MAP_PATH)["events"].items():
        j = jobs[name]
        assert abs(j["duration"] - ev["duration"]) < 1e-9, (name, j["duration"], ev["duration"])
        assert j["loop"] == ev["loop"], name


def test_jobs_have_the_required_fields():
    for j in load_json(JOBS_PATH)["jobs"]:
        for key in ("id", "prompt", "negative_prompt", "duration", "gen_seconds", "variants", "seed_base", "loop", "post"):
            assert key in j, (j.get("id"), key)
        assert j["variants"] == 3, j["id"]
        assert j["prompt"].strip() and j["negative_prompt"].strip(), j["id"]
        assert 0 < j["duration"] <= 24, j["id"]
        assert j["gen_seconds"] >= j["duration"], j["id"]
        assert j["gen_seconds"] <= 47, j["id"]       # Stable Audio Open 1.0 limit on its model card


def test_jobs_post_settings():
    for j in load_json(JOBS_PATH)["jobs"]:
        p = j["post"]
        assert p["trim_silence"] is True, j["id"]
        assert p["peak_dbfs"] == -3, j["id"]
        if j["loop"]:
            assert p["loop_crossfade_ms"] == 80, j["id"]
            assert p["fade_in_ms"] == 0 and p["fade_out_ms"] == 0, j["id"]
        else:
            assert p["loop_crossfade_ms"] == 0, j["id"]
            assert p["fade_in_ms"] == 5 and p["fade_out_ms"] == 30, j["id"]


def test_loop_jobs_are_long_enough_for_the_crossfade():
    for j in load_json(JOBS_PATH)["jobs"]:
        if j["loop"]:
            assert j["duration"] * 1000 >= 4 * j["post"]["loop_crossfade_ms"], j["id"]


def test_seeds_do_not_overlap():
    bases = sorted(j["seed_base"] for j in load_json(JOBS_PATH)["jobs"])
    assert len(bases) == len(set(bases))
    for a, b in zip(bases, bases[1:]):
        assert b - a > 3, (a, b)


def test_prompts_have_no_artist_brand_or_game_names():
    for j in load_json(JOBS_PATH)["jobs"]:
        text = (j["prompt"] + " " + j["negative_prompt"]).lower()
        for word in BANNED:
            assert re.search(r"\b" + re.escape(word) + r"\b", text) is None, (j["id"], word)


# ---- code tests -------------------------------------------------------------

def test_colab_job_has_an_identical_postprocess_block():
    assert block(JOB_SCRIPT_PATH) == block(POST_SCRIPT_PATH)


def test_colab_job_parses_and_names_its_model():
    with open(JOB_SCRIPT_PATH, "r", encoding="utf-8") as f:
        src = f.read()
    ast.parse(src)                               # syntax check only, the script is never run here
    assert re.search(r'^MODEL_ID\s*=\s*"stabilityai/stable-audio-open-1\.0"', src, re.M)
    assert re.search(r"^MODEL_LICENSE_NOTE\s*=", src, re.M)
    assert re.search(r"^LICENSE_ACK\s*=\s*False", src, re.M), "ship the job with the license gate closed"


def test_owner_supplied_jobs_match_event_map_and_are_skipped():
    jobs = load_json(JOBS_PATH)["jobs"]
    events = load_json(EVENT_MAP_PATH)["events"]
    expected = {k for k, v in events.items() if isinstance(v, dict) and str(v.get("source", "")).startswith("owner-")}
    marked = {j["id"] for j in jobs if j.get("owner_supplied") is True}
    assert len(expected) == 26, len(expected)   # 22 of the owner's Gemini sets (throw, ult, ult hit parts, impact_flame) + the 4 status sounds of 2026-11-22
    assert marked == expected, (marked ^ expected)
    with open(JOB_SCRIPT_PATH, "r", encoding="utf-8") as f:
        src = f.read()
    assert re.search(r'not\s+j\.get\("owner_supplied"\)', src), "colab/audio_job.py must skip owner_supplied jobs"


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    passed, failed = 0, 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
            print("ok   " + name)
        except Exception as e:
            failed += 1
            print("FAIL %s: %r" % (name, e))
    print("test_postprocess_audio: %d passed, %d failed" % (passed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
