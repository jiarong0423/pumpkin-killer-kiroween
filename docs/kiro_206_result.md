# Kiro task 206 result

## What changed

- `js/qr_code.js`: extended byte-mode QR encoding to level L versions 1–10 and level M versions 1–7. `codewords`, `encode`, and `draw` now accept a level (`'L'` remains the default); data is Reed–Solomon encoded and interleaved across the required block groups. Versions 7–10 write version information. Non-ASCII text includes UTF-8 ECI 26. `QrCode.draw` returns `false` for a payload beyond supported capacity rather than passing a `RangeError` to the page. The existing L vectors remain pinned, including the complete `HELLO WORLD` codeword array and matrix SHA-256.
- `scripts/test_qr_code.js`: checks every supported byte capacity, smallest fitting version, overflow behaviour, the retained L vector, `draw` overflow fallback, SVG output, and the hosted-link measurement.
- `scripts/test_qr_decode.py`: obtains matrices through the Node encoder, rasterizes them at six pixels per module with a four-module quiet zone, then attempts OpenCV decoding. It exits loudly with `SKIP` when no installed decoder can correctly decode the required UTF-8 ECI payloads.
- `scripts/make_site_qr.js`: accepts `node scripts/make_site_qr.js <https-url> [--out path]`, defaults `--out` to `(not published)`, emits a black-on-white SVG with a four-module quiet zone, and prints its selected version and level. It prefers M and falls back to L when M does not fit. No site QR asset was generated because no owner-provided hosted URL exists.

## Capacity table

| Version | L byte payload | M byte payload |
|---:|---:|---:|
| 1 | 17 | 14 |
| 2 | 32 | 26 |
| 3 | 53 | 42 |
| 4 | 78 | 62 |
| 5 | 106 | 84 |
| 6 | 134 | 106 |
| 7 | 154 | 122 |
| 8 | 192 | unsupported |
| 9 | 230 | unsupported |
| 10 | 271 | unsupported |

## Verification run

```text
node scripts/test_qr_code.js
qr code capacity L v1-v10 and M v1-v7: ok

python3 -B scripts/test_qr_decode.py
SKIP: cv2 QRCodeDetector cannot decode the required UTF-8 ECI payloads; pyzbar is not installed
```

## Could not verify

- The installed OpenCV `QRCodeDetector` decodes an ASCII baseline but cannot reliably decode required valid UTF-8 ECI payloads. `pyzbar` is not installed. I did not install a decoder. Therefore the required 200-random-text L/M decode proof was skipped rather than reported as passed. The main line needs to run `python3 -B scripts/test_qr_decode.py` in an environment with an ECI-capable installed decoder.
- The specified hosted-link assertion cannot be true under standard byte-mode QR capacity. `https://` plus a 30-character domain plus `/?room=ABC234` is 51 UTF-8 bytes. Version 3 at level M holds 42 byte-mode bytes, so this link correctly selects version 4 at level M. It fits version 3 at level L (53 bytes). The test pins the real version-4-M outcome instead of claiming an invalid version-3-M QR.
- No site QR was written because the owner has not supplied a real public URL. The CLI should be run after deployment, for example: `node scripts/make_site_qr.js https://<host>/ --out (not published)`.
