import os


MAX_ORDER_VALUE = int(os.getenv("MAX_ORDER_VALUE", "10000"))
MAX_UPSELL_VALUE = int(os.getenv("MAX_UPSELL_VALUE", "1000"))
MAX_UPSELL_PERCENT = float(os.getenv("MAX_UPSELL_PERCENT", "40"))


def validate_order(total_amount, upsell_amount=0):
    total_amount = float(total_amount)
    upsell_amount = float(upsell_amount)

    if total_amount <= 0:
        return {"allowed": False, "reason": "Invalid order amount."}

    if total_amount > MAX_ORDER_VALUE:
        return {
            "allowed": False,
            "reason": (
                f"Order ₹{total_amount:,.0f} exceeds the maximum "
                f"allowed amount of ₹{MAX_ORDER_VALUE:,.0f}."
            ),
        }

    if upsell_amount < 0:
        return {"allowed": False, "reason": "Invalid upsell amount."}

    if upsell_amount > MAX_UPSELL_VALUE:
        return {
            "allowed": False,
            "reason": (
                f"Upsell ₹{upsell_amount:,.0f} exceeds the maximum "
                f"allowed upsell of ₹{MAX_UPSELL_VALUE:,.0f}."
            ),
        }

    base_amount = total_amount - upsell_amount
    if base_amount <= 0 and upsell_amount > 0:
        return {"allowed": False, "reason": "Upsell cannot be the entire order."}

    if base_amount > 0:
        upsell_percent = (upsell_amount / base_amount) * 100
        if upsell_percent > MAX_UPSELL_PERCENT:
            return {
                "allowed": False,
                "reason": (
                    f"Upsell is {upsell_percent:.1f}% of the base order, "
                    f"above the {MAX_UPSELL_PERCENT:.0f}% policy limit."
                ),
            }

    return {"allowed": True, "reason": "Policy check passed."}
