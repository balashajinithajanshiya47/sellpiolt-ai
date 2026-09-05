import json
from pathlib import Path


# --------------------------------------------------
# PRODUCT DATA
# --------------------------------------------------

def load_products():
    path = Path(__file__).parent.parent / "data" / "products.json"

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------
# CATEGORY NORMALIZATION
# --------------------------------------------------

def normalize_category(category):
    """
    Convert common customer/category names into the
    category names used by products.json.
    """

    if not category:
        return "general"

    category = str(category).strip().lower()

    aliases = {
        # Earbuds
        "earbud": "earbuds",
        "earbuds": "earbuds",
        "earphone": "earbuds",
        "earphones": "earbuds",
        "headphone": "earbuds",
        "headphones": "earbuds",

        # Laptop
        "laptop": "laptop",
        "laptops": "laptop",
        "notebook": "laptop",
        "notebooks": "laptop",
        "macbook": "laptop",

        # Phone
        "phone": "phone",
        "phones": "phone",
        "mobile": "phone",
        "mobiles": "phone",
        "smartphone": "phone",
        "smartphones": "phone",

        # Watch
        "watch": "watch",
        "watches": "watch",
        "smartwatch": "watch",
        "smartwatches": "watch",

        # Shoes
        "shoe": "shoes",
        "shoes": "shoes",
        "sneaker": "shoes",
        "sneakers": "shoes",

        # Bags
        "bag": "bag",
        "bags": "bag",
        "backpack": "bag",
        "backpacks": "bag",

        # Keyboard
        "keyboard": "keyboard",
        "keyboards": "keyboard",

        # Mouse
        "mouse": "mouse",
        "mice": "mouse",
    }

    return aliases.get(category, category)


# --------------------------------------------------
# PREFERENCE NORMALIZATION
# --------------------------------------------------

def normalize_preference(preference):
    """
    Normalize customer preference values.
    """

    if not preference:
        return "price"

    preference = str(preference).strip().lower()

    aliases = {
        "battery": "battery",
        "battery life": "battery",
        "long battery": "battery",

        "rating": "rating",
        "ratings": "rating",
        "best rated": "rating",

        "price": "price",
        "cheap": "price",
        "cheapest": "price",
        "budget": "price",
        "lowest price": "price",
    }

    return aliases.get(preference, "price")


# --------------------------------------------------
# PREFERENCE SCORING
# --------------------------------------------------

def sort_products(products, preference):
    """
    Sort products according to customer preference.

    Supported preferences:
    - battery: highest battery first
    - rating: highest rating first
    - price: lowest price first
    """

    preference = normalize_preference(preference)

    if preference == "battery":

        products.sort(
            key=lambda x: (
                x.get("battery_hours") is not None,
                x.get("battery_hours", 0)
            ),
            reverse=True
        )

    elif preference == "rating":

        products.sort(
            key=lambda x: x.get("rating", 0),
            reverse=True
        )

    else:

        products.sort(
            key=lambda x: x.get("price", float("inf"))
        )

    return products


# --------------------------------------------------
# USE-CASE SCORING
# --------------------------------------------------

def score_use_case(product, use_case):
    """
    Give products a small relevance boost when their tags
    match the customer's use case.

    This does NOT replace the main preference sorting.
    It is only used as a relevance signal.
    """

    if not use_case:
        return 0

    use_case = str(use_case).strip().lower()

    tags = product.get("tags", [])

    if not isinstance(tags, list):
        return 0

    tag_text = " ".join(
        str(tag).lower()
        for tag in tags
    )

    words = [
        word
        for word in use_case.split()
        if len(word) >= 3
    ]

    return sum(
        1
        for word in words
        if word in tag_text
    )


# --------------------------------------------------
# PRODUCT RECOMMENDATION
# --------------------------------------------------

def recommend_products(
    budget,
    category="general",
    preference="battery",
    use_case=""
):
    """
    Recommend products from products.json.

    Recommendation considers:

    1. Product category
    2. Maximum customer budget
    3. Customer preference
    4. Optional use-case relevance
    """

    products = load_products()

    requested_category = normalize_category(category)
    preference = normalize_preference(preference)

    try:
        budget = float(budget)
    except (TypeError, ValueError):
        return []

    matching = []

    for product in products:

        # ------------------------------------------
        # CATEGORY
        # ------------------------------------------

        product_category = normalize_category(
            product.get("category", "")
        )

        if product_category != requested_category:
            continue

        # ------------------------------------------
        # PRICE
        # ------------------------------------------

        try:
            price = float(
                product.get("price", 0)
            )
        except (TypeError, ValueError):
            continue

        if price > budget:
            continue

        # ------------------------------------------
        # STORE USE-CASE SCORE
        # ------------------------------------------

        product["_use_case_score"] = score_use_case(
            product,
            use_case
        )

        matching.append(product)

    if not matching:
        return []

    # ----------------------------------------------
    # SORT
    # ----------------------------------------------

    if use_case:

        if preference == "battery":

            matching.sort(
                key=lambda x: (
                    x.get("_use_case_score", 0),
                    x.get("battery_hours") is not None,
                    x.get("battery_hours", 0)
                ),
                reverse=True
            )

        elif preference == "rating":

            matching.sort(
                key=lambda x: (
                    x.get("_use_case_score", 0),
                    x.get("rating", 0)
                ),
                reverse=True
            )

        else:

            matching.sort(
                key=lambda x: (
                    -x.get("_use_case_score", 0),
                    x.get("price", float("inf"))
                )
            )

    else:

        matching = sort_products(
            matching,
            preference
        )

    # ----------------------------------------------
    # REMOVE INTERNAL SCORE
    # ----------------------------------------------

    for product in matching:
        product.pop("_use_case_score", None)

    return matching