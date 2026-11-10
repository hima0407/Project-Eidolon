#!/usr/bin/env python3
"""Re-run every study in order and regenerate every figure and table in results/.

    python3 run_all.py            # everything (~4 min)
    python3 run_all.py 04 09      # only the studies whose number is given

Studies 01-02 run first: 01 measures the certified-trainer mass allowance and 02 writes the
Hansa-NG calibration that every later study loads.
"""
import runpy
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "studies"))
sys.path.insert(0, str(ROOT))
STUDIES = sorted((ROOT / "studies").glob("[0-9][0-9]_*.py"))


def main(only):
    t0 = time.time()
    for path in STUDIES:
        if only and path.name[:2] not in only:
            continue
        print(f"\n=== {path.stem} ===")
        t = time.time()
        sys.argv = [str(path)]
        runpy.run_path(str(path), run_name="__main__")
        print(f"    ({time.time() - t:.1f} s)")
    print(f"\nAll done in {time.time() - t0:.0f} s. Figures are in results/.")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
