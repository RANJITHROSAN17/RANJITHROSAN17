#!/usr/bin/env python3
"""Offline, deterministic, original SVG puzzle bank (no external assets/deps).
This is the geometric MVP generator, not the planned OpenCV/photo pipeline.
"""
import argparse
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTES = [('space', '#111827', '#94a3b8'), ('lab', '#062e32', '#5eead4'),
            ('terrain', '#263126', '#bef264'), ('safety', '#29251c', '#fbbf24')]

def generate(count, out):
    puzzles = []
    for i in range(count):
        rng = random.Random(7319 + i)
        pack, bg, fg = PALETTES[i % len(PALETTES)]
        size = 7 + (i % 3)
        col, row = rng.randrange(1, size-1), rng.randrange(1, size-1)
        step = 640 / size
        x, y = (col + .5) * step, (row + .5) * step
        r = step * .27
        shapes = []
        for gy in range(size):
            for gx in range(size):
                cx, cy = (gx + .5)*step, (gy + .5)*step
                # All instruments have a vertical needle; one has a horizontal needle.
                angle = 90 if (gx, gy) == (col, row) else 0
                shapes.append(f'<g transform="translate({cx:.3f} {cy:.3f}) rotate({angle})"><circle r="{r:.3f}" fill="none" stroke="{fg}" stroke-width="2"/><path d="M0 0 V{-r*.75:.3f}" stroke="{fg}" stroke-width="3" stroke-linecap="round"/><circle r="2" fill="{fg}"/></g>')
        image = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><rect width="640" height="640" fill="{bg}"/>{"".join(shapes)}</svg>'
        name = f'puzzle-{i:03d}.svg'
        asset = ROOT / 'public' / 'puzzles' / name
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_text(image)
        puzzles.append(dict(id=f'bank-{i:03d}', day=i, label=f'LENS #{i+1}', pack=pack,
                            imageRef=f'/puzzles/{name}', anomaly=dict(x=x/640, y=y/640),
                            radius=.03, difficulty=2+i%3, reveal='One instrument’s needle points sideways instead of up.', method='rotation'))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(version=1, generatedBy='tools/generate_puzzles.py', puzzles=puzzles), indent=2)+'\n')
    print(f'Generated {count} original puzzles and {out}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=28)
    parser.add_argument('--out', type=Path, default=ROOT/'src/shared/puzzle-bank.json')
    args = parser.parse_args()
    if not 1 <= args.count <= 1000:
        parser.error('count must be between 1 and 1000')
    generate(args.count, args.out)
