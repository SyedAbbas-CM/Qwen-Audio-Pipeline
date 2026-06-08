Project
  AI Audio Lab / Local Voice Cloning and Speech Production Pipeline
  Python, Qwen3-TTS, Qwen3-ASR, Qwen3-ForcedAligner, Faster-Whisper, FFmpeg, Librosa, SoundFile, PyTorch, Hugging Face, Apple Silicon, Bash, TSV/JSON pipelines

  Built a local end-to-end voice generation and speech post-production system for cloned narration on Apple Silicon, focused on reference-conditioned TTS, offline QC, alignment, pronunciation control, and final audio mastering.

  Resume Summary

  - Built a fully local AI voice cloning pipeline in Python around Qwen3-TTS for long-form narration, using reference-audio + transcript conditioning, sequential batch inference, post-processing, and final stitched marker delivery.
  - Designed a resumable generation orchestration layer with per-job status JSON, logs, timeout supervision, stale-run detection, retries, fallback repair paths, and config-driven defaults.
  - Implemented offline speech QA with Faster-Whisper ASR, similarity scoring, word error rate (WER), TSV reporting, shortlist generation, and approval-driven review workflows.
  - Integrated Qwen3-ASR and Qwen3-ForcedAligner for transcript-to-audio timing, and built heuristic/Whisper/Qwen-backed alignment fallbacks for word-level editing and prosody experiments.
  - Added pronunciation-aware synthesis via glossary-based normalization, synthesis_text manifests, pronunciation candidate discovery, and pronunciation QC for acronyms, proper nouns, symbols, and technical terms.
  - Developed delivery-intent and variant-generation tooling for reactive, annoyed, deadpan, sarcastic, and reflective voice directions, plus targeted rerender experiments for line-level performance control.
  - Built audio mastering/stitching pipelines with raw-vs-clean chunk routing, edge trimming, short crossfades, room-tone bedding, marker-level denoise/master passes, and full-transcript assembly.
  - Researched and debugged local TTS failure modes including silent generation hangs, reference-conditioning mismatch, chunk-boundary artifacts, prompt caching issues, and model noise behavior on Apple Silicon.

  Detailed Technical Contributions

  - Implemented Qwen clone wrapper in ai-audio-lab/scripts/qwen3-clone-say.py using Qwen3TTSModel.generate_voice_clone(...) with ref_audio + ref_text, temperature control, and reusable clone-prompt caching.
  - Added reusable voice_clone_prompt caching to reduce repeated prompt extraction overhead and explore consistency across chunk generations.
  - Built supervised one-take execution in ai-audio-lab/scripts/qwen-run-one-take.py:
      - writes raw.wav and clean.wav
      - logs stdout/stderr
      - records supervisor/child PIDs, hostname, runtime, status
      - enforces timeouts and kills stalled subprocess groups
  - Built sequential manifest runner in ai-audio-lab/scripts/qwen-run-queue.py:
      - reads TSV manifest rows
      - uses text vs synthesis_text
      - supports start-at, limit, skip-existing
      - injects reference paths, postprocess profile, timeout, cached prompt path
  - Implemented retry/fallback recovery in ai-audio-lab/scripts/qwen-retry.py for failed or stale jobs.
  - Built ASR QC in ai-audio-lab/scripts/qwen-asr-qc.py:
      - local Faster-Whisper execution
      - similarity scoring with difflib
      - WER via dynamic programming
      - backend status reporting
      - missing-model handling
  - Built alignment framework in ai-audio-lab/scripts/qwen-align.py:
      - silence-aware heuristic segmentation
      - Whisper word timestamps
      - Qwen forced-alignment backend
      - clause allocation and word-span interpolation
  - Built prosody-edit experiments in ai-audio-lab/scripts/qwen-prosody-edit.py for word-level pause/gain/stretch and whole-line timing changes.
  - Built pronunciation layer:
      - glossary config in ai-audio-lab/config/pronunciation-glossary.tsv
      - candidate scanner in ai-audio-lab/scripts/find-pronunciation-terms.py
      - glossary applier in ai-audio-lab/scripts/apply-pronunciation-glossary.py
      - pronunciation QC in ai-audio-lab/scripts/pronunciation-qc.py
  - Built delivery-intent layer:
      - transcript intent tagging in ai-audio-lab/scripts/parse-transcript.py
      - style shaping in ai-audio-lab/scripts/voice_direction.py
      - targeted probe renderer in ai-audio-lab/scripts/render-intent-probes.py
  - Built review/approval workflow:
      - review sheet generation in ai-audio-lab/scripts/make-review-sheet.py
      - review sheet application in ai-audio-lab/scripts/apply-review-sheet.py
      - final report generation in ai-audio-lab/scripts/qwen-review-report.py
      - approval semantics in ai-audio-lab/scripts/approve-take.py
  - Built final audio assembly pipeline:
      - source mapping in ai-audio-lab/scripts/stitch-manifest-from-sources.py
      - marker stitching/mastering in ai-audio-lab/scripts/stitch-markers-from-mapping.py
      - room-tone bedding in ai-audio-lab/scripts/add-roomtone-bed.py
      - shell postprocess presets in ai-audio-lab/scripts/postprocess-voice.sh
  - Iterated on multiple mastering profiles:
      - light
      - tail_rescue
      - stitch_safe
      - stitch_tight
      - stitch_softstart
      - marker_master
      - marker_denoise
  - Built and evaluated multiple final assembly strategies:
      - hard-concat chunk stitch
      - crossfaded clean-chunk markers
      - raw-chunk marker mastering
      - dry marker mastering without added bed
      - constant-bed masking tests
      - full-marker one-take generation probes
  - Ran controlled model and reference experiments:
      - Qwen3-TTS 0.6B Base vs 1.7B Base
      - long vs short vs verified-clean reference pairs
      - sanitized vs unsanitized reference tests
      - prompt-cached vs per-call clone conditioning
  - Managed model/tool environment setup locally:
      - uv-managed envs
      - Hugging Face local caches
      - Apple Silicon local inference constraints
      - Qwen3-ASR and Qwen3-ForcedAligner installation and download flows
  - Produced fully offline artifacts:
      - chunk WAVs
      - marker WAVs
      - full transcript WAVs
      - QC TSVs
      - alignment JSONs
      - mapping TSVs
      - review bundles for external model review

  Strong Resume Version
  AI Audio Lab | Local Voice Cloning, Speech QA, and Audio Mastering Pipeline

  - Engineered a local AI speech pipeline in Python using Qwen3-TTS, Qwen3-ASR, Qwen3-ForcedAligner, Faster-Whisper, FFmpeg, and PyTorch to generate, evaluate, align, edit, and master cloned narration on Apple Silicon.
  - Built a resumable batch orchestration system with timeout supervision, retry/fallback repair, per-job status/log artifacts, config-driven execution, and approval-based delivery workflows.
  - Implemented pronunciation-aware synthesis_text generation, forced alignment, WER-backed QC, intent-conditioned rerendering, and marker-level mastering with crossfades, room-tone control, and seam-reduction experiments.
  - Researched and debugged failure modes including silent inference hangs, reference-conditioning mismatch, prompt-cache instability, chunk-boundary artifacts, and model noise-floor inconsistency across long-form local speech generation.
