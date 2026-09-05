"""SellPilot AI — visual theme.

Pulled out of app.py so the main file reads as application logic rather
than a mix of logic and a 220-line inline stylesheet. Purely cosmetic:
moving this changes nothing about how the app behaves, only how the
source is organized. Import and call inject_theme() once, near the top
of app.py, before any UI is rendered.
"""

import streamlit as st


def inject_theme():
    st.markdown(
        """
    <style>
    .stApp {
        background:
            radial-gradient(
                circle at 90% 0%,
                rgba(76, 29, 149, 0.16),
                transparent 28%
            ),
            radial-gradient(
                circle at 0% 0%,
                rgba(14, 116, 144, 0.12),
                transparent 25%
            ),
            #f6f8fc;
    }

    .block-container {
        /* Use the full browser width instead of constraining the app to a
           narrow centered column. This keeps all existing sections intact
           while making the dashboard much easier to read on wide screens. */
        max-width: none !important;
        width: 100% !important;
        padding-top: 1.25rem;
        padding-bottom: 4rem;
        padding-left: clamp(0.75rem, 2vw, 2rem);
        padding-right: clamp(0.75rem, 2vw, 2rem);
    }

    [data-testid="stAppViewContainer"] .main .block-container {
        max-width: none !important;
    }

    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.92);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 0.8rem;
        border-radius: 14px;
    }

    .hero-native {
        padding: 1.5rem 1.7rem;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.08);
        background:
            linear-gradient(
                135deg,
                rgba(255,255,255,0.96),
                rgba(239,246,255,0.96)
            );
        margin-bottom: 1rem;
    }

    .kicker {
        color: #2563eb;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    .status-box {
        padding: 0.9rem 1rem;
        border-radius: 14px;
        background: rgba(255,255,255,0.92);
        border: 1px solid rgba(255,255,255,0.08);
    }

    .product-box {
        padding: 1rem;
        border-radius: 16px;
        background: rgba(255,255,255,0.94);
        border: 1px solid rgba(255,255,255,0.08);
    }

    .upsell-box {
        padding: 1rem;
        border-radius: 16px;
        background:
            linear-gradient(
                145deg,
                rgba(255,247,237,0.98),
                rgba(255,251,235,0.96)
            );
        border: 1px solid rgba(245,158,11,0.25);
    }

    .cart-box {
        padding: 1rem;
        border-radius: 16px;
        background: rgba(236,253,245,0.96);
        border: 1px solid rgba(34,197,94,0.20);
    }

    .small-muted {
        color: #64748b;
        font-size: 0.8rem;
    }

    .pipeline-step {
        text-align: center;
        padding: 0.75rem 0.35rem;
        border-radius: 13px;
        background: rgba(255,255,255,0.94);
        border: 1px solid rgba(255,255,255,0.07);
        min-height: 92px;
    }

    .pipeline-icon {
        font-size: 1.35rem;
    }

    .pipeline-name {
        font-weight: 750;
        font-size: 0.8rem;
    }

    .pipeline-desc {
        color: #64748b;
        font-size: 0.66rem;
    }

    div[data-testid="stButton"] > button {
        border-radius: 10px;
        min-height: 42px;
    }

    .audit-row {
        padding: 9px 12px;
        margin: 5px 0;
        border-radius: 10px;
        background: rgba(255,255,255,0.92);
        border: 1px solid rgba(255,255,255,0.07);
    }

    .audit-title {
        font-weight: 700;
        font-size: 0.86rem;
    }

    .audit-title span {
        opacity: 0.48;
        font-weight: 400;
    }

    .audit-details {
        margin-top: 2px;
        font-size: 0.76rem;
        opacity: 0.68;
        line-height: 1.35;
    }

    .customer-input-card {
        padding: 1.1rem 1.25rem 1rem 1.25rem;
        border-radius: 18px;
        background: linear-gradient(145deg, #ffffff, #eef6ff);
        border: 1px solid #bfdbfe;
        box-shadow: 0 12px 35px rgba(30,64,175,0.10);
        margin: 1.1rem 0 1.25rem 0;
    }

    .customer-input-label {
        color: #2563eb;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.15rem;
    }

    .customer-input-help {
        color: #64748b;
        font-size: 0.78rem;
        margin-bottom: 0.45rem;
    }

    .stTextInput input {
        border-radius: 12px !important;
        border: 1px solid #cbd5e1 !important;
        background: #ffffff !important;
        color: #0f172a !important;
        min-height: 46px !important;
        font-size: 1rem !important;
    }

    div[data-testid="stFormSubmitButton"] > button {
        border-radius: 12px !important;
        min-height: 46px !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #2563eb, #7c3aed) !important;
        color: white !important;
        border: 0 !important;
    }

    .hero-title {
        font-size: clamp(2rem, 4vw, 3.25rem);
        font-weight: 900;
        letter-spacing: -0.04em;
        color: #0f172a;
        margin-bottom: 0.15rem;
    }

    .hero-subtitle {
        color: #475569;
        font-size: 1.05rem;
        margin-bottom: 0.25rem;
    }

    .demo-card {
        border: 1px solid #dbeafe;
        background: linear-gradient(135deg,#eff6ff,#faf5ff);
        border-radius: 16px;
        padding: 0.85rem 1rem;
    }

    .explain-card {
        border: 1px solid #e2e8f0;
        background: #ffffff;
        border-radius: 14px;
        padding: 0.9rem 1rem;
    }
    </style>
        """,
        unsafe_allow_html=True,
    )
