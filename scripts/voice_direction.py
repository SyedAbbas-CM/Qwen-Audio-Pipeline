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

INTENT_TEMPERATURE = {
    "explaining": 0.35,
    "direct": 0.37,
    "determined": 0.39,
    "reactive": 0.41,
    "annoyed": 0.40,
    "deadpan": 0.33,
    "sarcastic": 0.36,
    "baffled": 0.37,
    "reflective": 0.34,
    "wondering": 0.35,
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


def remove_fillers(text: str) -> str:
    text = re.sub(r",?\s*\buh\b(?:\s*\.\.\.)?", "", text, flags=re.IGNORECASE)
    text = re.sub(r",?\s*\bum\b(?:\s*\.\.\.)?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([,.!?])", r"\1", text)
    return text.strip(" ,")


def with_sentence_punch(text: str) -> str:
    text = text.replace("—", ". ")
    text = text.replace(" - ", ". ")
    text = re.sub(r"\.\.\.\s*", ". ", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def deadpan_shape(text: str) -> str:
    text = remove_fillers(text)
    text = with_sentence_punch(text)
    return text


def annoyed_shape(text: str) -> str:
    text = tighten_opening(text)
    text = remove_fillers(text)
    text = with_sentence_punch(text)
    return text


def reactive_shape(text: str) -> str:
    text = text.replace("—", ". ")
    text = re.sub(r"\bthis guy's just,\s*", "this guy's ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bhe's\b", "he's", text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def baffled_shape(text: str) -> str:
    text = re.sub(r"\buh\b", "uh", text, flags=re.IGNORECASE)
    text = text.replace("... but", ". But")
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def reflective_shape(text: str) -> str:
    text = re.sub(r"\bAnyway,\s*uh\.\.\.\s*", "Anyway... ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def determined_shape(text: str) -> str:
    return remove_fillers(text)


def direct_shape(text: str) -> str:
    return tighten_opening(text)


def wondering_shape(text: str) -> str:
    return text.replace("—", "... ")


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


def choose_intent_temperature(intent: str, energy: str) -> float:
    base = INTENT_TEMPERATURE.get(intent, choose_temperature(energy))
    if energy == "lifted":
        return max(base, 0.39)
    if energy == "start-high":
        return max(base, 0.41)
    return base


def apply_intent(text: str, intent: str) -> str:
    if intent == "reactive":
        return reactive_shape(text)
    if intent == "annoyed":
        return annoyed_shape(text)
    if intent == "deadpan":
        return deadpan_shape(text)
    if intent == "sarcastic":
        return deadpan_shape(text)
    if intent == "baffled":
        return baffled_shape(text)
    if intent == "reflective":
        return reflective_shape(text)
    if intent == "determined":
        return determined_shape(text)
    if intent == "direct":
        return direct_shape(text)
    if intent == "wondering":
        return wondering_shape(text)
    return text


def build_variants(text: str, style: str, takes: int, intent: str = "explaining") -> list[dict[str, str]]:
    base = normalize_text(text)
    intended_base = apply_intent(base, intent)
    variants: list[tuple[str, str, str]] = [(intended_base, "steady", intent)]
    if intent == "reactive":
        variants.extend(
            [
                (reactive_shape(with_pause_after_first_sentence(base)), "lifted", "reactive"),
                (annoyed_shape(base), "start-high", "annoyed"),
                (deadpan_shape(base), "steady", "deadpan"),
            ]
        )
    elif intent == "annoyed":
        variants.extend(
            [
                (annoyed_shape(base), "lifted", "annoyed"),
                (deadpan_shape(base), "steady", "deadpan"),
                (with_sentence_punch(base), "start-high", "reactive"),
            ]
        )
    elif intent == "deadpan":
        variants.extend(
            [
                (deadpan_shape(base), "steady", "deadpan"),
                (with_sentence_punch(deadpan_shape(base)), "lifted", "sarcastic"),
                (tighten_opening(deadpan_shape(base)), "steady", "direct"),
            ]
        )
    elif intent == "baffled":
        variants.extend(
            [
                (baffled_shape(base), "steady", "baffled"),
                (with_pause_after_first_sentence(baffled_shape(base)), "lifted", "baffled"),
                (deadpan_shape(base), "steady", "deadpan"),
            ]
        )
    elif intent == "reflective":
        variants.extend(
            [
                (reflective_shape(base), "steady", "reflective"),
                (with_pause_after_first_sentence(reflective_shape(base)), "steady", "reflective"),
                (deadpan_shape(base), "steady", "deadpan"),
            ]
        )
    elif style == "performative":
        variants.extend(
            [
                (with_emphasis_breaks(with_pause_after_first_sentence(intended_base)), "lifted", intent),
                (with_soft_filler(intended_base), "steady", intent),
                (with_trailing_thought(with_pause_after_first_sentence(intended_base)), "start-high", intent),
            ]
        )
    elif style == "laidback":
        variants.extend(
            [
                (with_pause_after_first_sentence(intended_base), "steady", intent),
                (with_soft_filler(intended_base), "steady", intent),
                (with_emphasis_breaks(intended_base), "lifted", intent),
            ]
        )
    elif style == "sarcastic":
        variants.extend(
            [
                (with_trailing_thought(deadpan_shape(base)), "lifted", "sarcastic"),
                (with_pause_after_first_sentence(with_emphasis_breaks(deadpan_shape(base))), "lifted", "sarcastic"),
                (f"Okay... {deadpan_shape(base)}", "start-high", "sarcastic"),
            ]
        )
    else:
        variants.extend(
            [
                (with_pause_after_first_sentence(intended_base), "steady", intent),
                (with_emphasis_breaks(intended_base), "lifted", intent),
            ]
        )

    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item_text, energy, item_intent in variants:
        shaped = apply_energy(item_text, energy)
        key = (shaped, energy, item_intent)
        if key not in seen:
            seen.add(key)
            deduped.append(
                {
                    "text": shaped,
                    "energy": energy,
                    "intent": item_intent,
                    "temperature": f"{choose_intent_temperature(item_intent, energy):.2f}",
                }
            )
    while len(deduped) < takes:
        deduped.append(
            {
                "text": intended_base,
                "energy": "steady",
                "intent": intent,
                "temperature": f"{choose_intent_temperature(intent, 'steady'):.2f}",
            }
        )
    return deduped[:takes]
