# Experiment Log

## What Failed

### Fish Speech on this Mac

- too heavy for the hardware target
- not the right local fit for the workflow

### Qwen `x_vector_only` as main transcript path

- more stable than stronger clone mode
- but identity drifted
- accent drift happened
- "Nordic" effect showed up on rewritten lines

### Long one-pass chunks

- often timed out
- prosody became unstable
- long lines caused pace drift or breath-like breakdown

### Silent generation hangs on full transcript runs

- some chunks produce almost no useful log output
- logs often show only:
  - `Setting pad_token_id...`
- then the process sits until the 900 second timeout
- this happened under:
  - original voice full passes
  - friend voice full passes
  - Karachi 3 short full pass
- this is a real runtime robustness problem, not just a script-writing problem

### Long expressive reference as full baseline

- `karachi-3-24k-mono.wav` was too unstable as a full transcript baseline
- the full 70 second clip mixed multiple delivery modes
- early hook chunks timed out quickly
- conclusion:
  - useful as an intent/reference bank
  - bad as the default production anchor on this Mac

### Tiny stitched chunks

- obvious seams
- voice identity shifted between chunks
- pauses felt artificial

### Early cleanup chains

- some versions boosted the noise floor
- some versions produced tail roar
- some versions caused noise pumping
- some versions created "whooo" artifacts

### Naive resample-based speed edits

- tightened timing, but sometimes shifted perceived pitch/timbre
- created moments where the voice felt slightly less like the source speaker
- should be replaced with pitch-preserving tempo changes when possible

## What Succeeded

### Proper clone mode with short reference

- `ref_audio + ref_text` using:
  - `karachi-24k-mono-short.wav`
  - `reference-voice-short.txt`
- better identity than `x_vector_only`
- more stable than the earlier long full-reference path

### Karachi 3 short baseline

- `karachi-3-short-24k-mono.wav`
- `reference-voice-deeper-short-v1.txt`
- much more stable than the full Karachi 3 reference
- successful targeted probes:
  - `hook-c02`
  - `marker-17-balancing-c01`
  - `marker-26-the-boss-c04`
  - `marker-29-outro-c01`
- successful full-run output count:
  - `63` ready in the main tree
- fallback rescue succeeded for:
  - `marker-17-balancing-c02`
  - `marker-21-hallways-c01`
- one stubborn unresolved line remains:
  - `marker-14-lighting-c05`
  - `Could be interesting.`

### Verified clean 10 second Karachi 3 pair

- audio:
  - `references/karachi-3-clean-10s-24k-mono.wav`
- text:
  - `transcripts/reference-voice-deeper-clean-10s-v1.txt`
- this pair was manually verified against the recorded audio
- it removed the bad overlap/mismatch problems from the earlier Karachi 3 short reference variants
- with this pair:
  - `Qwen/Qwen3-TTS-12Hz-1.7B-Base` completed a clean `66/66` full transcript run
  - no fallback repair was needed

### Sequential 0.6B vs 1.7B benchmark on the clean 10 second pair

- benchmark rule:
  - one line at a time
  - one model at a time
  - no parallel local benchmarks on this Mac
- result:
  - `1.7B Base` sounded better than `0.6B Base`
  - `1.7B` became the chosen local new-voice path

### Raw-chunk marker mastering

- earlier marker sets still sounded chopped because:
  - each chunk was cleaned independently
  - the background texture changed from generation to generation
  - some chunks still carried too much trailing silence
- best current fix direction:
  - stitch from raw chunk WAVs
  - trim chunk edges lightly before stitching
  - use short crossfades
  - apply one marker-wide denoise/master pass
  - add one consistent roomtone bed at the end
- current marker comparison sets:
  - clean-chunk markers:
    - `outputs/final/devlog-final-1p7b-karachi3-clean10s-v1-markers`
  - first raw-chunk mastered pass:
    - `outputs/final/devlog-final-1p7b-karachi3-clean10s-v1-markers-rawmaster-v2`
  - tighter trim + marker denoise pass:
    - `outputs/final/devlog-final-1p7b-karachi3-clean10s-v1-markers-rawmaster-v3`

### Short sequential chunks

- this is the best current generation pattern on the Mac
- avoids giant row timeouts

### Queue + status + logs

- `qwen-run-one-take.py`
- `qwen-run-queue.py`
- `qwen-status.py`
- `qwen-queue-watch.py`

These made the pipeline observable and resumable.

### Marker-level merging

- `stitch-marker-audio.py`
- `outputs/qwen3-reftext-full-v2-markers`

This made the transcript reviewable in human terms instead of tiny per-chunk fragments.

### Production control layer

- `qwen-review-report.py`
- `approve-take.py`
- `approve-from-report.py`
- `stitch-approved-final.py`
- `add-roomtone-bed.py`

These moved the project from raw generation toward asset lifecycle management.

### V2 control hardening

- `config/voice-pipeline.json` now matches the actual working clone path
- queue/runner scripts now read config defaults
- `baseline_approved` is separated from real `approved`
- status JSON now includes PIDs and hostname
- `qwen-status.py` can distinguish active vs stale running jobs
- ASR download/setup path exists via `download-asr-models.py`
- `qwen-asr-qc.py` now reports `model_missing` cleanly and includes WER
- cached `small.en` faster-whisper now runs locally and produced the first real QC TSV

These changes reduce silent regressions back to the bad clone path and make the queue safer to resume.

### Heuristic alignment + prosody edit

- `qwen-align.py`
- `qwen-prosody-edit.py`

This is not true forced alignment yet, but it is enough to start practical post-generation direction tests on individual chunks.

### Official Qwen ASR + ForcedAligner integration

- installed `qwen-asr`
- downloaded:
  - `Qwen/Qwen3-ASR-0.6B`
  - `Qwen/Qwen3-ForcedAligner-0.6B`
- confirmed `Qwen3ASRModel` works locally
- confirmed direct `Qwen3ForcedAligner` works locally
- completed a full `qwen_forced_aligner` pass for all 66 transcript chunks

This is the first real transcript-to-audio alignment path in the repo that uses the intended text directly instead of only heuristics or Whisper timing guesses.

### Retry + fallback repair strategy

- direct retries often rescue timeout chunks
- fallback `x_vector_only` repair can rescue some stubborn chunks
- fallback is not guaranteed:
  - `marker-14-lighting-c05` still timed out under fallback
- this means the pipeline now has evidence for three categories:
  - retry-recovers
  - fallback-recovers
  - truly stubborn silent-hang cases

### Pronunciation/style rerender tests

- post-generation word edits are useful for timing/emphasis
- they do not fix pronunciation problems like `the` sounding too much like `tee`
- targeted rerenders with text variants are the correct layer for:
  - pronunciation steering
  - sentence style shifts
  - stronger delivery changes

This means the pipeline now has two distinct control layers:

- rerender layer:
  - wording
  - pronunciation steering
  - sentence style
- post-edit layer:
  - pause cleanup
  - emphasis
  - small timing adjustments

## Current Noise Conclusion

- some noise is model-side
- FFmpeg helps, but cannot fully erase it without tradeoffs
- better strategy is:
  - lighter chunk trimming
  - avoid aggressive per-chunk denoise as the final sound
  - normalize the marker as one unit
  - add a stable room tone bed later

## Current Identity Conclusion

- `ref_text` mode is the right direction
- but script wording and chunking still strongly affect perceived identity

## Current Runtime Conclusion

- this does not currently look like a clean OOM-crash pattern
- memory pressure is real on the Mac:
  - low free RAM
  - heavy compression
  - large historical swap activity
- but the failing Qwen jobs usually do not crash with a useful error
- instead they silently hang until timeout
- current best explanation:
  - runtime/model hangs under memory pressure or long-session state
  - plus occasional line/reference interaction problems

## Current Research Conclusion

The next research topics are now clearly split:

- `intent/performance research`
  - annoyed
  - sarcastic
  - deadpan
  - reactive
  - baffled
  - reflective
- `runtime robustness research`
  - why silent hangs happen
  - which retries help
  - when fallback helps
  - whether one-off fresh runs outperform long sequential sessions

## External Review Takeaway

- do not destabilize the baseline by piling on advanced modules too early
- build around:
  - QC
  - review
  - approvals
  - room tone
  - final stitching
- treat RVC, DeepFilterNet, AudioSR, and distributed orchestration as later experiments, not current baseline requirements
