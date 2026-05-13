from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("inputs", nargs="+")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        for item in args.inputs:
            fh.write(f"file '{Path(item).resolve()}'\n")
        manifest = fh.name

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            manifest,
            "-c",
            "copy",
            str(output),
        ],
        check=True,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
