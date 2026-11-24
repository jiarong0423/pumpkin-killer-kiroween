# Colab pipeline excerpt (the part that decides the look), copied 2026-11-10 from the running notebook

Model: Qwen/Qwen-Image-Edit-2511 via diffusers QwenImageEditPlusPipeline (bfloat16, layerwise float8, cpu offload). Per job, per variant (seed = 1000 + 17*variant):

    ref = fit(Image.open(ref_path))                 # ONE reference picture, padded square on magenta, resized to SIZE (1024)
    res = pipe(image=[ref],                         # <- a LIST: QwenImageEditPlusPipeline accepts several pictures
               prompt=f"{job['prompt']} {job.get('style', spec['style'])}",
               negative_prompt=job.get("negative", " "),
               num_inference_steps=STEPS (40), true_cfg_scale=TRUE_CFG (4.0),
               [width/height if the job has "w"/"h"], generator=seeded)

Job fields in colab/*.json: id, tier, ref (a key into spec["refs"], file in Drive inputs/), prompt, style (optional text appended), negative (optional), w, h (optional).
Reference keys that exist in Drive inputs: see spec["refs"] in the notebook (units, bar, etc.); a missing file falls back to older outputs for bride/reaper/hunchback only.

FINDING (main line, 2026-11-10): the five wind-ghost jobs used ref "bar" (a HUD bar picture) and prompt text only. The model had NO picture of the game's ghost or of the game's art style, so it drew its own soft-glow teal ghost ((not published)), not the game's thick-near-black-outline, warm-orange-glow cel style.
The pipeline can take more than one reference picture; the job format currently carries only one "ref". A job format with "refs": [style_ref, face_ref] would need a small change to the notebook cell (the main line makes it).
