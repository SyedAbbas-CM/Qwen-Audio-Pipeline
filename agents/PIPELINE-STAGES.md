# Pipeline Stages

## Stage 0: Authoring

Input:
- `transcripts/devlog-final.txt`

Goal:
- spoken-friendly script
- chunkable text

Exit criteria:
- wording is good enough to render

## Stage 1: Parsing

Script:
- `scripts/parse-transcript.py`

Output:
- `transcripts/devlog-final-manifest-reftext.tsv`

Goal:
- split text into short, sequential chunks

Exit criteria:
- no giant monologue rows
- chunk order matches marker order

## Stage 2: Generation

Scripts:
- `scripts/qwen-run-one-take.py`
- `scripts/qwen-run-queue.py`

Output:
- raw WAV
- clean WAV
- status JSON
- log file

Goal:
- produce one reviewable take per chunk

Exit criteria:
- `status = ready`

## Stage 3: QC

Planned:
- `scripts/qwen-asr-qc.py`
- `scripts/qwen-review-report.py`

Goal:
- verify that audio says the intended text

Exit criteria:
- pass / warn / fail score per chunk

## Stage 4: Human Review

Current:
- marker review WAVs in `outputs/qwen3-reftext-full-v2-markers`

Goal:
- decide which markers or chunks are acceptable

Exit criteria:
- keep / rewrite / rerender / manual fix decisions

## Stage 5: Approval

Planned:
- `scripts/approve-take.py`

Goal:
- mark which takes are actually approved

Exit criteria:
- approvals file exists

## Stage 6: Marker Polish

Planned:
- room tone bed
- better postprocess profiles

Goal:
- reduce noise pumping
- stabilize background feel

Exit criteria:
- markers sound less artificial in pauses

## Stage 7: Final Stitch

Planned:
- `scripts/stitch-approved-final.py`

Goal:
- create one final narration WAV from approved takes only

Exit criteria:
- `outputs/final/devlog-final.wav`

## Stage 8: Directed Performance

Planned:
- `scripts/qwen-align.py`
- `scripts/qwen-prosody-edit.py`

Goal:
- exact word timing and performance edits

Exit criteria:
- per-word pause/stretch/gain control works
