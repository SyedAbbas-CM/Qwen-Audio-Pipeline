# AI Audio Lab Agents

This folder is the working memory for the local Qwen voice pipeline.

Use these files as the source of truth before changing scripts, rerunning the transcript, or adding new pipeline stages.

## Files

- `PROJECT-PLAN.md`
  - The production roadmap.
  - Defines the target workflow from script editing to final narration export.

- `CURRENT-STAGE.md`
  - The current state of the pipeline right now.
  - Records what is working, what is still weak, and which output folders matter.

- `FILE-MAP.md`
  - Maps important scripts, transcripts, references, outputs, and reports.
  - Use this when figuring out where a stage reads from and writes to.

- `EXPERIMENT-LOG.md`
  - Records what was tried, what failed, and what succeeded.
  - Read this before repeating old dead ends.

- `PIPELINE-STAGES.md`
  - Breaks the pipeline into stages with goals, inputs, outputs, and exit criteria.
  - Useful when implementing or debugging one layer at a time.

- `NEXT-STEPS.md`
  - The immediate implementation queue.
  - This should be the first place to update after finishing a phase.

## Current Stage

We are past raw experimentation and into a basic production-pipeline phase.

Current status:
- `ref_audio + ref_text` cloning works better than `x_vector_only`
- short sequential chunks work
- marker-level merged review WAVs exist
- the transcript has been fully rendered into chunk WAVs and stitched into marker WAVs
- noise is reduced but not solved perfectly
- next serious work is QC, approvals, room tone, and final assembly

## Rules

- Do not assume a generated WAV is a finished asset.
- Do not overwrite approved or reviewable outputs without `--force` behavior.
- Prefer short chunks and sequential generation on the Mac.
- Read `EXPERIMENT-LOG.md` before introducing another cleanup or chunking hack.
- Update `CURRENT-STAGE.md` and `NEXT-STEPS.md` when a major milestone changes.
