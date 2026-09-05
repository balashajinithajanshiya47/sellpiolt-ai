"""Small inventory adapter used by the demo recommendation layer."""


def stock_for(product):
    try:
        return max(0, int(product.get("stock", 10)))
    except (TypeError, ValueError):
        return 0


def is_available(product):
    return stock_for(product) > 0


def filter_available(products):
    return [product for product in (products or []) if is_available(product)]
