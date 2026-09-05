"""✓ payment amount verification, ✓ invalid signature rejection,
✓ duplicate order prevention — all against the real FastAPI app, with the
Razorpay SDK calls mocked so no network access or real API keys are needed.
"""

import pytest
from fastapi.testclient import TestClient

import backend.main as main_module


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    """Each backend record is in-memory (see backend/main.py). Reset between
    tests so they don't leak into each other."""
    main_module.order_records.clear()
    main_module.payment_records.clear()
    yield
    main_module.order_records.clear()
    main_module.payment_records.clear()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        main_module, "create_order",
        lambda amount: {"id": "order_TEST123", "amount": int(amount) * 100, "currency": "INR"},
    )
    monkeypatch.setattr(main_module, "get_credentials", lambda: ("rzp_test_fake", "secret"))
    return TestClient(main_module.app)


def test_create_order_within_policy_succeeds(client):
    response = client.post("/create-order", json={
        "amount": 2098, "upsell_amount": 0,
        "client_order_key": "session-abc-12345",
    })
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["order_id"] == "order_TEST123"


def test_create_order_over_policy_limit_is_blocked_not_errored(client):
    response = client.post("/create-order", json={
        "amount": 15000, "upsell_amount": 0,
        "client_order_key": "session-abc-99999",
    })
    body = response.json()
    assert response.status_code == 200  # policy block is a normal response, not a 500
    assert body["success"] is False
    assert body["blocked"] is True


def test_duplicate_order_request_is_reused_not_recreated(client, monkeypatch):
    call_count = {"n": 0}

    def counting_create_order(amount):
        call_count["n"] += 1
        return {"id": f"order_{call_count['n']}", "amount": int(amount) * 100, "currency": "INR"}

    monkeypatch.setattr(main_module, "create_order", counting_create_order)

    same_key = "same-session-key-1234567890"
    first = client.post("/create-order", json={
        "amount": 2000, "upsell_amount": 0, "client_order_key": same_key,
    }).json()
    second = client.post("/create-order", json={
        "amount": 2000, "upsell_amount": 0, "client_order_key": same_key,
    }).json()

    assert call_count["n"] == 1  # Razorpay order only created once
    assert first["order_id"] == second["order_id"]
    assert second["reused"] is True


def test_different_session_keys_create_separate_orders(client, monkeypatch):
    call_count = {"n": 0}

    def counting_create_order(amount):
        call_count["n"] += 1
        return {"id": f"order_{call_count['n']}", "amount": int(amount) * 100, "currency": "INR"}

    monkeypatch.setattr(main_module, "create_order", counting_create_order)

    client.post("/create-order", json={
        "amount": 2000, "upsell_amount": 0, "client_order_key": "session-key-one-111",
    })
    client.post("/create-order", json={
        "amount": 2000, "upsell_amount": 0, "client_order_key": "session-key-two-222",
    })

    assert call_count["n"] == 2


def test_verify_payment_rejects_invalid_signature(client, monkeypatch):
    # Create a real order record first.
    client.post("/create-order", json={
        "amount": 2000, "upsell_amount": 0, "client_order_key": "sig-test-key-001",
    })

    def raise_bad_signature(order_id, payment_id, signature):
        raise ValueError("Payment signature verification failed.")

    monkeypatch.setattr(main_module, "verify_payment_signature", raise_bad_signature)

    response = client.post("/verify-payment", json={
        "razorpay_order_id": "order_TEST123",
        "razorpay_payment_id": "pay_fake",
        "razorpay_signature": "tampered_signature_value",
    })
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is False


def test_verify_payment_rejects_amount_mismatch(client, monkeypatch):
    client.post("/create-order", json={
        "amount": 2000, "upsell_amount": 0, "client_order_key": "amt-test-key-001",
    })

    monkeypatch.setattr(main_module, "verify_payment_signature", lambda *a, **k: True)
    monkeypatch.setattr(
        main_module, "fetch_payment",
        lambda payment_id: {
            "order_id": "order_TEST123",
            "amount": 999900,  # does not match the ₹2000 order (200000 paise)
            "status": "captured",
        },
    )

    response = client.post("/verify-payment", json={
        "razorpay_order_id": "order_TEST123",
        "razorpay_payment_id": "pay_fake",
        "razorpay_signature": "looks_valid_but_amount_is_wrong",
    })
    body = response.json()

    assert body["success"] is False
    assert "amount" in body["message"].lower()


def test_verify_payment_rejects_uncaptured_status(client, monkeypatch):
    client.post("/create-order", json={
        "amount": 2000, "upsell_amount": 0, "client_order_key": "status-test-key-001",
    })

    monkeypatch.setattr(main_module, "verify_payment_signature", lambda *a, **k: True)
    monkeypatch.setattr(
        main_module, "fetch_payment",
        lambda payment_id: {
            "order_id": "order_TEST123", "amount": 200000, "status": "authorized",
        },
    )

    response = client.post("/verify-payment", json={
        "razorpay_order_id": "order_TEST123",
        "razorpay_payment_id": "pay_fake",
        "razorpay_signature": "valid_but_not_captured_yet",
    })

    assert response.json()["success"] is False


def test_verify_payment_for_unknown_order_is_rejected(client):
    response = client.post("/verify-payment", json={
        "razorpay_order_id": "order_NEVER_CREATED",
        "razorpay_payment_id": "pay_fake",
        "razorpay_signature": "whatever_signature_value",
    })

    assert response.json()["success"] is False


def test_verify_payment_success_path_is_idempotent(client, monkeypatch):
    client.post("/create-order", json={
        "amount": 2000, "upsell_amount": 0, "client_order_key": "happy-path-key-001",
    })

    monkeypatch.setattr(main_module, "verify_payment_signature", lambda *a, **k: True)
    monkeypatch.setattr(
        main_module, "fetch_payment",
        lambda payment_id: {
            "order_id": "order_TEST123", "amount": 200000, "status": "captured",
        },
    )

    payload = {
        "razorpay_order_id": "order_TEST123",
        "razorpay_payment_id": "pay_real",
        "razorpay_signature": "valid_signature",
    }
    first = client.post("/verify-payment", json=payload).json()
    second = client.post("/verify-payment", json=payload).json()

    assert first["success"] is True
    assert second["success"] is True
    assert "already verified" in second["message"].lower()
