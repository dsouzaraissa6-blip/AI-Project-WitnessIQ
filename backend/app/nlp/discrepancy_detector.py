"""
WitnessIQ Discrepancy Detector

Compares extracted entities and semantically-related sentence pairs across
witness statements to identify:
  - Potential inconsistencies (same topic, different factual values)
  - Differences requiring review
  - Details reported by only one witness
  - Similar information (agreement)
  - Ambiguous or insufficient information

IMPORTANT METHODOLOGY NOTE
───────────────────────────
This module does NOT determine who is telling the truth. It flags textual
differences and topical similarities for human review.

A "potential inconsistency" means:
  - Two sentences appear to describe a similar event (high semantic similarity
    OR same entity category matched by rules), AND
  - The extracted factual values differ.

This is NOT proof of deception. Differences may arise from:
  - Observers at different positions or times.
  - Imprecise language or memory.
  - Different aspects of the same scene.
  - The sentences describing genuinely different events.

Classification key
──────────────────
potential_inconsistency  — Related claims with differing factual values.
difference_for_review    — Values differ but relatedness is uncertain.
one_witness_only         — A detail mentioned by only one witness.
similar                  — Matching or very close values across statements.
ambiguous                — Insufficient information to compare.
"""
import re
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


# ─── Time normalisation ───────────────────────────────────────────────────────

_TIME_RE = re.compile(
    r"(\d{1,2}):?(\d{2})?\s*([AaPp][Mm])?",
)


def _parse_minutes(time_str: str) -> Optional[int]:
    """
    Converts a time string like '8:15 PM', '20:45', '8 PM' to minutes-since-midnight.
    Returns None if unparseable.
    """
    s = time_str.strip().upper()
    m = _TIME_RE.search(s)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2)) if m.group(2) else 0
    ampm = m.group(3)
    if ampm == "PM" and hour != 12:
        hour += 12
    elif ampm == "AM" and hour == 12:
        hour = 0
    return hour * 60 + minute


def _time_difference_minutes(t1: str, t2: str) -> Optional[int]:
    """Returns absolute difference in minutes between two time strings."""
    a = _parse_minutes(t1)
    b = _parse_minutes(t2)
    if a is None or b is None:
        return None
    return abs(a - b)


# ─── Color normalisation ──────────────────────────────────────────────────────

_DARK_COLORS = {"black", "navy", "dark", "charcoal", "dark grey", "dark gray"}
_SIMILAR_COLORS = {
    frozenset({"grey", "gray"}),
    frozenset({"dark", "black"}),
}


def _colors_are_similar(c1: str, c2: str) -> bool:
    c1, c2 = c1.lower(), c2.lower()
    if c1 == c2:
        return True
    for pair in _SIMILAR_COLORS:
        if c1 in pair and c2 in pair:
            return True
    return False


# ─── Entity grouping ──────────────────────────────────────────────────────────

def _group_entities_by_type(entities: List[Dict]) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = {}
    for ent in entities:
        et = ent["entity_type"]
        groups.setdefault(et, []).append(ent)
    return groups


# ─── Main discrepancy functions ───────────────────────────────────────────────

def _make_discrepancy(
    category: str,
    w_a_label: str,
    w_b_label: str,
    w_a_text: str,
    w_b_text: str,
    w_a_sentence: str,
    w_b_sentence: str,
    w_a_sent_idx: int,
    w_b_sent_idx: int,
    classification: str,
    explanation: str,
    method: str,
    similarity_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "category": category,
        "witness_a_label": w_a_label,
        "witness_b_label": w_b_label,
        "witness_a_text": w_a_text,
        "witness_b_text": w_b_text,
        "witness_a_sentence": w_a_sentence,
        "witness_b_sentence": w_b_sentence,
        "witness_a_sentence_idx": w_a_sent_idx,
        "witness_b_sentence_idx": w_b_sent_idx,
        "classification": classification,
        "explanation": explanation,
        "detection_method": method,
        "similarity_score": similarity_score,
        "review_status": None,
        "review_note": None,
    }


def compare_time_entities(
    ents_a: List[Dict],
    ents_b: List[Dict],
    w_a_label: str,
    w_b_label: str,
    semantic_pairs: List[Dict],
) -> List[Dict[str, Any]]:
    """Compare TIME entities between two statements."""
    discrepancies = []
    times_a = ents_a  # already filtered to TIME
    times_b = ents_b

    for ta in times_a:
        for tb in times_b:
            diff = _time_difference_minutes(ta["value"], tb["value"])
            if diff is None:
                continue

            # Check if their source sentences are semantically related
            related = _sentences_are_related(
                ta["sentence"], tb["sentence"], ta["sentence_index"], tb["sentence_index"],
                semantic_pairs
            )

            if diff == 0:
                if related:
                    discrepancies.append(_make_discrepancy(
                        "Time", w_a_label, w_b_label,
                        ta["value"], tb["value"],
                        ta["sentence"], tb["sentence"],
                        ta["sentence_index"], tb["sentence_index"],
                        "similar",
                        f"Both witnesses report the same time: {ta['value']}.",
                        "rule_based",
                    ))
            elif diff <= 10:
                discrepancies.append(_make_discrepancy(
                    "Time", w_a_label, w_b_label,
                    ta["value"], tb["value"],
                    ta["sentence"], tb["sentence"],
                    ta["sentence_index"], tb["sentence_index"],
                    "difference_for_review",
                    (
                        f"{w_a_label} reports {ta['value']} and {w_b_label} reports {tb['value']} "
                        f"— a difference of {diff} minute(s). "
                        "This may reflect approximation or different sub-events."
                    ),
                    "rule_based",
                ))
            else:
                classification = "potential_inconsistency" if related else "difference_for_review"
                discrepancies.append(_make_discrepancy(
                    "Time", w_a_label, w_b_label,
                    ta["value"], tb["value"],
                    ta["sentence"], tb["sentence"],
                    ta["sentence_index"], tb["sentence_index"],
                    classification,
                    (
                        f"{w_a_label} reports {ta['value']} and {w_b_label} reports {tb['value']} "
                        f"— a difference of {diff} minute(s). "
                        "These appear to describe potentially similar events but with different reported times. "
                        "This does not establish which time is correct."
                    ),
                    "rule_based",
                ))
    return discrepancies


def compare_clothing_entities(
    ents_a: List[Dict],
    ents_b: List[Dict],
    w_a_label: str,
    w_b_label: str,
    semantic_pairs: List[Dict],
) -> List[Dict[str, Any]]:
    """Compare CLOTHING entities."""
    discrepancies = []
    for ca in ents_a:
        for cb in ents_b:
            extra_a = ca.get("extra", {})
            extra_b = cb.get("extra", {})
            item_a = extra_a.get("item", "")
            item_b = extra_b.get("item", "")
            color_a = extra_a.get("color", "")
            color_b = extra_b.get("color", "")

            # Only compare same clothing item
            if item_a != item_b:
                continue

            related = _sentences_are_related(
                ca["sentence"], cb["sentence"], ca["sentence_index"], cb["sentence_index"],
                semantic_pairs
            )

            if _colors_are_similar(color_a, color_b):
                if related:
                    discrepancies.append(_make_discrepancy(
                        "Clothing / Color", w_a_label, w_b_label,
                        ca["value"], cb["value"],
                        ca["sentence"], cb["sentence"],
                        ca["sentence_index"], cb["sentence_index"],
                        "similar",
                        f"Both witnesses describe similar {item_a}: '{ca['value']}' and '{cb['value']}'.",
                        "rule_based",
                    ))
            else:
                classification = "potential_inconsistency" if related else "difference_for_review"
                discrepancies.append(_make_discrepancy(
                    "Clothing / Color", w_a_label, w_b_label,
                    ca["value"], cb["value"],
                    ca["sentence"], cb["sentence"],
                    ca["sentence_index"], cb["sentence_index"],
                    classification,
                    (
                        f"{w_a_label} describes a '{ca['value']}' while {w_b_label} describes a '{cb['value']}'. "
                        f"The {item_a} color differs. "
                        "This may reflect genuinely different clothing, lighting conditions, or observer perspective. "
                        "This does not establish which description is correct."
                    ),
                    "rule_based",
                ))
    return discrepancies


def compare_vehicle_entities(
    ents_a: List[Dict],
    ents_b: List[Dict],
    w_a_label: str,
    w_b_label: str,
    semantic_pairs: List[Dict],
) -> List[Dict[str, Any]]:
    """Compare VEHICLE entities."""
    discrepancies = []
    for va in ents_a:
        for vb in ents_b:
            extra_a = va.get("extra", {})
            extra_b = vb.get("extra", {})
            item_a = extra_a.get("item", "")
            item_b = extra_b.get("item", "")
            color_a = extra_a.get("color", "")
            color_b = extra_b.get("color", "")

            if item_a != item_b:
                continue

            related = _sentences_are_related(
                va["sentence"], vb["sentence"], va["sentence_index"], vb["sentence_index"],
                semantic_pairs
            )

            if _colors_are_similar(color_a, color_b):
                if related:
                    discrepancies.append(_make_discrepancy(
                        "Vehicle", w_a_label, w_b_label,
                        va["value"], vb["value"],
                        va["sentence"], vb["sentence"],
                        va["sentence_index"], vb["sentence_index"],
                        "similar",
                        f"Both witnesses mention a similarly described {item_a}: '{va['value']}' and '{vb['value']}'.",
                        "rule_based",
                    ))
            else:
                classification = "potential_inconsistency" if related else "difference_for_review"
                discrepancies.append(_make_discrepancy(
                    "Vehicle", w_a_label, w_b_label,
                    va["value"], vb["value"],
                    va["sentence"], vb["sentence"],
                    va["sentence_index"], vb["sentence_index"],
                    classification,
                    (
                        f"{w_a_label} mentions a '{va['value']}' while {w_b_label} mentions a '{vb['value']}'. "
                        f"The {item_a} color differs."
                    ),
                    "rule_based",
                ))
    return discrepancies


def compare_location_entities(
    ents_a: List[Dict],
    ents_b: List[Dict],
    w_a_label: str,
    w_b_label: str,
    semantic_pairs: List[Dict],
) -> List[Dict[str, Any]]:
    """Compare LOCATION_DETAIL entities (entrances, exits, etc.)."""
    discrepancies = []
    for la in ents_a:
        for lb in ents_b:
            related = _sentences_are_related(
                la["sentence"], lb["sentence"], la["sentence_index"], lb["sentence_index"],
                semantic_pairs
            )
            if la["value"].lower() == lb["value"].lower():
                if related:
                    discrepancies.append(_make_discrepancy(
                        "Location", w_a_label, w_b_label,
                        la["value"], lb["value"],
                        la["sentence"], lb["sentence"],
                        la["sentence_index"], lb["sentence_index"],
                        "similar",
                        f"Both witnesses reference the same location detail: '{la['value']}'.",
                        "rule_based",
                    ))
            else:
                if not related:
                    continue
                classification = "potential_inconsistency" if related else "difference_for_review"
                discrepancies.append(_make_discrepancy(
                    "Location", w_a_label, w_b_label,
                    la["value"], lb["value"],
                    la["sentence"], lb["sentence"],
                    la["sentence_index"], lb["sentence_index"],
                    classification,
                    (
                        f"{w_a_label} references '{la['value']}' while {w_b_label} references '{lb['value']}'. "
                        "These may describe different vantage points or different events."
                    ),
                    "rule_based",
                ))
    return discrepancies


def find_unique_details(
    ents_a: List[Dict],
    ents_b: List[Dict],
    all_discrepancy_values: set,
    w_a_label: str,
    w_b_label: str,
) -> List[Dict[str, Any]]:
    """
    Finds entities mentioned by only one witness that are not already covered
    by a cross-statement comparison.
    """
    discrepancies = []
    types_to_check = {"TIME", "CLOTHING", "VEHICLE", "LOCATION_DETAIL"}

    values_b = {e["value"].lower() for e in ents_b if e["entity_type"] in types_to_check}
    values_a = {e["value"].lower() for e in ents_a if e["entity_type"] in types_to_check}

    for ea in ents_a:
        if ea["entity_type"] not in types_to_check:
            continue
        if ea["value"].lower() in all_discrepancy_values:
            continue
        if ea["value"].lower() not in values_b:
            discrepancies.append(_make_discrepancy(
                ea["entity_type"].replace("_", " ").title(),
                w_a_label, w_b_label,
                ea["value"], "(not mentioned)",
                ea["sentence"], "",
                ea["sentence_index"], -1,
                "one_witness_only",
                f"{w_a_label} mentions '{ea['value']}' but {w_b_label} does not reference a similar detail.",
                "rule_based",
            ))

    for eb in ents_b:
        if eb["entity_type"] not in types_to_check:
            continue
        if eb["value"].lower() in all_discrepancy_values:
            continue
        if eb["value"].lower() not in values_a:
            discrepancies.append(_make_discrepancy(
                eb["entity_type"].replace("_", " ").title(),
                w_a_label, w_b_label,
                "(not mentioned)", eb["value"],
                "", eb["sentence"],
                -1, eb["sentence_index"],
                "one_witness_only",
                f"{w_b_label} mentions '{eb['value']}' but {w_a_label} does not reference a similar detail.",
                "rule_based",
            ))

    return discrepancies


def _sentences_are_related(
    sent_a: str,
    sent_b: str,
    idx_a: int,
    idx_b: int,
    semantic_pairs: List[Dict],
    threshold: float = 0.45,
) -> bool:
    """
    Returns True if the two sentences appear in any semantic pair above threshold,
    or if they share enough keywords.
    """
    # Check semantic pairs
    for pair in semantic_pairs:
        if (pair["index_a"] == idx_a and pair["index_b"] == idx_b and
                pair["similarity_score"] >= threshold):
            return True
        if (pair["sentence_a"].strip().lower() == sent_a.strip().lower() and
                pair["sentence_b"].strip().lower() == sent_b.strip().lower() and
                pair["similarity_score"] >= threshold):
            return True

    # Keyword overlap fallback
    words_a = set(re.findall(r"\b\w{4,}\b", sent_a.lower()))
    words_b = set(re.findall(r"\b\w{4,}\b", sent_b.lower()))
    stop = {"that", "this", "with", "from", "they", "them", "their", "were", "have", "been"}
    words_a -= stop
    words_b -= stop
    if not words_a or not words_b:
        return False
    overlap = len(words_a & words_b) / min(len(words_a), len(words_b))
    return overlap >= 0.3


def detect_discrepancies(
    statement_pairs: List[Tuple[Dict, Dict]],  # list of (stmt_a_data, stmt_b_data)
    semantic_pairs_map: Dict[str, List[Dict]],  # key: "a_id-b_id"
) -> List[Dict[str, Any]]:
    """
    Master discrepancy detection function.

    Parameters
    ----------
    statement_pairs : list of (dict_a, dict_b) where each dict has:
        - id, witness_label, sentences, entities
    semantic_pairs_map : dict mapping "aid-bid" to list of semantic pairs

    Returns
    -------
    List of discrepancy dicts.
    """
    all_discrepancies: List[Dict[str, Any]] = []
    seen_pairs: set = set()

    for stmt_a, stmt_b in statement_pairs:
        pair_key = f"{stmt_a['id']}-{stmt_b['id']}"
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        w_a = stmt_a["witness_label"]
        w_b = stmt_b["witness_label"]
        ents_a = stmt_a.get("entities", [])
        ents_b = stmt_b.get("entities", [])
        semantic_pairs = semantic_pairs_map.get(pair_key, [])

        def filter_type(ents, etype):
            return [e for e in ents if e["entity_type"] == etype]

        # Compare by entity type
        time_d = compare_time_entities(
            filter_type(ents_a, "TIME"), filter_type(ents_b, "TIME"),
            w_a, w_b, semantic_pairs
        )
        clothing_d = compare_clothing_entities(
            filter_type(ents_a, "CLOTHING"), filter_type(ents_b, "CLOTHING"),
            w_a, w_b, semantic_pairs
        )
        vehicle_d = compare_vehicle_entities(
            filter_type(ents_a, "VEHICLE"), filter_type(ents_b, "VEHICLE"),
            w_a, w_b, semantic_pairs
        )
        location_d = compare_location_entities(
            filter_type(ents_a, "LOCATION_DETAIL"), filter_type(ents_b, "LOCATION_DETAIL"),
            w_a, w_b, semantic_pairs
        )

        pair_discrepancies = time_d + clothing_d + vehicle_d + location_d

        # Track values already compared to avoid redundant "unique detail" flags
        compared_values = set()
        for d in pair_discrepancies:
            compared_values.add(d["witness_a_text"].lower())
            compared_values.add(d["witness_b_text"].lower())

        unique_d = find_unique_details(ents_a, ents_b, compared_values, w_a, w_b)

        # Enrich with similarity scores where available
        for disc in pair_discrepancies:
            for sp in semantic_pairs:
                if (sp["index_a"] == disc["witness_a_sentence_idx"] and
                        sp["index_b"] == disc["witness_b_sentence_idx"]):
                    disc["similarity_score"] = sp["similarity_score"]
                    disc["detection_method"] = "combined"
                    break

        all_discrepancies.extend(pair_discrepancies)
        all_discrepancies.extend(unique_d)

    # Deduplicate by (category, a_text, b_text, a_label, b_label)
    seen = set()
    unique = []
    for d in all_discrepancies:
        key = (d["category"], d["witness_a_text"], d["witness_b_text"],
               d["witness_a_label"], d["witness_b_label"])
        if key not in seen:
            seen.add(key)
            unique.append(d)

    return unique
