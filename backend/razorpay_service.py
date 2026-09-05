import os
import uuid

import razorpay


def get_credentials():
    key_id = (os.getenv("RAZORPAY_KEY_ID") or "").strip()
    key_secret = (os.getenv("RAZORPAY_KEY_SECRET") or "").strip()

    if not key_id or not key_secret:
        raise RuntimeError(
            "Razorpay credentials are not configured. "
            "Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in Render Environment Variables."
        )

    return key_id, key_secret


def get_client():
    key_id, key_secret = get_credentials()
    return razorpay.Client(auth=(key_id, key_secret))


def create_order(amount):
    """Create a Razorpay order. amount is INR rupees; SDK receives paise."""
    amount_rupees = int(round(float(amount)))
    amount_paise = amount_rupees * 100

    if amount_paise < 100:
        raise ValueError("Razorpay order amount must be at least ₹1.")

    order_data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": "sellpilot_" + uuid.uuid4().hex[:12],
        "notes": {"source": "SellPilot AI"},
    }

    return get_client().order.create(data=order_data)


def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    get_client().utility.verify_payment_signature(
        {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }
    )
    return True


def fetch_payment(razorpay_payment_id):
    return get_client().payment.fetch(razorpay_payment_id)
