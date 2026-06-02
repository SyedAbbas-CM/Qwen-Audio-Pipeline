# Project Plan

## Goal

Turn the local Qwen voice setup from "generated WAVs" into a small production-grade voice pipeline for game devlogs, narration, and later in-game dialogue work.

## Target Workflow

1. Edit master script:
   - `transcripts/devlog-final.txt`

2. Parse into short chunks:
   - `scripts/parse-transcript.py`
   - output:
     - `transcripts/devlog-final-manifest-reftext.tsv`

3. Generate Qwen chunks sequentially:
   - `scripts/qwen-run-queue.py`
   - output:
     - `outputs/qwen3-reftext-full-v2/<segment-id>/take-01-raw.wav`
     - `outputs/qwen3-reftext-full-v2/<segment-id>/take-01-clean.wav`
     - `outputs/qwen3-reftext-full-v2/<segment-id>/take-01-clean.status.json`
     - `outputs/qwen3-reftext-full-v2/<segment-id>/take-01-clean.log.txt`

4. Run ASR QC:
   - current:
     - `scripts/qwen-asr-qc.py`
     - `scripts/download-asr-models.py`
   - output:
     - `reports/qwen-asr-qc.tsv`
   - current limitation:
     - first real offline ASR pass may still be running on the current chunk set

5. Generate review report:
   - current:
     - `scripts/qwen-review-report.py`
   - output:
     - `reports/qwen-review-report.tsv`

6. Approve or reject takes:
   - current:
     - `scripts/approve-take.py`
     - `scripts/approve-from-report.py`
   - output:
     - `transcripts/approved-takes.tsv`

7. Stitch by marker:
   - current:
     - `scripts/stitch-markers-from-mapping.py`
   - output:
     - `outputs/final/devlog-final-1p7b-karachi3-clean10s-v1-markers/*.wav`
     - `outputs/final/devlog-final-1p7b-karachi3-clean10s-v1-markers-rawmaster-v2/*.wav`
     - `outputs/final/devlog-final-1p7b-karachi3-clean10s-v1-markers-rawmaster-v3/*.wav`
   - current best direction:
     - stitch from raw chunk WAVs
     - lightly trim chunk edges before stitching
     - short crossfades
     - marker-wide denoise/master pass
     - one consistent roomtone bed at the end

8. Add optional room tone:
   - current:
     - `scripts/add-roomtone-bed.py`
   - output:
     - `outputs/qwen3-reftext-full-v2-markers-roomtone/*.wav`

9. Stitch final approved narration:
   - current:
     - `scripts/stitch-approved-final.py`
   - output:
     - `outputs/final/devlog-final.wav`
   - current comparison output:
     - `outputs/final/devlog-final-unapproved.wav`
     - `outputs/final/devlog-final-approved-baseline.wav`
   - current strongest clean full narration:
     - `outputs/final/devlog-final-1p7b-karachi3-clean10s-v1.wav`

10. Run alignment:
   - current:
     - `scripts/qwen-align.py`
   - output:
     - `alignments/qwen3-reftext-full-v2/<segment-id>.words.json`
   - current state:
     - supports `whisper_words` using cached `faster-whisper`
     - supports `qwen_forced_aligner` using `Qwen3-ForcedAligner-0.6B`
     - keeps `silence_aware_heuristic` as fallback
   - current limitation:
     - WhisperX/MFA still worth future A/B comparison

11. Prosody edit:
   - current:
     - `scripts/qwen-prosody-edit.py`
   - output:
     - `outputs/prosody/*.wav`
   - current capability:
     - pause after word
     - gain boost on word
     - word stretch
     - whole-line speed

12. Pronunciation/style rerender tests:
   - current:
     - `scripts/qwen-run-one-take.py`
     - targeted variant text inputs
   - purpose:
     - test pronunciation steering
     - test sentence-style alternatives
     - compare rerender-vs-edit decisions on bad chunks

13. Pronunciation / synthesis text layer:
   - planned:
     - `config/pronunciation-glossary.tsv`
     - `scripts/find-pronunciation-terms.py`
     - `scripts/apply-pronunciation-glossary.py`
     - `scripts/pronunciation-qc.py`
   - purpose:
     - preserve human script text
     - produce Qwen-ready `synthesis_text`
     - control acronyms, names, technical terms, and symbols before generation

14. Controlled model research:
   - planned:
     - `config/model-registry.json`
     - `scripts/benchmark-tts-models.py`
     - `scripts/test-qwen-aligner-units.py`
     - `scripts/speaker-drift-qc.py`
     - optional `scripts/enhance-speech.py`
   - purpose:
     - compare candidate models/tools without destabilizing the baseline

15. Runtime robustness analysis:
   - planned:
     - failure classification
     - retry/fallback provenance tracking
     - isolated one-off rerun testing
     - queue-state degradation checks
   - purpose:
     - understand silent generation hangs
     - distinguish bad-line problems from runtime instability
     - reduce manual babysitting during full transcript runs

## Production Rule

A take is not production-ready until it passes:

1. generation status = `ready`
2. ASR QC = `pass` or human override
3. human review = `approved`
4. optional room tone / prosody / postprocess applied
5. included in approved final stitch

For marker delivery quality:

6. final marker should be assembled from a stitch-safe chunk path
7. avoid hard concat of aggressively denoised per-chunk WAVs

## Immediate Implementation Order

### Phase 1

- `qwen-asr-qc.py`
- `download-asr-models.py`
- `qwen-review-report.py`
- `approve-take.py`
- `stitch-approved-final.py`

Current state:
- implemented
- offline ASR download path implemented
- first real ASR pass in progress/verification
- baseline approval semantics now separated from real approval
- still needs real human approval decisions to be useful end-to-end

### Phase 2

- `add-roomtone-bed.py`
- better postprocess profiles
- `stitch-approved-markers.py` if needed

Current state:
- roomtone pass implemented
- tuning and listening validation still needed

### Phase 3

- `qwen-align.py`
- `qwen-prosody-edit.py`
- per-chunk prosody instruction JSON

Current state:
- first working prototype exists
- supports word gain, pause insertion, word stretch, and whole-line speed
- does not yet support true pitch-preserving per-word timing edits
- now works better with normalized word matching against Whisper word outputs

## V2 Hardening Already Applied

- `config/voice-pipeline.json` now points to the working short reference path
- config defaults now flow into:
  - `qwen-run-queue.py`
  - `qwen-run-one-take.py`
- `qwen-asr-qc.py` now supports:
  - offline cached model use
  - `--model-path`
  - `--cache-dir`
  - `--device`
  - `--compute-type`
  - WER output
  - explicit `model_missing` vs `asr_error`
- `baseline_approved` is now distinct from `approved`
- `stitch-approved-final.py` now supports:
  - approved-only by default
  - `--allow-baseline`
  - `--allow-unapproved`
- status JSON now includes:
  - `supervisor_pid`
  - `child_pid`
  - `hostname`
- `qwen-status.py` now distinguishes active vs stale running jobs via PID checks
- `qwen-align.py` now supports:
  - `--aligner heuristic`
  - `--aligner whisper_words`
  - `--aligner qwen_forced_aligner`
- editable review sheet path now exists:
  - `scripts/make-review-sheet.py`
  - `scripts/apply-review-sheet.py`
  - `reports/qwen-review-sheet.tsv`

### Phase 4

### Phase 4

- pronunciation glossary + `synthesis_text`
- pronunciation candidate scan
- pronunciation QC
- controlled 3-to-5 line benchmark harness

### Phase 5

- GPU worker queue for the workstation
- stronger ASR QC on the workstation
- retry workers
- optional enhancement / AudioSR / voice conversion

### Phase 5.5

- runtime robustness analysis
- better chunk retry/fallback strategy
- isolated one-off repro harness for stubborn lines
- better error logging around silent generation hangs

Guardrails:
- do not add RVC to the baseline pipeline
- do not make DeepFilterNet the default cleanup path
- do not add AudioSR to the default path
- do not add Celery/Redis during the M1 phase
- do not rebuild around vLLM/Triton until the current baseline is A/B tested
- do not switch to Qwen TTS 1.7B family as the baseline before small benchmarks
- do not make enhancement models default before single-marker A/B tests
- do not assume phoneme-ready alignment until arbitrary-unit tests are run
- do not treat silent timeouts as solved just because retries sometimes work
- do not switch to a new reference as "stable" until it survives a full transcript plus repair pass

## Review Integration

External review reinforced these priorities:

1. Think in terms of asset lifecycle, not just generated WAVs.
2. Stabilize QC, approvals, room tone, and final stitching before deeper model experimentation.
3. Treat advanced modules as optional later experiments:
   - RVC
   - DeepFilterNet
   - AudioSR
   - distributed worker infrastructure
4. Investigate reusable Qwen clone prompts later, but do not replace the working `ref_audio + ref_text` path until tested.

## Word-Level Future Direction

Once alignment exists, each word can be manipulated precisely:

- pause after exact word
- slight word stretch
- word gain boost
- lower final word pitch
- remove awkward micro-gap

That is the layer that moves this from generic AI narration into directed performance.

## Current Practical Rule

Use the right control layer for the right problem:

- rerender when the problem is:
  - pronunciation
  - accent drift
  - wording/style mismatch
- rewrite when the problem is:
  - pathological short line that repeatedly hangs
  - unclear or overly bare phrase
- treat repeated silent timeouts as:
  - runtime robustness failures
  - not automatically as script failures
  - awkward sentence style
  - wrong emotional read

- post-edit when the problem is:
  - tiny pause shape
  - emphasis
  - slight timing cleanup
  - seam cleanup

- normalize before generation when the problem is:
  - acronym pronunciation
  - proper noun pronunciation
  - technical term pronunciation
  - symbols/digits mixed into words
