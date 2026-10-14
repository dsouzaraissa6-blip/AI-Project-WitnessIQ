"""
WitnessIQ — Tests for Discrepancy Detection Logic

These tests verify core comparison rules without requiring ML models.
Tests cover: time comparison, color/clothing, vehicles, unique details,
paraphrasing, identical info, and ambiguous/unrelated claims.
"""
import pytest
from app.nlp.discrepancy_detector import (
    _parse_minutes,
    _time_difference_minutes,
    _colors_are_similar,
    compare_time_entities,
    compare_clothing_entities,
    compare_vehicle_entities,
    detect_discrepancies,
)
from app.nlp.entity_extractor import extract_entities, split_into_sentences


# ─── Time parsing ─────────────────────────────────────────────────────────────

class TestTimeParsing:
    def test_parse_12h_pm(self):
        assert _parse_minutes("8:15 PM") == 20 * 60 + 15

    def test_parse_12h_am(self):
        assert _parse_minutes("8:15 AM") == 8 * 60 + 15

    def test_parse_24h(self):
        assert _parse_minutes("20:45") == 20 * 60 + 45

    def test_parse_no_minutes(self):
        assert _parse_minutes("9 PM") == 21 * 60

    def test_parse_midnight(self):
        assert _parse_minutes("12:00 AM") == 0

    def test_parse_noon(self):
        assert _parse_minutes("12:00 PM") == 12 * 60

    def test_time_difference_30min(self):
        diff = _time_difference_minutes("8:15 PM", "8:45 PM")
        assert diff == 30

    def test_time_difference_zero(self):
        diff = _time_difference_minutes("8:15 PM", "8:15 PM")
        assert diff == 0

    def test_time_difference_5min(self):
        diff = _time_difference_minutes("8:15 PM", "8:20 PM")
        assert diff == 5

    def test_time_difference_invalid(self):
        diff = _time_difference_minutes("unknown time", "8:15 PM")
        assert diff is None


# ─── Color similarity ─────────────────────────────────────────────────────────

class TestColorSimilarity:
    def test_identical_colors(self):
        assert _colors_are_similar("black", "black") is True

    def test_grey_gray_similar(self):
        assert _colors_are_similar("grey", "gray") is True

    def test_black_blue_not_similar(self):
        assert _colors_are_similar("black", "blue") is False

    def test_red_blue_not_similar(self):
        assert _colors_are_similar("red", "blue") is False

    def test_case_insensitive(self):
        assert _colors_are_similar("Black", "black") is True


# ─── Entity extraction ────────────────────────────────────────────────────────

class TestEntityExtraction:
    def test_extract_time(self):
        text = "At approximately 8:15 PM, I saw a man leave."
        result = extract_entities(text)
        times = [e for e in result["entities"] if e["entity_type"] == "TIME"]
        assert len(times) >= 1
        assert "8:15 PM" in times[0]["value"] or "8:15" in times[0]["value"]

    def test_extract_clothing(self):
        text = "He was wearing a black jacket and dark trousers."
        result = extract_entities(text)
        clothing = [e for e in result["entities"] if e["entity_type"] == "CLOTHING"]
        assert len(clothing) >= 1
        values = [c["value"].lower() for c in clothing]
        assert any("black jacket" in v for v in values)

    def test_extract_vehicle(self):
        text = "A red car was parked near the entrance."
        result = extract_entities(text)
        vehicles = [e for e in result["entities"] if e["entity_type"] == "VEHICLE"]
        assert len(vehicles) >= 1
        assert any("red" in v["value"].lower() for v in vehicles)

    def test_extract_location_detail(self):
        text = "He exited through the front entrance."
        result = extract_entities(text)
        locs = [e for e in result["entities"] if e["entity_type"] == "LOCATION_DETAIL"]
        assert len(locs) >= 1

    def test_sentence_splitting(self):
        text = "I saw a man. He was running. The car was red."
        sentences = split_into_sentences(text)
        assert len(sentences) == 3

    def test_no_false_clothing_positives(self):
        """Ensure non-clothing sentences don't trigger clothing extraction."""
        text = "The sky was blue today."
        result = extract_entities(text)
        clothing = [e for e in result["entities"] if e["entity_type"] == "CLOTHING"]
        assert len(clothing) == 0


# ─── Discrepancy detection — demo case ───────────────────────────────────────

STMT_A = {
    "id": 1,
    "witness_label": "Witness A",
    "content": (
        "I was standing across the road outside the jewellery store. "
        "At approximately 8:15 PM, I saw a man leave through the front entrance. "
        "He was wearing a black jacket and dark trousers. "
        "A red car was parked near the entrance. "
        "I could not see the driver's face."
    ),
}

STMT_B = {
    "id": 2,
    "witness_label": "Witness B",
    "content": (
        "I was standing near the bus stop across from the jewellery store. "
        "At around 8:45 PM, I noticed a man exiting through the front entrance. "
        "He appeared to be wearing a blue jacket and dark trousers. "
        "A red car was parked near the store entrance. "
        "I did not see the driver's face."
    ),
}

STMT_C = {
    "id": 3,
    "witness_label": "Witness C",
    "content": (
        "I was inside a nearby shop when I heard shouting at approximately 8:20 PM. "
        "I then noticed a person running toward the rear lane. "
        "I could not identify the person or determine what had happened inside the jewellery store."
    ),
}


def _extract_for_detection(stmt: dict) -> dict:
    result = extract_entities(stmt["content"])
    return {
        "id": stmt["id"],
        "witness_label": stmt["witness_label"],
        "content": stmt["content"],
        "sentences": result["sentences"],
        "entities": result["entities"],
    }


class TestDiscrepancyDetection:
    def test_time_discrepancy_a_vs_b(self):
        """8:15 PM vs 8:45 PM should be flagged."""
        pa = _extract_for_detection(STMT_A)
        pb = _extract_for_detection(STMT_B)
        discrepancies = detect_discrepancies([(pa, pb)], {})
        time_discs = [d for d in discrepancies if d["category"] == "Time"]
        assert len(time_discs) >= 1
        classifications = {d["classification"] for d in time_discs}
        assert "potential_inconsistency" in classifications or "difference_for_review" in classifications

    def test_jacket_color_discrepancy(self):
        """Black jacket vs blue jacket should be flagged."""
        pa = _extract_for_detection(STMT_A)
        pb = _extract_for_detection(STMT_B)
        discrepancies = detect_discrepancies([(pa, pb)], {})
        clothing_discs = [d for d in discrepancies if d["category"] == "Clothing / Color"]
        assert len(clothing_discs) >= 1
        # At least one should be an inconsistency/difference
        classifications = {d["classification"] for d in clothing_discs}
        assert "potential_inconsistency" in classifications or "difference_for_review" in classifications

    def test_semantic_match_is_reported_as_combined_detection(self):
        """A semantic match combined with a rule-based difference reports both methods."""
        stmt_a = _extract_for_detection({
            "id": 70,
            "witness_label": "Witness A",
            "content": "He wore a black jacket.",
        })
        stmt_b = _extract_for_detection({
            "id": 71,
            "witness_label": "Witness B",
            "content": "He wore a blue jacket.",
        })
        semantic_pairs = [{
            "index_a": 0,
            "index_b": 0,
            "sentence_a": stmt_a["sentences"][0],
            "sentence_b": stmt_b["sentences"][0],
            "similarity_score": 0.82,
            "method": "tfidf_cosine",
        }]

        discrepancies = detect_discrepancies(
            [(stmt_a, stmt_b)],
            {"70-71": semantic_pairs},
        )

        clothing = next(d for d in discrepancies if d["category"] == "Clothing / Color")
        assert clothing["detection_method"] == "combined"
        assert clothing["similarity_score"] == 0.82

    def test_red_car_agreement(self):
        """Red car in both statements should produce 'similar' classification."""
        pa = _extract_for_detection(STMT_A)
        pb = _extract_for_detection(STMT_B)
        discrepancies = detect_discrepancies([(pa, pb)], {})
        vehicle_discs = [d for d in discrepancies if d["category"] == "Vehicle"]
        similar = [d for d in vehicle_discs if d["classification"] == "similar"]
        # Both mention red car — should detect agreement
        assert len(similar) >= 1

    def test_demo_shared_trousers_and_driver_visibility(self):
        """The demo retains the matching clothing and non-identification passages."""
        pa = _extract_for_detection(STMT_A)
        pb = _extract_for_detection(STMT_B)
        discrepancies = detect_discrepancies([(pa, pb)], {})

        trousers = [
            d for d in discrepancies
            if d["category"] == "Clothing / Color"
            and d["witness_a_text"].lower() == "dark trousers"
        ]
        assert any(d["classification"] == "similar" for d in trousers)
        assert any(
            e["entity_type"] == "NEGATION" and "driver's face" in e["sentence"].lower()
            for e in pa["entities"]
        )
        assert any(
            e["entity_type"] == "NEGATION" and "driver's face" in e["sentence"].lower()
            for e in pb["entities"]
        )

    def test_demo_witness_c_rear_lane_is_kept_as_unique_detail(self):
        """Witness C's event detail remains separate from the exit observations."""
        pa = _extract_for_detection(STMT_A)
        pc = _extract_for_detection(STMT_C)
        discrepancies = detect_discrepancies([(pa, pc)], {})

        assert any(
            e["entity_type"] == "TIME" and "8:20 PM" in e["value"]
            for e in pc["entities"]
        )
        assert any(
            d["classification"] == "one_witness_only"
            and "rear lane" in d["witness_b_text"].lower()
            for d in discrepancies
        )

    def test_identical_info_not_flagged_as_inconsistency(self):
        """Identical statements should not generate inconsistency flags."""
        stmt = {
            "id": 10,
            "witness_label": "Witness X",
            "content": "At 9:00 PM, I saw a man leave through the front entrance.",
        }
        stmt2 = {
            "id": 11,
            "witness_label": "Witness Y",
            "content": "At 9:00 PM, I saw a man leave through the front entrance.",
        }
        pa = _extract_for_detection(stmt)
        pb = _extract_for_detection(stmt2)
        discrepancies = detect_discrepancies([(pa, pb)], {})
        inconsistencies = [
            d for d in discrepancies
            if d["classification"] == "potential_inconsistency"
        ]
        assert len(inconsistencies) == 0

    def test_different_colors_flagged(self):
        """Black jacket vs red jacket should always be flagged."""
        sa = {
            "id": 20,
            "witness_label": "W1",
            "content": "He was wearing a black jacket.",
        }
        sb = {
            "id": 21,
            "witness_label": "W2",
            "content": "He was wearing a red jacket.",
        }
        pa = _extract_for_detection(sa)
        pb = _extract_for_detection(sb)
        discrepancies = detect_discrepancies([(pa, pb)], {})
        assert len(discrepancies) >= 1
        classifications = {d["classification"] for d in discrepancies}
        assert "potential_inconsistency" in classifications or "difference_for_review" in classifications

    def test_missing_info_one_witness_only(self):
        """Detail mentioned only by one witness should produce 'one_witness_only'."""
        sa = {
            "id": 30,
            "witness_label": "W1",
            "content": "At 8:15 PM, I saw a man leave. A red car was parked outside.",
        }
        sb = {
            "id": 31,
            "witness_label": "W2",
            "content": "I saw someone leaving the building.",
        }
        pa = _extract_for_detection(sa)
        pb = _extract_for_detection(sb)
        discrepancies = detect_discrepancies([(pa, pb)], {})
        one_only = [d for d in discrepancies if d["classification"] == "one_witness_only"]
        assert len(one_only) >= 1

    def test_approximate_times_not_exact_contradiction(self):
        """
        Times within 10 minutes should produce 'difference_for_review' not 'potential_inconsistency'.
        This reflects that approximation is common and should not automatically be treated as contradictory.
        """
        sa = {"id": 40, "witness_label": "W1", "content": "It happened at approximately 8:15 PM."}
        sb = {"id": 41, "witness_label": "W2", "content": "It happened at around 8:20 PM."}
        pa = _extract_for_detection(sa)
        pb = _extract_for_detection(sb)
        discrepancies = detect_discrepancies([(pa, pb)], {})
        time_discs = [d for d in discrepancies if d["category"] == "Time"]
        # 5-minute difference should be 'difference_for_review' not 'potential_inconsistency'
        for d in time_discs:
            assert d["classification"] != "potential_inconsistency", (
                f"5-minute difference should not be potential_inconsistency, got: {d['classification']}"
            )

    def test_unrelated_statements_no_false_positives(self):
        """Completely unrelated statements should not produce inconsistency flags."""
        sa = {
            "id": 50,
            "witness_label": "W1",
            "content": "I was shopping at the supermarket.",
        }
        sb = {
            "id": 51,
            "witness_label": "W2",
            "content": "The library was closed on Monday.",
        }
        pa = _extract_for_detection(sa)
        pb = _extract_for_detection(sb)
        discrepancies = detect_discrepancies([(pa, pb)], {})
        inconsistencies = [
            d for d in discrepancies
            if d["classification"] in ("potential_inconsistency", "difference_for_review")
        ]
        assert len(inconsistencies) == 0

    def test_paraphrased_same_time(self):
        """'8:15 PM' and '8:15 in the evening' may not both be parsed, but should not conflict."""
        sa = {"id": 60, "witness_label": "W1", "content": "The event happened at 8:15 PM."}
        sb = {"id": 61, "witness_label": "W2", "content": "The event occurred at 8:15 PM."}
        pa = _extract_for_detection(sa)
        pb = _extract_for_detection(sb)
        discrepancies = detect_discrepancies([(pa, pb)], {})
        time_discs = [d for d in discrepancies if d["category"] == "Time"]
        # Same time, should be 'similar' if both parsed
        for d in time_discs:
            assert d["classification"] == "similar" or d["classification"] == "difference_for_review"
