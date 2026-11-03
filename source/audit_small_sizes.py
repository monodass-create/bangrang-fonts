"""출시된 글꼴을 변경하지 않고 작은 한글 전체의 래스터 중복·누락을 검사한다."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import struct
import sys
from PIL import ImageFont, __version__, features

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT
FONTS = ROOT / 'fonts'
OUT.mkdir(parents=True, exist_ok=True)


def scan(path, size):
    font = ImageFont.truetype(str(path), size)
    gray, binary = defaultdict(list), defaultdict(list)
    empty, low_coverage = [], []
    for cp in range(0xac00, 0xd7a4):
        # 같은 기준선의 실제 위치도 서명에 포함한다. 이 검사는 FreeType 단일 위치 조건이다.
        mask, offset = font.getmask2(chr(cp), mode='L', anchor='ls')
        raw = bytes(mask)
        header = struct.pack('4i', *mask.size, *offset)
        gray[hashlib.sha256(header + raw).digest()].append(chr(cp))
        threshold = bytes(255 if p >= 128 else 0 for p in raw)
        binary[hashlib.sha256(header + threshold).digest()].append(chr(cp))
        if not any(raw):
            empty.append(chr(cp))
        if not any(threshold):
            low_coverage.append(chr(cp))
    return {
        'size_px': size,
        'tested_syllables': 11172,
        'empty_rasters': empty,
        'no_pixels_at_threshold_128': low_coverage,
        'identical_grayscale_groups': [v for v in gray.values() if len(v) > 1],
        'identical_threshold_128_groups': [v for v in binary.values() if len(v) > 1],
    }


report = {
    'scope': 'Pillow FreeType rendering at one integer origin; no Windows DPI or user readability certification',
    'threshold_note': 'Threshold duplicates discard antialiasing differences and are candidates for review, not proof of identical displayed glyphs.',
    'renderer': {'Pillow': __version__, 'FreeType': features.version_module('freetype2')},
    'fonts': [],
}
for name, sizes in ([] if '--render-only' in sys.argv else [('BangrangUI-Regular.ttf', (11, 13, 15, 18, 24)),
                    ('BangrangChronicle-Regular.ttf', (18, 24, 32))]):
    path = FONTS / name
    entry = {'font': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'rasters': []}
    for size in sizes:
        result = scan(path, size)
        entry['rasters'].append(result)
        print(name, size, 'gray duplicates', len(result['identical_grayscale_groups']),
              'threshold candidates', len(result['identical_threshold_128_groups']), flush=True)
    report['fonts'].append(entry)
if report['fonts']:
    (OUT / 'small-size-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
