from __future__ import annotations

import argparse
from pathlib import Path

import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REF = ROOT / "references" / "karachi.m4a"
DEFAULT_MODEL = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("text")
    parser.add_argument("--reference", default=str(DEFAULT_REF))
    parser.add_argument("--reference-text", default="")
    parser.add_argument("--reference-text-file", default="")
    parser.add_argument("--language", default="English")
    parser.add_argument("--model-id", default=DEFAULT_MODEL)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--x-vector-only", action="store_true")
    parser.add_argument("--temperature", type=float, default=0.35)
    parser.add_argument("--voice-clone-prompt-file", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_file = Path(args.output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    ref_text = args.reference_text
    if args.reference_text_file and not args.x_vector_only:
        ref_text = Path(args.reference_text_file).read_text(encoding="utf-8").strip()

    model = Qwen3TTSModel.from_pretrained(args.model_id)
    voice_clone_prompt = None
    if args.voice_clone_prompt_file:
        prompt_path = Path(args.voice_clone_prompt_file)
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        if prompt_path.exists():
            voice_clone_prompt = torch.load(prompt_path, map_location="cpu", weights_only=False)
        else:
            voice_clone_prompt = model.create_voice_clone_prompt(
                ref_audio=args.reference,
                ref_text=ref_text or None,
                x_vector_only_mode=args.x_vector_only,
            )
            torch.save(voice_clone_prompt, prompt_path)

    generate_kwargs = dict(
        text=args.text,
        language=args.language,
        non_streaming_mode=True,
        temperature=args.temperature,
    )
    if voice_clone_prompt is not None:
        generate_kwargs["voice_clone_prompt"] = voice_clone_prompt
    else:
        generate_kwargs.update(
            ref_audio=args.reference,
            ref_text=ref_text or None,
            x_vector_only_mode=args.x_vector_only,
        )

    wavs, sr = model.generate_voice_clone(**generate_kwargs)
    sf.write(out_file, wavs[0], sr)
    print(out_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
