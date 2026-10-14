"""
WitnessIQ Entity Extractor
Extracts named entities and factual claims from witness statement text.

Methods:
  - spaCy NER (en_core_web_sm) for PERSON, GPE, LOC, ORG, DATE, TIME, CARDINAL
  - Rule-based pattern matching for colors, clothing, vehicles, and objects
  - python-dateutil for normalising time/date strings

Every extracted fact carries a 'source' field indicating detection method.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ─── Color and clothing patterns ─────────────────────────────────────────────

COLOR_WORDS = [
    "red", "blue", "black", "white", "green", "yellow", "grey", "gray",
    "brown", "purple", "orange", "pink", "navy", "dark", "light", "beige",
    "maroon", "silver", "gold", "cream", "tan",
]

CLOTHING_WORDS = [
    "jacket", "coat", "shirt", "jumper", "hoodie", "trousers", "jeans",
    "shorts", "skirt", "dress", "suit", "cap", "hat", "scarf", "gloves",
    "shoes", "boots", "trainers", "sneakers", "vest", "tie",
]

VEHICLE_WORDS = [
    "car", "vehicle", "van", "truck", "lorry", "motorbike", "motorcycle",
    "bicycle", "bike", "taxi", "bus", "suv",
]

OBJECT_WORDS = [
    "bag", "backpack", "rucksack", "briefcase", "phone", "mobile",
    "laptop", "box", "parcel", "package", "weapon", "knife", "gun",
]

# Regex: time patterns like 8:15 PM, 20:15, around 8, half past eight
TIME_PATTERN = re.compile(
    r"\b(?:approximately\s+|around\s+|about\s+|at\s+)?"
    r"(?:[01]?\d|2[0-3]):[0-5]\d(?:\s*[APap][Mm])?"
    r"|\b(?:[01]?\d|2[0-3])\s*(?:AM|PM|am|pm)\b",
    re.IGNORECASE,
)

# Regex: color + clothing/vehicle combos
COLOR_CLOTHING_PATTERN = re.compile(
    r"\b(" + "|".join(COLOR_WORDS) + r")\s+(" + "|".join(CLOTHING_WORDS) + r")\b",
    re.IGNORECASE,
)

COLOR_VEHICLE_PATTERN = re.compile(
    r"\b(" + "|".join(COLOR_WORDS) + r")\s+(" + "|".join(VEHICLE_WORDS) + r")\b",
    re.IGNORECASE,
)

DIRECTION_PATTERN = re.compile(
    r"\b(front|rear|back|side|main|secondary|emergency)[\s-](entrance|exit|door|lane|street)\b",
    re.IGNORECASE,
)

NEGATION_PATTERN = re.compile(
    r"\b(could not|couldn't|did not|didn't|was not|wasn't|unable to|failed to)\s+(see|identify|determine|observe)\b",
    re.IGNORECASE,
)


@dataclass
class ExtractedEntity:
    entity_type: str
    value: str
    sentence: str
    sentence_index: int
    source: str
    normalized: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using a simple rule-based splitter.
    Falls back if spaCy is unavailable.
    """
    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Split on . ! ? followed by space + uppercase
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [s.strip() for s in sentences if s.strip()]


def _extract_rule_based(sentence: str, sentence_index: int) -> List[ExtractedEntity]:
    """Extract entities using regex rules."""
    entities: List[ExtractedEntity] = []

    # Times
    for m in TIME_PATTERN.finditer(sentence):
        entities.append(ExtractedEntity(
            entity_type="TIME",
            value=m.group(0).strip(),
            sentence=sentence,
            sentence_index=sentence_index,
            source="rule_based",
        ))

    # Color + clothing
    for m in COLOR_CLOTHING_PATTERN.finditer(sentence):
        entities.append(ExtractedEntity(
            entity_type="CLOTHING",
            value=m.group(0).strip(),
            sentence=sentence,
            sentence_index=sentence_index,
            source="rule_based",
            extra={"color": m.group(1).lower(), "item": m.group(2).lower()},
        ))

    # Color + vehicle
    for m in COLOR_VEHICLE_PATTERN.finditer(sentence):
        entities.append(ExtractedEntity(
            entity_type="VEHICLE",
            value=m.group(0).strip(),
            sentence=sentence,
            sentence_index=sentence_index,
            source="rule_based",
            extra={"color": m.group(1).lower(), "item": m.group(2).lower()},
        ))

    # Directions/entrances
    for m in DIRECTION_PATTERN.finditer(sentence):
        entities.append(ExtractedEntity(
            entity_type="LOCATION_DETAIL",
            value=m.group(0).strip(),
            sentence=sentence,
            sentence_index=sentence_index,
            source="rule_based",
        ))

    # Negations (didn't see face, etc.)
    for m in NEGATION_PATTERN.finditer(sentence):
        entities.append(ExtractedEntity(
            entity_type="NEGATION",
            value=m.group(0).strip(),
            sentence=sentence,
            sentence_index=sentence_index,
            source="rule_based",
        ))

    return entities


def _extract_with_spacy(nlp, text: str, sentences: List[str]) -> List[ExtractedEntity]:
    """Use spaCy NER on the full text, mapped back to sentence indices."""
    entities: List[ExtractedEntity] = []
    doc = nlp(text)

    for ent in doc.ents:
        if ent.label_ not in {"PERSON", "GPE", "LOC", "ORG", "DATE", "TIME", "CARDINAL", "FAC"}:
            continue
        # Find which sentence this entity belongs to
        ent_start = ent.start_char
        char_offset = 0
        sent_idx = 0
        for idx, sent in enumerate(sentences):
            if ent_start <= char_offset + len(sent):
                sent_idx = idx
                break
            char_offset += len(sent) + 1  # +1 for space

        entities.append(ExtractedEntity(
            entity_type=ent.label_,
            value=ent.text,
            sentence=sentences[sent_idx] if sent_idx < len(sentences) else sentences[-1],
            sentence_index=sent_idx,
            source="spacy_ner",
        ))

    return entities


def extract_entities(text: str, nlp=None) -> Dict[str, Any]:
    """
    Main extraction function.
    Returns dict with 'sentences' and 'entities' lists.
    If nlp (spaCy model) is provided, uses NER; otherwise rule-based only.
    """
    sentences = split_into_sentences(text)
    all_entities: List[ExtractedEntity] = []

    # Rule-based for every sentence
    for idx, sent in enumerate(sentences):
        rule_ents = _extract_rule_based(sent, idx)
        all_entities.extend(rule_ents)

    # spaCy NER if available
    if nlp is not None:
        try:
            spacy_ents = _extract_with_spacy(nlp, text, sentences)
            # De-duplicate: spaCy TIME entities may overlap with rule-based TIME
            existing_values = {(e.entity_type, e.value.lower()) for e in all_entities}
            for ent in spacy_ents:
                key = (ent.entity_type, ent.value.lower())
                if key not in existing_values:
                    all_entities.append(ent)
                    existing_values.add(key)
        except Exception as exc:
            logger.warning("spaCy extraction error: %s", exc)

    return {
        "sentences": sentences,
        "entities": [
            {
                "entity_type": e.entity_type,
                "value": e.value,
                "sentence": e.sentence,
                "sentence_index": e.sentence_index,
                "source": e.source,
                "normalized": e.normalized,
                "extra": e.extra,
            }
            for e in all_entities
        ],
    }
