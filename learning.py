"""Lightweight, audit-driven learning signals for SellPilot AI.

No model training is required: the system uses observed recommendation and
upsell outcomes to improve future ranking while keeping the original
recommendation logic intact.
"""

import re
from collections import defaultdict


_PRODUCT_ID_RE = re.compile(r"(?:Product ID|product_id|ID):\s*([A-Za-z0-9_-]+)")
_PRODUCT_IDS_RE = re.compile(r"Products:\s*([^|]+)")


def _id_from_details(details):
    match = _PRODUCT_ID_RE.search(str(details))
    return match.group(1).strip() if match else None


def _exposed_ids(details):
    match = _PRODUCT_IDS_RE.search(str(details))
    if not match:
        return []
    return [item.strip() for item in match.group(1).split(",") if item.strip()]


def product_learning_stats(logs):
    """Return exposure/selection/selection-rate signals by product ID."""
    exposures = defaultdict(int)
    selections = defaultdict(int)

    for row in logs or []:
        if len(row) < 4:
            continue
        _, action, details, _ = row
        action = str(action)
        details = str(details)

        if action == "Recommendation Exposure":
            for product_id in _exposed_ids(details):
                exposures[product_id] += 1

        elif action == "Product Selected":
            product_id = _id_from_details(details)
            if product_id:
                selections[product_id] += 1

    stats = {}
    for product_id in set(exposures) | set(selections):
        exposure = exposures[product_id]
        selected = selections[product_id]
        stats[product_id] = {
            "exposures": exposure,
            "selections": selected,
            "selection_rate": (selected / exposure) if exposure else 0.0,
        }
    return stats


def upsell_learning_stats(logs):
    """Return offered/accepted/attach-rate signals by upsell product ID."""
    offered = defaultdict(int)
    accepted = defaultdict(int)

    for row in logs or []:
        if len(row) < 4:
            continue
        _, action, details, _ = row
        action = str(action)
        details = str(details)
        product_id = _id_from_details(details)
        if not product_id:
            continue
        if action == "Upsell Offered":
            offered[product_id] += 1
        elif action == "Upsell Accepted":
            accepted[product_id] += 1

    stats = {}
    for product_id in set(offered) | set(accepted):
        o = offered[product_id]
        a = accepted[product_id]
        stats[product_id] = {
            "offered": o,
            "accepted": a,
            "attach_rate": (a / o) if o else 0.0,
        }
    return stats


def rerank_recommendations(recommendations, logs):
    """Blend original ranking with a small historical selection signal.

    Cold-start behavior remains unchanged. Historical data only gets a
    bounded bonus, so a high-quality new product can still rank first.
    """
    if not recommendations:
        return []

    stats = product_learning_stats(logs)
    ranked = []

    for original_index, product in enumerate(recommendations):
        product_id = str(product.get("id", ""))
        signal = stats.get(product_id, {})
        rate = float(signal.get("selection_rate", 0.0))
        exposure = int(signal.get("exposures", 0))

        # Confidence grows slowly and caps at 1.0. This prevents one
        # accidental click from overpowering the recommendation agent.
        confidence = min(exposure / 10.0, 1.0)
        learning_bonus = rate * 0.20 * confidence
        rank_score = -original_index + learning_bonus

        enriched = dict(product)
        enriched["learning_selection_rate"] = rate
        enriched["learning_exposures"] = exposure
        enriched["learning_bonus"] = learning_bonus
        ranked.append((rank_score, original_index, enriched))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in ranked]


def rank_upsell_candidates(candidates, logs):
    """Rank compatible upsells using historical attach rate when available.

    agents/upsell_agent.py currently inlines an equivalent scoring step
    (it needs to blend attach-rate with tag-compatibility and price in a
    single pass), so this standalone helper is kept for direct unit
    testing and for any future caller that only needs the learning
    signal in isolation.
    """
    stats = upsell_learning_stats(logs)
    ranked = []
    for index, product in enumerate(candidates):
        s = stats.get(str(product.get("id", "")), {})
        attach = float(s.get("attach_rate", 0.0))
        offered = int(s.get("offered", 0))
        confidence = min(offered / 10.0, 1.0)
        bonus = attach * 0.5 * confidence
        ranked.append((bonus, index, product))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in ranked]
