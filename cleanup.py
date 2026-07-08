#!/usr/bin/env python3
"""Rename every file in a folder to lowercase with spaces replaced by dashes."""
import sys
from pathlib import Path


def cleanup(folder: Path) -> None:
    for f in folder.iterdir():
        if not f.is_file():
            continue
        new_name = f.name.lower().replace(" ", "-")
        if new_name == f.name:
            continue
        target = f.with_name(new_name)
        if target.exists():
            print(f"skip (exists): {f.name} -> {new_name}")
            continue
        f.rename(target)
        print(f"{f.name} -> {new_name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python cleanup.py <folder>")
    folder = Path(sys.argv[1])
    if not folder.is_dir():
        sys.exit(f"not a folder: {folder}")
    cleanup(folder)
