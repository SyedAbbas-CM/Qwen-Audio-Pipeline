from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from voice_direction import apply_energy, choose_temperature


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "voice-pipeline.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "qwen3-energy-probes"

PROBE_LINES = [
    ("dungeon-start", "So, this is where the dungeon loop really starts."),
    ("systems-line", "This is where the systems actually start stacking together."),
    ("boss-line", "And this is where the boss fight starts getting a little messy."),
]

ENERGIES = ["steady", "lifted", "start-high"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--timeout-sec", type=int, default=900)
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    model_id = config["qwen_model_id"]
    reference = config["reference"]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for slug, base_text in PROBE_LINES:
        for energy in ENERGIES:
            shaped = apply_energy(base_text, energy)
            temperature = choose_temperature(energy)
            out_dir = output_dir / slug / energy
            out_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    str(ROOT / "envs" / "qwen3" / "bin" / "python"),
                    str(ROOT / "scripts" / "qwen-run-one-take.py"),
                    "--text",
                    shaped,
                    "--x-vector-only",
                    "--temperature",
                    str(temperature),
                    "--model-id",
                    model_id,
                    "--reference",
                    reference,
                    "--timeout-sec",
                    str(args.timeout_sec),
                    "--output-raw",
                    str(out_dir / "raw.wav"),
                    "--output-clean",
                    str(out_dir / "clean.wav"),
                ],
                cwd=ROOT,
                check=True,
            )
            (out_dir / "input.txt").write_text(shaped, encoding="utf-8")
            print(out_dir / "clean.wav")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
