# Next Steps

## Immediate

1. Do not generate more transcript audio right now.
2. Use the editable review sheet:
   - `reports/qwen-review-sheet.tsv`
3. Apply review letters with:
   - `scripts/apply-review-sheet.py`
4. Review marker WAVs in:
   - `outputs/qwen3-reftext-full-v2-markers`
5. Compare roomtone-stabilized markers in:
   - `outputs/qwen3-reftext-full-v2-markers-roomtone`
6. Compare the stitched narration:
   - `outputs/final/devlog-final-unapproved.wav`
7. Compare the approved-baseline narration:
   - `outputs/final/devlog-final-approved-baseline.wav`
8. Use the QC shortlist:
   - `reports/qwen-qc-shortlist.tsv`
9. Prioritize:
   - rerender `marker-4-intro-c04`
   - review/manual edit the `needs_manual_edit` set before broader rerenders

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

- use `whisper_words` mode in `scripts/qwen-align.py` as the default local word-timestamp path
- keep heuristic `scripts/qwen-align.py` timing as fallback
- extend `scripts/qwen-prosody-edit.py` beyond pause/gain/stretch
- add instruction JSON per chunk for lines worth directing
- later add WhisperX/MFA for stronger alignment than faster-whisper timestamps

### Explicitly Later

- RVC / voice conversion experiments
- DeepFilterNet as optional cleanup profile
- AudioSR / super-resolution
- Celery / Redis / distributed orchestration
- vLLM / Triton / other inference stack changes
- reusable Qwen clone prompt optimization after baseline A/B

## Practical Review Order

Listen first to:

- `hook.wav`
- `marker-4-intro.wav`
- `marker-5-physics.wav`
- `marker-17-balancing.wav`
- `marker-26-the-boss.wav`
- `marker-29-outro.wav`

## Current Recommendation

Do not regenerate the entire transcript again unless:
- reference setup changes
- clone mode changes
- chunking logic changes globally

Otherwise:
- rerender only the bad chunks
- keep the rest of the transcript stable
- use roomtone and targeted word edits before resorting to global rerenders
