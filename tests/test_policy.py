"""✓ policy blocking — the ₹10,000 limit, upsell caps, and invalid amounts."""

from backend.policy import validate_order, MAX_ORDER_VALUE, MAX_UPSELL_VALUE, MAX_UPSELL_PERCENT


def test_order_within_limit_is_allowed():
    result = validate_order(total_amount=2098, upsell_amount=0)
    assert result["allowed"] is True


def test_order_over_max_value_is_blocked():
    result = validate_order(total_amount=MAX_ORDER_VALUE + 1, upsell_amount=0)
    assert result["allowed"] is False
    assert "exceeds" in result["reason"].lower()


def test_order_exactly_at_max_value_is_allowed():
    result = validate_order(total_amount=MAX_ORDER_VALUE, upsell_amount=0)
    assert result["allowed"] is True


def test_zero_or_negative_order_is_blocked():
    assert validate_order(total_amount=0, upsell_amount=0)["allowed"] is False
    assert validate_order(total_amount=-500, upsell_amount=0)["allowed"] is False


def test_negative_upsell_amount_is_blocked():
    result = validate_order(total_amount=2000, upsell_amount=-100)
    assert result["allowed"] is False


def test_upsell_over_absolute_cap_is_blocked():
    result = validate_order(total_amount=5000, upsell_amount=MAX_UPSELL_VALUE + 1)
    assert result["allowed"] is False


def test_upsell_over_percent_cap_is_blocked():
    # base = 100, upsell = 90 -> 90% of base, above MAX_UPSELL_PERCENT (40%)
    result = validate_order(total_amount=190, upsell_amount=90)
    assert result["allowed"] is False
    assert "%" in result["reason"]


def test_upsell_entirely_covering_order_is_blocked():
    result = validate_order(total_amount=500, upsell_amount=500)
    assert result["allowed"] is False
