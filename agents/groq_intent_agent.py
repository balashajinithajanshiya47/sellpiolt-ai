import os
import json

from groq import Groq


def _get_api_key():
    """Read Groq credentials without hard-coding them into the project."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    if key:
        return key

    try:
        import streamlit as st
        return str(st.secrets.get("GROQ_API_KEY", "")).strip()
    except Exception:
        return ""


def is_llm_configured():
    """True if a Groq API key is available, i.e. intent analysis will use the
    real LLM. False means the deterministic keyword fallback is active.
    Used by the UI so the AI-engine status is never silently hidden."""
    return bool(_get_api_key())


def _get_client():
    key = _get_api_key()
    if not key:
        return None
    return Groq(api_key=key)


# --------------------------------------------------
# MODEL
# --------------------------------------------------

MODEL_NAME = "openai/gpt-oss-120b"


# --------------------------------------------------
# CUSTOMER INTENT AGENT
# --------------------------------------------------

def analyze_customer_intent(
    message,
    conversation_history=None
):
    """
    Analyze the customer's current message while
    considering previous conversation context.

    Returns:
        category
        budget
        preference
        use_case
        summary
    """

    if conversation_history is None:
        conversation_history = []


    # --------------------------------------------------
    # BUILD CONVERSATION CONTEXT
    # --------------------------------------------------

    history_text = ""

    for item in conversation_history:

        role = item.get("role", "user")
        content = item.get("content", "")

        history_text += (
            f"{role.upper()}: {content}\n"
        )


    # --------------------------------------------------
    # SYSTEM PROMPT
    # --------------------------------------------------

    system_prompt = """
You are the Customer Intent Agent for SellPilot AI.

Your job is to understand a customer's shopping request.

Extract:

1. category
2. budget
3. preference
4. use_case
5. summary

Supported categories may include:

- earbuds
- laptop
- phone
- watch
- shoes
- bag
- keyboard
- mouse
- general

Supported preferences may include:

- battery
- rating
- price
- performance
- quality
- lightweight
- premium
- camera

IMPORTANT:

The customer may continue the conversation over multiple messages.

Use previous conversation context when available.

If the customer says:

"Actually I mostly use them at the gym"

and the previous message was:

"I need earbuds under 3000"

you should preserve:

category = earbuds
budget = 3000

and update:

use_case = gym use

If the customer says:

"Show me something cheaper"

preserve the previous category and use case,
but update the preference toward price.

Do not invent information that the customer did not provide.

Return ONLY valid JSON.

Example:

{
    "category": "earbuds",
    "budget": 3000,
    "preference": "battery",
    "use_case": "gym use",
    "summary": "Looking for wireless earbuds under 3000 for gym use with good battery."
}
"""


    # --------------------------------------------------
    # USER PROMPT
    # --------------------------------------------------

    user_prompt = f"""
Previous conversation:

{history_text}

Current customer message:

{message}

Analyze the customer's complete shopping intent.

Return ONLY JSON.
"""


    # --------------------------------------------------
    # GROQ REQUEST
    # --------------------------------------------------

    client = _get_client()

    if client is None:
        # Local/demo fallback: keeps the UI usable when GROQ_API_KEY is not
        # configured. When a key is present, Groq remains the primary engine.
        text = f"{history_text}\n{message}".lower()

        category = "general"
        category_words = {
            "earbuds": ["earbud", "earphone", "headphone"],
            "laptop": ["laptop", "notebook", "macbook"],
            "phone": ["phone", "mobile", "smartphone", "iphone", "android"],
            "watch": ["watch", "smartwatch"],
            "shoes": ["shoe", "sneaker"],
            "bag": ["bag", "backpack"],
            "keyboard": ["keyboard"],
            "mouse": ["mouse", "mice"],
        }
        for cat, words in category_words.items():
            if any(word in text for word in words):
                category = cat
                break

        import re
        amounts = re.findall(r"(?:₹|rs\.?\s*)?\s*(\d{3,6})(?:\s*(?:k|thousand))?", text)
        budget = None
        if amounts:
            try:
                budget = float(amounts[-1])
                if "k" in text and budget < 100:
                    budget *= 1000
            except ValueError:
                budget = None

        preference = "rating"
        if any(x in text for x in ["battery", "battery life", "long battery"]):
            preference = "battery"
        elif any(x in text for x in ["cheap", "cheaper", "lowest price", "budget", "affordable"]):
            preference = "price"

        use_case = ""
        for candidate in ["gym", "student", "office", "gaming", "travel", "running", "fitness"]:
            if candidate in text:
                use_case = candidate + " use"
                break

        if budget is None:
            budget = None

        summary = (
            f"Looking for {category}"
            + (f" under ₹{budget:,.0f}" if budget is not None else "")
            + (f" for {use_case}" if use_case else "")
            + f" with {preference} priority."
        )
        return {
            "category": category,
            "budget": budget,
            "preference": preference,
            "use_case": use_case,
            "summary": summary,
        }

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=500,
    )

    # --------------------------------------------------
    # EXTRACT RESPONSE
    # --------------------------------------------------

    content = (
        response.choices[0]
        .message
        .content
        .strip()
    )


    # --------------------------------------------------
    # CLEAN MARKDOWN JSON
    # --------------------------------------------------

    if content.startswith("```"):

        content = (
            content
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )


    # --------------------------------------------------
    # PARSE JSON
    # --------------------------------------------------

    try:

        result = json.loads(content)

    except json.JSONDecodeError:

        raise ValueError(
            "Groq returned invalid JSON: "
            + content
        )


    # --------------------------------------------------
    # NORMALIZE RESULT
    # --------------------------------------------------

    category = result.get(
        "category",
        "general"
    )

    budget = result.get(
        "budget"
    )

    preference = result.get(
        "preference",
        "rating"
    )

    use_case = result.get(
        "use_case",
        ""
    )

    summary = result.get(
        "summary",
        ""
    )


    # --------------------------------------------------
    # BUDGET NORMALIZATION
    # --------------------------------------------------

    if budget is not None:

        try:

            budget = float(budget)

        except (
            TypeError,
            ValueError
        ):

            budget = None


    # --------------------------------------------------
    # FINAL INTENT
    # --------------------------------------------------

    return {

        "category": category,

        "budget": budget,

        "preference": preference,

        "use_case": use_case,

        "summary": summary

    }