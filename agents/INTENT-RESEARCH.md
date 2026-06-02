# Intent Research

## Goal

Move from generic narration to directed delivery.

The current pipeline can already do:
- pronunciation control before generation
- chunk generation and repair
- alignment
- basic post-generation timing edits

The weak point is `intent separation`.

Right now many lines still collapse into the same broad delivery bucket:
- calm explanation
- slight pause variation
- same overall narration contour

We need to engineer distinct intent classes that survive cloning.

## What To Research

### 1. Intent Taxonomy

Define a small set of intents that are actually useful in this project.

Current candidate set:
- `explaining`
- `reactive`
- `annoyed`
- `deadpan`
- `sarcastic`
- `baffled`
- `reflective`
- `determined`
- `direct`
- `wondering`

Research question:
- which of these are genuinely distinguishable with the current local Qwen stack?

### 2. Lexical Cues

Research how wording influences perceived intent.

Examples:
- annoyed:
  - shorter clauses
  - fewer fillers
  - more blunt verbs
- deadpan:
  - simpler syntax
  - less punctuation drama
  - flatter wording
- sarcasm:
  - contrast phrase
  - understatement
  - punch word near the end
- reactive:
  - front-loaded trigger words
  - interruption
  - sharper opening

Research question:
- which text edits change intent without breaking identity?

Sub-question:
- which exact words or phrase shapes make something read as:
  - annoyed
  - dry sarcasm
  - deadpan
  - baffled
without sounding overacted?

### 3. Prosodic Cues

Research which acoustic dimensions matter per intent:
- sentence attack
- pause placement
- pause length
- speaking rate
- emphasis placement
- pitch movement
- phrase-final falloff

Research question:
- what can be solved before generation vs after generation?

Need specific focus on:
- phrase-initial attack
- phrase-final fall
- whether monotone sarcasm is really flatter pitch, or just reduced emphasis plus dry timing
- whether annoyance is sharper attack, faster cadence, or stronger consonant emphasis

### 4. Reference Conditioning

Research whether intent-specific reference clips improve delivery more than text shaping alone.

Likely reference bank:
- neutral / explanatory
- reactive
- annoyed
- deadpan
- sarcastic

Research question:
- does one short reference per intent outperform one generic reference for all lines?

Current finding:
- a long mixed-intent reference can destabilize generation
- a shorter neutral reference appears more stable
- we should test:
  - short neutral baseline
  - short annoyed reference
  - short deadpan reference
  - short sarcastic reference

### 5. Model Capability

Research whether stronger Qwen variants improve style separation.

Candidates later:
- `Qwen3-TTS-12Hz-0.6B-CustomVoice`
- `Qwen3-TTS-12Hz-1.7B-Base`
- `Qwen3-TTS-12Hz-1.7B-CustomVoice`

Research question:
- is the current limitation mainly prompting/text, or is it model capacity/style control?

This matters because:
- if `reactive` separates but `annoyed` and `sarcastic` collapse together,
  the bottleneck may be model/style control rather than just text shaping

## Engineering Plan

### Stage A: Better Reference

Record a new reference script that includes:
- neutral explanation
- annoyed
- deadpan
- reactive
- sarcastic
- baffled
- reflective

Current file:
- `transcripts/reference-voice-deeper-v1.txt`

Current practical baseline:
- `references/karachi-3-short-24k-mono.wav`
- `transcripts/reference-voice-deeper-short-v1.txt`

Current non-baseline expressive bank:
- `references/karachi-3-24k-mono.wav`

### Stage B: Intent Bench

For a small fixed line set, generate:
- same line
- multiple intent labels
- same speaker
- same model

Suggested lines:
- `Wait, look at this. He's spamming way too many bombs.`
- `I definitely need to fix that.`
- `I genuinely don't know why the boss keeps doing that.`
- `The project still has problems, but the bones are good.`

Compare:
- text only
- text + intent shaping
- text + intent-specific reference later
- old short baseline reference vs new short deeper baseline reference

### Stage C: Scoring

Judge each output on:
- identity retention
- distinctness from neutral
- naturalness
- usefulness for video placement

### Stage D: Manifest Integration

Once the best cues are known:
- keep `intent` in manifests
- add stronger shaping rules
- optionally add `intent_reference` later

## Practical Rule

Use the right layer for the right problem:

- pronunciation problem:
  - fix before generation with `synthesis_text`
- intent problem:
  - fix with wording, intent shaping, and maybe intent-specific reference
- timing problem:
  - fix after generation with alignment/prosody
- noise problem:
  - fix at cleanup or marker polish

## Current Recommendation

Do not overcomplicate this with ten emotions.

Start with four that matter most:
- `reactive`
- `annoyed`
- `deadpan`
- `sarcastic`

Then add:
- `baffled`
- `reflective`

That is enough to make the devlog feel directed instead of uniformly narrated.

## Why The New Full Transcript Struggled

Observed issue:
- full transcript generation with `karachi-3-24k-mono.wav` struggled early
- short probe generation with `karachi-3-short-24k-mono.wav` was much more stable

Working hypothesis:
- the long reference mixed multiple delivery modes
- that increases conditioning ambiguity and instability for `ref_audio + ref_text`
- the model handles a shorter neutral/deeper clip better as a cloning anchor

Pipeline fix:
- keep one short stable baseline reference
- use longer expressive references only as intent-specific research material
