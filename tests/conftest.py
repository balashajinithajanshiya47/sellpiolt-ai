"""Shared fixtures for the SellPilot AI test suite.

Run with:  pytest -v
No network calls or Razorpay/Groq credentials are required. Anything that
would normally hit an external service (Razorpay, Groq) is mocked so the
suite runs the same way locally and in CI.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def sample_products():
    """Small, deterministic product catalog independent of data/products.json."""
    return [
        {
            "id": "T-EB-1",
            "name": "Test Earbuds Pro",
            "category": "earbuds",
            "price": 2499,
            "battery_hours": 40,
            "rating": 4.5,
            "tags": ["wireless", "noise cancellation", "long battery"],
            "stock": 5,
        },
        {
            "id": "T-EB-2",
            "name": "Test Earbuds Lite",
            "category": "earbuds",
            "price": 1799,
            "battery_hours": 20,
            "rating": 4.0,
            "tags": ["wireless", "lightweight"],
            "stock": 0,  # deliberately out of stock
        },
        {
            "id": "T-EB-3",
            "name": "Test Earbuds Elite",
            "category": "earbuds",
            "price": 3299,
            "battery_hours": 50,
            "rating": 4.7,
            "tags": ["wireless", "premium", "noise cancellation"],
            "stock": 3,
        },
        {
            "id": "T-ACC-1",
            "name": "Test Charging Case",
            "category": "accessory",
            "price": 499,
            "rating": 4.1,
            "tags": ["wireless", "noise cancellation"],
            "stock": 10,
        },
    ]


@pytest.fixture
def empty_logs():
    return []


@pytest.fixture
def sample_audit_logs():
    """Rows shaped like database.audit.get_audit_logs() output:
    (timestamp, action, details, status)
    """
    return [
        ("2026-09-01T10:00:00", "Recommendation Exposure",
         "[Session: S1] Products: T-EB-1, T-EB-3", "SUCCESS"),
        ("2026-09-01T10:00:05", "Product Selected",
         "[Session: S1] Product ID: T-EB-1", "SUCCESS"),
        ("2026-09-01T10:00:10", "Upsell Offered",
         "[Session: S1] Product ID: T-ACC-1", "SUCCESS"),
        ("2026-09-01T10:00:15", "Upsell Accepted",
         "[Session: S1] Product ID: T-ACC-1", "SUCCESS"),
    ]
