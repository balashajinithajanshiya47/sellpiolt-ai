"""Adaptive learning: outcomes should nudge future ranking without overriding
cold-start relevance or letting one accidental click dominate."""

from learning import (
    product_learning_stats,
    upsell_learning_stats,
    rerank_recommendations,
    rank_upsell_candidates,
)


def test_product_learning_stats_computes_selection_rate(sample_audit_logs):
    stats = product_learning_stats(sample_audit_logs)

    assert stats["T-EB-1"]["exposures"] == 1
    assert stats["T-EB-1"]["selections"] == 1
    assert stats["T-EB-1"]["selection_rate"] == 1.0
    # Exposed but never selected.
    assert stats["T-EB-3"]["selections"] == 0


def test_upsell_learning_stats_computes_attach_rate(sample_audit_logs):
    stats = upsell_learning_stats(sample_audit_logs)

    assert stats["T-ACC-1"]["offered"] == 1
    assert stats["T-ACC-1"]["accepted"] == 1
    assert stats["T-ACC-1"]["attach_rate"] == 1.0


def test_cold_start_ranking_is_unchanged_with_no_history(sample_products, empty_logs):
    ranked = rerank_recommendations(sample_products, empty_logs)
    original_ids = [p["id"] for p in sample_products]
    ranked_ids = [p["id"] for p in ranked]

    assert ranked_ids == original_ids


def test_low_confidence_signal_cannot_override_strong_original_ranking(sample_products):
    # Only ONE exposure/selection recorded for the item ranked last -> low
    # confidence. It must not leap to first place over items with no signal
    # at all but a better original position.
    logs = [
        ("t", "Recommendation Exposure", "Products: T-EB-1, T-EB-2, T-EB-3", "SUCCESS"),
        ("t", "Product Selected", "Product ID: T-EB-3", "SUCCESS"),
    ]
    ranked = rerank_recommendations(sample_products, logs)

    assert ranked[0]["id"] == "T-EB-1"  # original top choice still wins


def test_rerank_handles_empty_recommendations(empty_logs):
    assert rerank_recommendations([], empty_logs) == []


def test_rank_upsell_candidates_prefers_higher_attach_rate():
    candidates = [
        {"id": "A", "name": "Low attach"},
        {"id": "B", "name": "High attach"},
    ]
    logs = [
        ("t", "Upsell Offered", "Product ID: B", "SUCCESS")
        for _ in range(10)
    ] + [
        ("t", "Upsell Accepted", "Product ID: B", "SUCCESS")
        for _ in range(9)
    ]

    ranked = rank_upsell_candidates(candidates, logs)

    assert ranked[0]["id"] == "B"
