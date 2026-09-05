"""Inventory-aware filtering: the AI must never recommend what the merchant can't sell."""

import inventory


def test_stock_for_defaults_to_ten_when_missing():
    assert inventory.stock_for({}) == 10


def test_stock_for_handles_negative_and_invalid_values():
    assert inventory.stock_for({"stock": -5}) == 0
    assert inventory.stock_for({"stock": "not-a-number"}) == 0


def test_is_available_true_for_positive_stock():
    assert inventory.is_available({"stock": 1}) is True


def test_is_available_false_for_zero_stock():
    assert inventory.is_available({"stock": 0}) is False


def test_filter_available_removes_out_of_stock_items(sample_products):
    result = inventory.filter_available(sample_products)
    ids = [p["id"] for p in result]

    assert "T-EB-2" not in ids  # stock: 0 in fixture
    assert "T-EB-1" in ids
    assert "T-EB-3" in ids


def test_filter_available_handles_empty_and_none():
    assert inventory.filter_available([]) == []
    assert inventory.filter_available(None) == []
