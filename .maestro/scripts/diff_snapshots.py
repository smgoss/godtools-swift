#!/usr/bin/env python3
"""
Pixel-diff two snapshot directories produced by snapshot.sh.

Usage:
    python3 .maestro/scripts/diff_snapshots.py [--baseline NAME] [--current NAME] [--threshold 0.005]

Default baseline name: "baseline".
Default current name:  "current".

Reports per-file pixel deltas. Writes a side-by-side diff PNG for any pair whose
pixel difference exceeds the threshold (fraction of mismatched pixels, 0..1).
Output written to .maestro/snapshots/diff/<abbrev>/<page>.png and a summary
to .maestro/snapshots/diff/report.html.

Requires Pillow:  pip install pillow
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError:
    print("This script requires Pillow. Install:  pip install pillow", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[2]
SNAP_ROOT = ROOT / ".maestro" / "snapshots"


def collect_pngs(d: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for f in d.rglob("*.png"):
        rel = f.relative_to(d).as_posix()
        out[rel] = f
    return out


def diff_pair(a: Path, b: Path) -> tuple[float, Image.Image | None]:
    img_a = Image.open(a).convert("RGBA")
    img_b = Image.open(b).convert("RGBA")
    if img_a.size != img_b.size:
        return 1.0, None  # full mismatch
    delta = ImageChops.difference(img_a, img_b)
    bbox = delta.getbbox()
    if bbox is None:
        return 0.0, None
    pixels = list(delta.getdata())
    diff_count = sum(1 for r, g, b, a in pixels if r or g or b or a)
    total = img_a.size[0] * img_a.size[1]
    return (diff_count / total), delta


def render_side_by_side(a: Path, b: Path, delta: Image.Image | None, out: Path) -> None:
    img_a = Image.open(a).convert("RGBA")
    img_b = Image.open(b).convert("RGBA")
    target_w = max(img_a.width, img_b.width)
    target_h = max(img_a.height, img_b.height)
    panels = [img_a, img_b]
    if delta is not None:
        panels.append(delta.convert("RGBA"))
    composite = Image.new("RGBA", (target_w * len(panels), target_h), (255, 255, 255, 255))
    for i, p in enumerate(panels):
        composite.paste(p, (i * target_w, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    composite.save(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="baseline")
    parser.add_argument("--current", default="current")
    parser.add_argument("--threshold", type=float, default=0.005, help="fraction of pixels that may differ before flagging (0..1)")
    args = parser.parse_args()

    base_dir = SNAP_ROOT / args.baseline
    cur_dir = SNAP_ROOT / args.current
    if not base_dir.is_dir():
        print(f"baseline dir missing: {base_dir}", file=sys.stderr)
        return 2
    if not cur_dir.is_dir():
        print(f"current dir missing: {cur_dir}", file=sys.stderr)
        return 2

    base = collect_pngs(base_dir)
    cur = collect_pngs(cur_dir)
    keys = sorted(set(base) | set(cur))

    diff_dir = SNAP_ROOT / "diff"
    diff_dir.mkdir(parents=True, exist_ok=True)

    results: list[tuple[str, str, float, Path | None]] = []
    fails = 0
    for k in keys:
        a = base.get(k)
        b = cur.get(k)
        if a is None or b is None:
            status = "missing-baseline" if a is None else "missing-current"
            results.append((k, status, 1.0, None))
            fails += 1
            print(f"  ✗ {k}  {status}")
            continue
        ratio, delta = diff_pair(a, b)
        if ratio > args.threshold:
            out = diff_dir / k
            render_side_by_side(a, b, delta, out)
            results.append((k, "diff", ratio, out))
            fails += 1
            print(f"  ✗ {k}  diff={ratio:.4f}  -> {out.relative_to(ROOT)}")
        else:
            results.append((k, "ok", ratio, None))
            print(f"  ✓ {k}  diff={ratio:.4f}")

    # Summary HTML
    report = diff_dir / "report.html"
    rows = []
    for k, status, ratio, out in results:
        cls = "ok" if status == "ok" else "fail"
        link = f'<a href="{out.relative_to(diff_dir)}">side-by-side</a>' if out else ""
        rows.append(f'<tr class="{cls}"><td>{k}</td><td>{status}</td><td>{ratio:.4f}</td><td>{link}</td></tr>')
    report.write_text(
        f"""<!doctype html>
<title>godtools snapshot diff: {args.baseline} → {args.current}</title>
<style>
  body {{ font: 14px monospace; padding: 20px; }}
  table {{ border-collapse: collapse; }}
  td, th {{ border: 1px solid #ccc; padding: 4px 8px; }}
  tr.fail {{ background: #fff3f3; }}
  tr.ok {{ background: #f3fff3; }}
</style>
<h1>{args.baseline} → {args.current}  ({fails} failing of {len(keys)})</h1>
<table><tr><th>file</th><th>status</th><th>diff</th><th></th></tr>
{''.join(rows)}
</table>
""",
        encoding="utf-8",
    )
    print(f"\nReport: {report.relative_to(ROOT)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
