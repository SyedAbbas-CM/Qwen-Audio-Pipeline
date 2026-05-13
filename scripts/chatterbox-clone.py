from pathlib import Path

import perth
import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references" / "karachi.m4a"
OUT_DIR = ROOT / "outputs" / "chatterbox"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TEXT = (
    "This is a cloned voice test for local video narration. "
    "The delivery should sound calm, clear, and slightly deeper."
)


if perth.PerthImplicitWatermarker is None:
    perth.PerthImplicitWatermarker = perth.DummyWatermarker

device = "mps" if torch.backends.mps.is_available() else "cpu"
model = ChatterboxTTS.from_pretrained(device=device)
wav = model.generate(
    TEXT,
    audio_prompt_path=str(REF),
    exaggeration=0.3,
    cfg_weight=0.35,
    temperature=0.7,
)

out_file = OUT_DIR / "karachi-clone.wav"
ta.save(str(out_file), wav, model.sr)
print(out_file)
