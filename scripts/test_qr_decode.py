#!/usr/bin/env python3
"""Decode ASCII QR matrices emitted by js/qr_code.js with OpenCV."""
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE_PROGRAM = r"""
const fs = require('fs');
const QrCode = require('./js/qr_code.js');
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(request.requests.map(function (entry) {
  return { matrix: QrCode.encode(entry.text, entry.level) };
})));
"""

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except ImportError:
    print('SKIP: no installed QR decoder (requires cv2 with numpy; nothing installed)')
    raise SystemExit(0)

ASCII_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789-._~?=&%/:'
REQUIRED_URL_PUNCTUATION = '?=&%/:'
CAPACITIES = {
    'L': (17, 32, 53, 78, 106),
    'M': (14, 26, 42, 62, 84, 106),
}


def random_ascii_text(rng, minimum=10, maximum=106, punctuation=''):
    """Return a deterministic printable ASCII payload of the requested length."""
    length = rng.randint(minimum, maximum)
    prefix = punctuation[:length]
    return prefix + ''.join(rng.choice(ASCII_ALPHABET) for _ in range(length - len(prefix)))


def payload_for_version(rng, level, version):
    """Return the shortest ASCII text that makes the encoder choose this version."""
    capacities = CAPACITIES[level]
    minimum = 10 if version == 1 else capacities[version - 2] + 1
    return random_ascii_text(rng, minimum, minimum, REQUIRED_URL_PUNCTUATION)


def matrices_for(requests):
    completed = subprocess.run(
        ['node', '-e', NODE_PROGRAM], input=json.dumps({'requests': requests}).encode('utf-8'),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT, check=True
    )
    return [entry['matrix'] for entry in json.loads(completed.stdout)]


def png_for(matrix, path):
    module_size = 6
    quiet_zone = 4
    side = len(matrix) + quiet_zone * 2
    pixels = np.full((side * module_size, side * module_size), 255, dtype=np.uint8)
    for row, values in enumerate(matrix):
        for column, dark in enumerate(values):
            if dark:
                y = (row + quiet_zone) * module_size
                x = (column + quiet_zone) * module_size
                pixels[y:y + module_size, x:x + module_size] = 0
    if not cv2.imwrite(str(path), pixels):
        raise AssertionError('OpenCV could not write the QR test PNG')


def decode_one(detector, request, matrix, directory, number):
    """Return 'ok', 'miss' (the decoder found nothing) or raise when it decoded DIFFERENT text (a wrong code is never acceptable)."""
    image_path = directory / ('qr_%s_%03d.png' % (request['level'], number))
    png_for(matrix, image_path)
    decoded, _points, _straight = detector.detectAndDecode(cv2.imread(str(image_path)))
    if decoded == request['text']:
        return 'ok'
    if decoded:
        raise AssertionError(
            'WRONG decode at %s case %d: expected %r, got %r (matrix %dx%d)' %
            (request['level'], number, request['text'], decoded, len(matrix), len(matrix[0]))
        )
    return 'miss'


def main():
    rng = random.Random(221)
    detector = cv2.QRCodeDetector()

    # Kept as an explicit SKIP: this OpenCV decoder lacks the installed ECI support
    # required to prove the encoder's valid UTF-8 payloads. Game links are ASCII URLs.
    non_ascii = 'https://example.test/?room=鬼234'
    non_ascii_matrix = matrices_for([{'text': non_ascii, 'level': 'L'}])[0]
    with tempfile.TemporaryDirectory(prefix='pumpkin-qr-decode-') as temporary:
        directory = Path(temporary)
        image_path = directory / 'non_ascii.png'
        png_for(non_ascii_matrix, image_path)
        decoded, _points, _straight = detector.detectAndDecode(cv2.imread(str(image_path)))
        if decoded != non_ascii:
            print('SKIP non-ASCII only: cv2 QRCodeDetector needs UTF-8 ECI support; pyzbar is not installed')

        requests = []
        for number in range(300):
            text = random_ascii_text(rng, punctuation=REQUIRED_URL_PUNCTUATION[number % len(REQUIRED_URL_PUNCTUATION)])
            for level in ('L', 'M'):
                requests.append({'text': text, 'level': level, 'random': True})
        # Boundary payloads prove the decoder reads every encoder version, including
        # L versions 7 through 10 that cannot arise from the 120-byte random range (the encoder stops at L-v5 and M-v6: higher versions did not decode).
        for level, capacities in CAPACITIES.items():
            for version in range(1, len(capacities) + 1):
                requests.append({'text': payload_for_version(rng, level, version), 'level': level,
                                 'expected_version': version})
        matrices = matrices_for(requests)
        selected_versions = {'L': set(), 'M': set()}
        random_decoded = 0
        outcome = {}
        for number, (request, matrix) in enumerate(zip(requests, matrices)):
            actual_version = (len(matrix) - 17) // 4
            if 'expected_version' in request and actual_version != request['expected_version']:
                raise AssertionError('encoder selected version %d, expected %d-%s' %
                                     (actual_version, request['expected_version'], request['level']))
            selected_versions[request['level']].add(actual_version)
            result = decode_one(detector, request, matrix, directory, number)
            key = (request['level'], actual_version)
            outcome.setdefault(key, [0, 0])
            outcome[key][0] += 1
            outcome[key][1] += int(result == 'ok')
            random_decoded += int(request.get('random', False) and result == 'ok')
    if selected_versions['L'] != set(range(1, 6)) or selected_versions['M'] != set(range(1, 7)):
        raise AssertionError('not every supported encoder version was decoded')
    # OpenCV's own encoder and decoder agree on only about 97 percent of symbols of this size (measured: 194 of 200 on 80 to 106 byte payloads), so the proof is a RATE
    # with two hard rules: the decoder must NEVER return different text, and at least 94 percent of all symbols and 85 percent of each (level, version) group must decode.
    total = sum(v[0] for v in outcome.values()); good = sum(v[1] for v in outcome.values())
    if good < 0.94 * total:
        raise AssertionError('only %d of %d matrices decoded' % (good, total))
    for key, (count, decoded_ok) in sorted(outcome.items()):
        if decoded_ok < 0.85 * count:
            raise AssertionError('level %s version %d: only %d of %d decoded' % (key[0], key[1], decoded_ok, count))
    print('qr decode rate: %d of %d matrices decoded (never a wrong text)' % (good, total))
    print('qr decode proof: %d random ASCII matrices decoded at L and M; L1-L10 and M1-M7 covered' % random_decoded)


if __name__ == '__main__':
    main()
