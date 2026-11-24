# Pumpkin Killer — Colab audio job (Stable Audio Open 1.0 through diffusers).
#
# HOW TO USE (Colab, GPU = A100; use a FRESH runtime, not the one used for the art job):
#   Cell 1  (install)   !pip install -q -U diffusers "transformers<5" accelerate soundfile
#                       (the art job also needs transformers<5; a fresh runtime avoids version clashes)
#   Cell 2  (this file) paste the whole file. FIRST do the LICENSE CHECK below, then set LICENSE_ACK = True.
# Hugging Face: the model is gated. Accept its terms on the model page with your account, then add a
#   Colab secret named HF_TOKEN (key icon in the left bar) holding a read token. The script reads it.
# Inputs  : Google Drive  MyDrive/PumpkinKiller/inputs/audio_jobs.json   (from colab/audio_jobs.json)
# Outputs : MyDrive/PumpkinKiller/audio_out/<id>_v<N>.wav   post-processed (trim, fade/loop crossfade, -3 dBFS)
#           MyDrive/PumpkinKiller/audio_raw/<id>_v<N>.wav   the model output before post-processing
#           MyDrive/PumpkinKiller/audio_out/generation_log.jsonl   one line per file: model, seed, prompt
# Every file is written the moment it is finished and finished files are skipped on a re-run, so a
# disconnect loses nothing. One failure never stops the loop.
#
# LICENSE CHECK (do this before you set LICENSE_ACK = True). The weights are under the Stability AI
# Community License, which is free below USD 1M annual revenue and asks commercial users to register.
# Read these pages yourself, today, and check them against the contest rules:
#   https://huggingface.co/stabilityai/stable-audio-open-1.0         (model card, terms to accept)
#   https://stability.ai/license                                      (registration, revenue limit)
#   https://stability.ai/community-license-agreement                  (the license text)
#   https://stability.ai/use-policy                                   (acceptable use, AI disclosure)
#
# NOT TESTED: this script was written without a GPU and without running it. The calls to diffusers follow
# the model card (StableAudioPipeline, negative_prompt, audio_end_in_s, generator). Run ONE job first:
# ONLY = ["throw_spear"]. Nobody has listened to any output.

import os, json, time, gc

MODEL_ID = "stabilityai/stable-audio-open-1.0"
MODEL_LICENSE_NOTE = "Stability AI Community License (as written on the model card). Check the pages above."
LICENSE_ACK = False   # set True only after you read the license pages above

ONLY = []             # [] = every job; or a list of job ids, e.g. ["throw_spear"]
VARIANTS = None       # None = each job's own "variants" (3); or an int to override
STEPS = 100           # the model card example uses 200; fewer steps are faster and usually a little rougher
BASE = "/content/drive/MyDrive/PumpkinKiller"

if not LICENSE_ACK:
    raise RuntimeError("LICENSE_ACK is False. Read the license pages listed at the top of this file first.")

import numpy as np
import soundfile as sf
from google.colab import drive
drive.mount("/content/drive")
IN_DIR, OUT_DIR, RAW_DIR = f"{BASE}/inputs", f"{BASE}/audio_out", f"{BASE}/audio_raw"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)

HF_TOKEN = None
try:
    from google.colab import userdata
    HF_TOKEN = userdata.get("HF_TOKEN")
except Exception:
    HF_TOKEN = None   # fall back to a token cached by `huggingface-cli login`, if any


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


import torch
from diffusers import StableAudioPipeline

spec = json.load(open(f"{IN_DIR}/audio_jobs.json", encoding="utf-8"))
all_jobs = [j for j in spec["jobs"] if not ONLY or j["id"] in ONLY]
owner_skipped = sum(1 for j in all_jobs if j.get("owner_supplied"))
jobs = [j for j in all_jobs if not j.get("owner_supplied")]
total = sum(int(VARIANTS or j.get("variants", 3)) for j in jobs)
print(f"{len(jobs)} jobs ({owner_skipped} owner-supplied skipped), {total} files")

if not torch.cuda.is_available():
    raise RuntimeError("No GPU. Runtime > Change runtime type > A100.")
try:
    del pipe
except NameError:
    pass
gc.collect(); torch.cuda.empty_cache()
pipe = StableAudioPipeline.from_pretrained(MODEL_ID, torch_dtype=torch.float16, token=HF_TOKEN)
pipe = pipe.to("cuda")
pipe.set_progress_bar_config(disable=True)
SR = int(pipe.vae.sampling_rate)
print("GPU GB:", round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1), " sample rate:", SR)


def generate(job, seed):
    """One waveform, shape (samples, channels), float32."""
    gen = torch.Generator("cuda").manual_seed(int(seed))
    audio = pipe(
        job["prompt"],
        negative_prompt=job.get("negative_prompt") or None,
        num_inference_steps=STEPS,
        audio_end_in_s=float(job["gen_seconds"]),
        num_waveforms_per_prompt=1,
        generator=gen,
    ).audios
    return audio[0].T.float().cpu().numpy()


done, skipped, failed = 0, 0, []
for j in jobs:
    n_var = int(VARIANTS or j.get("variants", 3))
    for v in range(1, n_var + 1):
        name = f"{j['id']}_v{v}.wav"
        out_path = f"{OUT_DIR}/{name}"
        if os.path.exists(out_path):
            skipped += 1
            continue
        t0 = time.time()
        try:
            seed = int(j["seed_base"]) + v
            raw = generate(j, seed)
            if not np.isfinite(raw).all():
                raise ValueError("model output contains NaN or inf")
            if float(np.max(np.abs(raw))) < 1e-4:
                raise ValueError("model output is silent")
            sf.write(f"{RAW_DIR}/{name}", raw, SR, subtype="PCM_16")
            loop = bool(j.get("loop"))
            final = postprocess(raw, SR, j.get("post"), duration=j.get("duration"), loop=loop)
            sf.write(out_path, final, SR, subtype="PCM_16")   # written last: its existence means "finished"
            with open(f"{OUT_DIR}/generation_log.jsonl", "a", encoding="utf-8") as lg:
                lg.write(json.dumps({"file": name, "model": MODEL_ID, "seed": seed, "steps": STEPS,
                                     "prompt": j["prompt"], "negative_prompt": j.get("negative_prompt"),
                                     "license_note": MODEL_LICENSE_NOTE}) + "\n")
            done += 1
            seam = f"  seam={loop_seam_ratio(final):.2f}" if loop else ""
            print(f"OK  {j['id']} v{v}  {time.time() - t0:.0f}s  {final.shape[0] / SR:.2f}s{seam}")
        except Exception as e:                      # keep going; report at the end
            failed.append((j["id"], v, repr(e)[:200]))
            print(f"ERR {j['id']} v{v}: {repr(e)[:200]}")
        gc.collect(); torch.cuda.empty_cache()

print(f"done={done} skipped={skipped} failed={len(failed)} of {total}")
for f in failed:
    print("FAILED", f)
