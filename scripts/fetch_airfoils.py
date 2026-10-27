#!/usr/bin/env python3
"""Fetch NACA 63-415 coordinates with basic validation before replacing the local file.

Network access is required. The checked-in coordinate file should be retained if
this fetch fails; the script writes to a temporary file and only then replaces it.
"""
from __future__ import annotations
from pathlib import Path
import os
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "xflr5" / "naca63415.dat"
URL = "https://airfoiltools.com/airfoil/seligdatfile?airfoil=n63415-il"


def validate_coordinates(text: str) -> tuple[bool, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 20:
        return False, f"too few non-empty lines ({len(lines)})"
    if any(token in text[:500].lower() for token in ("<!doctype html", "<html", "access denied")):
        return False, "server returned HTML/error content instead of coordinates"
    numeric_rows = 0
    points: list[tuple[float, float]] = []
    for line in lines[1:]:
        fields = line.replace(",", " ").split()
        if len(fields) < 2:
            continue
        try:
            x, y = float(fields[0]), float(fields[1])
        except ValueError:
            continue
        if not (-0.05 <= x <= 1.05 and -0.5 <= y <= 0.5):
            return False, f"coordinate outside expected normalized bounds: {x}, {y}"
        points.append((x, y))
        numeric_rows += 1
    if numeric_rows < 20:
        return False, f"too few numeric coordinate rows ({numeric_rows})"
    if max(x for x, _ in points) < 0.95 or min(x for x, _ in points) > 0.05:
        return False, "coordinates do not span the expected chord range"
    return True, f"validated {numeric_rows} numeric coordinate rows"


def main() -> int:
    request = urllib.request.Request(URL, headers={"User-Agent": "Project-Eidolon/1.0"})
    print(f"Fetching NACA 63-415 coordinates from {URL}")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            text = response.read().decode("utf-8", errors="strict")
    except Exception as exc:
        print(f"ERROR: download failed; existing file was not changed: {exc}")
        return 1

    valid, message = validate_coordinates(text)
    if not valid:
        print(f"ERROR: downloaded data rejected ({message}); existing file was not changed")
        return 1

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="naca63415_", suffix=".dat", dir=TARGET.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text.rstrip() + "\n")
        Path(temporary).replace(TARGET)
    except Exception:
        try:
            Path(temporary).unlink(missing_ok=True)
        except OSError:
            pass
        raise
    print(f"SUCCESS: {message}; wrote {TARGET.relative_to(ROOT)}")
    print("Note: coordinate-format validation does not independently verify airfoil provenance or geometry quality.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
