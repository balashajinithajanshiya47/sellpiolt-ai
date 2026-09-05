# SellPilot AI — Test Suite

Automated tests covering the core logic that sits behind every AI/money
decision in the app: intent extraction, recommendation, upsell relevance,
inventory-awareness, transaction policy, adaptive learning, and payment
robustness (duplicate-order prevention, signature/amount/status checks).

No live Razorpay or Groq credentials are required — external calls are
mocked so the suite runs the same way locally and in CI.

## Run

```bash
pip install -r requirements-dev.txt
pytest -v
```

## Coverage map

| File                     | Covers                                                              |
|---------------------------|----------------------------------------------------------------------|
| `test_intent.py`          | Category + budget + preference extraction (deterministic fallback path) |
| `test_recommendation.py`  | Budget filtering, category filtering, preference sorting, use-case boost |
| `test_upsell.py`          | Compatible-category matching, never suggesting the same product, inventory exclusion |
| `test_inventory.py`       | Stock parsing and out-of-stock filtering                             |
| `test_policy.py`          | ₹10,000 order cap, upsell absolute/percent caps, invalid amounts     |
| `test_learning.py`        | Selection/attach-rate stats, bounded rerank, cold-start stability    |
| `test_payment.py`         | Duplicate-order idempotency, signature rejection, amount/status mismatch rejection |

These are unit/integration tests for CI and code review — you don't need to
show them in the pitch video, but a public repo with a real, passing test
suite is a strong signal that the system is correct-by-design rather than
"got it working once."
