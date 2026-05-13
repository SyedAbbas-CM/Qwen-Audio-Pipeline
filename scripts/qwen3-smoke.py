from pathlib import Path

import soundfile as sf
from qwen_tts import Qwen3TTSModel


out_dir = Path(__file__).resolve().parents[1] / "outputs" / "qwen3"
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "smoke.wav"

model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice")
speaker = model.get_supported_speakers()[0]
wavs, sr = model.generate_custom_voice(
    text="This is a Qwen three TTS smoke test.",
    speaker=speaker,
    language="English",
)
sf.write(out_file, wavs[0], sr)
print(out_file)
