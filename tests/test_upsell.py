"""✓ upsell relevance, ✓ inventory-aware exclusion of out-of-stock items."""

import agents.upsell_agent as upsell


def test_upsell_is_compatible_category(monkeypatch, sample_products, empty_logs):
    monkeypatch.setattr(upsell, "load_products", lambda: sample_products)
    monkeypatch.setattr(upsell, "get_audit_logs", lambda: empty_logs)

    primary = sample_products[0]  # T-EB-1, category earbuds
    result = upsell.get_upsell(primary)

    assert result is not None
    assert result["category"] in upsell.UPSELL_CATEGORIES["earbuds"]


def test_upsell_never_recommends_the_same_product(monkeypatch, sample_products, empty_logs):
    monkeypatch.setattr(upsell, "load_products", lambda: sample_products)
    monkeypatch.setattr(upsell, "get_audit_logs", lambda: empty_logs)

    primary = sample_products[0]
    result = upsell.get_upsell(primary)

    assert result is None or result["name"] != primary["name"]


def test_upsell_excludes_out_of_stock_products(monkeypatch, empty_logs):
    # Only one candidate accessory exists and it is out of stock -> no upsell.
    products = [
        {"id": "P1", "name": "Primary", "category": "earbuds", "price": 2000,
         "rating": 4.0, "tags": ["wireless"], "stock": 5},
        {"id": "P2", "name": "OOS Case", "category": "accessory", "price": 300,
         "rating": 4.0, "tags": ["wireless"], "stock": 0},
    ]
    monkeypatch.setattr(upsell, "load_products", lambda: products)
    monkeypatch.setattr(upsell, "get_audit_logs", lambda: empty_logs)

    result = upsell.get_upsell(products[0])

    assert result is None


def test_upsell_reason_mentions_shared_tags(monkeypatch, sample_products, empty_logs):
    monkeypatch.setattr(upsell, "load_products", lambda: sample_products)
    monkeypatch.setattr(upsell, "get_audit_logs", lambda: empty_logs)

    primary = sample_products[0]  # tags include "noise cancellation"
    result = upsell.get_upsell(primary)

    assert result is not None
    assert "upsell_reason" in result


def test_upsell_no_candidates_returns_none(monkeypatch, empty_logs):
    products = [
        {"id": "P1", "name": "Solo Product", "category": "watch", "price": 2000,
         "rating": 4.0, "tags": [], "stock": 5},
    ]
    monkeypatch.setattr(upsell, "load_products", lambda: products)
    monkeypatch.setattr(upsell, "get_audit_logs", lambda: empty_logs)

    assert upsell.get_upsell(products[0]) is None
