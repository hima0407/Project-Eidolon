"""Shared helpers for the numbered study scripts."""
import json
import numpy as np
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from eidolon import style  # noqa: E402  (applies the plot style)


def write_json(path: Path, obj):
    def conv(o):
        try:
            return float(o)
        except Exception:
            return str(o)
    path.write_text(json.dumps(obj, indent=2, default=conv))
    print(f"  wrote {path.relative_to(ROOT)}")


def write_csv(path: Path, header, rows):
    import csv
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([f"{float(v):.6g}" if isinstance(v, (float, np.floating)) else v for v in r])
    print(f"  wrote {path.relative_to(ROOT)}")
