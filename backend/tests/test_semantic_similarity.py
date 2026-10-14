from app.nlp.semantic_similarity import _embed_sentences_tfidf, find_similar_pairs


def test_tfidf_fallback_vectors_have_consistent_dimensions():
    vectors = _embed_sentences_tfidf([
        "A person left through the front entrance.",
        "A red car was parked outside.",
    ])

    assert len({len(vector) for vector in vectors}) == 1


def test_tfidf_fallback_finds_related_demo_exit_claims():
    matches = find_similar_pairs(
        ["At approximately 8:15 PM, I saw a man leave through the front entrance."],
        ["At around 8:45 PM, I noticed a man exiting through the front entrance."],
        threshold=0.25,
    )

    assert len(matches) == 1
    assert matches[0]["method"] == "tfidf_cosine"


def test_tfidf_fallback_does_not_match_unrelated_demo_claims():
    matches = find_similar_pairs(
        ["At approximately 8:15 PM, I saw a man leave through the front entrance."],
        ["I was inside a shop and heard shouting at 8:20 PM."],
        threshold=0.25,
    )

    assert matches == []
