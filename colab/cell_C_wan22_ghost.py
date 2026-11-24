# Colab single cell: Model C, official Wan2.2 TI2V-5B inference. No token or secret is used.
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

try:
    # Installs are first so this cell remains self-contained on a fresh Colab runtime.
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub", "Pillow", "imageio[ffmpeg]", "av"])
    from google.colab import drive
    drive.mount("/content/drive", force_remount=False)

    import imageio.v3 as iio
    from huggingface_hub import snapshot_download
    from PIL import Image

    DRIVE = Path("/content/drive/MyDrive/PumpkinKiller")
    OUT = DRIVE / "out"
    REF = OUT / "fx_ghost_idle_v1_ghost1.png"
    OUT.mkdir(parents=True, exist_ok=True)
    if not REF.is_file():
        raise FileNotFoundError("missing approved reference: %s" % REF)

    REPO = Path("/content/Wan2.2")
    if not REPO.exists():
        subprocess.check_call(["git", "clone", "--depth", "1", "https://github.com/Wan-Video/Wan2.2.git", str(REPO)])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", str(REPO / "requirements.txt")])
    CHECKPOINT = Path("/content/Wan2.2-TI2V-5B")
    if not CHECKPOINT.exists():
        snapshot_download("Wan-AI/Wan2.2-TI2V-5B", local_dir=str(CHECKPOINT))

    # TI2V-5B supports 720P only. Letterboxing retains the sole reference's scale and magenta matte.
    source = Image.open(REF).convert("RGB")
    fitted = source.copy()
    fitted.thumbnail((1280, 704), Image.Resampling.LANCZOS)
    input_image = Image.new("RGB", (1280, 704), (251, 0, 247))
    input_image.paste(fitted, ((1280 - fitted.width) // 2, (704 - fitted.height) // 2))
    input_path = OUT / "testC_input.png"
    input_image.save(input_path)

    video = OUT / "testC_ghost_blow.mp4"
    prompt = (
        "One isolated facing-right cartoon ghost on a flat #FF00FF background. Start calm, then open a round O mouth, "
        "then squeeze both eyes shut and blow one strong pale cyan mist spray to the RIGHT. Preserve the exact identity, "
        "scale, thick near-black contour, thin warm-orange outer rim, and flat three-tone cel shading of the input ghost. "
        "No extra characters, lantern, chain, ground, text, watermark, photorealism, 3D, airbrush, or pink in the ghost."
    )

    def gpu_memory_mb():
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True, capture_output=True, check=True,
        )
        return max(int(line.strip()) for line in result.stdout.splitlines() if line.strip())

    command = [
        sys.executable, "generate.py", "--task", "ti2v-5B", "--size", "1280*704", "--frame_num", "25",
        "--ckpt_dir", str(CHECKPOINT), "--offload_model", "True", "--convert_model_dtype", "--t5_cpu",
        "--image", str(input_path), "--prompt", prompt, "--base_seed", "20261110", "--save_file", str(video),
    ]
    # The official program logs this immediately before WanTI2V.generate(). Start
    # the fair timer there, after the checkpoint has loaded but before sampling.
    peak, started = 0, None
    process = subprocess.Popen(command, cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, bufsize=1)
    def relay_output():
        for line in process.stdout:
            print(line, end="")
            if "Generating video" in line and timer[0] is None:
                timer[0] = time.perf_counter()
    timer = [None]
    reader = threading.Thread(target=relay_output, daemon=True)
    reader.start()
    while process.poll() is None:
        if timer[0] is not None:
            try:
                peak = max(peak, gpu_memory_mb())
            except Exception:
                pass  # Report the generation result even if this runtime has no nvidia-smi telemetry.
        time.sleep(0.25)
    reader.join(timeout=5)
    if process.returncode:
        raise RuntimeError("official Wan generate.py exited %d" % process.returncode)
    if timer[0] is None:
        raise RuntimeError("could not find Wan's 'Generating video' log marker for a fair inference timer")
    started = timer[0]
    elapsed = time.perf_counter() - started
    try:
        peak = max(peak, gpu_memory_mb())
    except Exception:
        pass

    frames = list(iio.imiter(video, plugin="pyav"))
    if len(frames) < 25:
        raise RuntimeError("expected 25 generated frames, got %d" % len(frames))
    selected = [(0, "testC_frame_00.png"), (12, "testC_frame_12.png"), (24, "testC_frame_24.png")]
    records = []
    for index, filename in selected:
        Image.fromarray(frames[index]).save(OUT / filename)
        records.append({"file": filename, "frame": index})
        print("%s: from 25-frame clip, generation %.2f s, peak %d MB" % (filename, elapsed, peak))
    (OUT / "testC_metrics.json").write_text(json.dumps({
        "model": "C", "run_seconds": elapsed, "peak_vram_mb": peak, "records": records,
    }, indent=2), encoding="utf-8")
except Exception as error:  # one visible line makes notebook failures easy to capture in the main-line log
    print("ERROR Model C Wan2.2 TI2V-5B: %r" % error)
