#!/usr/bin/env python3
"""Post-processing for generated audio (numpy plus soundfile or the stdlib wave module).

The functions between the BEGIN and END markers are copied verbatim into
``colab/audio_job.py`` so that the Colab job and this local script do the same
thing. ``scripts/test_postprocess_audio.py`` checks that the two copies are
identical. Change both or neither.

Steps, in this order: mono (optional), trim silence, cut to the final duration,
then either the loop crossfade (loops) or the fades (one-shots), then
normalise the peak.

Batch use (re-process raw files that were downloaded from Drive):

    python3 scripts/postprocess_audio.py --jobs colab/audio_jobs.json \
        --input audio_raw --output audio_out [--only id1,id2] [--report]

Input files must be named ``<id>_v<N>.wav`` and must be RAW (not already
processed): running this on processed files applies the fades and the loop
crossfade a second time.

Nobody has listened to the output of this script. The tests use synthetic
signals only.
"""
import argparse
import glob
import json
import os
import sys
import wave

import numpy as np


# --- BEGIN POSTPROCESS (shared by colab/audio_job.py and scripts/postprocess_audio.py, keep identical) ---
DEFAULT_POST = {
    "mono": True,
    "trim_silence": True,
    "trim_threshold_db": -45.0,
    "fade_in_ms": 5.0,
    "fade_out_ms": 30.0,
    "peak_dbfs": -3.0,
    "loop_crossfade_ms": 0.0,
}


def db_to_gain(db):
    return float(10.0 ** (float(db) / 20.0))


def as_2d(x):
    """Float32 array shaped (samples, channels)."""
    a = np.asarray(x, dtype=np.float32)
    if a.ndim == 1:
        a = a[:, None]
    return a


def to_mono(x):
    a = as_2d(x)
    return a.mean(axis=1, keepdims=True).astype(np.float32)


def trim_silence(x, sr, threshold_db=-45.0, pre_ms=2.0, post_ms=10.0):
    """Cut leading and trailing samples below threshold_db, measured against the clip peak."""
    a = as_2d(x)
    if a.shape[0] == 0:
        return a
    level = np.max(np.abs(a), axis=1)
    peak = float(level.max())
    if peak <= 1e-9:
        return a
    idx = np.nonzero(level > peak * db_to_gain(threshold_db))[0]
    start = max(0, int(idx[0]) - int(sr * pre_ms / 1000.0))
    end = min(a.shape[0], int(idx[-1]) + 1 + int(sr * post_ms / 1000.0))
    return a[start:end]


def cut_to_seconds(x, sr, seconds):
    a = as_2d(x)
    if seconds is None:
        return a
    n = int(round(sr * float(seconds)))
    return a[:n] if a.shape[0] > n else a


def apply_fades(x, sr, fade_in_ms=5.0, fade_out_ms=30.0):
    a = as_2d(x).copy()
    n = a.shape[0]
    n_in = min(n, int(round(sr * float(fade_in_ms) / 1000.0)))
    n_out = min(n, int(round(sr * float(fade_out_ms) / 1000.0)))
    if n_in > 0:
        a[:n_in] *= np.linspace(0.0, 1.0, n_in, dtype=np.float32)[:, None]
    if n_out > 0:
        a[n - n_out:] *= np.linspace(1.0, 0.0, n_out, dtype=np.float32)[:, None]
    return a


def normalise_peak(x, peak_dbfs=-3.0):
    a = as_2d(x)
    peak = float(np.max(np.abs(a))) if a.size else 0.0
    if peak <= 1e-9:
        return a
    return (a * (db_to_gain(peak_dbfs) / peak)).astype(np.float32)


def loop_crossfade(x, sr, ms=80.0):
    """Blend the tail into the head. The result is c samples shorter than the input
    (c = ms in samples) and its last sample is followed smoothly by its first."""
    a = as_2d(x)
    n = a.shape[0]
    c = int(round(sr * float(ms) / 1000.0))
    if c <= 0:
        return a
    if 2 * c > n:
        raise ValueError("clip too short for a %.0f ms loop crossfade" % float(ms))
    ramp = np.linspace(0.0, 1.0, c, dtype=np.float32)[:, None]
    out = a[: n - c].copy()
    out[:c] = a[:c] * ramp + a[n - c:] * (1.0 - ramp)
    return out


def loop_seam_ratio(x):
    """Step from the last sample to the first, divided by the mean sample-to-sample step.
    Near 1 or below: no click when looped. Well above 1: a click is likely."""
    a = as_2d(x)
    if a.shape[0] < 2:
        return 0.0
    jump = float(np.max(np.abs(a[0] - a[-1])))
    step = float(np.mean(np.abs(np.diff(a, axis=0))))
    return jump / step if step > 1e-12 else 0.0


def postprocess(x, sr, post=None, duration=None, loop=False):
    """Run the whole chain. Loops get the crossfade and no fades (a fade would dip at the seam)."""
    p = dict(DEFAULT_POST)
    if post:
        p.update(post)
    a = as_2d(x)
    if p["mono"] and a.shape[1] > 1:
        a = to_mono(a)
    if p["trim_silence"]:
        a = trim_silence(a, sr, p["trim_threshold_db"])
    a = cut_to_seconds(a, sr, duration)
    if loop:
        a = loop_crossfade(a, sr, p["loop_crossfade_ms"])
    else:
        a = apply_fades(a, sr, p["fade_in_ms"], p["fade_out_ms"])
    return normalise_peak(a, p["peak_dbfs"])
# --- END POSTPROCESS ---


def _read_wav_stdlib(path):
    with wave.open(path, "rb") as w:
        channels, width, sr, frames = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(frames)
    if width != 2:
        raise ValueError("stdlib reader supports 16-bit PCM only, got %d bytes per sample (install soundfile)" % width)
    data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    return data.reshape(-1, channels), int(sr)


def _write_wav_stdlib(path, data, sr):
    a = as_2d(data)
    pcm = np.clip(np.round(a * 32767.0), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(a.shape[1])
        w.setsampwidth(2)
        w.setframerate(int(sr))
        w.writeframes(pcm.tobytes())


def read_wav(path):
    """Return (float32 array shaped (samples, channels), sample rate)."""
    try:
        import soundfile as sf
    except ImportError:
        return _read_wav_stdlib(path)
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    return data, int(sr)


def write_wav(path, data, sr):
    """Write 16-bit PCM."""
    try:
        import soundfile as sf
    except ImportError:
        _write_wav_stdlib(path, data, sr)
        return
    sf.write(path, as_2d(data), int(sr), subtype="PCM_16")


def run_batch(spec, in_dir, out_dir, only=None):
    """Process every ``<id>_v*.wav`` in in_dir for the jobs in spec. Returns a list of
    (file name, status, seam ratio or None). Never raises for one bad file."""
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for job in spec["jobs"]:
        if only and job["id"] not in only:
            continue
        for path in sorted(glob.glob(os.path.join(in_dir, job["id"] + "_v*.wav"))):
            name = os.path.basename(path)
            try:
                data, sr = read_wav(path)
                loop = bool(job.get("loop"))
                out = postprocess(data, sr, job.get("post"), duration=job.get("duration"), loop=loop)
                write_wav(os.path.join(out_dir, name), out, sr)
                results.append((name, "OK", loop_seam_ratio(out) if loop else None))
            except Exception as e:  # keep going, report at the end
                results.append((name, "ERR " + repr(e)[:160], None))
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description="Post-process raw generated WAV files.")
    ap.add_argument("--jobs", default="colab/audio_jobs.json", help="job file with the post settings")
    ap.add_argument("--input", required=True, help="folder with raw <id>_v<N>.wav files")
    ap.add_argument("--output", required=True, help="folder for the processed files")
    ap.add_argument("--only", default="", help="comma separated job ids")
    ap.add_argument("--report", action="store_true", help="print the loop seam ratio of loop files")
    args = ap.parse_args(argv)
    with open(args.jobs, "r", encoding="utf-8") as f:
        spec = json.load(f)
    only = [s for s in args.only.split(",") if s]
    results = run_batch(spec, args.input, args.output, only)
    bad = 0
    for name, status, seam in results:
        if status == "OK":
            extra = "  seam=%.2f" % seam if (args.report and seam is not None) else ""
            print("OK  %s%s" % (name, extra))
        else:
            bad += 1
            print("ERR %s: %s" % (name, status))
    print("processed=%d failed=%d" % (len(results) - bad, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
