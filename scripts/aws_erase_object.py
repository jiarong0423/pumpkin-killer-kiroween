#!/usr/bin/env python3
"""One Bedrock call via the AWS CLI: Stability "Erase Object" with an explicit mask.

Usage: aws_erase_object.py <in.png> <mask.png> <out.png> [--profile P] [--region R]
- mask: white = erase, black = keep (same size as the input).
- Input RGBA is flattened on flat light grey (service wants RGB).
- Exactly ONE paid call per run; logs to docs/aws_image_calls.log. Credentials never read or printed.
Exit code 0 on success, 1 on failure.
"""
import sys, io, json, base64, argparse, logging, subprocess, tempfile, shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "docs/aws_image_calls.log"
MODEL = "us.stability.stable-image-erase-object-v1:0"
AWS = shutil.which("aws") or "/opt/homebrew/bin/aws"

def b64png(img):
    buf = io.BytesIO(); img.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("mask"); ap.add_argument("dst")
    ap.add_argument("--profile", default="fitstyle"); ap.add_argument("--region", default="us-east-1")
    a = ap.parse_args()
    logging.basicConfig(filename=str(LOG), level=logging.INFO, format="%(asctime)s %(message)s")
    tmp = Path(tempfile.mkdtemp(prefix="awsimg_"))
    try:
        im = Image.open(a.src).convert("RGBA")
        bg = Image.new("RGBA", im.size, (200, 200, 200, 255)); bg.alpha_composite(im)
        mask = Image.open(a.mask).convert("L")
        if mask.size != im.size:
            raise RuntimeError(f"mask size {mask.size} != image size {im.size}")
        body = {"image": b64png(bg.convert("RGB")), "mask": b64png(mask), "output_format": "png"}
        (tmp / "body.json").write_text(json.dumps(body))
        r = subprocess.run([AWS, "bedrock-runtime", "invoke-model", "--model-id", MODEL,
                            "--body", f"fileb://{tmp/'body.json'}", "--content-type", "application/json",
                            "--accept", "application/json", "--cli-binary-format", "raw-in-base64-out",
                            "--profile", a.profile, "--region", a.region, str(tmp / "out.json")],
                           capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            raise RuntimeError("aws cli failed: " + r.stderr.strip()[:300])
        out = json.loads((tmp / "out.json").read_text())
        reason = (out.get("finish_reasons") or [None])[0]
        if reason or not out.get("images"):
            raise RuntimeError(f"no image returned finish_reason={reason}")
        Path(a.dst).write_bytes(base64.b64decode(out["images"][0]))
        logging.info("OK model=%s src=%s mask=%s -> %s", MODEL, a.src, a.mask, a.dst)
        print("OK", a.dst)
        return 0
    except Exception as e:  # noqa
        logging.error("ERROR %s: %s", type(e).__name__, str(e)[:300])
        print("ERROR", type(e).__name__, str(e)[:300], file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    sys.exit(main())
