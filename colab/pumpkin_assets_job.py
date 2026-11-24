# Pumpkin Killer — Colab asset job (Qwen-Image-Edit-2509, image edit from a reference).
#
# HOW TO USE (Colab, GPU = A100 or L4; run the cells in order):
#   Cell 1  (install)   !pip install -q -U "transformers<5" diffusers accelerate sentencepiece protobuf bitsandbytes   (transformers 5.x gave pure-noise images)
#   Cell 2  (this file) paste the whole file, set ONLY / VARIANTS below, run.
# Inputs  : Google Drive  MyDrive/PumpkinKiller/inputs/   (the 5 reference PNGs) and  jobs.json
# Outputs : Google Drive  MyDrive/PumpkinKiller/out/<job_id>_v<N>.png   (flat magenta background)
# Every image is written to Drive the moment it is finished, so a disconnect loses nothing; finished
# jobs are skipped when you run the cell again.
#
# NOT TESTED by the author (no GPU where this was written). Run ONE job first (ONLY = ["skeleton_spear_item"]).

import os, json, time, gc

from job_refs import resolve_refs

ONLY = []            # [] = every job of the chosen tiers; or a list of job ids, e.g. ["skeleton_spear_item"]
TIERS = ["P1"]       # which tiers to run: P1 first, then P2
VARIANTS = 2         # images per job (pick the best one later)
STEPS = 40
TRUE_CFG = 4.0
SIZE = 1024
BASE = "/content/drive/MyDrive/PumpkinKiller"

from google.colab import drive
drive.mount("/content/drive")
IN_DIR, OUT_DIR = f"{BASE}/inputs", f"{BASE}/out"
os.makedirs(OUT_DIR, exist_ok=True)

import torch
from PIL import Image
from diffusers import QwenImageEditPlusPipeline

spec = json.load(open(f"{IN_DIR}/jobs.json", encoding="utf-8"))
jobs = [j for j in spec["jobs"] if (not ONLY or j["id"] in ONLY) and (ONLY or j["tier"] in TIERS)]
print(f"{len(jobs)} jobs x {VARIANTS} variants")

# fp8 weight storage (~20 GB) + bf16 compute: fits a 40 GB A100. (4-bit nf4 produced pure-noise images, layer-by-layer
# offload took >8 min per image.) Measured 2026-11-08 on an A100 40GB: about 125-175 s per 1024 px image.
try:
    del pipe
except NameError:
    pass
gc.collect(); torch.cuda.empty_cache()
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
MODEL = "Qwen/Qwen-Image-Edit-2509"
pipe = QwenImageEditPlusPipeline.from_pretrained(MODEL, torch_dtype=torch.bfloat16)
pipe.transformer.enable_layerwise_casting(storage_dtype=torch.float8_e4m3fn, compute_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload()
pipe.set_progress_bar_config(disable=True)
print("GPU GB:", round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1))

def fit(img):
    """Pad to a square canvas on magenta so the reference keeps its proportions."""
    img = img.convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 0, 255, 255)); bg.alpha_composite(img)
    side = max(bg.size)
    canvas = Image.new("RGB", (side, side), (255, 0, 255))
    canvas.paste(bg.convert("RGB"), ((side - bg.width) // 2, (side - bg.height) // 2))
    return canvas.resize((SIZE, SIZE), Image.LANCZOS)

done, failed = 0, []
for j in jobs:
    if "refs" in j:
        refs = [fit(Image.open(f"{IN_DIR}/{path}")) for path in resolve_refs(j, spec["refs"])]
    else:
        ref = fit(Image.open(f"{IN_DIR}/{spec['refs'][j['ref']]}"))
    for v in range(1, VARIANTS + 1):
        out_path = f"{OUT_DIR}/{j['id']}_v{v}_{TAG}.png"
        if os.path.exists(out_path):
            continue
        t0 = time.time()
        try:
            if "refs" in j:
                res = pipe(image=refs, prompt=f"{j['prompt']} {j.get('style', spec['style'])}", negative_prompt=" ",
                           num_inference_steps=STEPS, true_cfg_scale=TRUE_CFG,
                           generator=torch.Generator(device="cuda").manual_seed(1000 + 17 * v)).images[0]
            else:
                res = pipe(image=[ref], prompt=f"{j['prompt']} {j.get('style', spec['style'])}", negative_prompt=" ",
                           num_inference_steps=STEPS, true_cfg_scale=TRUE_CFG,
                           generator=torch.Generator(device="cuda").manual_seed(1000 + 17 * v)).images[0]
            res.save(out_path)
            done += 1
            print(f"OK  {j['id']} v{v}  {time.time() - t0:.0f}s")
        except Exception as e:                      # keep going; report at the end
            failed.append((j["id"], v, repr(e)[:200]))
            print(f"ERR {j['id']} v{v}: {repr(e)[:200]}")
        gc.collect(); torch.cuda.empty_cache()

print(f"done={done} failed={len(failed)}")
for f in failed:
    print("FAILED", f)
