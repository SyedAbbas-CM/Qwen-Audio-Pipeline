from pathlib import Path

import perth
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
import torch


out_dir = Path(__file__).resolve().parents[1] / "outputs" / "chatterbox"
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "smoke.wav"

# Work around broken optional watermark import in resemble-perth.
if perth.PerthImplicitWatermarker is None:
    perth.PerthImplicitWatermarker = perth.DummyWatermarker

device = "mps" if torch.backends.mps.is_available() else "cpu"
model = ChatterboxTTS.from_pretrained(device=device)
wav = model.generate("This is a Chatterbox smoke test.")
ta.save(str(out_file), wav, model.sr)
print(out_file)
