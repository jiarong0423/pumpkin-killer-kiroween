#!/usr/bin/env python3
"""One Bedrock call via the AWS CLI: Stability "Search and Replace" on a unit image.

Usage: aws_search_replace.py <in.png> <out.png> <search_prompt> <prompt> [--profile P] [--region R]
- Input RGBA is flattened on a flat light-grey background (the service wants RGB).
- Exactly ONE paid API call per run. Appends a line to docs/aws_image_calls.log.
- Uses the AWS CLI (no boto3 needed); credentials are never read or printed here.
Exit code 0 on success, 1 on failure.
"""
import sys, io, json, base64, argparse, logging, subprocess, tempfile, shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "docs/aws_image_calls.log"
MODEL = "us.stability.stable-image-search-replace-v1:0"  # on-demand needs the inference profile id
AWS = shutil.which("aws") or "/opt/homebrew/bin/aws"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst"); ap.add_argument("search"); ap.add_argument("prompt")
    ap.add_argument("--profile", default="fitstyle"); ap.add_argument("--region", default="us-east-1")
    a = ap.parse_args()
    logging.basicConfig(filename=str(LOG), level=logging.INFO, format="%(asctime)s %(message)s")
    tmp = Path(tempfile.mkdtemp(prefix="awsimg_"))
    try:
        im = Image.open(a.src).convert("RGBA")
        bg = Image.new("RGBA", im.size, (200, 200, 200, 255))
        bg.alpha_composite(im)
        buf = io.BytesIO(); bg.convert("RGB").save(buf, "PNG")
        body = {"image": base64.b64encode(buf.getvalue()).decode(), "prompt": a.prompt,
                "search_prompt": a.search, "output_format": "png"}
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
        logging.info("OK model=%s src=%s -> %s search=%r", MODEL, a.src, a.dst, a.search)
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
