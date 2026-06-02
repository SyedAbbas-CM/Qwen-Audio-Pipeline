# Next Steps

## Immediate

1. Use the verified Karachi 3 clean pair as the active new-voice baseline:
   - `references/karachi-3-clean-10s-24k-mono.wav`
   - `transcripts/reference-voice-deeper-clean-10s-v1.txt`
2. Keep `Qwen/Qwen3-TTS-12Hz-1.7B-Base` as the chosen new-voice model path on this machine.
3. Keep benchmarks strictly sequential:
   - one line at a time
   - one model at a time
   - one fresh process at a time
   - no parallel local benchmarks
4. Move final assembly to:
   - raw chunk inputs
   - short crossfades
   - marker-level roomtone bed
   - marker-level postprocess
5. Reduce chunk-level cleanup aggression:
   - prefer `stitch_safe`
   - avoid using `light` as the default production chunk profile
6. Compare:
   - `devlog-final-1p7b-karachi3-clean10s-v1-markers`
   - `devlog-final-1p7b-karachi3-clean10s-v1-markers-mastered`
   - `devlog-final-1p7b-karachi3-clean10s-v1-markers-rawmaster-v2`
7. If `rawmaster-v2` is clearly better, make raw-chunk marker mastering the default final pipeline.
8. Seed and maintain:
   - `config/pronunciation-glossary.tsv`
9. Keep the spoken-manifest stage:
   - `text` = human script
   - `synthesis_text` = Qwen-ready text
10. Keep the pronunciation candidate scan:
   - acronyms
   - mixed alphanumeric terms
   - symbols
   - proper nouns
11. Keep current generated audio stable while building this layer.
12. Use the current QC shortlist:
   - `reports/qwen-qc-shortlist.tsv`
13. Apply new pronunciation/style rerenders only to flagged chunks first.
14. Use:
   - `transcripts/devlog-final-manifest-spoken.tsv`
   - `reports/pronunciation-candidates.tsv`
   - `reports/pronunciation-qc.tsv`
   as the new baseline pronunciation workflow
15. Use the new intent layer on lines that feel too flat:
   - `reactive`
   - `annoyed`
   - `deadpan`
   - `sarcastic`
   before broad rerenders
16. Treat long expressive references as research assets, not default generation references.
17. Use short neutral references for baseline clone stability.
18. Document every stubborn timeout with:
   - line text
   - reference mode
   - retry mode
   - whether isolated one-off succeeded
19. Document every benchmark run with:
   - model
   - reference pair
   - line text
   - whether it was run sequentially

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
- keep single-file mode in `scripts/add-roomtone-bed.py`
- keep short crossfades in `scripts/stitch-markers-from-mapping.py`
- evaluate whether `18 ms` or `24 ms` is the better default
- prefer raw chunk stitching over clean chunk stitching when building final markers
- add more postprocess profiles only if rawmaster-v2 still pumps too much
- decide whether `stitch-approved-markers.py` is needed

### Phase 3: Alignment + Prosody

- compare `qwen_forced_aligner` against `whisper_words` on the flagged chunks
- decide which alignment backend becomes the default local word-edit path
- likely default to `qwen_forced_aligner` for transcript-to-audio word edits
- keep heuristic `scripts/qwen-align.py` timing as fallback
- extend `scripts/qwen-prosody-edit.py` beyond pause/gain/stretch
- add instruction JSON per chunk for lines worth directing
- later add WhisperX/MFA for stronger alignment than faster-whisper timestamps

### Phase 3.5: Delivery Intent

- keep `intent` in the parsed manifest
- use `scripts/render-intent-probes.py` on the lines that feel too samey
- treat intent problems as:
  - pre-generation shaping problems
  - not post-EQ problems
- research why some intents collapse together under the current clone setup
- separate:
  - wording problem
  - reference-conditioning problem
  - model-capability problem
- start with:
  - `marker-17-balancing`
  - `marker-26-the-boss`
  - `marker-29-outro`
- formalize an intent research bench:
  - exact line set
  - exact wording variants
  - exact reference variants
  - human scoring rubric for:
    - annoyed
    - sarcastic
    - deadpan
    - reactive

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

### Phase 5.5: Runtime Robustness Research

- classify current failures into:
  - long-line failure
  - silent hang
  - queue-state degradation
  - reference-conditioning instability
  - fallback-only recovery
- add better failure logging if possible
- compare:
  - same-line in long queue
  - same-line in fresh one-off process
  - same-line rewritten slightly
  - same-line with alternate reference path
- determine whether fresh-process-per-chunk is safer than the current queue model on this Mac

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

Do not regenerate the whole transcript again from scratch yet unless the voice itself needs to change.

Do this next:
- keep `1.7B + clean 10s pair` as the generation baseline
- use raw-chunk marker mastering as the next assembly baseline candidate
- do not use guessed or ASR-derived reference transcripts as trusted clone baselines
- benchmark only 3 to 5 fixed lines across future model variants
- benchmark those lines sequentially, never in parallel on this Mac
- keep the generation baseline stable while tuning assembly/mastering
