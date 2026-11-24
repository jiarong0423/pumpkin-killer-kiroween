# Ghost model test plan — 2026-11-10

## Scope and fixed controls
- Input: exactly `out/fx_ghost_idle_v1_ghost1.png`, once per candidate; never edit an output into the next input.
- Output A/B: 1024-square PNGs `testA_`/`testB_` for puff then hard blow; fixed seed 20261110 and the shared style/negative blocks.
- Output C: one 25-frame, 24 fps 1280x704 clip `testC_`; score frames 00, 12, and 24. This is 1.04 seconds, the shortest 4n+1 sequence accepted by Wan's CLI.
- Measure inference only after weights load: wall seconds and peak allocated/observed VRAM; exclude installs, downloads, Drive mount, and model load.
- Run on the same fresh Colab GPU class, without a warm-up image or retry; retain every file and `*_metrics.json`.

## Model B selection, in five lines
- Use `segmind/SSD-1B`, an ungated Apache-2.0 SDXL-derived checkpoint, through `StableDiffusionXLImg2ImgPipeline`.
- Its img2img input is the single approved ghost, so it supplies image-reference conditioning without another weight.
- Strength 0.28 keeps identity and scale more strongly than the requested expression edit; it is a fair failure if this is too weak.
- SSD-1B is smaller than SDXL base, which keeps the comparison practical while retaining the SDXL family requested for B.
- Do not load IP-Adapter or a refiner, so B has one public model weight and no unreported reference path.

## Licences and sources
- A: Qwen-Image-Edit-2511 plus LightX2V Lightning 8-step LoRA, Apache-2.0; the public Lightning card is [here](https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning) but its licence section could not open through fetch.
- B: SSD-1B, Apache-2.0, as declared in its [model card](https://huggingface.co/segmind/SSD-1B); no IP-Adapter/refiner weight is loaded.
- C: Wan-AI/Wan2.2-TI2V-5B and official Wan2.2 code, Apache-2.0; its [official README](https://github.com/Wan-Video/Wan2.2) specifies `ti2v-5B`, 1280x704, 24 fps, 24 GB minimum VRAM, and 4n+1 frames.

## A-only timing addition (exactly 10 lines)
```python
import json, time; testA_records = []
torch.cuda.synchronize()
torch.cuda.reset_peak_memory_stats()
testA_started = time.perf_counter()
# keep the existing pipe(...) and image save unchanged here
torch.cuda.synchronize()
testA_record = {"file": out_name, "seconds": time.perf_counter() - testA_started, "peak_vram_mb": int(torch.cuda.max_memory_allocated() / 1048576)}
testA_records.append(testA_record)
print("%s: %.2f s, peak %d MB" % (out_name, testA_record["seconds"], testA_record["peak_vram_mb"]))
(OUT / "testA_metrics.json").write_text(json.dumps({"model": "A", "records": testA_records}, indent=2), encoding="utf-8")
```
Place lines 2–4 before each existing A pipe call, and lines 6–10 after that image saves; initialise line 1 once before its loop.

## Main-line procedure and gate
1. Stage the approved reference in Drive `out/`; confirm its source hash, dimensions, and flat-magenta matte before A.
2. Run the existing A cell with its two controlled ghost prompts plus the ten timing lines, then preserve `testA_*` and metadata.
3. Run `cell_B_sdxl_ghost.py`, then `cell_C_wan22_ghost.py`; do not change prompts, seed, or reference after seeing A.
4. Run `score_ghost_tests.py` with all `testA_`, `testB_`, and selected `testC_` PNGs and their three metadata files.
5. Record each image's matte standard deviation, tight-key halo width, foreground palette distance, tight-silhouette area/height ratios, keyability, seconds, peak VRAM, plus visual checks for the required mouth, eyes, and rightward mist.
6. The scorer fails an image at matte SD >8, halo >12 px, palette distance >0.35, height scale outside 0.70–1.45, or an empty tight key; owner review remains required for the action.
7. Switch the pipeline only if B or C passes every required frame/image, visibly preserves identity and both actions, and beats A's all-pass result on the recorded quality measures without worse feasible time/VRAM.

## Unverified
No cell or model has run. Wan2.2 TI2V-5B feasibility on a Colab L4 advertised as 24 GB, its actual download access, and its actual 1-second quality are unverified.

Content was rephrased for compliance with licensing restrictions.
