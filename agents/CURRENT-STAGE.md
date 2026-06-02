# Current Stage

## Pipeline Stage

We are in the transition from "working generation pipeline" to "basic production pipeline".

Done:
- clean full new-voice run completed with:
  - `Qwen/Qwen3-TTS-12Hz-1.7B-Base`
  - `references/karachi-3-clean-10s-24k-mono.wav`
  - `transcripts/reference-voice-deeper-clean-10s-v1.txt`
  - `66/66` chunks ready with no fallback
- stitched clean 1.7B full narration:
  - `outputs/final/devlog-final-1p7b-karachi3-clean10s-v1.wav`
  - `outputs/final/devlog-final-1p7b-karachi3-clean10s-v1.mapping.tsv`
- stitched clean 1.7B marker set:
  - `outputs/final/devlog-final-1p7b-karachi3-clean10s-v1-markers`
- raw-chunk mastered marker path added:
  - stitch from `take-01-raw.wav`
  - short crossfades
  - marker-level roomtone bed
  - marker-level postprocess
- raw-mastered marker set built:
  - `outputs/final/devlog-final-1p7b-karachi3-clean10s-v1-markers-rawmaster-v2`
- transcript parsing
- sequential Qwen generation
- status/log tracking
- marker-level stitching
- marker-level room tone bed pass
- short `ref_audio + ref_text` path
- full chunk render for the devlog
- marker-level merged review WAVs
- review report generation
- approval baseline file
- silence-aware heuristic word alignment
- basic word-level prosody editing prototype
- final full narration stitch for comparison
- final approved-baseline narration stitch
- offline ASR download/setup path
- real offline ASR QC pass on the current transcript
- review report with WER/backend status columns
- config-backed queue/runner defaults
- baseline approval semantics split from real approval
- editable review sheet generation
- real `whisper_words` alignment backend using cached `faster-whisper`
- official `Qwen3-ForcedAligner-0.6B` downloaded and tested successfully
- official `Qwen3-ASR-0.6B` downloaded and tested successfully
- full `qwen_forced_aligner` alignment pass completed for all 66 chunks
- pronunciation/style rerender A/B/C testing path working
- V6 planning scaffolding for pronunciation and model research
  - `config/pronunciation-glossary.tsv`
  - `config/model-registry.json`
  - `transcripts/benchmark-lines.tsv`
- first working pronunciation layer
  - `scripts/find-pronunciation-terms.py`
  - `scripts/apply-pronunciation-glossary.py`
  - `scripts/pronunciation-qc.py`
  - `transcripts/devlog-final-manifest-spoken.tsv`
  - `reports/pronunciation-candidates.tsv`
  - `reports/pronunciation-qc.tsv`
- first working delivery-intent layer
  - `scripts/parse-transcript.py` now infers `intent`
  - `scripts/voice_direction.py` now shapes by `intent`
  - `scripts/render-intent-probes.py` can render targeted `reactive / annoyed / deadpan / sarcastic` probes
- deeper-reference clone comparison now tested
  - long expressive reference:
    - `references/karachi-3-24k-mono.wav`
    - unstable for broad full-transcript generation
  - short neutral/deeper reference:
    - `references/karachi-3-short-24k-mono.wav`
    - `transcripts/reference-voice-deeper-short-v1.txt`
    - stable enough for targeted probes
- full Karachi 3 short rerender is mostly complete
  - main output:
    - `outputs/qwen3-karachi3-short-full-v1`
  - current state:
    - `63` ready in the main tree
    - `2` additional chunks recovered in fallback repair
    - `1` stubborn chunk still hanging
  - fallback repair output:
    - `outputs/qwen3-karachi3-short-repair-xvec`
- Karachi 3 short fallback recoveries confirmed:
  - `marker-17-balancing-c02`
  - `marker-21-hallways-c01`
- slim external review bundle prepared:
  - `qwen-audio-pipeline-review-slim-v7.zip`
- full spoken-manifest rerender started for the original voice
  - `outputs/qwen3-reftext-spoken-full-v1`
- one previously failed spoken chunk repaired successfully
  - `marker-21-hallways-c02`
- complete stitched narration built from the spoken run with fallback only where needed
  - `outputs/final/devlog-final-yours-spoken-v1.wav`
  - `outputs/final/devlog-final-yours-spoken-v1.mapping.tsv`

Not done:
- meaningful human approval decisions across the transcript
- higher-quality aligner backend like WhisperX/MFA for future comparison
- higher-quality per-word time/pitch editing
- better reusable pronunciation/style variant generation flow
- glossary-driven `synthesis_text` manifest flow
- pronunciation QC refinement as glossary expands
- controlled TTS benchmark harness
- final judgment on whether raw-mastered markers are good enough to replace the older clean-chunk marker set
- root-cause isolation for silent generation hangs
- intent/emotion research implementation beyond the first probe layer

## Current Best Path

Use:
- verified clean 10 second Karachi 3 reference pair
  - `references/karachi-3-clean-10s-24k-mono.wav`
  - `transcripts/reference-voice-deeper-clean-10s-v1.txt`
- `Qwen/Qwen3-TTS-12Hz-1.7B-Base`
- proper clone mode
  - `ref_audio + ref_text`
- sequential queue
  - `scripts/qwen-run-queue.py`

Avoid as default:
- `x_vector_only`
- long monologue chunks
- heavy rewrite before voice identity is stable
- aggressive silence chasing
- per-chunk denoise/limiter as the final marker sound

## Current Output Folders

- chunked transcript outputs:
  - `outputs/qwen3-reftext-full-v2`
- marker-level merged review WAVs:
  - `outputs/qwen3-reftext-full-v2-markers`
- marker-level roomtone review WAVs:
  - `outputs/qwen3-reftext-full-v2-markers-roomtone`
- stitched full narration for comparison:
  - `outputs/final/devlog-final-unapproved.wav`
- approved-baseline narration:
  - `outputs/final/devlog-final-approved-baseline.wav`
- word alignments:
  - `alignments/qwen3-reftext-full-v2`
- first prosody-edit outputs:
  - `outputs/prosody`
- approvals:
  - `transcripts/approved-takes.tsv`
- ASR QC:
  - `reports/qwen-asr-qc.tsv`
- review report:
  - `reports/qwen-review-report.tsv`
- pronunciation tests:
  - `outputs/qwen3-pronunciation-tests`
- pronunciation/model research scaffolding:
  - `config/pronunciation-glossary.tsv`
  - `config/model-registry.json`
  - `transcripts/benchmark-lines.tsv`
- spoken-manifest full rerender:
  - `outputs/qwen3-reftext-spoken-full-v1`
- stitched mixed-source spoken full narration:
  - `outputs/final/devlog-final-yours-spoken-v1.wav`
  - `outputs/final/devlog-final-yours-spoken-v1.mapping.tsv`

## Current Problems

- low-level generated noise still exists
- denoise can reduce noise, but overdoing it causes pumping or artifacts
- chunk seams can be obvious if chunking is too aggressive
- some script wording is still too pause-heavy
- many lines still share too much of the same narration contour unless explicitly shaped by intent
- long reference clips that mix multiple intent modes can destabilize `ref_audio + ref_text` generation
- a single expressive reference is not automatically a better cloning baseline than a shorter neutral one
- ASR QC is now working locally with cached `faster-whisper`
- current alignment now supports:
  - `whisper_words` from `faster-whisper`
  - `qwen_forced_aligner` from `Qwen3-ForcedAligner-0.6B`
  - `silence_aware_heuristic` as fallback
- the spoken-manifest full rerender still hangs on the five outro chunks in this environment
- current full narration therefore falls back to the earlier pass for:
  - `marker-29-outro-c01`
  - `marker-29-outro-c02`
  - `marker-29-outro-c03`
  - `marker-29-outro-c04`
  - `marker-29-outro-c05`
- per-chunk `light` cleanup causes:
  - noise-floor pumping
  - seam exaggeration
  - tails that feel like they soften or dip
- hard-concat marker stitching is not good enough as a final assembly path

## Current QC Shortlist

Flagged by the first real ASR pass:

- `marker-4-intro-c04`
  - `needs_retry`
  - failed ASR similarity
- `marker-14-lighting-c01`
  - `needs_manual_edit`
- `marker-26-the-boss-c01`
  - `needs_manual_edit`
- `marker-12-testing-c01`
  - `needs_manual_edit`
- `marker-16-elites-c02`
  - `needs_manual_edit`
- `marker-22-inventory-stats-c03`
  - `needs_manual_edit`
- `marker-6-vfx-c01`
  - `needs_manual_edit`
- `marker-21-hallways-c02`
  - `needs_manual_edit`
- `marker-18-stats-armor-c02`
  - `needs_manual_edit`

## Current Win

The transcript is now rendered in chunks, reviewable by marker, stitchable into a full narration, and editable at a basic word level. That is the first real production-style baseline this project has had.

The strongest current local baseline is now the clean `1.7B + verified 10s Karachi 3 pair` run. The main open quality problem is post-generation assembly, not voice cloning.

## Current Upgrade

The pipeline now also supports:

- an editable TSV review sheet:
  - `reports/qwen-review-sheet.tsv`
- applying letter-coded decisions back into approvals:
  - `scripts/apply-review-sheet.py`
- real word timestamps from Whisper for current generated WAVs:
  - `alignments/qwen3-reftext-full-v2/*.words.json`
- real Qwen forced-aligner timestamps for comparison:
  - `alignments/qwen3-reftext-qfa-test/*.words.json`
- pronunciation rerender comparisons:
  - `outputs/qwen3-pronunciation-tests/marker-14-lighting/*.wav`

## Current Direction

The next real pipeline layer is pronunciation control before generation:

- original script text stays human-readable
- `synthesis_text` becomes the Qwen-ready form
- glossary/G2P solves names, acronyms, and technical terms
- Qwen forced aligner and prosody edits stay focused on timing/emphasis after generation

The first version of that layer now exists and is usable.

The next adjacent layer is delivery intent:

- not just `style`
- but `reactive`, `annoyed`, `deadpan`, `sarcastic`, `reflective`, `baffled`, `explaining`
- this is the right answer for lines that need dry complaint, monotone sarcasm, or deliberate annoyance

## Current Reference Rule

For cloning stability:

- use a short neutral/deeper reference as the default baseline
- keep longer expressive references as an `intent bank`, not the main transcript baseline

Current finding:

- `karachi-3-24k-mono.wav` is useful as a richer voice sample
- but it is too broad/long for reliable full transcript generation on this setup
- `karachi-3-short-24k-mono.wav` is the better practical baseline for the next clone comparison stage
- even with `karachi-3-short-24k-mono.wav`, a small number of chunks can still silently hang
- the current worst stubborn chunk is:
  - `marker-14-lighting-c05`
  - text:
    - `Could be interesting.`
- that line has timed out under:
  - `ref_audio + ref_text`
  - `x_vector_only` fallback
  - a fresh isolated one-off rerun
- this means the remaining problem is not only "long text fails"
- the repo now has evidence of a deeper runtime/generation hang issue

## Karachi 3 Short State

Current Karachi 3 short status:

- main tree:
  - `63` ready
  - `1` unresolved stubborn chunk
- fallback repair successes:
  - `outputs/qwen3-karachi3-short-repair-xvec/marker-17-balancing-c02/take-01-clean.wav`
  - `outputs/qwen3-karachi3-short-repair-xvec/marker-21-hallways-c01/take-01-clean.wav`
- fallback repair failure so far:
  - `outputs/qwen3-karachi3-short-repair-xvec/marker-14-lighting-c05`

Important implication:

- the Karachi 3 short voice is usable
- but the generation pipeline still needs repair-and-stitch logic even on the improved reference
- one unresolved hang is enough to block a clean final stitch, so robustness remains a core pipeline problem

## Failure Diagnosis

Current best diagnosis for the remaining failures:

- logs are nearly empty:
  - only the initial `pad_token_id` line appears
  - then the process sits until timeout
- this does not look like:
  - a normal Python exception
  - a postprocess failure
  - a simple long-line problem
- this more likely looks like:
  - silent model/runtime hangs
  - long-session queue instability
  - memory-pressure-related stalls on this Mac
  - or a rare text/reference interaction that the current runtime does not recover from cleanly

Current memory-pressure clue:

- system state showed only a small amount of unused RAM
- heavy compression and large historical swap activity were present
- that suggests memory pressure is real, but not a clean OOM-kill signature

Current research rule:

- treat these as `silent generation hangs`
- not as plain "bad script" failures
- future debugging should isolate:
  - queue-state effects
  - per-line effects
  - reference-conditioning effects
  - runtime/memory-pressure effects

## Current Reference Rule

For the Karachi 3 voice specifically:

- do not use ASR-guessed or loosely matched short reference text
- do not use a clipped audio span unless the transcript has been manually verified against that exact clip
- current verified-good small pair:
  - `references/karachi-3-clean-10s-24k-mono.wav`
  - `transcripts/reference-voice-deeper-clean-10s-v1.txt`

Recent finding:

- a bad `ref_audio + ref_text` match was enough to make `Could be interesting.` silently hang
- the same line succeeded once the reference pair was tightly matched

## Local Benchmark Rule

On this 16 GB Apple Silicon Mac:

- do not benchmark TTS variants in parallel
- do not benchmark multiple lines at once when comparing `0.6B` vs `1.7B`
- use:
  - one model
  - one line
  - one verified reference pair
  - one fresh process

Reason:

- parallel local probes produced misleading failures, especially on `1.7B`
- the first successful `1.7B` result came only after:
  - shrinking the reference pair
  - matching transcript to clip
  - running a single sequential probe
