# Colab single cell: Model B, SDXL img2img. No Hugging Face token is required.
import json
import subprocess
import sys
import time
from pathlib import Path

subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "diffusers", "transformers", "accelerate", "safetensors", "Pillow"])

from google.colab import drive

drive.mount("/content/drive", force_remount=False)

import torch
from diffusers import StableDiffusionXLImg2ImgPipeline
from PIL import Image

DRIVE = Path("/content/drive/MyDrive/PumpkinKiller")
OUT = DRIVE / "out"
REF = OUT / "fx_ghost_idle_v1_ghost1.png"
OUT.mkdir(parents=True, exist_ok=True)
if not REF.is_file():
    print("ERROR missing approved reference: %s" % REF)
    raise SystemExit(1)

# SSD-1B is the Apache-2.0 SDXL-derived weight this cell loads.
# img2img at low strength preserves the one supplied ghost rather than chaining edits.
try:
    pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
        "segmind/SSD-1B", torch_dtype=torch.float16, variant="fp16", use_safetensors=True,
    ).to("cuda")
    pipe.enable_attention_slicing()
except Exception as error:
    print("ERROR loading SDXL: %r" % error)
    raise

STYLE = (
    "Dark-fantasy 2D cartoon game art. Thick clean near-black contour, then a thin warm-orange outer glow. "
    "Flat three-tone cel shading and soft highlights; no airbrush or realistic material rendering. "
    "Isolated sprite: solid #FF00FF background, no ground or cast shadow, 10–12% margin. "
    "Do not use photorealism, 3D/plastic, painterly gradients, thin linework, text, watermarks, extra figures, "
    "or magenta/pink inside the subject."
)
NEGATIVE = "realistic, photo, 3D render, plastic shine, painterly, airbrushed gradient, thin line art, soft outline, text, letters, watermark, ground, cast shadow, extra character, duplicate subject, magenta or pink inside the subject"
JOBS = [
    ("testB_puff.png", "Edit the one reference ghost only. Keep its facing-right silhouette, size, colours, and identity. Give it a round open O mouth and a small puff of pale cyan mist blowing to the RIGHT. " + STYLE),
    ("testB_hard.png", "Edit the one reference ghost only. Keep its facing-right silhouette, size, colours, and identity. Make its mouth widest, squeeze both eyes shut, and emit one strong pale cyan mist spray to the RIGHT. " + STYLE),
]

reference = Image.open(REF).convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
records = []
for index, (filename, prompt) in enumerate(JOBS):
    try:
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        image = pipe(
            prompt=prompt, negative_prompt=NEGATIVE, image=reference, strength=0.28,
            guidance_scale=6.5, num_inference_steps=30,
            generator=torch.Generator("cuda").manual_seed(20261110 + index),
        ).images[0]
        torch.cuda.synchronize()
        seconds = time.perf_counter() - started
        peak = int(torch.cuda.max_memory_allocated() / (1024 * 1024))
        image.save(OUT / filename)
        records.append({"file": filename, "seconds": seconds, "peak_vram_mb": peak})
        print("%s: %.2f s, peak %d MB" % (filename, seconds, peak))
    except Exception as error:  # keep the second controlled case runnable after one failure
        print("ERROR %s: %r" % (filename, error))

(OUT / "testB_metrics.json").write_text(json.dumps({"model": "B", "records": records}, indent=2), encoding="utf-8")
