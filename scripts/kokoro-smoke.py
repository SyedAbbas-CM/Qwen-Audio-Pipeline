from pathlib import Path

import soundfile as sf
from kokoro import KPipeline


out_dir = Path(__file__).resolve().parents[1] / "outputs" / "kokoro"
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "smoke.wav"

pipeline = KPipeline(lang_code="a")
result = next(pipeline("This is a Kokoro smoke test.", voice="af_heart"))
_, _, audio = result
sf.write(out_file, audio, 24000)
print(out_file)
