"""Deliver the atlas plate to the competition runner."""

import os
from pathlib import Path
from shutil import copyfile


def main():
    default_root = Path(__file__).resolve().parent
    source = Path(os.environ.get("MAKEFUN_INPUT_DIR", default_root))
    target = Path(os.environ["MAKEFUN_OUTPUT_DIR"])
    target.mkdir(parents=True, exist_ok=True)
    copyfile(source / "assets" / "entry.png", target / "entry.png")


if __name__ == "__main__":
    main()
