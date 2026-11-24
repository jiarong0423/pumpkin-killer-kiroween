# Pumpkin Killer - Colab layered-split job (Qwen-Image-Layered through diffusers).
#
# What it does: takes ONE finished scene picture and splits it into several RGBA layers (sky, far shapes, trees,
# tombstones, ground, ...) so the game can scroll them at different speeds and sway them in the wind.
# Design: docs/visual_quality_plan.md (part B). Game side: js/scene_layers.js, docs/scene_layers_integration.md.
#
# HOW TO USE (Colab, GPU = A100 40 GB; use a FRESH runtime):
#   Cell 1  (install)   !pip install -q -U git+https://github.com/huggingface/diffusers "transformers<5" accelerate pillow numpy
#                       (the layered pipeline is new; a released diffusers may not have it yet. The art job found that
#                       transformers 5.x gave pure-noise images, so keep transformers<5 here too.)
#                       Optional, only when UPSCALE = True:  !pip install -q realesrgan basicsr
#   Cell 2  (this file) paste the whole file. Set PHASE, ONLY, LAYERS below. Run.
#   PHASE = "decompose"  -> writes raw layers + a contact sheet per seed. Look at the sheet.
#   (by hand)            -> write MyDrive/PumpkinKiller/inputs/layer_map_<scene>.json (format below).
#   PHASE = "finish"     -> cleans, optionally upscales, names, crops and checks the mapped layers.
#
# Inputs  : Drive MyDrive/PumpkinKiller/out/<file>.png            the scene picture (JOBS[i]["input"])
#           Drive MyDrive/PumpkinKiller/inputs/layer_map_<scene>.json   (phase "finish" only)
# Outputs : MyDrive/PumpkinKiller/layers_raw/<scene>/<scene>_s<seed>_L<n>_<idx>.png   raw layers, working size
#           MyDrive/PumpkinKiller/layers_raw/<scene>/<scene>_s<seed>_L<n>_sheet.png   contact sheet (checkerboard)
#           MyDrive/PumpkinKiller/layers_out/<scene>/<nn>_<name>.png                  final layers
#           MyDrive/PumpkinKiller/layers_out/<scene>/report.json                      quality checks
#           MyDrive/PumpkinKiller/layers_out/<scene>/manifest.draft.json              draft manifest for the game
# Every file is written the moment it is finished and finished files are skipped on a re-run, so a disconnect
# loses nothing. One failure never stops the loop.
#
# layer_map_<scene>.json (written by hand after looking at the contact sheet):
#   { "seed": 777, "layers": 8,
#     "map": [ { "index": 0, "name": "sky",    "depth": 0,  "opaque": true,  "parallax": 0 },
#              { "index": 3, "name": "trees",  "depth": 20, "rect": [0, 80, 1920, 820], "parallax": 0.35,
#                "sway": 14, "pivotY": 860 },
#              { "index": [5, 6], "name": "tombs", "depth": 30, "rect": [0, 540, 1920, 360], "parallax": 0.7 } ] }
#   "index" may be a list: those raw layers are composited into one named layer (the model sometimes splits finer
#   than we want). "rect" is where the layer goes on the 1920 x 1080 canvas; the layer is cropped to it.
#
# LICENCE CHECK (do this before you set LICENSE_ACK = True):
#   The model: Apache 2.0 according to the task brief. Read the licence line on https://huggingface.co/Qwen/Qwen-Image-Layered
#   The upscaler (only if UPSCALE = True): Real-ESRGAN, https://github.com/xinntao/Real-ESRGAN . From memory its code is
#   BSD-3-Clause. THIS WAS NOT CHECKED when the file was written (no web access). Read its LICENSE file, the
#   notes of the weights file you download (RealESRGAN_x4plus.pth), and the contest rules. If the licence is not
#   clear, leave UPSCALE = False and regenerate the scene natively at 1920 x 1080 instead.
#
# NOT TESTED: this script was written without a GPU and was never run. The calls to diffusers follow the model card
# as the author remembers it (QwenImageLayeredPipeline, layers, resolution, true_cfg_scale, cfg_normalize,
# use_en_prompt, generator, output.images[0] = list of RGBA layers). If an argument name differs, the first run
# fails with a clear TypeError; fix the name from the model card. Run ONE scene first: ONLY = ["graveyard"].

import os, json, time, gc

LICENSE_ACK = False     # set True only after you read the licence pages above
PHASE = "decompose"     # "decompose" or "finish"
ONLY = []               # [] = every job; or a list of scene ids, e.g. ["graveyard"]
LAYERS = 8              # 4 or 8 (the game allows at most 8 layers per scene)
RESOLUTION = 1024       # the model's working size: 640 or 1024
STEPS = 50
TRUE_CFG = 4.0
SEEDS = [777, 778, 779]  # three tries per scene; pick the best sheet
UPSCALE = False         # True: Real-ESRGAN 2x on the RGB channels (read the licence note first)
TARGET_W, TARGET_H = 1920, 1080
BASE = "/content/drive/MyDrive/PumpkinKiller"

# One entry per scene. "input" is a file in MyDrive/PumpkinKiller/out/ (the Edit job's output folder).
JOBS = [
    {"id": "graveyard", "input": "bg_graveyard_native_v1.png"},
    {"id": "belltower", "input": "bg_belltower_native_v1.png"},
    {"id": "pumpkin",   "input": "bg_pumpkin_field_native_v1.png"},
]

# Defaults used for manifest.draft.json when the layer map does not say otherwise.
# (depth, parallax, plane); same numbers as the example in docs/visual_quality_plan.md.
SLOT_DEFAULTS = {
    "sky": (0, 0.0, "back"), "moon_glow": (5, 0.02, "back"), "castle": (10, 0.1, "back"),
    "trees": (20, 0.35, "back"), "tombs": (30, 0.7, "back"), "ground": (40, 1.0, "back"),
    "fog": (50, 0.9, "back"), "foreground": (90, 1.3, "front"),
}

if not LICENSE_ACK:
    raise RuntimeError("LICENSE_ACK is False. Read the licence notes at the top of this file first.")

import numpy as np
from PIL import Image, ImageDraw
from google.colab import drive
drive.mount("/content/drive")
IN_DIR, OUT_SRC = f"{BASE}/inputs", f"{BASE}/out"
RAW_DIR, FIN_DIR = f"{BASE}/layers_raw", f"{BASE}/layers_out"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(FIN_DIR, exist_ok=True)


# ----------------------------------------------------------------------------------------------------------
# helpers (pure numpy / PIL, usable without a GPU)

def checkerboard(size, cell=24):
    w, h = size
    a = np.zeros((h, w, 3), np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    a[((yy // cell + xx // cell) % 2) == 0] = (70, 70, 70)
    a[((yy // cell + xx // cell) % 2) == 1] = (110, 110, 110)
    return Image.fromarray(a, "RGB")


def contact_sheet(layers, thumb_w=480):
    """A grid of the layers over a checkerboard so you can see the alpha. Index is written on each tile."""
    th = int(thumb_w * layers[0].height / layers[0].width)
    cols = 4 if len(layers) > 4 else len(layers)
    rows = (len(layers) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows * th), (30, 30, 30))
    for i, lay in enumerate(layers):
        tile = checkerboard((thumb_w, th))
        small = lay.convert("RGBA").resize((thumb_w, th), Image.LANCZOS)
        tile.paste(small, (0, 0), small)
        ImageDraw.Draw(tile).text((8, 6), f"#{i}", fill=(255, 255, 0))
        sheet.paste(tile, ((i % cols) * thumb_w, (i // cols) * th))
    return sheet


def bleed_colour(img, iters=8):
    """Copy colour from opaque neighbours into transparent pixels (alpha untouched), so resizing never mixes in
    black or magenta from the invisible pixels. np.roll wraps at the edges; with 8 iterations that only matters
    for layers whose opposite edges are both opaque, where nothing needs filling anyway."""
    a = np.asarray(img.convert("RGBA"), dtype=np.uint8).copy()
    rgb = a[..., :3].astype(np.float32)
    known = a[..., 3] > 8
    for _ in range(iters):
        if known.all():
            break
        acc = np.zeros_like(rgb)
        cnt = np.zeros(known.shape, np.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                k = np.roll(known, (dy, dx), (0, 1))
                acc += np.roll(rgb, (dy, dx), (0, 1)) * k[..., None]
                cnt += k
        fill = (~known) & (cnt > 0)
        rgb[fill] = acc[fill] / cnt[fill][:, None]
        known = known | fill
    a[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


_UPSAMPLER = None


def upscale2x(img):
    """RGB through Real-ESRGAN (2x), alpha through Lanczos. Returns None when the upscaler is not usable."""
    global _UPSAMPLER
    if not UPSCALE:
        return None
    try:
        if _UPSAMPLER is None:
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
            url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
            _UPSAMPLER = RealESRGANer(scale=4, model_path=url, model=model, tile=512, tile_pad=10, pre_pad=0, half=True)
        rgba = img.convert("RGBA")
        bgr = np.asarray(rgba.convert("RGB"))[..., ::-1].copy()          # the library expects BGR
        out, _ = _UPSAMPLER.enhance(bgr, outscale=2)
        rgb = Image.fromarray(np.ascontiguousarray(out[..., ::-1]), "RGB")
        alpha = rgba.getchannel("A").resize(rgb.size, Image.LANCZOS)
        rgb.putalpha(alpha)
        return rgb
    except Exception as e:          # known failure: basicsr import error with a newer torchvision
        print("upscale skipped:", repr(e)[:200])
        _UPSAMPLER = False
        return None


def check_layer(img, opaque=False):
    """Numbers for the quality table in docs/visual_quality_plan.md (B9). Thresholds there are INVENTED."""
    a = np.asarray(img.convert("RGBA"))
    alpha = a[..., 3]
    rgb = a[..., :3].astype(int)
    vis = alpha > 16
    magenta = vis & (rgb[..., 0] > 200) & (rgb[..., 2] > 200) & (rgb[..., 1] < 90)
    nvis = int(vis.sum())
    semi = (alpha > 16) & (alpha < 240)
    return {
        "size": list(img.size),
        "coverage": round(float(vis.mean()), 4),
        "magenta_px": int(magenta.sum()),
        "semi_transparent_share": round(float(semi.sum()) / nvis, 4) if nvis else 0.0,
        "opaque_ok": bool((alpha == 255).all()) if opaque else None,
        "empty": nvis == 0,
    }


def tile_seam(img):
    """Mean absolute difference between the first and last column of a tileable layer (0..255)."""
    a = np.asarray(img.convert("RGBA")).astype(float)
    return float(np.abs(a[:, 0, :] - a[:, -1, :]).mean())


def recomposite_psnr(layers, original):
    """Composite the layers (given back to front, already at the original size) and compare with the input."""
    base = Image.new("RGBA", original.size, (0, 0, 0, 255))
    for lay in layers:
        base.alpha_composite(lay.convert("RGBA").resize(original.size, Image.LANCZOS))
    a = np.asarray(base.convert("RGB"), dtype=np.float64)
    b = np.asarray(original.convert("RGB"), dtype=np.float64)
    mse = float(((a - b) ** 2).mean())
    return 99.0 if mse == 0 else round(10 * np.log10(255.0 ** 2 / mse), 2)


# ----------------------------------------------------------------------------------------------------------
# phase 1: decompose

def run_decompose(jobs):
    import torch
    from diffusers import QwenImageLayeredPipeline
    gc.collect()
    torch.cuda.empty_cache()
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    pipe = QwenImageLayeredPipeline.from_pretrained("Qwen/Qwen-Image-Layered", torch_dtype=torch.bfloat16)
    # Same memory recipe as colab/pumpkin_assets_job.py (fp8 weight storage, bf16 compute, CPU offload).
    # ASSUMPTION: the layered pipeline has the same `transformer` attribute. If not, remove these two lines.
    pipe.transformer.enable_layerwise_casting(storage_dtype=torch.float8_e4m3fn, compute_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()
    pipe.set_progress_bar_config(disable=True)
    failed = []
    for j in jobs:
        src = f"{OUT_SRC}/{j['input']}"
        out_dir = f"{RAW_DIR}/{j['id']}"
        os.makedirs(out_dir, exist_ok=True)
        if not os.path.exists(src):
            failed.append((j["id"], 0, "input not found: " + src))
            print("MISSING", src)
            continue
        image = Image.open(src).convert("RGBA")
        print(f"{j['id']}: input {image.size}")
        for seed in SEEDS:
            sheet_path = f"{out_dir}/{j['id']}_s{seed}_L{LAYERS}_sheet.png"
            if os.path.exists(sheet_path):
                continue
            t0 = time.time()
            try:
                out = pipe(image=image, negative_prompt=" ", true_cfg_scale=TRUE_CFG,
                           num_inference_steps=STEPS, num_images_per_prompt=1, layers=LAYERS,
                           resolution=RESOLUTION, cfg_normalize=True, use_en_prompt=True,
                           generator=torch.Generator(device="cuda").manual_seed(seed))
                layers = out.images[0]
                print(f"  seed {seed}: {len(layers)} layers, size {layers[0].size}")   # the first run tells the real size
                for i, lay in enumerate(layers):
                    lay.convert("RGBA").save(f"{out_dir}/{j['id']}_s{seed}_L{LAYERS}_{i:02d}.png")
                contact_sheet(layers).save(sheet_path)            # written last: its existence marks the seed as done
                print(f"OK  {j['id']} seed {seed}  {time.time() - t0:.0f}s")
            except Exception as e:
                failed.append((j["id"], seed, repr(e)[:200]))
                print(f"ERR {j['id']} seed {seed}: {repr(e)[:200]}")
            gc.collect()
            torch.cuda.empty_cache()
    print(f"decompose done, failed={len(failed)}")
    for f in failed:
        print("FAILED", f)


# ----------------------------------------------------------------------------------------------------------
# phase 2: finish

def finish_scene(j):
    map_path = f"{IN_DIR}/layer_map_{j['id']}.json"
    if not os.path.exists(map_path):
        print("no layer map for", j["id"], "- write", map_path, "after looking at the sheet")
        return
    spec = json.load(open(map_path, encoding="utf-8"))
    seed, n = spec["seed"], spec.get("layers", LAYERS)
    raw_dir, out_dir = f"{RAW_DIR}/{j['id']}", f"{FIN_DIR}/{j['id']}"
    os.makedirs(out_dir, exist_ok=True)
    original = Image.open(f"{OUT_SRC}/{j['input']}").convert("RGB")
    report, manifest_layers, finished = {}, [], []
    for entry in sorted(spec["map"], key=lambda m: m["depth"]):
        idx = entry["index"] if isinstance(entry["index"], list) else [entry["index"]]
        parts = [Image.open(f"{raw_dir}/{j['id']}_s{seed}_L{n}_{i:02d}.png").convert("RGBA") for i in idx]
        img = parts[0]
        for extra in parts[1:]:
            img = Image.alpha_composite(img, extra.resize(img.size, Image.LANCZOS))
        img = bleed_colour(img)
        up = upscale2x(img)
        if up is not None:
            img = up
        full = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)      # the raw layer covers the whole canvas
        rect = entry.get("rect")
        if rect:
            x, y, w, h = rect
            full = full.crop((x, y, x + w, y + h))
        name, nn = entry["name"], f"{int(entry['depth']):02d}"
        path = f"{out_dir}/{nn}_{name}.png"
        full.save(path, optimize=True)
        # For the recomposite check, put the cropped layer back where it belongs on the full canvas.
        if rect:
            placed = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
            placed.paste(full, (rect[0], rect[1]))
        else:
            placed = full
        finished.append(placed)
        rep = check_layer(full, opaque=bool(entry.get("opaque")))
        if entry.get("tileX"):
            rep["tile_seam"] = round(tile_seam(full), 2)
        report[name] = rep
        depth, parallax, plane = SLOT_DEFAULTS.get(name, (entry["depth"], 0.5, "back"))
        ml = {"name": name, "file": f"assets/layers/{j['id']}/{nn}_{name}.png", "depth": entry["depth"],
              "parallax": entry.get("parallax", parallax)}
        for key in ("rect", "sway", "swayHz", "pivotY", "tileX", "drift", "calmDrift", "blend", "alpha", "pulse",
                    "pulseHz", "plane", "required"):
            if key in entry:
                ml[key] = entry[key]
        if "plane" not in ml and plane == "front":
            ml["plane"] = "front"
        manifest_layers.append(ml)
        print(f"  {nn}_{name}: {rep}")
    report["_recomposite_psnr_db"] = recomposite_psnr(finished, original)
    json.dump(report, open(f"{out_dir}/report.json", "w", encoding="utf-8"), indent=2)
    json.dump({"version": 1, "scene": j["id"], "width": TARGET_W, "height": TARGET_H, "maxCamera": 24,
               "layers": manifest_layers}, open(f"{out_dir}/manifest.draft.json", "w", encoding="utf-8"), indent=2)
    print(f"{j['id']}: finished {len(manifest_layers)} layers, recomposite PSNR {report['_recomposite_psnr_db']} dB")


jobs = [j for j in JOBS if not ONLY or j["id"] in ONLY]
print(f"{len(jobs)} scenes, phase {PHASE}")
if PHASE == "decompose":
    run_decompose(jobs)
elif PHASE == "finish":
    for j in jobs:
        try:
            finish_scene(j)
        except Exception as e:
            print(f"ERR finish {j['id']}: {repr(e)[:300]}")
else:
    raise ValueError("PHASE must be 'decompose' or 'finish'")
