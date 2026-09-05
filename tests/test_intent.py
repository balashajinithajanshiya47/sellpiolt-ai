"""✓ category extraction, ✓ budget extraction (fallback path).

These tests exercise analyze_customer_intent() WITHOUT a GROQ_API_KEY, which
forces the deterministic fallback branch. This keeps the suite runnable in
CI/offline while still covering the extraction contract the LLM branch must
also satisfy (same return shape: category, budget, preference, use_case,
summary).
"""

import os

import pytest

os.environ.pop("GROQ_API_KEY", None)

from agents.groq_intent_agent import analyze_customer_intent, is_llm_configured


def test_is_llm_configured_false_without_key(monkeypatch):
    monkeypatch.setattr("agents.groq_intent_agent._get_api_key", lambda: "")
    assert is_llm_configured() is False


def test_is_llm_configured_true_with_key(monkeypatch):
    monkeypatch.setattr("agents.groq_intent_agent._get_api_key", lambda: "fake-key-123")
    assert is_llm_configured() is True


@pytest.fixture(autouse=True)
def no_streamlit_secrets(monkeypatch):
    # Ensure the fallback path is used even if a local secrets.toml exists.
    monkeypatch.setattr(
        "agents.groq_intent_agent._get_api_key", lambda: ""
    )


def test_extracts_category_from_message():
    result = analyze_customer_intent("I need earbuds under 3000 with good battery")
    assert result["category"] == "earbuds"


def test_extracts_budget_from_message():
    result = analyze_customer_intent("I need a laptop under 45000")
    assert result["budget"] == 45000.0


def test_extracts_battery_preference():
    result = analyze_customer_intent("earbuds with long battery life")
    assert result["preference"] == "battery"


def test_extracts_price_preference_for_cheap_requests():
    result = analyze_customer_intent("show me the cheapest earbuds")
    assert result["preference"] == "price"


def test_returns_expected_shape():
    result = analyze_customer_intent("phone under 20000")
    for key in ("category", "budget", "preference", "use_case", "summary"):
        assert key in result


def test_unrecognized_product_falls_back_to_general():
    result = analyze_customer_intent("I need a spaceship")
    assert result["category"] == "general"


def test_uses_case_word_detected():
    result = analyze_customer_intent("earbuds for gym use under 3000")
    assert "gym" in result["use_case"]
