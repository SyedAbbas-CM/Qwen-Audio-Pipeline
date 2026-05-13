from __future__ import annotations

import re


LEADING_FILLER_RE = re.compile(
    r"^(?:(?:so|well|okay|alright|and|but|i)\s*,?\s*(?:um+|uh+)?\s*(?:\.\.\.)?\s*)+",
    re.IGNORECASE,
)
UM_WORD_RE = re.compile(r"\bum+\b", re.IGNORECASE)
FILLER_PAUSE_RE = re.compile(r"\b(uh|um)\.\.\.\s+(well|so|okay|alright|but)\b", re.IGNORECASE)
DOUBLE_FALLTHROUGH_RE = re.compile(r"([A-Za-z])\.\.\.\s+([a-z])")

ENERGY_TEMPERATURE = {
    "steady": 0.35,
    "lifted": 0.42,
    "start-high": 0.48,
}


def normalize_text(text: str) -> str:
    text = " ".join(text.strip().split())
    text = UM_WORD_RE.sub("uh", text)
    text = text.replace("..,.", ".")
    text = text.replace("...,", "...")
    text = re.sub(r"\.{4,}", "...", text)
    text = FILLER_PAUSE_RE.sub(lambda m: f"{m.group(1)}, {m.group(2)}", text)
    text = DOUBLE_FALLTHROUGH_RE.sub(r"\1, \2", text)
    return text


def with_pause_after_first_sentence(text: str) -> str:
    parts = text.split(". ", 1)
    if len(parts) == 2:
        return f"{parts[0]}... {parts[1]}"
    return text


def with_soft_filler(text: str) -> str:
    parts = text.split(". ", 1)
    if len(parts) == 2:
        return f"{parts[0]}. Uh... {parts[1]}"
    return f"Uh... {text}"


def with_emphasis_breaks(text: str) -> str:
    text = text.replace(", ", "... ")
    text = re.sub(r"\s+[—-]\s+", "... ", text)
    return text


def with_trailing_thought(text: str) -> str:
    if text.endswith("."):
        return text[:-1] + "... yeah."
    return text + "... yeah."


def tighten_opening(text: str) -> str:
    text = LEADING_FILLER_RE.sub("", text).strip()
    text = re.sub(r"\.\.\.\s+", ", ", text, count=1)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def apply_energy(text: str, energy: str) -> str:
    if energy == "steady":
        return text
    if energy == "lifted":
        text = re.sub(r"\.\.\.\s+", ", ", text, count=1)
        return text
    if energy == "start-high":
        tightened = tighten_opening(text)
        return tightened or text
    return text


def choose_temperature(energy: str) -> float:
    return ENERGY_TEMPERATURE.get(energy, ENERGY_TEMPERATURE["steady"])


def build_variants(text: str, style: str, takes: int) -> list[dict[str, str]]:
    base = normalize_text(text)
    variants: list[tuple[str, str]] = [(base, "steady")]
    if style == "performative":
        variants.extend(
            [
                (with_emphasis_breaks(with_pause_after_first_sentence(base)), "lifted"),
                (with_soft_filler(base), "steady"),
                (with_trailing_thought(with_pause_after_first_sentence(base)), "start-high"),
            ]
        )
    elif style == "laidback":
        variants.extend(
            [
                (with_pause_after_first_sentence(base), "steady"),
                (with_soft_filler(base), "steady"),
                (with_emphasis_breaks(base), "lifted"),
            ]
        )
    elif style == "sarcastic":
        variants.extend(
            [
                (with_trailing_thought(base), "lifted"),
                (with_pause_after_first_sentence(with_emphasis_breaks(base)), "lifted"),
                (f"Okay... {base}", "start-high"),
            ]
        )
    else:
        variants.extend(
            [
                (with_pause_after_first_sentence(base), "steady"),
                (with_emphasis_breaks(base), "lifted"),
            ]
        )

    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item_text, energy in variants:
        shaped = apply_energy(item_text, energy)
        key = (shaped, energy)
        if key not in seen:
            seen.add(key)
            deduped.append(
                {
                    "text": shaped,
                    "energy": energy,
                    "temperature": f"{choose_temperature(energy):.2f}",
                }
            )
    while len(deduped) < takes:
        deduped.append(
            {
                "text": base,
                "energy": "steady",
                "temperature": f"{choose_temperature('steady'):.2f}",
            }
        )
    return deduped[:takes]
