import os
import re
import uuid
from datetime import datetime

import requests
import streamlit as st
import streamlit.components.v1 as components

from agents.recommendation_agent import recommend_products
from agents.upsell_agent import get_upsell
from agents.groq_intent_agent import analyze_customer_intent, is_llm_configured

import ui.theme
import analytics.payment_history

from inventory import filter_available, stock_for
from learning import rerank_recommendations, product_learning_stats, upsell_learning_stats

from database.audit import (
    init_db,
    log_event,
    get_audit_logs,
    get_audit_logs_json,
)


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SellPilot AI",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

BACKEND_URL = os.getenv("BACKEND_URL", "https://sellpilot-ai-30l8.onrender.com").rstrip("/")
MAX_ORDER_VALUE = 10000


# ============================================================
# DATABASE
# ============================================================

init_db()


# ============================================================
# CUSTOM CSS
# NOTE: This file intentionally uses native Streamlit widgets
# for the main UI. HTML is NOT used for the hero/pipeline,
# preventing raw <div> markup from appearing on screen.
# ============================================================

ui.theme.inject_theme()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "recommendations": [],
    "selected_product": None,
    "upsell_product": None,
    "cart": [],
    "confirmed": False,
    "razorpay_order_id": None,
    "payment_verified": False,
    "payment_id": None,
    "active_category": None,
    "active_budget": None,
    "active_preference": None,
    "active_use_case": "",
    "last_summary": "",
    "chat_history": [],
    "upsell_logged": False,
    "policy_logged": False,
    "order_logged": False,
    "confirmation_logged": False,
    "payment_logged": False,
    "completion_logged": False,
    "payment_initiated_logged": False,
    "last_error": None,
    "clarification_question": None,
    "recommendation_exposed": False,
    "razorpay_checkout_key": None,
    "razorpay_checkout_amount": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

if "session_id" not in st.session_state:
    st.session_state.session_id = (
        "SP-"
        + datetime.now().strftime("%Y%m%d-%H%M%S-")
        + uuid.uuid4().hex[:4].upper()
    )


# ============================================================
# HELPERS
# ============================================================

def audit(action, details, status="SUCCESS"):
    log_event(
        action,
        f"[Session: {st.session_state.session_id}] {details}",
        status,
    )


def reset_transaction_state():
    st.session_state.cart = []
    st.session_state.confirmed = False
    st.session_state.razorpay_order_id = None
    st.session_state.payment_verified = False
    st.session_state.payment_id = None

    st.session_state.upsell_logged = False
    st.session_state.policy_logged = False
    st.session_state.order_logged = False
    st.session_state.confirmation_logged = False
    st.session_state.payment_logged = False
    st.session_state.payment_initiated_logged = False
    st.session_state.completion_logged = False
    st.session_state.last_error = None
    st.session_state.razorpay_checkout_key = None
    st.session_state.razorpay_checkout_amount = None


def new_customer():
    audit(
        "New Customer",
        "Started a new customer session.",
        "INFO",
    )

    st.session_state.session_id = (
        "SP-"
        + datetime.now().strftime("%Y%m%d-%H%M%S-")
        + uuid.uuid4().hex[:4].upper()
    )

    st.session_state.recommendations = []
    st.session_state.selected_product = None
    st.session_state.upsell_product = None
    st.session_state.active_category = None
    st.session_state.active_budget = None
    st.session_state.active_preference = None
    st.session_state.active_use_case = ""
    st.session_state.last_summary = ""
    st.session_state.chat_history = []
    st.session_state.clarification_question = None
    st.session_state.recommendation_exposed = False

    reset_transaction_state()


def detect_category(message):
    text = message.lower()

    if any(
        word in text
        for word in [
            "earbud",
            "earbuds",
            "earphone",
            "earphones",
            "headphone",
            "headphones",
        ]
    ):
        return "earbuds"

    if any(
        word in text
        for word in [
            "laptop",
            "notebook",
            "macbook",
        ]
    ):
        return "laptop"

    if any(
        word in text
        for word in [
            "phone",
            "mobile",
            "smartphone",
            "iphone",
            "android",
        ]
    ):
        return "phone"

    if any(
        word in text
        for word in [
            "watch",
            "smartwatch",
        ]
    ):
        return "watch"

    if any(
        word in text
        for word in [
            "shoe",
            "shoes",
            "sneaker",
            "sneakers",
        ]
    ):
        return "shoes"

    if any(
        word in text
        for word in [
            "bag",
            "backpack",
        ]
    ):
        return "bag"

    if any(
        word in text
        for word in [
            "keyboard",
            "keyboards",
        ]
    ):
        return "keyboard"

    if any(
        word in text
        for word in [
            "mouse",
            "mice",
        ]
    ):
        return "mouse"

    return "general"


def safe_float(value, fallback):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def product_tags(product):
    tags = product.get("tags", [])
    return ", ".join(str(tag) for tag in tags) if tags else "No tags"


def render_payment_checkout(order_id, razorpay_key, amount):
    checkout_html = f"""
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>

    <div style="
        padding:18px;
        border-radius:14px;
        background:#111827;
        border:1px solid rgba(255,255,255,0.10);
        font-family:Arial,sans-serif;
        color:white;
    ">
        <div style="font-size:18px;font-weight:700;margin-bottom:10px;">
            Secure Razorpay Checkout
        </div>

        <div style="opacity:.75;margin-bottom:14px;">
            Order: {order_id}
        </div>

        <button
            id="rzp-button"
            style="
                background:#2563eb;
                color:white;
                border:none;
                padding:12px 22px;
                border-radius:9px;
                font-size:16px;
                cursor:pointer;
            "
        >
            💳 Pay ₹{amount / 100:.0f}
        </button>

        <div
            id="payment-status"
            style="
                margin-top:14px;
                font-size:15px;
                font-weight:bold;
            "
        ></div>
    </div>

    <script>
    var options = {{
        "key": "{razorpay_key}",
        "amount": "{amount}",
        "currency": "INR",
        "name": "SellPilot AI",
        "description": "SellPilot AI Purchase",
        "order_id": "{order_id}",

        "handler": function(response) {{

            document.getElementById("payment-status").innerHTML =
                "⏳ Payment received. Verifying signature...";

            fetch(
                "{BACKEND_URL}/verify-payment",
                {{
                    method: "POST",
                    headers: {{
                        "Content-Type": "application/json"
                    }},
                    body: JSON.stringify({{
                        "razorpay_order_id":
                            response.razorpay_order_id,

                        "razorpay_payment_id":
                            response.razorpay_payment_id,

                        "razorpay_signature":
                            response.razorpay_signature
                    }})
                }}
            )
            .then(response => response.json())
            .then(data => {{

                if (data.success) {{

                    document.getElementById(
                        "payment-status"
                    ).innerHTML =
                        "✅ Payment Verified Successfully! " +
                        "Use 'Check Payment Status' below to refresh the dashboard.";

                }} else {{

                    document.getElementById(
                        "payment-status"
                    ).innerHTML =
                        "❌ Payment Verification Failed.";

                }}

            }})
            .catch(error => {{

                document.getElementById(
                    "payment-status"
                ).innerHTML =
                    "⚠️ Verification request failed.";

            }});
        }},

        "modal": {{

            "ondismiss": function() {{

                document.getElementById(
                    "payment-status"
                ).innerHTML =
                    "Payment window closed.";

            }}

        }}
    }};

    var rzp = new Razorpay(options);

    document.getElementById(
        "rzp-button"
    ).onclick = function(e) {{

        rzp.open();
        e.preventDefault();

    }};
    </script>
    """

    components.html(checkout_html, height=560, scrolling=True)


# ============================================================
# ANALYSIS HELPER
# ============================================================

def analyze_customer_request(message, sidebar_budget, sidebar_preference):
    """Run intent extraction + recommendations for the submitted request."""
    history_for_agent = [
        {
            "role": item["role"],
            "content": item["content"],
        }
        for item in st.session_state.chat_history
    ]

    try:
        try:
            intent = analyze_customer_intent(
                message,
                history_for_agent,
            )
        except TypeError:
            # Backward compatibility with older intent-agent signatures.
            intent = analyze_customer_intent(message)

        if not isinstance(intent, dict):
            intent = {}

        category = intent.get("category", "general")
        groq_budget = intent.get("budget")
        groq_preference = intent.get(
            "preference",
            sidebar_preference,
        )
        use_case = intent.get("use_case", "") or ""
        summary = intent.get("summary", "") or ""

        if not category or category == "general":
            category = detect_category(message)

        active_budget = safe_float(
            groq_budget,
            sidebar_budget,
        )

        if not groq_preference:
            groq_preference = sidebar_preference

        # Do not pretend to understand an ambiguous request. Ask one concise
        # clarification question when the category cannot be identified.
        if category == "general":
            question = (
                "What type of product are you looking for — "
                "earbuds, laptop, phone, watch, shoes, bag, keyboard or mouse?"
            )
            st.session_state.clarification_question = question
            st.session_state.recommendations = []
            audit(
                "Clarification Requested",
                f"Could not confidently identify a product category from: {message}",
                "INFO",
            )
            st.session_state.chat_history.append(
                {"role": "assistant", "content": question}
            )
            return True

        st.session_state.clarification_question = None

        st.session_state.active_category = category
        st.session_state.active_budget = active_budget
        st.session_state.active_preference = groq_preference
        st.session_state.active_use_case = use_case
        st.session_state.last_summary = summary

        audit(
            "Customer Intent",
            f"Customer request: {message} | "
            f"Category: {category} | "
            f"Budget: ₹{active_budget} | "
            f"Preference: {groq_preference} | "
            f"Use case: {use_case}",
            "SUCCESS",
        )

        assistant_summary = (
            summary
            if summary
            else (
                f"I understood that you're looking for {category} "
                f"within ₹{active_budget:,.0f}"
                + (f" for {use_case}" if use_case else "")
                + "."
            )
        )

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": assistant_summary,
            }
        )

        try:
            recommendations = recommend_products(
                budget=active_budget,
                category=category,
                preference=groq_preference,
                use_case=use_case,
            ) or []
        except TypeError:
            # Backward compatibility with older recommendation-agent signatures.
            recommendations = recommend_products(
                budget=active_budget,
                category=category,
                preference=groq_preference,
            ) or []

        # Inventory is a hard availability constraint. Then apply a bounded
        # historical selection signal so the system improves over time.
        recommendations = filter_available(recommendations)
        recommendations = rerank_recommendations(
            recommendations,
            get_audit_logs(),
        )
        st.session_state.recommendations = recommendations

        if recommendations:
            exposure_ids = ",".join(
                str(product.get("id")) for product in recommendations[:6]
                if product.get("id")
            )
            audit(
                "Recommendation Exposure",
                f"Products: {exposure_ids} | Category: {category} | "
                f"Budget: ₹{active_budget} | Preference: {groq_preference}",
                "INFO",
            )
            st.session_state.recommendation_exposed = True

        audit(
            "Recommendation Generated",
            f"Category: {category} | "
            f"Budget: ₹{active_budget} | "
            f"Preference: {groq_preference} | "
            f"Use case: {use_case} | "
            f"Found {len(recommendations)} available matching products",
            "SUCCESS",
        )

        if recommendations:
            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": (
                        f"I found {len(recommendations)} matching "
                        f"{category} product(s)."
                    ),
                }
            )
        else:
            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": (
                        f"I couldn't find a {category} product within "
                        f"₹{active_budget:,.0f}. Try increasing the budget "
                        "or changing the category."
                    ),
                }
            )

        return True

    except Exception as exc:
        st.session_state.last_error = str(exc)
        audit(
            "Customer Intent Failed",
            f"Intent/recommendation processing failed: {exc}",
            "FAILED",
        )

        category = detect_category(message)
        active_budget = float(sidebar_budget)
        groq_preference = sidebar_preference
        use_case = ""

        st.session_state.active_category = category
        st.session_state.active_budget = active_budget
        st.session_state.active_preference = groq_preference
        st.session_state.active_use_case = use_case

        try:
            fallback_recommendations = (
                recommend_products(
                    budget=active_budget,
                    category=category,
                    preference=groq_preference,
                    use_case=use_case,
                ) or []
            )
            st.session_state.recommendations = rerank_recommendations(
                filter_available(fallback_recommendations),
                get_audit_logs(),
            )
        except TypeError:
            st.session_state.recommendations = (
                recommend_products(
                    budget=active_budget,
                    category=category,
                    preference=groq_preference,
                ) or []
            )
        except Exception as recommendation_error:
            st.session_state.recommendations = []
            st.error(
                "Recommendation fallback also failed: "
                f"{recommendation_error}"
            )

        return False


def normalize_upsell(candidate, selected_product):
    """Accept the normal dict response and a few safe legacy shapes."""
    if isinstance(candidate, dict):
        if isinstance(candidate.get("product"), dict):
            candidate = candidate["product"]
        elif isinstance(candidate.get("upsell"), dict):
            candidate = candidate["upsell"]

    if not isinstance(candidate, dict):
        return None

    name = candidate.get("name")
    price = candidate.get("price")
    if not name or price is None:
        return None

    try:
        price = float(price)
    except (TypeError, ValueError):
        return None

    if price <= 0 or str(name).strip() == str(selected_product.get("name", "")).strip():
        return None

    normalized = dict(candidate)
    normalized["price"] = price
    return normalized


def create_backend_order(total, upsell_amount):
    """Create an idempotent server-side Razorpay order."""
    total_rupees = int(round(float(total)))
    upsell_rupees = int(round(float(upsell_amount)))
    item_ids = [str(item.get("id")) for item in st.session_state.cart if item.get("id")]
    client_order_key = (
        st.session_state.session_id
        + "|"
        + ",".join(item_ids)
        + f"|{total_rupees}|{upsell_rupees}"
    )

    return requests.post(
        f"{BACKEND_URL}/create-order",
        json={
            "amount": total_rupees,
            "upsell_amount": upsell_rupees,
            "client_order_key": client_order_key,
            "item_ids": item_ids,
        },
        timeout=30,
    )


def backend_error_message(response):
    """Extract useful FastAPI/Razorpay error details instead of only HTTP code."""
    try:
        data = response.json()
        if isinstance(data, dict):
            return str(
                data.get("message")
                or data.get("detail")
                or data.get("error")
                or data
            )
    except ValueError:
        pass

    text = (response.text or "").strip()
    return text[:500] if text else f"HTTP {response.status_code}"


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ Customer Controls")

sidebar_budget = st.sidebar.number_input(
    "Fallback Maximum Budget (₹)",
    min_value=500,
    max_value=100000,
    value=3000,
    step=100,
)

sidebar_preference = st.sidebar.selectbox(
    "Fallback Preference",
    [
        "battery",
        "rating",
        "price",
    ],
)

if st.sidebar.button("🩺 Check Payment Service", width="stretch"):
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            if health_data.get("razorpay_configured"):
                st.sidebar.success(
                    f"Payment API online • {health_data.get('razorpay_mode', 'configured')} mode"
                )
            else:
                st.sidebar.error(
                    "Payment API is online, but Razorpay credentials are missing on Render."
                )
        else:
            st.sidebar.error(f"Payment API returned HTTP {health_response.status_code}.")
    except requests.RequestException as exc:
        st.sidebar.error(f"Payment API unreachable: {exc}")

st.sidebar.divider()

st.sidebar.caption(
    "Groq is the primary intent engine. "
    "Sidebar values are used only when the AI cannot "
    "extract a field."
)

if st.sidebar.button(
    "🧹 Clear Current Transaction",
    width="stretch",
):
    reset_transaction_state()
    st.rerun()



# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero-native">
        <div class="kicker">● AI SALES AGENT ONLINE</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero-title">🛒 SellPilot AI</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Autonomous AI Revenue Agent for Modern Merchants</div>', unsafe_allow_html=True)

st.caption(
    "Understand → Personalize → Recommend → Upsell → "
    "Protect → Convert → Verify"
)

if is_llm_configured():
    st.success("🧠 AI Engine: **Groq LLM active** — intent understanding is model-driven.", icon="✅")
else:
    st.warning(
        "🧠 AI Engine: **Fallback mode** — GROQ_API_KEY is not set, so intent "
        "extraction is running on deterministic keyword matching instead of "
        "the LLM. Set GROQ_API_KEY in Streamlit Cloud Secrets to enable the "
        "real model.",
        icon="⚠️",
    )


# ============================================================
# JUDGE DEMO SHORTCUTS
# ============================================================

st.markdown("### 🎬 Judge Demo Scenarios")
st.caption("Use one of these controlled scenarios to demonstrate the complete workflow quickly.")
demo_cols = st.columns(3)
demo_cases = [
    ("🎧 Gym Earbuds", "I need wireless earbuds under ₹3000 for gym use with good battery"),
    ("💻 Student Laptop", "I need a laptop under ₹60000 for student work with good performance"),
    ("📱 Budget Smartphone", "I need a smartphone under ₹20000 with a good camera"),
]
for demo_col, (label, prompt) in zip(demo_cols, demo_cases):
    with demo_col:
        if st.button(label, key=f"demo_{label}", width="stretch"):
            st.session_state.draft_message = prompt
            st.session_state.demo_hint = f"Demo loaded: {prompt}"
            st.rerun()

if st.session_state.get("demo_hint"):
    st.info(st.session_state.demo_hint)

# ============================================================
# CUSTOMER INPUT — TOP / CENTER
# ============================================================

input_left, input_center, input_right = st.columns([1, 7, 1])

with input_center:
    st.markdown(
        '<div class="customer-input-card">'
        '<div class="customer-input-label">● CUSTOMER REQUEST</div>'
        '<div class="customer-input-help">'
        'Describe what you want — product, budget, use case or preference. '
        'Then press Analyze.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.form("customer_analyze_form", clear_on_submit=False):
        form_col1, form_col2 = st.columns([5.5, 1.2])

        with form_col1:
            message = st.text_input(
                "Customer request",
                value=st.session_state.get("draft_message", ""),
                placeholder=(
                    "Example: I need wireless earbuds under ₹3000 "
                    "for gym use with good battery"
                ),
                label_visibility="collapsed",
            )

        with form_col2:
            analyze_clicked = st.form_submit_button(
                "🔎 Analyze",
                width="stretch",
            )

    if analyze_clicked:
        message = message.strip()
        st.session_state.draft_message = message

        if not message:
            st.warning("Please enter the customer's requirement first.")
        else:
            # Start a fresh recommendation/transaction state for the new analysis,
            # but keep the same session ID and conversation history.
            st.session_state.recommendations = []
            st.session_state.selected_product = None
            st.session_state.upsell_product = None
            reset_transaction_state()

            st.session_state.chat_history.append(
                {
                    "role": "user",
                    "content": message,
                }
            )

            analyze_customer_request(
                message,
                sidebar_budget,
                sidebar_preference,
            )

            st.rerun()



# ============================================================
# TOP STATUS
# ============================================================

status_col1, status_col2, status_col3 = st.columns(
    [1.1, 1.5, 0.7]
)

with status_col1:
    st.markdown(
        '<div class="status-box">'
        '<div class="kicker">CURRENT SESSION</div>'
        f'<b>{st.session_state.session_id}</b>'
        "</div>",
        unsafe_allow_html=True,
    )

with status_col2:
    category_display = (
        st.session_state.active_category
        or "Not detected"
    )

    if st.session_state.active_budget is not None:
        budget_display = (
            f"₹{st.session_state.active_budget:,.0f}"
        )
    else:
        budget_display = "Not detected"

    st.markdown(
        '<div class="status-box">'
        '<div class="kicker">CUSTOMER PROFILE</div>'
        f"<b>{category_display}</b>"
        f" &nbsp;•&nbsp; Budget: <b>{budget_display}</b>"
        "</div>",
        unsafe_allow_html=True,
    )

with status_col3:
    if st.button(
        "🆕 New Customer",
        width="stretch",
    ):
        new_customer()
        st.rerun()


# ============================================================
# PIPELINE
# ============================================================

st.markdown("### 🔄 AI Revenue Pipeline")

pipeline_items = [
    ("🧠", "Intent", "Understand"),
    ("🤖", "Recommend", "Personalize"),
    ("💡", "Upsell", "Increase value"),
    ("🔐", "Policy", "Safety gate"),
    ("💳", "Payment", "Process"),
    ("✅", "Verified", "Confirm"),
    ("📜", "Audit", "Record"),
]

pipeline_cols = st.columns(len(pipeline_items))

for col, (icon, name, desc) in zip(
    pipeline_cols,
    pipeline_items,
):
    with col:
        st.markdown(
            f"""
            <div class="pipeline-step">
                <div class="pipeline-icon">{icon}</div>
                <div class="pipeline-name">{name}</div>
                <div class="pipeline-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# CONVERSATION
# ============================================================

if st.session_state.clarification_question:
    st.info(f"💬 {st.session_state.clarification_question}")

if st.session_state.chat_history:
    with st.expander("💬 Conversation", expanded=True):
        for chat_item in st.session_state.chat_history:
            with st.chat_message(chat_item["role"]):
                st.write(chat_item["content"])


# ============================================================
# PRODUCT RECOMMENDATIONS
# ============================================================

if st.session_state.recommendations:

    st.divider()
    st.markdown("### 🤖 AI Recommendations")
    st.caption("Top matches are shown side-by-side so the customer can choose without excessive scrolling.")

    recs = st.session_state.recommendations[:6]

    # Explainable recommendation summary: show decision factors, not hidden reasoning.
    active_budget = float(st.session_state.get("active_budget") or 0)
    active_pref = str(st.session_state.get("active_preference") or "preference")
    active_use = str(st.session_state.get("active_use_case") or "general use")
    st.markdown(
        f"""<div class="explain-card"><b>🧠 Why these recommendations?</b><br>
        🎯 Use case: <b>{active_use}</b> &nbsp; • &nbsp;
        💰 Budget: <b>₹{active_budget:,.0f}</b> &nbsp; • &nbsp;
        ⭐ Priority: <b>{active_pref}</b><br>
        <span style="color:#64748b;font-size:0.82rem;">Products are matched using customer intent, availability, product relevance and bounded learning signals.</span>
        </div>""",
        unsafe_allow_html=True,
    )
    recommendation_cols = st.columns(min(3, len(recs)))

    for index, product in enumerate(recs):
        with recommendation_cols[index % len(recommendation_cols)]:
            with st.container(border=True):
                st.markdown(f"**{product['name']}**")
                st.caption(f"{product.get('category', 'N/A').title()}")
                st.markdown(f"### ₹{product['price']:,}")

                metric_a, metric_b = st.columns(2)
                with metric_a:
                    st.caption(f"⭐ {product.get('rating', 'N/A')}")
                with metric_b:
                    if "battery_hours" in product:
                        st.caption(f"🔋 {product.get('battery_hours')} hrs")
                    else:
                        st.caption("✓ AI matched")

                st.caption(product_tags(product))
                stock = stock_for(product)
                learning_rate = float(product.get("learning_selection_rate", 0.0))
                exposure_count = int(product.get("learning_exposures", 0))
                stock_text = f"📦 {stock} in stock" if stock > 0 else "🚫 Out of stock"
                if exposure_count:
                    st.caption(f"{stock_text} • 📈 {learning_rate * 100:.0f}% observed selection rate")
                else:
                    st.caption(f"{stock_text} • 🆕 cold-start product")

                if st.button(
                    "🛒 Select",
                    key=f"select_product_{product['id']}_{index}",
                    width="stretch",
                ):
                    # Clear only the old transaction before generating the new
                    # upsell. This ordering is important: reset_transaction_state()
                    # must NOT run after get_upsell().
                    reset_transaction_state()
                    st.session_state.selected_product = product
                    st.session_state.upsell_product = None

                    try:
                        generated_upsell = get_upsell(product)
                        normalized = normalize_upsell(
                            generated_upsell,
                            product,
                        )

                        if normalized:
                            st.session_state.upsell_product = normalized
                        else:
                            audit(
                                "Upsell Generation Failed",
                                "Upsell agent returned no usable complementary product.",
                                "FAILED",
                            )
                    except Exception as upsell_error:
                        st.session_state.upsell_product = None
                        audit(
                            "Upsell Generation Failed",
                            f"Could not generate upsell: {upsell_error}",
                            "FAILED",
                        )

                    audit(
                        "Product Selected",
                        f"Product ID: {product.get('id', 'N/A')} | "
                        f"Selected {product['name']} for ₹{product['price']}",
                        "SUCCESS",
                    )

                    st.rerun()

# ============================================================
# SELECTED PRODUCT
# ============================================================

if st.session_state.selected_product:

    product = st.session_state.selected_product

    st.divider()
    st.markdown("### 🛍️ Selected Product")

    selected_col1, selected_col2 = st.columns(
        [2, 1]
    )

    with selected_col1:
        st.success(
            f"{product['name']} — ₹{product['price']:,}"
        )

        st.caption(
            "Selected as the primary purchase."
        )

    with selected_col2:
        if st.button(
            "↩️ Change Product",
            width="stretch",
        ):
            st.session_state.selected_product = None
            st.session_state.upsell_product = None
            reset_transaction_state()
            st.rerun()


# ============================================================
# UPSELL
# ============================================================

if (
    st.session_state.selected_product
    and st.session_state.upsell_product
    and not st.session_state.cart
):

    product = st.session_state.selected_product
    upsell = st.session_state.upsell_product

    st.divider()
    st.markdown("### 💡 Smart Upsell")

    st.markdown(
        f"""
        <div class="upsell-box">
            <b>Recommended add-on</b><br>
            Since you're purchasing <b>{product['name']}</b>,
            consider <b>{upsell['name']}</b> for
            <b>₹{upsell['price']:,}</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    upsell_stats = upsell_learning_stats(get_audit_logs()).get(
        str(upsell.get("id", "")), {}
    )
    reason = upsell.get(
        "upsell_reason",
        "Selected as a compatible add-on for your chosen product.",
    )
    st.caption(f"🎯 Why this add-on: {reason}")
    if upsell_stats.get("offered"):
        st.caption(
            f"📈 Observed attach rate for this add-on: "
            f"{upsell_stats.get('attach_rate', 0) * 100:.0f}%"
        )

    if not st.session_state.upsell_logged:
        audit(
            "Upsell Offered",
            f"Product ID: {upsell.get('id', 'N/A')} | "
            f"Offered {upsell['name']} for ₹{upsell['price']} | "
            f"Reason: {upsell.get('upsell_reason', 'Compatible add-on')}",
            "SUCCESS",
        )
        st.session_state.upsell_logged = True

    upsell_col1, upsell_col2 = st.columns(2)

    with upsell_col1:
        if st.button(
            "✅ Add Upsell",
            key="add_upsell",
            width="stretch",
        ):
            st.session_state.cart = [
                product,
                upsell,
            ]

            audit(
                "Upsell Accepted",
                f"Product ID: {upsell.get('id', 'N/A')} | "
                f"Customer added {upsell['name']} to cart",
                "SUCCESS",
            )

            st.success(
                f"{upsell['name']} added to cart."
            )

    with upsell_col2:
        if st.button(
            "❌ No Thanks",
            key="no_upsell",
            width="stretch",
        ):
            st.session_state.cart = [
                product,
            ]

            audit(
                "Upsell Declined",
                f"Product ID: {upsell.get('id', 'N/A')} | "
                f"Customer declined {upsell['name']}",
                "INFO",
            )

            st.info(
                "Continuing with the primary product."
            )


# ============================================================
# CART + SAFETY GATE
# ============================================================

if st.session_state.cart:

    st.divider()
    st.markdown("### 🛒 Cart")

    total = sum(
        float(item.get("price", 0))
        for item in st.session_state.cart
    )

    cart_col1, cart_col2 = st.columns(
        [2.2, 1]
    )

    with cart_col1:
        for item in st.session_state.cart:
            st.markdown(
                f"**{item['name']}** — "
                f"₹{item['price']:,}"
            )

            st.caption(
                product_tags(item)
            )

    with cart_col2:
        st.metric(
            "Order Total",
            f"₹{total:,.0f}",
        )

    st.markdown(
        '<div class="cart-box">'
        "<b>🔐 AI Safety Gate</b><br>"
        "AI can recommend and prepare the transaction, "
        "but the policy gate and customer confirmation "
        "must pass before payment."
        "</div>",
        unsafe_allow_html=True,
    )

    if total <= MAX_ORDER_VALUE:

        st.success(
            f"✓ Policy Check Passed — "
            f"₹{total:,.0f} is within the "
            f"₹{MAX_ORDER_VALUE:,} transaction limit."
        )

        if not st.session_state.policy_logged:
            audit(
                "Transaction Policy",
                f"Order ₹{total} passed the "
                f"₹{MAX_ORDER_VALUE:,} limit",
                "SUCCESS",
            )
            st.session_state.policy_logged = True

        # --------------------------------------------------------
        # CONFIRM PURCHASE
        # --------------------------------------------------------

        if not st.session_state.confirmed:

            if st.button(
                "🔒 Confirm Purchase",
                key="confirm_purchase",
                width="stretch",
            ):

                if not st.session_state.confirmation_logged:
                    audit(
                        "Customer Confirmed",
                        f"Customer confirmed purchase "
                        f"worth ₹{total}",
                        "SUCCESS",
                    )
                    st.session_state.confirmation_logged = True

                upsell_amount = 0

                if len(st.session_state.cart) > 1:
                    upsell_amount = float(
                        st.session_state.cart[1].get(
                            "price",
                            0,
                        )
                    )

                try:
                    response = create_backend_order(
                        total,
                        upsell_amount,
                    )

                    if not (200 <= response.status_code < 300):
                        detail = backend_error_message(response)
                        audit(
                            "Razorpay Order Creation Failed",
                            f"Backend returned HTTP {response.status_code} "
                            f"for order amount ₹{total} | {detail}",
                            "FAILED",
                        )
                        st.error(
                            "❌ Razorpay order creation failed: "
                            f"HTTP {response.status_code} — {detail}"
                        )
                    else:
                        try:
                            data = response.json()
                        except ValueError:
                            data = {}

                        if data.get("success"):
                            order_id = data.get("order_id")
                            razorpay_key = data.get("key_id")
                            amount_raw = data.get("amount")

                            if not order_id or not razorpay_key or amount_raw is None:
                                detail = (
                                    "Backend response is missing order_id, key_id or amount."
                                )
                                audit(
                                    "Razorpay Order Creation Failed",
                                    detail,
                                    "FAILED",
                                )
                                st.error(f"❌ {detail}")
                            else:
                                amount = int(amount_raw)
                                st.session_state.razorpay_order_id = order_id
                                st.session_state.confirmed = True
                                st.session_state.razorpay_checkout_key = razorpay_key
                                st.session_state.razorpay_checkout_amount = amount

                                if not st.session_state.order_logged:
                                    audit(
                                        "Razorpay Order Created",
                                        f"Order ID: {order_id}, Amount: ₹{total}",
                                        "SUCCESS",
                                    )
                                    st.session_state.order_logged = True

                                st.success(
                                    "✓ Policy passed and Razorpay order created."
                                )
                                st.code(order_id, language=None)

                                if not st.session_state.payment_initiated_logged:
                                    audit(
                                        "Payment Initiated",
                                        f"Razorpay checkout ready for Order ID: {order_id}, "
                                        f"Amount: ₹{total}",
                                        "SUCCESS",
                                    )
                                    st.session_state.payment_initiated_logged = True
                        else:
                            error_message = backend_error_message(response)
                            audit(
                                "Razorpay Order Creation Failed",
                                error_message,
                                "FAILED",
                            )
                            st.error(f"❌ {error_message}")

                except requests.exceptions.ConnectionError:
                    audit(
                        "Payment Service Error",
                        "Cannot connect to FastAPI "
                        "while creating order.",
                        "FAILED",
                    )

                    st.error(
                        "❌ Cannot connect to FastAPI. "
                        "Make sure the deployed backend is running."
                    )

                except requests.exceptions.Timeout:
                    audit(
                        "Payment Service Error",
                        "Payment server timed out.",
                        "FAILED",
                    )

                    st.error(
                        "❌ Payment server took too long to respond."
                    )

                except Exception as exc:
                    audit(
                        "Payment Service Error",
                        f"Unexpected payment error: {exc}",
                        "FAILED",
                    )

                    st.error(
                        f"❌ Payment service error: {exc}"
                    )

        # --------------------------------------------------------
        # CHECKOUT
        # --------------------------------------------------------

        if (
            st.session_state.confirmed
            and st.session_state.razorpay_order_id
            and not st.session_state.payment_verified
        ):

            order_id = st.session_state.razorpay_order_id

            # Retrieve key/amount again from backend if the page
            # was rerun after order creation.
            if (
                "razorpay_checkout_key" not in st.session_state
                or st.session_state.razorpay_checkout_key is None
            ):
                try:
                    # The backend's payment-status endpoint is used
                    # only for status, so create-order is not called
                    # again. The key is expected to be available from
                    # the first creation response.
                    pass
                except Exception:
                    pass

            # Store checkout details when order is created.
            # If they are available, render the checkout.
            checkout_key = st.session_state.get(
                "razorpay_checkout_key"
            )
            checkout_amount = st.session_state.get(
                "razorpay_checkout_amount"
            )

            if checkout_key and checkout_amount:
                st.markdown("#### 💳 Secure Payment")

                render_payment_checkout(
                    order_id,
                    checkout_key,
                    checkout_amount,
                )
            else:
                st.info(
                    "Razorpay order is ready. "
                    "Use the payment status section below "
                    "to continue/check the transaction."
                )

    else:

        # --------------------------------------------------------
        # POLICY BLOCK
        # --------------------------------------------------------

        st.error(
            f"🚫 Transaction Blocked\n\n"
            f"Order amount: ₹{total:,.0f}\n"
            f"Maximum allowed: ₹{MAX_ORDER_VALUE:,}\n\n"
            "💳 Payment was NOT initiated."
        )

        if not st.session_state.policy_logged:
            audit(
                "Transaction Policy",
                f"Order ₹{total} blocked because it "
                f"exceeds ₹{MAX_ORDER_VALUE:,}",
                "BLOCKED",
            )

            audit(
                "Order Blocked",
                f"Payment not initiated because "
                f"₹{total:,.0f} exceeds policy limit "
                f"₹{MAX_ORDER_VALUE:,}",
                "BLOCKED",
            )

            st.session_state.policy_logged = True


# ============================================================
# BUILDATHON FAILURE DEMO
# ============================================================

if st.session_state.razorpay_order_id:

    st.divider()
    st.markdown("### 🧪 Buildathon Safety Demo")

    st.caption(
        "Demonstrate that a tampered payment signature is "
        "rejected by the backend rather than being treated "
        "as a successful payment."
    )

    if st.button(
        "🔐 Simulate Invalid Payment Signature",
        key="simulate_invalid_signature",
        width="stretch",
    ):

        demo_order_id = (
            st.session_state.razorpay_order_id
        )

        try:
            verification_response = requests.post(
                f"{BACKEND_URL}/verify-payment",
                json={
                    "razorpay_order_id": demo_order_id,
                    "razorpay_payment_id":
                        "pay_demo_invalid",
                    "razorpay_signature":
                        "invalid_signature_demo",
                },
                timeout=30,
            )

            if verification_response.status_code == 200:

                verification_data = (
                    verification_response.json()
                )

                if verification_data.get(
                    "success"
                ) is False:

                    audit(
                        "Payment Verification Failed",
                        "Buildathon demo: invalid/tampered "
                        "payment signature rejected safely.",
                        "FAILED",
                    )

                    st.error(
                        "❌ Payment Verification Failed"
                    )

                    st.success(
                        "✅ Invalid signature rejected safely. "
                        "Payment was NOT marked successful."
                    )

                else:
                    audit(
                        "Payment Verification Failed",
                        "Buildathon demo returned an unexpected "
                        "success result for an invalid signature.",
                        "FAILED",
                    )

                    st.error(
                        "⚠️ Unexpected result: invalid "
                        "signature was accepted."
                    )

            else:
                audit(
                    "Payment Verification Failed",
                    f"Invalid signature demo returned HTTP "
                    f"{verification_response.status_code}",
                    "FAILED",
                )

                st.error(
                    "❌ Verification request failed safely "
                    f"(HTTP {verification_response.status_code})."
                )

        except requests.exceptions.RequestException as exc:
            audit(
                "Payment Verification Failed",
                f"Invalid signature demo request error: {exc}",
                "FAILED",
            )

            st.error(
                f"❌ Verification request failed safely: {exc}"
            )


# ============================================================
# PAYMENT STATUS
# ============================================================

if st.session_state.razorpay_order_id:

    st.divider()
    st.markdown("### 🔎 Payment Status")

    st.write(
        "Razorpay Order ID: "
        f"`{st.session_state.razorpay_order_id}`"
    )

    if st.button(
        "🔄 Check Payment Status",
        key="check_payment",
        width="stretch",
    ):

        try:
            status_response = requests.get(
                f"{BACKEND_URL}/payment-status/"
                + st.session_state.razorpay_order_id,
                timeout=30,
            )

            if status_response.status_code == 200:

                status_data = status_response.json()

                payment_status = status_data.get(
                    "status"
                )

                if payment_status == "verified":

                    st.session_state.payment_verified = True

                    st.session_state.payment_id = (
                        status_data.get("payment_id")
                    )

                    if not st.session_state.payment_logged:
                        audit(
                            "Payment Verified",
                            f"Order ID: "
                            f"{st.session_state.razorpay_order_id} | "
                            f"Payment ID: "
                            f"{status_data.get('payment_id', 'N/A')}",
                            "SUCCESS",
                        )
                        st.session_state.payment_logged = True

                    st.success(
                        "✅ Payment Verified Successfully!"
                    )

                    if not st.session_state.completion_logged:
                        audit(
                            "Order Completed",
                            f"Order "
                            f"{st.session_state.razorpay_order_id} "
                            "successfully verified and completed",
                            "SUCCESS",
                        )
                        st.session_state.completion_logged = True

                    if status_data.get("payment_id"):
                        st.write(
                            "Payment ID: "
                            f"`{status_data['payment_id']}`"
                        )

                elif payment_status == "failed":

                    st.session_state.payment_verified = False

                    if not st.session_state.payment_logged:
                        audit(
                            "Payment Failed",
                            f"Payment verification failed "
                            f"for order "
                            f"{st.session_state.razorpay_order_id}",
                            "FAILED",
                        )
                        st.session_state.payment_logged = True

                    st.error(
                        "❌ Payment Verification Failed."
                    )

                else:
                    st.info(
                        "⏳ Payment is still pending."
                    )

            else:
                audit(
                    "Payment Status Check Failed",
                    f"Backend returned HTTP "
                    f"{status_response.status_code} "
                    f"for order "
                    f"{st.session_state.razorpay_order_id}",
                    "FAILED",
                )

                st.error(
                    "Unable to retrieve payment status."
                )

        except requests.exceptions.ConnectionError:
            st.error(
                "❌ Cannot connect to FastAPI."
            )

        except requests.exceptions.Timeout:
            st.error(
                "❌ Payment status request timed out."
            )

        except Exception as exc:
            st.error(
                f"❌ Payment status error: {exc}"
            )


# ============================================================
# PAYMENT SUCCESS
# ============================================================

if st.session_state.payment_verified:

    st.divider()

    st.success(
        "🎉 SellPilot AI payment completed successfully!"
    )

    st.info(
        "The payment signature has been verified "
        "by the backend."
    )


# ============================================================
# AI AGENT NETWORK
# ============================================================

st.divider()
st.markdown("### 🤝 AI Agent Network")
st.caption("Specialized agents/modules handle each stage of the customer-to-payment journey.")

agent_items = [
    ("🧠", "Customer Intent Agent", "Groq understands category, budget, preference, context and use case."),
    ("🤖", "Recommendation Agent", "Ranks products using budget, category, preference and use case."),
    ("💡", "Upsell Agent", "Suggests a complementary product without bypassing customer choice."),
    ("🔐", "Policy Agent", f"Blocks transactions above the ₹{MAX_ORDER_VALUE:,} safety limit."),
    ("💳", "Payment Agent", "Creates Razorpay test orders and verifies payment signatures."),
    ("📜", "Audit Agent", "Records AI, policy and payment decisions with timestamps."),
]

agent_cols = st.columns(3)
for index, (icon, name, description) in enumerate(agent_items):
    with agent_cols[index % 3]:
        with st.container(border=True):
            st.markdown(f"**{icon} {name}**")
            st.caption(description)


# ============================================================
# CURRENT SESSION STATUS
# ============================================================

st.divider()
st.markdown("### 🎯 Current Session Status")

st.caption("Live state for the active customer session.")

current_logs = [
    row
    for row in get_audit_logs()
    if len(row) >= 4
    and f"[Session: {st.session_state.session_id}]"
    in str(row[2])
]

current_completed = any(
    len(row) >= 3
    and str(row[1]) == "Order Completed"
    for row in current_logs
)

current_upsell = any(
    len(row) >= 3
    and str(row[1]) == "Upsell Accepted"
    for row in current_logs
)

current_blocked = any(
    len(row) >= 4
    and str(row[3]) == "BLOCKED"
    for row in current_logs
)

current_failed = any(
    len(row) >= 4
    and str(row[3]) == "FAILED"
    for row in current_logs
)

status_col1, status_col2, status_col3, status_col4 = (
    st.columns(4)
)

with status_col1:
    st.write(
        f"**Session:** `{st.session_state.session_id}`"
    )

with status_col2:
    st.write(
        "**Upsell:** ✅ Accepted"
        if current_upsell
        else
        "**Upsell:** — Not accepted"
    )

with status_col3:
    st.write(
        "**Order:** ✅ Completed"
        if current_completed
        else
        "**Order:** ⏳ Not completed"
    )

with status_col4:
    if current_blocked:
        st.write("**Policy:** 🚫 Blocked")
    elif current_failed:
        st.write("**Payment:** ❌ Failure recorded")
    else:
        st.write("**Policy/Payment:** ✅ No failure recorded")


# ============================================================
# MERCHANT COMMAND CENTER
# ============================================================

st.divider()
st.markdown("### 🏪 Merchant Command Center")

st.caption(
    "Recorded metrics come only from the audit database. "
    "The separate growth section below is explicitly labeled "
    "as buildathon simulation data."
)

command_logs = get_audit_logs()

command_sessions = set()
completed_order_ids = set()
completed_revenues = {}

upsell_offered_count = 0
upsell_accepted_count = 0
blocked_count = 0
failed_event_count = 0

for log_row in command_logs:

    if len(log_row) < 4:
        continue

    timestamp, action, details, status = log_row

    details_text = str(details)
    action_text = str(action)
    status_text = str(status)

    # Session extraction
    if "[Session:" in details_text:
        try:
            session_part = (
                details_text.split(
                    "[Session:",
                    1,
                )[1]
            )

            session_id_from_log = (
                session_part.split(
                    "]",
                    1,
                )[0].strip()
            )

            if session_id_from_log:
                command_sessions.add(
                    session_id_from_log
                )

        except (IndexError, AttributeError):
            pass

    # Counts
    if action_text == "Upsell Offered":
        upsell_offered_count += 1

    if action_text == "Upsell Accepted":
        upsell_accepted_count += 1

    if status_text == "BLOCKED":
        blocked_count += 1

    if status_text == "FAILED":
        failed_event_count += 1

    # Order revenue
    if action_text == "Razorpay Order Created":

        order_match = re.search(
            r"Order ID:\s*([^,]+),\s*Amount:\s*₹([0-9,]+(?:\.[0-9]+)?)",
            details_text,
        )

        if order_match:
            order_id = (
                order_match.group(1).strip()
            )

            try:
                completed_revenues[order_id] = float(
                    order_match.group(2).replace(",", "")
                )
            except ValueError:
                pass

    # Completed orders
    if action_text == "Order Completed":

        completed_match = re.search(
            r"Order\s+([^\s]+)\s+successfully",
            details_text,
        )

        if completed_match:
            completed_order_ids.add(
                completed_match.group(1).strip()
            )


recorded_completed_revenue = sum(
    completed_revenues[order_id]
    for order_id in completed_order_ids
    if order_id in completed_revenues
)

recorded_completed_orders = len(
    completed_order_ids
)

recorded_aov = (
    recorded_completed_revenue
    / recorded_completed_orders
    if recorded_completed_orders
    else 0
)

recorded_attach_rate = (
    upsell_accepted_count
    / upsell_offered_count
    * 100
    if upsell_offered_count
    else 0
)

learning_stats = product_learning_stats(command_logs)
learned_products = sorted(
    [
        (pid, stats)
        for pid, stats in learning_stats.items()
        if stats.get("exposures", 0)
    ],
    key=lambda item: item[1].get("selection_rate", 0),
    reverse=True,
)

cc1, cc2, cc3, cc4 = st.columns(4)

with cc1:
    st.metric(
        "Recorded Sessions",
        f"{len(command_sessions)}",
    )

with cc2:
    st.metric(
        "Completed Orders",
        f"{recorded_completed_orders}",
    )

with cc3:
    st.metric(
        "Recorded Revenue",
        f"₹{recorded_completed_revenue:,.0f}",
    )

with cc4:
    st.metric(
        "Recorded AOV",
        f"₹{recorded_aov:,.0f}",
    )

cc5, cc6, cc7, cc8 = st.columns(4)

with cc5:
    st.metric(
        "Upsell Attach Rate",
        f"{recorded_attach_rate:.1f}%",
    )

with cc6:
    st.metric(
        "Upsells Accepted",
        f"{upsell_accepted_count}",
    )

with cc7:
    st.metric(
        "Blocked Events",
        f"{blocked_count}",
    )

with cc8:
    st.metric(
        "Failed Events",
        f"{failed_event_count}",
    )


# ============================================================
# ADAPTIVE SALES SIGNALS
# ============================================================

st.markdown("#### 🧠 Adaptive Sales Signals")
st.caption(
    "SellPilot learns from observed customer choices. "
    "Historical signals are bounded so new products are never locked out by cold-start bias."
)

if learned_products:
    signal_rows = []
    for product_id, stats in learned_products[:6]:
        signal_rows.append(
            {
                "Product": product_id,
                "Exposed": stats.get("exposures", 0),
                "Selected": stats.get("selections", 0),
                "Observed Selection": f"{stats.get('selection_rate', 0) * 100:.1f}%",
            }
        )
    st.dataframe(signal_rows, width="stretch", hide_index=True)
else:
    st.info("Learning activates automatically after customers see and select recommendations.")

# ============================================================
# RECENT MERCHANT EVENTS
# ============================================================

st.markdown("#### 🧭 Recent Merchant Events")

if command_logs:

    recent_rows = command_logs[-10:][::-1]

    event_table = []

    for timestamp, action, details, status in recent_rows:
        event_table.append(
            {
                "Time": str(timestamp),
                "Action": str(action),
                "Status": str(status),
                "Details": str(details).replace(
                    "[Session:",
                    "Session:",
                ),
            }
        )

    st.dataframe(
        event_table,
        width="stretch",
        hide_index=True,
        height=220,
    )

else:
    st.info(
        "No merchant events have been recorded yet."
    )
st.divider()
analytics.payment_history.render_payment_history(command_logs, blocked_count)



st.divider()
st.markdown("### 📈 Buildathon Growth Simulation")

st.caption(
    "These are transparent demo assumptions, not real merchant "
    "performance. Use this section to explain the commercial "
    "impact of the AI upsell."
)

DEMO_SESSIONS = 100
DEMO_UPSELL_OFFERED = 100
DEMO_UPSELL_ACCEPTED = 32
DEMO_BASE_ORDER_VALUE = 3000
DEMO_UPSELL_VALUE = 899

demo_attach_rate = (
    DEMO_UPSELL_ACCEPTED
    / DEMO_UPSELL_OFFERED
    * 100
)

demo_revenue_without_upsell = (
    DEMO_SESSIONS
    * DEMO_BASE_ORDER_VALUE
)

demo_revenue_uplift = (
    DEMO_UPSELL_ACCEPTED
    * DEMO_UPSELL_VALUE
)

demo_total_revenue = (
    demo_revenue_without_upsell
    + demo_revenue_uplift
)

demo_aov_without_upsell = (
    demo_revenue_without_upsell
    / DEMO_SESSIONS
)

demo_aov_with_upsell = (
    demo_total_revenue
    / DEMO_SESSIONS
)

demo_uplift_percent = (
    demo_revenue_uplift
    / demo_revenue_without_upsell
    * 100
)

growth1, growth2, growth3, growth4 = st.columns(4)

with growth1:
    st.metric(
        "Demo Sessions",
        f"{DEMO_SESSIONS}",
    )

with growth2:
    st.metric(
        "Upsell Attach Rate",
        f"{demo_attach_rate:.1f}%",
    )

with growth3:
    st.metric(
        "Demo Revenue",
        f"₹{demo_total_revenue:,.0f}",
    )

with growth4:
    st.metric(
        "Revenue Uplift",
        f"₹{demo_revenue_uplift:,.0f}",
    )

aov1, aov2, aov3 = st.columns(3)

with aov1:
    st.metric(
        "Base AOV",
        f"₹{demo_aov_without_upsell:,.0f}",
    )

with aov2:
    st.metric(
        "AOV With Upsell",
        f"₹{demo_aov_with_upsell:,.0f}",
    )

with aov3:
    st.metric(
        "AOV Lift",
        f"{demo_uplift_percent:.1f}%",
    )

growth_data = {
    "Metric": [
        "Demo sessions",
        "Upsell offered",
        "Upsell accepted",
        "Upsell attach rate",
        "Revenue without upsell",
        "Additional upsell revenue",
        "Total demo revenue",
    ],
    "Value": [
        f"{DEMO_SESSIONS}",
        f"{DEMO_UPSELL_OFFERED}",
        f"{DEMO_UPSELL_ACCEPTED}",
        f"{demo_attach_rate:.1f}%",
        f"₹{demo_revenue_without_upsell:,.0f}",
        f"₹{demo_revenue_uplift:,.0f}",
        f"₹{demo_total_revenue:,.0f}",
    ],
}

st.table(growth_data)

st.success(
    "🎯 Buildathon story: SellPilot AI combines conversational "
    "intent understanding, personalized recommendation, "
    "contextual upsell, a hard safety gate, customer confirmation, "
    "verified payment and auditability in one revenue workflow."
)


# ============================================================
# REAL DATABASE AUDIT TRAIL
# ============================================================

st.divider()
st.markdown("### 📜 AI Audit Trail")
st.caption(
    "Every important AI, policy and payment action is recorded with timestamp, session, details and status."
)

logs = get_audit_logs()

if logs:
    audit_scope_col, audit_status_col, audit_export_col = st.columns([2, 1, 1])

    with audit_scope_col:
        audit_scope = st.selectbox(
            "Audit scope",
            ["Current session", "All sessions"],
            key="audit_scope",
            label_visibility="collapsed",
        )

    with audit_status_col:
        audit_status = st.selectbox(
            "Status",
            ["All", "SUCCESS", "BLOCKED", "FAILED", "INFO"],
            key="audit_status",
            label_visibility="collapsed",
        )

    with audit_export_col:
        st.download_button(
            "⬇️ Export JSON",
            data=get_audit_logs_json(),
            file_name=f"audit_{st.session_state.session_id}.json",
            mime="application/json",
            width="stretch",
        )

    if audit_scope == "Current session":
        visible_logs = [
            row for row in logs
            if len(row) >= 4
            and f"[Session: {st.session_state.session_id}]" in str(row[2])
        ]
    else:
        visible_logs = list(logs)

    if audit_status != "All":
        visible_logs = [
            row for row in visible_logs
            if len(row) >= 4 and str(row[3]) == audit_status
        ]

    visible_logs = visible_logs[-8:][::-1]
    st.caption(f"Showing {len(visible_logs)} recent event(s) • compact live view")

    for timestamp, action, details, status in visible_logs:
        try:
            readable_time = datetime.fromisoformat(str(timestamp)).strftime("%d %b · %I:%M %p")
        except (ValueError, TypeError):
            readable_time = str(timestamp)

        status_icon = {
            "SUCCESS": "🟢",
            "BLOCKED": "🟠",
            "FAILED": "🔴",
            "INFO": "🔵",
        }.get(str(status), "⚪")

        clean_details = str(details)
        if f"[Session: {st.session_state.session_id}]" in clean_details:
            clean_details = clean_details.replace(
                f"[Session: {st.session_state.session_id}]", ""
            ).strip(" |")

        st.markdown(
            f"""
            <div class="audit-row">
                <div class="audit-title">{status_icon} {action} <span>· {readable_time}</span></div>
                <div class="audit-details">{clean_details}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("🗃️ View full historical audit evidence", expanded=False):
        historical_rows = [
            {
                "Time": str(row[0]),
                "Action": str(row[1]),
                "Status": str(row[3]),
                "Details": str(row[2]),
            }
            for row in logs[::-1]
            if len(row) >= 4
        ]
        st.dataframe(
            historical_rows,
            width="stretch",
            hide_index=True,
            height=260,
        )
else:
    st.info("No audit events recorded yet.")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "SellPilot AI • Autonomous revenue workflow • "
    "Human confirmation + policy gate + verified payment + audit trail"
)
