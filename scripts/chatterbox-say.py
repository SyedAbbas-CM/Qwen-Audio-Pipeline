from __future__ import annotations

import argparse
from pathlib import Path

import perth
import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REF = ROOT / "references" / "karachi.m4a"
OUT_DIR = ROOT / "outputs" / "chatterbox"


PRESETS = {
    "neutral": {
        "exaggeration": 0.30,
        "cfg_weight": 0.35,
        "temperature": 0.70,
        "repetition_penalty": 1.15,
    },
    "laidback": {
        "exaggeration": 0.20,
        "cfg_weight": 0.30,
        "temperature": 0.62,
        "repetition_penalty": 1.12,
    },
    "energetic": {
        "exaggeration": 0.55,
        "cfg_weight": 0.42,
        "temperature": 0.85,
        "repetition_penalty": 1.18,
    },
    "ad": {
        "exaggeration": 0.68,
        "cfg_weight": 0.48,
        "temperature": 0.88,
        "repetition_penalty": 1.20,
    },
    "grounded": {
        "exaggeration": 0.26,
        "cfg_weight": 0.38,
        "temperature": 0.64,
        "repetition_penalty": 1.14,
    },
    "sarcastic": {
        "exaggeration": 0.34,
        "cfg_weight": 0.40,
        "temperature": 0.72,
        "repetition_penalty": 1.16,
    },
    "performative": {
        "exaggeration": 0.82,
        "cfg_weight": 0.52,
        "temperature": 0.92,
        "repetition_penalty": 1.18,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("text")
    parser.add_argument("--preset", choices=sorted(PRESETS), default="neutral")
    parser.add_argument("--reference", default=str(DEFAULT_REF))
    parser.add_argument("--output-name", default="line.wav")
    parser.add_argument("--output-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if perth.PerthImplicitWatermarker is None:
        perth.PerthImplicitWatermarker = perth.DummyWatermarker

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = ChatterboxTTS.from_pretrained(device=device)
    settings = PRESETS[args.preset]

    wav = model.generate(
        args.text,
        audio_prompt_path=args.reference,
        exaggeration=settings["exaggeration"],
        cfg_weight=settings["cfg_weight"],
        temperature=settings["temperature"],
        repetition_penalty=settings["repetition_penalty"],
    )

    out_file = Path(args.output_path) if args.output_path else OUT_DIR / args.output_name
    out_file.parent.mkdir(parents=True, exist_ok=True)
    ta.save(str(out_file), wav, model.sr)
    print(out_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
