# 🛒 SellPilot AI
### AI Revenue Agent for Modern Merchants

SellPilot AI demonstrates a complete customer-to-revenue workflow:

**Customer Intent → Recommendation → Smart Upsell → Policy Gate → Customer Confirmation → Razorpay Test Payment → Backend Verification → Audit Trail → Merchant Intelligence**

## Included in this final package

- Top-centered customer request bar
- **🔎 Analyze** button
- Conversational intent understanding with Groq
- Local fallback intent extraction when Groq is not configured
- Category, budget, preference and use-case extraction
- Product recommendations with availability and learning signals
- Product selection
- Inventory-aware complementary upsell
- Customer accept/decline control for upsell
- ₹10,000 transaction policy gate
- Human/customer confirmation before payment
- Razorpay Test Mode checkout
- Backend signature verification + payment lookup
- Invalid/tampered signature demonstration
- Payment status checking
- SQLite audit trail with session IDs
- Audit export
- Merchant Command Center
- Adaptive sales signals
- Clearly labelled buildathon growth simulation
- Light, modern frontend styling instead of a black/dark-blue interface
- Render deployment configuration

## Project structure

```text
sellpilot-ai/
├── app.py
├── requirements.txt
├── data/
│   └── products.json
├── agents/
│   ├── recommendation_agent.py
│   ├── groq_intent_agent.py
│   └── upsell_agent.py
├── backend/
│   ├── main.py
│   ├── policy.py
│   └── razorpay_service.py
├── database/
│   └── audit.py
├── learning.py
├── inventory.py
├── ui/
│   └── theme.py            # extracted stylesheet (was inline in app.py)
├── analytics/
│   └── payment_history.py  # payment history + failure-reason breakdown
├── tests/
│   ├── test_intent.py
│   ├── test_recommendation.py
│   ├── test_upsell.py
│   ├── test_inventory.py
│   ├── test_policy.py
│   ├── test_learning.py
│   └── test_payment.py
├── requirements-dev.txt
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── render.yaml
└── Procfile
```

## Run the Streamlit app locally

```bash
python -m venv venv
```

Windows:
```bash
venv\Scripts\activate
```

Install:
```bash
pip install -r requirements.txt
```

Run:
```bash
streamlit run app.py
```

The app starts even without Groq credentials by using a safe local intent fallback. For the full AI intent experience, configure `GROQ_API_KEY`.

## Run the FastAPI payment backend locally

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Then set:

```text
BACKEND_URL=http://localhost:8000
```

before starting Streamlit.

## Run the test suite

```bash
pip install -r requirements-dev.txt
pytest -v
```

49 tests cover intent extraction, recommendation filtering, upsell
relevance, inventory-aware exclusion, policy blocking (the ₹10,000 order
cap and upsell caps), adaptive learning/reranking, and payment robustness
(duplicate-order idempotency, invalid-signature rejection, amount/status
mismatch rejection). No live Razorpay/Groq credentials are required — see
`tests/README.md` for the full coverage map.

## Environment variables

### Streamlit
```text
GROQ_API_KEY=your_key
BACKEND_URL=https://sellpilot-ai-30l8.onrender.com
```

### Render backend
```text
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
MAX_ORDER_VALUE=10000
MAX_UPSELL_VALUE=1000
MAX_UPSELL_PERCENT=40
```

Never commit real keys. Use Streamlit Secrets and Render Environment Variables.

## Judge/demo flow

1. Enter a request at the **top-centered Customer Request** box.
2. Click **🔎 Analyze**.
3. Review the detected category, budget, preference and use case.
4. Select a recommended product.
5. Review the contextual upsell and accept or decline it.
6. Review the cart and policy gate.
7. Click **🔒 Confirm Purchase**.
8. Create the Razorpay test order.
9. Complete Razorpay Test Mode checkout.
10. Click **🔄 Check Payment Status**.
11. Verify the success/failure result in the audit trail.
12. Use **🔐 Simulate Invalid Payment Signature** to demonstrate rejection.
13. Show the Merchant Command Center and the clearly labelled growth simulation.

## Deployment

### Streamlit Cloud
- Connect the repository.
- Main file: `app.py`.
- Add `GROQ_API_KEY` and `BACKEND_URL` in Streamlit Secrets.
- Do not upload `.streamlit/secrets.toml`.

### Render
- Connect the repository.
- Build: `pip install -r requirements.txt`
- Start:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```
- Add Razorpay test credentials in Render Environment Variables.

Current intended backend default:
`https://sellpilot-ai-30l8.onrender.com`

Current live app:
`https://sellpilot-ai.streamlit.app/`

## Safety design

The frontend does not mark a payment successful by itself. The backend:

- checks the policy before order creation,
- verifies the Razorpay signature,
- fetches the payment from Razorpay,
- checks the expected order ID,
- checks the actual paid amount,
- requires captured status,
- records failures,
- and exposes payment status.

The AI recommends; the customer confirms; the backend verifies.
