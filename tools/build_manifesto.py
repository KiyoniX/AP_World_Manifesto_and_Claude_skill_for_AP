"""Build the manifesto's PDF and DOCX from its Markdown source.

Usage: python tools/build_manifesto.py [--out dist]

Needs pandoc 3 on PATH, and typst on PATH for the PDF. The outputs are release assets, never committed.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "manifesto" / "AP_World_Manifesto.md"
COMMON_OPTIONS = ["--standalone", "--toc", "--toc-depth=2"]
FORMATS = {
    "docx": [],
    "pdf": ["--pdf-engine=typst", "--variable=papersize:a4", "--variable=margin.x:2cm", "--variable=margin.y:2cm"],
}


def require(tool: str) -> str:
    path = shutil.which(tool)
    if path is None:
        sys.exit(f"{tool} not found on PATH")
    return path


def build(out_dir: Path) -> list[Path]:
    pandoc = require("pandoc")
    require("typst")
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for extension, options in FORMATS.items():
        output = out_dir / f"{SOURCE.stem}.{extension}"
        subprocess.run([pandoc, str(SOURCE), *COMMON_OPTIONS, *options, "--output", str(output)], check=True)
        outputs.append(output)
    return outputs


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    for output in build(parser.parse_args(argv).out):
        print(f"Built {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
