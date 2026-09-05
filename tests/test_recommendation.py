"""✓ budget extraction / filtering, ✓ recommendation limits (category + stock-agnostic ranking)."""

import agents.recommendation_agent as rec


def test_filters_out_products_over_budget(monkeypatch, sample_products):
    monkeypatch.setattr(rec, "load_products", lambda: sample_products)

    results = rec.recommend_products(budget=2000, category="earbuds", preference="price")

    assert all(p["price"] <= 2000 for p in results)
    assert "T-EB-3" not in [p["id"] for p in results]  # ₹3299 > budget


def test_filters_by_category(monkeypatch, sample_products):
    monkeypatch.setattr(rec, "load_products", lambda: sample_products)

    results = rec.recommend_products(budget=10000, category="earbuds", preference="price")

    assert all(p["category"] == "earbuds" for p in results)
    assert "T-ACC-1" not in [p["id"] for p in results]


def test_unknown_category_returns_no_results(monkeypatch, sample_products):
    monkeypatch.setattr(rec, "load_products", lambda: sample_products)

    results = rec.recommend_products(budget=10000, category="drone", preference="price")

    assert results == []


def test_preference_battery_sorts_highest_first(monkeypatch, sample_products):
    monkeypatch.setattr(rec, "load_products", lambda: sample_products)

    results = rec.recommend_products(budget=10000, category="earbuds", preference="battery")

    battery_values = [p.get("battery_hours", 0) for p in results]
    assert battery_values == sorted(battery_values, reverse=True)


def test_preference_price_sorts_lowest_first(monkeypatch, sample_products):
    monkeypatch.setattr(rec, "load_products", lambda: sample_products)

    results = rec.recommend_products(budget=10000, category="earbuds", preference="price")

    prices = [p["price"] for p in results]
    assert prices == sorted(prices)


def test_category_and_preference_aliases_are_normalized(monkeypatch, sample_products):
    monkeypatch.setattr(rec, "load_products", lambda: sample_products)

    results = rec.recommend_products(budget=10000, category="earphones", preference="cheapest")

    assert len(results) > 0
    prices = [p["price"] for p in results]
    assert prices == sorted(prices)


def test_use_case_boosts_matching_tag_products(monkeypatch, sample_products):
    monkeypatch.setattr(rec, "load_products", lambda: sample_products)

    results = rec.recommend_products(
        budget=10000, category="earbuds", preference="rating", use_case="noise cancellation"
    )

    # Products tagged with the use-case terms should be ranked ahead of
    # equally-or-lower-rated products without the tag.
    top_ids = [p["id"] for p in results[:2]]
    assert "T-EB-2" not in top_ids  # not tagged "noise cancellation"


def test_invalid_budget_returns_empty_list(monkeypatch, sample_products):
    monkeypatch.setattr(rec, "load_products", lambda: sample_products)

    assert rec.recommend_products(budget="not-a-number", category="earbuds") == []
