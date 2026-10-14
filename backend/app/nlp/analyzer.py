"""
WitnessIQ Analysis Orchestrator

Coordinates the full analysis pipeline:
  1. Sentence splitting
  2. Entity extraction (spaCy + rule-based)
  3. Semantic similarity across all statement pairs
  4. Discrepancy detection
  5. Result assembly
"""
import logging
import itertools
from typing import List, Dict, Any, Optional

from .entity_extractor import extract_entities
from .semantic_similarity import find_similar_pairs, get_model_status
from .discrepancy_detector import detect_discrepancies

logger = logging.getLogger(__name__)

# Lazy-loaded spaCy model
_nlp = None
_spacy_available = False


def _load_spacy():
    global _nlp, _spacy_available
    if _nlp is not None:
        return _nlp, _spacy_available
    try:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
        _spacy_available = True
        logger.info("spaCy model 'en_core_web_sm' loaded.")
    except Exception as exc:
        logger.warning("Could not load spaCy model: %s. Using rule-based extraction only.", exc)
        _nlp = None
        _spacy_available = False
    return _nlp, _spacy_available


def _get_nlp_status() -> Dict[str, Any]:
    _, available = _load_spacy()
    return {
        "spacy": {
            "available": available,
            "model": "en_core_web_sm" if available else None,
            "fallback": "rule_based_regex" if not available else None,
        }
    }


def analyze_statements(statements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main analysis entry point.

    Parameters
    ----------
    statements : list of dicts with keys:
        - id (int)
        - witness_label (str)
        - content (str)

    Returns
    -------
    dict with keys: summary, discrepancies, extracted_facts, semantic_matches, model_info
    """
    if len(statements) < 2:
        raise ValueError("At least two statements are required for comparison.")

    nlp, _ = _load_spacy()
    model_status = {**_get_nlp_status(), **get_model_status()}
    similarity_threshold = model_status["sentence_transformer"]["threshold"]

    # Step 1: Extract entities and sentences per statement
    processed: List[Dict[str, Any]] = []
    all_extracted_facts = []

    for stmt in statements:
        result = extract_entities(stmt["content"], nlp=nlp)
        processed.append({
            "id": stmt["id"],
            "witness_label": stmt["witness_label"],
            "content": stmt["content"],
            "sentences": result["sentences"],
            "entities": result["entities"],
        })
        # Build flat list of extracted facts for response
        for ent in result["entities"]:
            all_extracted_facts.append({
                "statement_id": stmt["id"],
                "witness_label": stmt["witness_label"],
                "entity_type": ent["entity_type"],
                "value": ent["value"],
                "sentence": ent["sentence"],
                "sentence_index": ent["sentence_index"],
                "source": ent["source"],
            })

    # Step 2: Semantic similarity for all pairs of statements
    all_semantic_matches = []
    semantic_pairs_map: Dict[str, List[Dict]] = {}

    for stmt_a, stmt_b in itertools.combinations(processed, 2):
        pair_key = f"{stmt_a['id']}-{stmt_b['id']}"
        pairs = find_similar_pairs(
            stmt_a["sentences"],
            stmt_b["sentences"],
            threshold=similarity_threshold,
        )
        semantic_pairs_map[pair_key] = pairs

        for p in pairs:
            all_semantic_matches.append({
                "statement_a_id": stmt_a["id"],
                "statement_b_id": stmt_b["id"],
                "witness_a": stmt_a["witness_label"],
                "witness_b": stmt_b["witness_label"],
                "sentence_a": p["sentence_a"],
                "sentence_b": p["sentence_b"],
                "sentence_a_index": p["index_a"],
                "sentence_b_index": p["index_b"],
                "similarity_score": p["similarity_score"],
                "match_method": p["method"],
            })

    # Step 3: Discrepancy detection
    statement_pairs = list(itertools.combinations(processed, 2))
    discrepancies = detect_discrepancies(statement_pairs, semantic_pairs_map)

    # Step 4: Build summary
    inconsistency_types = {"potential_inconsistency", "difference_for_review"}
    unique_detail_count = sum(
        1 for d in discrepancies if d["classification"] == "one_witness_only"
    )
    flagged_count = sum(
        1 for d in discrepancies if d["classification"] in inconsistency_types
    )

    entity_method = (
        "spaCy NER + rule-based entity extraction"
        if model_status["spacy"]["available"]
        else "Rule-based entity extraction"
    )
    similarity_method = (
        "Sentence-Transformer semantic similarity"
        if model_status["sentence_transformer"]["available"]
        else "TF-IDF cosine similarity"
    )

    summary = {
        "statements_analyzed": len(statements),
        "related_pairs_found": len(all_semantic_matches),
        "discrepancies_flagged": flagged_count,
        "unique_details_count": unique_detail_count,
        "analysis_method": (
            f"{entity_method} + {similarity_method} + rule-based comparisons"
        ),
        "model_status": model_status,
    }

    return {
        "summary": summary,
        "discrepancies": discrepancies,
        "extracted_facts": all_extracted_facts,
        "semantic_matches": all_semantic_matches,
        "model_info": model_status,
    }
