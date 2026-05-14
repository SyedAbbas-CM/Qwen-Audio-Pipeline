# Next Steps

## Immediate

1. Finish the original-voice spoken-manifest pass by repairing the five stuck outro chunks.
2. After that, run the equivalent full spoken-manifest transcript for the WhatsApp friend voice.
3. Seed and maintain:
   - `config/pronunciation-glossary.tsv`
4. Add a spoken-manifest stage:
   - `text` = human script
   - `synthesis_text` = Qwen-ready text
5. Add a pronunciation candidate scan:
   - acronyms
   - mixed alphanumeric terms
   - symbols
   - proper nouns
6. Keep current generated audio stable while building this layer.
7. Use the current QC shortlist:
   - `reports/qwen-qc-shortlist.tsv`
8. Apply new pronunciation/style rerenders only to flagged chunks first.
9. Use:
   - `transcripts/devlog-final-manifest-spoken.tsv`
   - `reports/pronunciation-candidates.tsv`
   - `reports/pronunciation-qc.tsv`
   as the new baseline pronunciation workflow

## Implementation Queue

### Phase 1: QC + Review

- use the real ASR-backed `scripts/qwen-asr-qc.py` output to identify bad chunks
- use `scripts/qwen-review-report.py`
- replace baseline approvals with real decisions via `scripts/approve-take.py`
- use `scripts/stitch-approved-final.py` from curated approvals instead of blanket baseline approval
- add WER alongside difflib similarity in `qwen-asr-qc.py`
- keep `baseline_approved` separate from real `approved`

### Phase 2: Marker Polish

- tune `scripts/add-roomtone-bed.py`
- add single-file mode to `scripts/add-roomtone-bed.py`
- add more postprocess profiles
- decide whether `stitch-approved-markers.py` is needed

### Phase 3: Alignment + Prosody

- compare `qwen_forced_aligner` against `whisper_words` on the flagged chunks
- decide which alignment backend becomes the default local word-edit path
- likely default to `qwen_forced_aligner` for transcript-to-audio word edits
- keep heuristic `scripts/qwen-align.py` timing as fallback
- extend `scripts/qwen-prosody-edit.py` beyond pause/gain/stretch
- add instruction JSON per chunk for lines worth directing
- later add WhisperX/MFA for stronger alignment than faster-whisper timestamps

### Phase 4: Pronunciation + G2P

- `config/pronunciation-glossary.tsv`
- `scripts/find-pronunciation-terms.py`
- `scripts/apply-pronunciation-glossary.py`
- `scripts/pronunciation-qc.py`
- update queue/QC scripts to respect `synthesis_text`
- keep original `text` unchanged for human review

### Phase 5: Controlled Model Research

- `config/model-registry.json`
- `scripts/benchmark-tts-models.py`
- `scripts/test-qwen-aligner-units.py`
- `scripts/speaker-drift-qc.py`
- optional `scripts/enhance-speech.py`

### Explicitly Later

- RVC / voice conversion experiments
- DeepFilterNet as optional cleanup profile
- AudioSR / super-resolution
- Celery / Redis / distributed orchestration
- vLLM / Triton / other inference stack changes
- reusable Qwen clone prompt optimization after baseline A/B
- Qwen TTS 1.7B family as baseline replacement before benchmarking
- DeepFilterNet / Resemble Enhance as default
- viseme/lipsync pipeline before pronunciation layer is stable

## Practical Review Order

Listen first to:

- `hook.wav`
- `marker-4-intro.wav`
- `marker-5-physics.wav`
- `marker-17-balancing.wav`
- `marker-26-the-boss.wav`
- `marker-29-outro.wav`

## Current Recommendation

Do not regenerate the whole transcript again from scratch yet.

Do this next:
- repair the five spoken-manifest outro chunks
- keep the current stitched original-voice narration as the listening baseline
- only after that start the full friend-voice pass
- benchmark only 3 to 5 fixed lines across future model variants
- keep the current baseline stable until those results justify a switch
