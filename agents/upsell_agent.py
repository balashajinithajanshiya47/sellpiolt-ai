import json
from pathlib import Path

from database.audit import get_audit_logs
from inventory import is_available
from learning import upsell_learning_stats


def load_products():
    path = Path(__file__).parent.parent / "data" / "products.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


UPSELL_CATEGORIES = {
    "earbuds": ["accessory"],
    "laptop": ["mouse", "keyboard", "accessory"],
    "phone": ["accessory"],
    "watch": ["accessory"],
    "shoes": ["accessory"],
    "bag": ["accessory"],
    "keyboard": ["mouse", "accessory"],
    "mouse": ["keyboard", "accessory"],
}


def _reason(primary, addon):
    primary_tags = {str(t).lower() for t in primary.get("tags", [])}
    addon_tags = {str(t).lower() for t in addon.get("tags", [])}
    overlap = primary_tags & addon_tags
    if overlap:
        return "Matched to your selected product through compatible features: " + ", ".join(sorted(overlap)[:3])
    return "Selected as a compatible add-on for your chosen product category."


def get_upsell(product):
    """Return the best compatible, in-stock add-on with a learning signal."""
    products = load_products()
    category = str(product.get("category", "")).lower()
    product_name = product.get("name")
    allowed_categories = UPSELL_CATEGORIES.get(category, ["accessory"])

    candidates = []
    product_tags = {str(t).lower() for t in product.get("tags", [])}

    for item in products:
        if item.get("name") == product_name:
            continue
        if item.get("category") not in allowed_categories:
            continue
        if not is_available(item):
            continue

        item_tags = {str(t).lower() for t in item.get("tags", [])}
        tag_match = len(product_tags & item_tags)
        rating = float(item.get("rating", 0) or 0)
        price = float(item.get("price", 0) or 0)

        # Relevance first, then rating, then affordability.
        item = dict(item)
        item["compatibility_score"] = tag_match
        item["upsell_reason"] = _reason(product, item)
        item["_base_score"] = (tag_match * 10.0) + rating + max(0.0, 5.0 - price / 1000.0)
        candidates.append(item)

    if not candidates:
        return None

    # Learning bonus is deliberately bounded so historical behavior can
    # improve the choice without overpowering product relevance.
    learning = upsell_learning_stats(get_audit_logs())

    def final_score(item):
        signal = learning.get(str(item.get("id")), {})
        attach = float(signal.get("attach_rate", 0.0))
        offered = int(signal.get("offered", 0))
        confidence = min(offered / 10.0, 1.0)
        return float(item.get("_base_score", 0.0)) + (attach * 3.0 * confidence)

    candidates.sort(key=final_score, reverse=True)

    result = dict(candidates[0])
    result.pop("_base_score", None)
    return result
