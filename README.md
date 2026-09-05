# 🛒 SellPilot AI

### AI Revenue Agent for Modern Merchants

> **Customer Intent → Recommendation → Smart Upsell → Policy Gate → Confirmation → Payment → Verification → Audit → Merchant Intelligence**

SellPilot AI is an **AI-powered revenue agent for modern merchants** that transforms a natural-language customer request into a complete, controlled and auditable sales journey.

Unlike a traditional chatbot that only answers customer questions, SellPilot AI connects **AI-powered intent understanding, personalized recommendations, inventory-aware upselling, transaction policies, customer confirmation, Razorpay Test Mode payments, backend verification, audit logging, adaptive learning, and merchant intelligence** into one workflow.

---

## 🌐 Live Project

### 🚀 Live Application

**https://sellpilot-ai47.streamlit.app**

### 💻 GitHub Repository

**https://github.com/balashajinithajanshiya47/sellpiolt-ai**

### ⚙️ Backend

**https://sellpilot-ai-30l8.onrender.com**

---

# 💡 The Core Idea

Modern e-commerce systems are good at displaying products, but a successful sale involves much more than product search.

A customer may say:

> *"I need wireless earbuds under ₹2,500 with good battery life for college."*

SellPilot AI converts this unstructured request into a structured sales workflow:

```text
Customer Request
       ↓
AI Intent Understanding
       ↓
Requirement Extraction
       ↓
Personalized Recommendations
       ↓
Product Selection
       ↓
Inventory-Aware Upsell
       ↓
Customer Accept / Decline
       ↓
Policy Gate
       ↓
Customer Confirmation
       ↓
Razorpay Test Payment
       ↓
Backend Verification
       ↓
Audit Trail
       ↓
Merchant Intelligence
```

The system is designed around one principle:

> **The AI recommends. The customer confirms. The backend verifies.**

---

# 🎯 Problem Statement

Traditional online shopping often separates several important processes:

* Customer support
* Product discovery
* Recommendations
* Upselling
* Payment
* Fraud/risk checks
* Transaction verification
* Merchant analytics

This creates a fragmented customer journey.

A recommendation engine may suggest a product, but it does not necessarily know whether:

* The product is available
* An upsell is relevant
* The cart exceeds business limits
* The customer actually confirmed the purchase
* The payment is genuine
* The payment amount is correct
* The payment belongs to the expected order
* The transaction should be recorded for future intelligence

### SellPilot AI connects these stages into one intelligent revenue workflow.

---

# 🧠 AI-Powered Intent Understanding

SellPilot AI uses **Groq-powered conversational AI** to understand natural-language customer requests.

It extracts important shopping signals such as:

* 🏷️ Product category
* 💰 Budget
* ⭐ Preference
* 🎯 Use case
* 📝 Customer requirements

### Example

**Customer:**

```text
I need wireless earbuds under ₹2,000 with good battery
life for travelling.
```

**Extracted intent:**

```text
Category  → Earbuds
Budget    → ₹2,000
Preference → Good battery life
Use case  → Travelling
```

This structured intent is then passed to the recommendation workflow.

---

# 🔄 Local Fallback Intelligence

SellPilot AI does not completely depend on an external AI credential.

If `GROQ_API_KEY` is not configured, the application can use a **local fallback intent extraction mechanism**.

This provides:

* Better demo reliability
* Graceful degradation
* Easier local development
* Reduced dependency on external credentials

The application can therefore start even without Groq credentials.

---

# 🛍️ Personalized Product Recommendations

The recommendation engine matches products against the customer's requirements.

It considers signals such as:

* Category
* Budget
* Preferences
* Use case
* Product availability
* Learning signals

Instead of blindly displaying products, SellPilot AI attempts to identify products that provide the best fit for the current customer.

### Recommendation Flow

```text
Customer Intent
      ↓
Category Filtering
      ↓
Budget Filtering
      ↓
Preference Matching
      ↓
Availability Check
      ↓
Learning / Ranking Signals
      ↓
Recommended Products
```

---

# 📦 Inventory-Aware Recommendations

Product availability is part of the recommendation workflow.

The system can avoid recommending products that are unavailable and can use inventory information while generating complementary upsell opportunities.

This creates a more realistic commerce workflow than a static product catalogue.

---

# 📈 Smart Upselling

SellPilot AI does not simply recommend the most expensive product.

It uses an **inventory-aware complementary upsell mechanism** to identify relevant additional products.

For example:

```text
Customer
   ↓
Selects Wireless Earbuds
   ↓
System identifies complementary product
   ↓
Customer can Accept / Decline
```

### Customer Control

The customer explicitly decides whether to accept the upsell.

```text
        Recommended Upsell
              ↓
       ┌──────┴──────┐
       ↓             ↓
    Accept         Decline
       ↓             ↓
   Add to Cart    Continue
```

This keeps the upsell customer-controlled rather than forcing additional products into the purchase.

---

# 🛡️ Policy Gate

SellPilot AI includes a business policy layer before payment.

### Transaction Limit

```text
MAX_ORDER_VALUE = ₹10,000
```

### Upsell Controls

```text
MAX_UPSELL_VALUE   = ₹1,000
MAX_UPSELL_PERCENT = 40%
```

The policy layer can prevent transactions that violate configured business rules.

This creates a separation between:

```text
AI Recommendation
        ↓
Business Policy
        ↓
Customer Confirmation
        ↓
Payment
```

The AI therefore does not have unrestricted authority to create a transaction.

---

# 👤 Customer Confirmation

Before payment, SellPilot AI requires customer confirmation.

The workflow is:

```text
Recommendation
      ↓
Cart Review
      ↓
Policy Check
      ↓
Customer Confirmation
      ↓
Payment
```

This provides an important human-in-the-loop control.

---

# 💳 Razorpay Test Mode Integration

SellPilot AI integrates with **Razorpay Test Mode** to demonstrate a realistic payment workflow without using real money.

The system supports:

* Test order creation
* Razorpay checkout
* Payment status checking
* Signature verification
* Payment lookup
* Invalid signature demonstration
* Amount validation
* Order validation

### Payment Flow

```text
Customer Confirmation
        ↓
Create Razorpay Test Order
        ↓
Razorpay Checkout
        ↓
Payment
        ↓
Backend Verification
        ↓
Success / Failure
        ↓
Audit Trail
```

---

# 🔐 Backend Payment Verification

The frontend does **not** decide whether a payment is successful.

The backend performs the verification.

It checks:

### 1. Signature

The Razorpay payment signature is verified.

### 2. Order ID

The payment is checked against the expected order.

### 3. Amount

The actual paid amount is compared against the expected amount.

### 4. Payment Status

The system requires the appropriate captured payment state.

### 5. Payment Lookup

The backend can retrieve payment information for additional validation.

---

# 🧪 Invalid / Tampered Payment Demonstration

SellPilot AI includes a demonstration mechanism for an **invalid payment signature**.

This allows judges to see that the backend does not blindly trust a payment response from the frontend.

Example:

```text
Valid Payment
     ↓
Signature Verification
     ↓
Verification Passed
```

versus:

```text
Tampered / Invalid Signature
     ↓
Signature Verification
     ↓
❌ Verification Rejected
```

This demonstrates why payment verification belongs on the backend.

---

# 🗄️ SQLite Audit Trail

Every important sales and payment interaction can be recorded using SQLite.

The audit system uses **session IDs** to associate actions with the customer journey.

The audit trail can capture events such as:

* Customer interaction
* Intent extraction
* Product selection
* Upsell decision
* Policy result
* Purchase confirmation
* Payment events
* Verification results
* Failure events

This creates an auditable record of the sales process.

---

# 📊 Merchant Command Center

SellPilot AI includes a **Merchant Command Center** designed to give merchants visibility into the sales workflow.

It provides insights into areas such as:

* Sales activity
* Customer interactions
* Adaptive sales signals
* Payment activity
* Failure patterns
* Growth opportunities

The objective is to move from:

```text
"What did the customer buy?"
```

to:

```text
"Why did the customer buy,
what influenced the decision,
and how can the merchant improve conversion?"
```

---

# 🧠 Adaptive Sales Intelligence

SellPilot AI incorporates learning signals into the recommendation workflow.

Customer interactions can contribute to adaptive signals that influence future ranking and sales intelligence.

The idea is:

```text
Customer Interaction
        ↓
Observed Signal
        ↓
Learning Layer
        ↓
Updated Ranking
        ↓
Improved Recommendations
```

This creates a foundation for continuously improving recommendation quality.

---

# 📈 Buildathon Growth Simulation

The Merchant Command Center also includes a **clearly labelled growth simulation**.

This is intentionally separated from real transaction data.

It demonstrates how merchant-facing intelligence could be used to estimate potential business growth without presenting simulated numbers as actual revenue.

---

# 🖥️ User Experience

The application uses a modern, lightweight interface designed around the sales journey.

### Customer Interface

Key UI elements include:

* Top-centered customer request bar
* 🔎 Analyze button
* Conversational interaction
* Intent summary
* Product recommendations
* Product selection
* Upsell controls
* Cart review
* Policy status
* Purchase confirmation
* Payment status
* Audit information

The interface uses a **light, modern visual style** rather than a traditional black/dark-blue dashboard.

---

# ✨ Complete Feature Set

| Feature                    | Description                                    |
| -------------------------- | ---------------------------------------------- |
| 🔎 AI Intent Analysis      | Understands natural-language customer requests |
| 🧠 Groq Integration        | Conversational intent understanding            |
| 🔄 Local Fallback          | Works without Groq credentials                 |
| 🏷️ Intent Extraction      | Category, budget, preference and use case      |
| 🛍️ Recommendations        | Personalized product matching                  |
| 📦 Inventory Awareness     | Avoids unavailable product paths               |
| 📈 Smart Upsell            | Contextual complementary products              |
| 👤 Customer Control        | Accept / decline upsell                        |
| 🛡️ Policy Gate            | Enforces transaction and upsell limits         |
| ✅ Customer Confirmation    | Human confirmation before payment              |
| 💳 Razorpay Test Mode      | Realistic test payment workflow                |
| 🔐 Signature Verification  | Protects payment verification                  |
| 🔎 Payment Lookup          | Backend payment validation                     |
| 🧪 Invalid Signature Demo  | Demonstrates tamper rejection                  |
| 💰 Amount Validation       | Detects amount mismatches                      |
| 📋 Audit Trail             | Records sales and payment events               |
| 🆔 Session IDs             | Tracks customer journeys                       |
| 📊 Merchant Command Center | Merchant-facing intelligence                   |
| 🧠 Adaptive Learning       | Uses sales signals for ranking                 |
| 📈 Growth Simulation       | Buildathon-labelled merchant simulation        |
| 🧪 Automated Tests         | 49 tests across core functionality             |
| ☁️ Cloud Deployment        | Streamlit + Render deployment                  |

---

# 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │      CUSTOMER       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   STREAMLIT UI      │
                         │ Customer Interface  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │       AI INTENT LAYER         │
                    │                               │
                    │ Groq Intent Agent             │
                    │ Local Fallback                │
                    │ Category / Budget / Preference│
                    │ Use Case Extraction           │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────┐
                    │     RECOMMENDATION ENGINE     │
                    │                               │
                    │ Product Matching              │
                    │ Availability                  │
                    │ Learning Signals              │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────┐
                    │       UPSELL ENGINE           │
                    │                               │
                    │ Complementary Products        │
                    │ Inventory Awareness            │
                    │ Customer Accept / Decline     │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────┐
                    │        POLICY GATE             │
                    │                               │
                    │ Order Limit                   │
                    │ Upsell Limit                  │
                    │ Business Rules                │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────┐
                    │   CUSTOMER CONFIRMATION       │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────┐
                    │       RAZORPAY TEST MODE      │
                    │                               │
                    │ Order → Checkout → Payment    │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────┐
                    │    BACKEND VERIFICATION       │
                    │                               │
                    │ Signature                     │
                    │ Order ID                      │
                    │ Amount                        │
                    │ Payment Status                │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────┐
                    │       SQLITE AUDIT TRAIL      │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────┐
                    │    MERCHANT INTELLIGENCE      │
                    │                               │
                    │ Analytics + Learning Signals  │
                    │ Sales Insights + Simulation   │
                    └───────────────────────────────┘
```

---

# 📁 Project Structure

```text
sellpilot-ai/
│
├── app.py
├── requirements.txt
│
├── data/
│   └── products.json
│
├── agents/
│   ├── recommendation_agent.py
│   ├── groq_intent_agent.py
│   └── upsell_agent.py
│
├── backend/
│   ├── main.py
│   ├── policy.py
│   └── razorpay_service.py
│
├── database/
│   └── audit.py
│
├── learning.py
├── inventory.py
│
├── ui/
│   └── theme.py
│
├── analytics/
│   └── payment_history.py
│
├── tests/
│   ├── test_intent.py
│   ├── test_recommendation.py
│   ├── test_upsell.py
│   ├── test_inventory.py
│   ├── test_policy.py
│   ├── test_learning.py
│   └── test_payment.py
│
├── requirements-dev.txt
│
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
│
├── render.yaml
└── Procfile
```

---

# 🧩 Core Modules

### `app.py`

Main Streamlit application and customer-facing sales workflow.

### `agents/groq_intent_agent.py`

Handles conversational customer intent understanding using Groq when configured.

### `agents/recommendation_agent.py`

Handles product recommendation and ranking.

### `agents/upsell_agent.py`

Generates contextual complementary upsell opportunities.

### `inventory.py`

Provides inventory-aware product handling.

### `backend/main.py`

FastAPI backend responsible for payment-related API operations.

### `backend/policy.py`

Implements transaction and upsell policy rules.

### `backend/razorpay_service.py`

Handles Razorpay Test Mode order and payment operations.

### `database/audit.py`

Maintains the SQLite audit trail.

### `learning.py`

Handles adaptive sales and recommendation signals.

### `analytics/payment_history.py`

Provides payment history and failure-reason analysis.

### `ui/theme.py`

Contains the application's extracted UI styling.

---

# 🧪 Testing

SellPilot AI includes a dedicated automated test suite.

```bash
pip install -r requirements-dev.txt
pytest -v
```

### 49 tests cover:

* Intent extraction
* Recommendation filtering
* Upsell relevance
* Inventory-aware exclusion
* Policy blocking
* ₹10,000 order cap
* Upsell caps
* Adaptive learning
* Recommendation reranking
* Duplicate-order idempotency
* Invalid-signature rejection
* Amount mismatch rejection
* Payment status validation

The tests do **not require live Razorpay or Groq credentials**.

---

# 💻 Run Locally

## 1. Clone the Repository

```bash
git clone https://github.com/balashajinithajanshiya47/sellpiolt-ai.git
cd sellpiolt-ai
```

## 2. Create Virtual Environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Run Streamlit

```bash
streamlit run app.py
```

---

# ⚙️ Run the FastAPI Backend

In a separate terminal:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

For local development:

```text
BACKEND_URL=http://localhost:8000
```

Then start the Streamlit application.

---

# 🔑 Environment Variables

## Streamlit

```text
GROQ_API_KEY=your_key
BACKEND_URL=https://sellpilot-ai-30l8.onrender.com
```

## Render Backend

```text
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
MAX_ORDER_VALUE=10000
MAX_UPSELL_VALUE=1000
MAX_UPSELL_PERCENT=40
```

### 🔐 Security

**Never commit real API keys or secrets to GitHub.**

Use:

* Streamlit Secrets for Streamlit
* Render Environment Variables for the backend

The repository includes:

```text
.streamlit/secrets.toml.example
```

as a configuration reference.

---

# ☁️ Deployment

## Streamlit Community Cloud

1. Connect the GitHub repository.
2. Select `app.py` as the main file.
3. Configure:

   * `GROQ_API_KEY`
   * `BACKEND_URL`
4. Deploy.

Do not upload the real:

```text
.streamlit/secrets.toml
```

---

## Render

The FastAPI backend can be deployed using Render.

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Configure Razorpay Test Mode credentials through Render Environment Variables.

### Current Backend

```text
https://sellpilot-ai-30l8.onrender.com
```

---

# 🎬 Judge / Demo Flow

The complete buildathon demonstration can be performed in the following sequence:

### 1️⃣ Customer Request

Enter a request into the top-centered **Customer Request** box.

### 2️⃣ Analyze

Click:

```text
🔎 Analyze
```

### 3️⃣ Review Intent

Show the extracted:

* Category
* Budget
* Preference
* Use case

### 4️⃣ Product Recommendation

Review the products matched to the customer's requirements.

### 5️⃣ Select Product

Choose a recommended product.

### 6️⃣ Smart Upsell

Review the complementary recommendation.

Choose:

```text
Accept
```

or:

```text
Decline
```

### 7️⃣ Policy Gate

Show the transaction and upsell policy validation.

### 8️⃣ Customer Confirmation

Click:

```text
🔒 Confirm Purchase
```

### 9️⃣ Razorpay Test Checkout

Create the Razorpay Test Mode order and complete the test checkout.

### 🔟 Verify Payment

Click:

```text
🔄 Check Payment Status
```

Show the backend verification result.

### 1️⃣1️⃣ Security Demonstration

Use:

```text
🔐 Simulate Invalid Payment Signature
```

to demonstrate that an invalid signature is rejected.

### 1️⃣2️⃣ Audit Trail

Show the recorded transaction/session events.

### 1️⃣3️⃣ Merchant Command Center

Finish by demonstrating:

* Sales signals
* Payment insights
* Adaptive intelligence
* Clearly labelled growth simulation

---

# 🛡️ Safety & Trust Architecture

A central design decision in SellPilot AI is that **AI output is not treated as proof of payment**.

The frontend cannot simply declare:

```text
Payment Successful
```

Instead:

```text
AI Recommendation
       ↓
Customer Confirmation
       ↓
Backend Order Creation
       ↓
Razorpay Payment
       ↓
Signature Verification
       ↓
Payment Lookup
       ↓
Order ID Validation
       ↓
Amount Validation
       ↓
Captured Status Validation
       ↓
Audit Trail
```

This architecture reduces the risk of accepting an invalid or manipulated payment response.

---

# 🔒 Defense-in-Depth

SellPilot AI applies multiple controls:

```text
Layer 1 → AI recommendation
Layer 2 → Inventory validation
Layer 3 → Policy gate
Layer 4 → Customer confirmation
Layer 5 → Payment signature verification
Layer 6 → Order validation
Layer 7 → Amount validation
Layer 8 → Payment status validation
Layer 9 → Audit logging
```

This makes the system more than a recommendation chatbot.

It is a **controlled AI commerce workflow**.

---

# 🚀 Future Enhancements

SellPilot AI can be expanded into a full AI commerce platform.

Potential future capabilities include:

* Real-time inventory APIs
* Live product marketplace integrations
* Customer purchase history
* Customer lifetime-value prediction
* Dynamic pricing intelligence
* Competitor price comparison
* Multi-agent sales architecture
* Voice shopping assistant
* WhatsApp commerce integration
* Automated customer follow-ups
* Advanced fraud detection
* Merchant revenue forecasting
* Multi-language commerce
* Personalized marketing campaigns
* Autonomous sales analytics
* Human sales-agent handoff

---

# 🏆 What Makes SellPilot AI Stand Out?

Many AI commerce projects stop at:

```text
Customer → Chatbot → Recommendation
```

SellPilot AI goes further:

```text
Customer
   ↓
Understand Intent
   ↓
Personalize
   ↓
Recommend
   ↓
Upsell
   ↓
Apply Policy
   ↓
Get Confirmation
   ↓
Process Payment
   ↓
Verify Payment
   ↓
Record Audit
   ↓
Learn
   ↓
Provide Merchant Intelligence
```

This demonstrates the transition from a **simple AI chatbot** to an **AI-powered revenue agent**.

---

# 🎯 Project Vision

The vision behind SellPilot AI is to give merchants an intelligent digital sales assistant that can participate in the complete customer journey.

The system should help merchants:

* Understand customers
* Recommend better products
* Increase relevant sales
* Protect transactions
* Maintain an audit trail
* Learn from sales signals
* Make better business decisions

### Our vision:

> **Build an AI revenue agent that doesn't just sell products — it understands customers, protects transactions, learns from interactions, and helps merchants grow.**

---

# 📌 One-Line Summary

> **SellPilot AI is an autonomous AI revenue agent that converts customer intent into personalized, policy-controlled, verified and auditable commerce transactions.**

---

# 👥 Built For

### 🏆 Buildathon / Hackathon Project

SellPilot AI demonstrates how **Generative AI + recommendation systems + business rules + payment verification + analytics** can be combined into a practical AI commerce solution.

---

# ⭐ Support the Project

If you find SellPilot AI interesting, consider giving the repository a ⭐ on GitHub.

### SellPilot AI

**Understand → Recommend → Upsell → Protect → Convert → Verify → Learn**
