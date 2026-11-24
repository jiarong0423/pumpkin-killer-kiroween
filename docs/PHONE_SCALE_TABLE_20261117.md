# Phone scale table (landscape), 2026-11-17

Source of the sizes: `docs/device_specs/phone_viewports_20261117.csv` (third-party aggregator, every value labelled unverified by the page; the owner's phone is measured). Formulas and constants: `scripts/phone_scale_table.py` header. World 1920 x 1080, stage height = viewport height - 52 (dock strip), scale s = stage height / 1080, canvas width at most 2.6 x stage height.

Object sizes on screen = world size x s (CSS px). Unit = 220 frame, hit = 140 x 190 box, bar = 150 wide HP bar, crate = 64, spear = 210 long. 'x phone' = s divided by the owner's phone s (fullscreen). Flags: SMALL = unit under 60 px; EMPTY = unused screen width beyond the 2.6 aspect cap.

| Phone | Case | Viewport | Stage w x h | s | x phone | Unit | Hit box | HP bar | Crate | Spear | Pad each side | Flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Apple iPhone 17 Pro Max | fullscreen | 956x440 | 956x388 | 0.359 | 1.26 | 79 | 50x68 | 54 | 23 | 75 | 133 | - |
| Apple iPhone 17 Pro Max | address bar | 912x346 | 764x294 | 0.272 | 0.95 | 60 | 38x52 | 41 | 17 | 57 | 121 | SMALL EMPTY W 148px |
| Apple iPhone 17 Pro | fullscreen | 874x402 | 874x350 | 0.324 | 1.14 | 71 | 45x62 | 49 | 21 | 68 | 126 | - |
| Apple iPhone 17 Pro | address bar | 830x308 | 666x256 | 0.237 | 0.83 | 52 | 33x45 | 36 | 15 | 50 | 105 | SMALL EMPTY W 164px |
| Apple iPhone Air | fullscreen | 912x420 | 912x368 | 0.341 | 1.19 | 75 | 48x65 | 51 | 22 | 72 | 129 | - |
| Apple iPhone Air | address bar | 868x326 | 712x274 | 0.254 | 0.89 | 56 | 36x48 | 38 | 16 | 53 | 113 | SMALL EMPTY W 156px |
| Apple iPhone 17 | fullscreen | 874x402 | 874x350 | 0.324 | 1.14 | 71 | 45x62 | 49 | 21 | 68 | 126 | - |
| Apple iPhone 17 | address bar | 830x308 | 666x256 | 0.237 | 0.83 | 52 | 33x45 | 36 | 15 | 50 | 105 | SMALL EMPTY W 164px |
| Apple iPhone 16e | fullscreen | 844x390 | 844x338 | 0.313 | 1.10 | 69 | 44x59 | 47 | 20 | 66 | 122 | - |
| Apple iPhone 16e | address bar | 800x296 | 634x244 | 0.226 | 0.79 | 50 | 32x43 | 34 | 14 | 47 | 100 | SMALL EMPTY W 166px |
| Apple iPhone 15 Pro Max | fullscreen | 932x430 | 932x378 | 0.350 | 1.23 | 77 | 49x66 | 52 | 22 | 74 | 130 | - |
| Apple iPhone 15 Pro Max | address bar | 888x336 | 738x284 | 0.263 | 0.92 | 58 | 37x50 | 39 | 17 | 55 | 117 | SMALL EMPTY W 150px |
| Apple iPhone 15 Pro | fullscreen | 852x393 | 852x341 | 0.316 | 1.11 | 69 | 44x60 | 47 | 20 | 66 | 123 | - |
| Apple iPhone 15 Pro | address bar | 808x299 | 642x247 | 0.229 | 0.80 | 50 | 32x43 | 34 | 15 | 48 | 102 | SMALL EMPTY W 166px |
| Apple iPhone 14 Plus | fullscreen | 926x428 | 926x376 | 0.348 | 1.22 | 77 | 49x66 | 52 | 22 | 73 | 129 | - |
| Apple iPhone 14 Plus | address bar | 882x334 | 733x282 | 0.261 | 0.92 | 57 | 37x50 | 39 | 17 | 55 | 116 | SMALL EMPTY W 149px |
| Apple iPhone 14 | fullscreen | 844x390 | 844x338 | 0.313 | 1.10 | 69 | 44x59 | 47 | 20 | 66 | 122 | - |
| Apple iPhone 14 | address bar | 800x296 | 634x244 | 0.226 | 0.79 | 50 | 32x43 | 34 | 14 | 47 | 100 | SMALL EMPTY W 166px |
| Apple iPhone SE (3rd gen) | fullscreen | 667x375 | 667x323 | 0.299 | 1.05 | 66 | 42x57 | 45 | 19 | 63 | 46 | - |
| Apple iPhone SE (3rd gen) | address bar | 623x281 | 595x229 | 0.212 | 0.74 | 47 | 30x40 | 32 | 14 | 45 | 94 | SMALL EMPTY W 28px |
| Apple iPhone 13 mini | fullscreen | 812x375 | 812x323 | 0.299 | 1.05 | 66 | 42x57 | 45 | 19 | 63 | 119 | - |
| Apple iPhone 13 mini | address bar | 768x281 | 595x229 | 0.212 | 0.74 | 47 | 30x40 | 32 | 14 | 45 | 94 | SMALL EMPTY W 173px |
| Google Pixel 10 Pro XL | fullscreen | 921x414 | 921x362 | 0.335 | 1.18 | 74 | 47x64 | 50 | 21 | 70 | 139 | - |
| Google Pixel 10 Pro XL | address bar | 877x320 | 697x268 | 0.248 | 0.87 | 55 | 35x47 | 37 | 16 | 52 | 110 | SMALL EMPTY W 180px |
| Google Pixel 10 Pro | fullscreen | 914x410 | 914x358 | 0.331 | 1.16 | 73 | 46x63 | 50 | 21 | 70 | 139 | - |
| Google Pixel 10 Pro | address bar | 870x316 | 686x264 | 0.244 | 0.86 | 54 | 34x46 | 37 | 16 | 51 | 109 | SMALL EMPTY W 184px |
| Google Pixel 10 | fullscreen | 923x412 | 923x360 | 0.333 | 1.17 | 73 | 47x63 | 50 | 21 | 70 | 142 | - |
| Google Pixel 10 | address bar | 879x318 | 692x266 | 0.246 | 0.86 | 54 | 34x47 | 37 | 16 | 52 | 109 | SMALL EMPTY W 187px |
| Google Pixel 8 | fullscreen | 915x412 | 915x360 | 0.333 | 1.17 | 73 | 47x63 | 50 | 21 | 70 | 138 | - |
| Google Pixel 8 | address bar | 871x318 | 692x266 | 0.246 | 0.86 | 54 | 34x47 | 37 | 16 | 52 | 109 | SMALL EMPTY W 179px |
| Google Pixel 7 Pro | fullscreen | 892x412 | 892x360 | 0.333 | 1.17 | 73 | 47x63 | 50 | 21 | 70 | 126 | - |
| Google Pixel 7 Pro | address bar | 848x318 | 692x266 | 0.246 | 0.86 | 54 | 34x47 | 37 | 16 | 52 | 109 | SMALL EMPTY W 156px |
| Samsung Galaxy S25 Ultra | fullscreen | 891x412 | 891x360 | 0.333 | 1.17 | 73 | 47x63 | 50 | 21 | 70 | 126 | - |
| Samsung Galaxy S25 Ultra | address bar | 847x318 | 692x266 | 0.246 | 0.86 | 54 | 34x47 | 37 | 16 | 52 | 109 | SMALL EMPTY W 155px |
| Samsung Galaxy S25 | fullscreen | 780x360 | 780x308 | 0.285 | 1.00 | 63 | 40x54 | 43 | 18 | 60 | 116 | - |
| Samsung Galaxy S25 | address bar | 736x266 | 556x214 | 0.198 | 0.69 | 44 | 28x38 | 30 | 13 | 42 | 88 | SMALL EMPTY W 180px |
| Samsung Galaxy S23+ | fullscreen | 854x384 | 854x332 | 0.307 | 1.08 | 68 | 43x58 | 46 | 20 | 65 | 132 | - |
| Samsung Galaxy S23+ | address bar | 810x290 | 619x238 | 0.220 | 0.77 | 48 | 31x42 | 33 | 14 | 46 | 98 | SMALL EMPTY W 191px |
| Samsung Galaxy S21 | fullscreen | 800x360 | 800x308 | 0.285 | 1.00 | 63 | 40x54 | 43 | 18 | 60 | 126 | - |
| Samsung Galaxy S21 | address bar | 756x266 | 556x214 | 0.198 | 0.69 | 44 | 28x38 | 30 | 13 | 42 | 88 | SMALL EMPTY W 200px |
| Samsung Galaxy Z Flip6 | fullscreen | 960x393 | 887x341 | 0.316 | 1.11 | 69 | 44x60 | 47 | 20 | 66 | 140 | EMPTY W 73px |
| Samsung Galaxy Z Flip6 | address bar | 916x299 | 642x247 | 0.229 | 0.80 | 50 | 32x43 | 34 | 15 | 48 | 102 | SMALL EMPTY W 274px |
| Samsung Galaxy Z Fold6 (cover) | fullscreen | 792x323 | 705x271 | 0.251 | 0.88 | 55 | 35x48 | 38 | 16 | 53 | 111 | SMALL EMPTY W 87px |
| Samsung Galaxy Z Fold6 (cover) | address bar | 748x229 | 460x177 | 0.164 | 0.57 | 36 | 23x31 | 25 | 10 | 34 | 73 | SMALL EMPTY W 288px |
| Samsung Galaxy Z Fold6 (main) | fullscreen | 720x619 | 720x405 | 0.375 | 1.31 | 82 | 52x71 | 56 | 24 | 79 | 0 | LETTERBOX H 162px |
| Samsung Galaxy Z Fold6 (main) | address bar | 676x525 | 676x380 | 0.352 | 1.23 | 77 | 49x67 | 53 | 23 | 74 | 0 | LETTERBOX H 93px |
| Huawei Mate 70 Pro | fullscreen | 885x411 | 885x359 | 0.332 | 1.17 | 73 | 47x63 | 50 | 21 | 70 | 123 | - |
| Huawei Mate 70 Pro | address bar | 841x317 | 689x265 | 0.245 | 0.86 | 54 | 34x47 | 37 | 16 | 52 | 109 | SMALL EMPTY W 152px |
| Xiaomi 15 Pro | fullscreen | 914x412 | 914x360 | 0.333 | 1.17 | 73 | 47x63 | 50 | 21 | 70 | 137 | - |
| Xiaomi 15 Pro | address bar | 870x318 | 692x266 | 0.246 | 0.86 | 54 | 34x47 | 37 | 16 | 52 | 109 | SMALL EMPTY W 178px |
| OPPO Find X8 Pro | fullscreen | 869x395 | 869x343 | 0.318 | 1.11 | 70 | 44x60 | 48 | 20 | 67 | 130 | - |
| OPPO Find X8 Pro | address bar | 825x301 | 647x249 | 0.231 | 0.81 | 51 | 32x44 | 35 | 15 | 48 | 102 | SMALL EMPTY W 178px |
| vivo X200 Pro | fullscreen | 875x394 | 875x342 | 0.317 | 1.11 | 70 | 44x60 | 48 | 20 | 66 | 134 | - |
| vivo X200 Pro | address bar | 831x300 | 645x248 | 0.230 | 0.81 | 51 | 32x44 | 34 | 15 | 48 | 102 | SMALL EMPTY W 186px |
| Honor Magic7 Pro | fullscreen | 875x400 | 875x348 | 0.322 | 1.13 | 71 | 45x61 | 48 | 21 | 68 | 128 | - |
| Honor Magic7 Pro | address bar | 831x306 | 660x254 | 0.235 | 0.82 | 52 | 33x45 | 35 | 15 | 49 | 104 | SMALL EMPTY W 171px |
| Realme RMX2075 (owner phone - measured) | fullscreen | 800x360 | 800x308 | 0.285 | 1.00 | 63 | 40x54 | 43 | 18 | 60 | 126 | - |
| Realme RMX2075 (owner phone - measured) | address bar | 756x266 | 556x214 | 0.198 | 0.69 | 44 | 28x38 | 30 | 13 | 42 | 88 | SMALL EMPTY W 200px |

## Reverse formula

For a wanted unit size U (CSS px): s = U / 220, stage height = 1080 x s, viewport height = 1080 x s + 52, stage width = min(2.6 x stage height, viewport width). Examples: U = 60 needs viewport height >= 347; U = 70 needs >= 396; U = 80 needs >= 445.
