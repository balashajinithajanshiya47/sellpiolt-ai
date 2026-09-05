import hashlib
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.policy import (
    MAX_ORDER_VALUE,
    MAX_UPSELL_PERCENT,
    MAX_UPSELL_VALUE,
    validate_order,
)
from backend.razorpay_service import (
    create_order,
    fetch_payment,
    get_credentials,
    verify_payment_signature,
)


# In-memory records are sufficient for a single Render service instance used by
# the demo. The client_order_key makes repeated clicks idempotent within that
# instance and prevents accidental duplicate order creation.
order_records = {}
payment_records = {}

app = FastAPI(title="SellPilot AI Payment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrderRequest(BaseModel):
    amount: float = Field(gt=0)
    upsell_amount: float = Field(default=0, ge=0)
    client_order_key: str = Field(min_length=8, max_length=512)
    item_ids: List[str] = Field(default_factory=list, max_length=20)


class PaymentVerificationRequest(BaseModel):
    razorpay_order_id: str = Field(min_length=5, max_length=100)
    razorpay_payment_id: str = Field(min_length=5, max_length=100)
    razorpay_signature: str = Field(min_length=10, max_length=500)


@app.get("/")
def home():
    return {"status": "online", "service": "SellPilot AI Payment API"}


@app.get("/health")
def health():
    try:
        key_id, _ = get_credentials()
        razorpay_configured = True
        razorpay_mode = "test" if key_id.startswith("rzp_test_") else "live/other"
    except Exception:
        razorpay_configured = False
        razorpay_mode = "not configured"

    return {
        "status": "ok",
        "razorpay_configured": razorpay_configured,
        "razorpay_mode": razorpay_mode,
        "policy": {
            "max_order_value_inr": MAX_ORDER_VALUE,
            "max_upsell_value_inr": MAX_UPSELL_VALUE,
            "max_upsell_percent": MAX_UPSELL_PERCENT,
        },
    }


@app.post("/create-order")
def create_payment_order(request: OrderRequest):
    total_amount = int(round(request.amount))
    upsell_amount = int(round(request.upsell_amount))

    policy = validate_order(total_amount, upsell_amount)
    if not policy["allowed"]:
        return {"success": False, "blocked": True, "message": policy["reason"]}

    # Hash the client key so no raw customer/session string becomes a cache key.
    idempotency_key = hashlib.sha256(request.client_order_key.encode("utf-8")).hexdigest()
    existing = order_records.get(idempotency_key)
    if existing:
        return {
            "success": True,
            "reused": True,
            "order_id": existing["order_id"],
            "amount": existing["amount"],
            "currency": existing["currency"],
            "key_id": existing["key_id"],
        }

    try:
        order = create_order(total_amount)
        key_id, _ = get_credentials()

        expected_amount = int(order["amount"])
        if expected_amount != total_amount * 100:
            return {
                "success": False,
                "blocked": False,
                "message": "Payment server returned an unexpected order amount.",
            }

        order_records[idempotency_key] = {
            "order_id": order["id"],
            "amount": expected_amount,
            "currency": order["currency"],
            "key_id": key_id,
            "upsell_amount": upsell_amount,
            "item_ids": list(request.item_ids),
        }

        return {
            "success": True,
            "reused": False,
            "order_id": order["id"],
            "amount": expected_amount,
            "currency": order["currency"],
            "key_id": key_id,
        }

    except Exception as exc:
        message = str(exc).strip() or "Razorpay order creation failed."
        # Return the real provider/configuration message so Render failures are
        # diagnosable from Streamlit instead of being hidden behind HTTP 500.
        return {
            "success": False,
            "blocked": False,
            "message": f"Razorpay order creation failed: {message}",
        }


@app.post("/verify-payment")
def verify_payment_order(request: PaymentVerificationRequest):
    # Refuse verification for an order we did not create through this service.
    order_record = next(
        (record for record in order_records.values() if record["order_id"] == request.razorpay_order_id),
        None,
    )
    if not order_record:
        payment_records[request.razorpay_order_id] = {"status": "failed"}
        return {"success": False, "message": "Unknown or expired Razorpay order."}

    if payment_records.get(request.razorpay_order_id, {}).get("status") == "verified":
        return {
            "success": True,
            "message": "Payment was already verified.",
            "payment_id": payment_records[request.razorpay_order_id].get("payment_id"),
        }

    try:
        # 1) Cryptographic signature verification.
        verify_payment_signature(
            request.razorpay_order_id,
            request.razorpay_payment_id,
            request.razorpay_signature,
        )

        # 2) Trusted backend lookup. Do not trust amount/order metadata supplied
        # by the browser; compare the actual Razorpay payment to our order.
        payment = fetch_payment(request.razorpay_payment_id)
        payment_order_id = str(payment.get("order_id") or "")
        payment_amount = int(payment.get("amount") or 0)
        payment_status = str(payment.get("status") or "").lower()

        if payment_order_id != request.razorpay_order_id:
            raise ValueError("Payment does not belong to the expected order.")

        if payment_amount != int(order_record["amount"]):
            raise ValueError("Payment amount does not match the confirmed order amount.")

        if payment_status != "captured":
            raise ValueError(f"Payment is not captured (status: {payment_status or 'unknown'}).")

        payment_records[request.razorpay_order_id] = {
            "status": "verified",
            "payment_id": request.razorpay_payment_id,
            "amount": payment_amount,
        }
        return {
            "success": True,
            "message": "Payment verified successfully",
            "payment_id": request.razorpay_payment_id,
        }

    except Exception as exc:
        payment_records[request.razorpay_order_id] = {"status": "failed"}
        return {"success": False, "message": f"Payment verification failed: {str(exc)}"}


@app.get("/payment-status/{order_id}")
def payment_status(order_id: str):
    record = payment_records.get(order_id)
    if not record:
        return {"status": "pending"}
    return record
