"""Payment History & Failure Analysis panel.

Self-contained: reads only the audit log rows and the blocked-event count
already computed by the caller (app.py's Merchant Command Center section)
and renders its own metrics, table, and failure-reason chart. Moved out of
app.py purely for readability — behavior is unchanged.
"""

import re

import streamlit as st


def render_payment_history(command_logs, blocked_count):
    st.markdown("### 💳 Payment History & Failure Analysis")
    st.caption(
        "Every payment attempt recorded by the backend — success, decline, and "
        "policy block — with the reason captured directly from the audit trail. "
        "This is what a merchant (or a judge) would check after a customer says "
        "'my payment didn't go through.'"
    )

    def _extract_order_id(details_text):
        for pattern in (
            r"Order ID:\s*([A-Za-z0-9_\-]+)",
            r"for order\s+([A-Za-z0-9_\-]+)",
            r"\b(order_[A-Za-z0-9]+)\b",
        ):
            match = re.search(pattern, details_text)
            if match:
                return match.group(1).strip().rstrip(",")
        return None


    def _extract_amount(details_text):
        match = re.search(r"₹\s*([0-9,]+(?:\.[0-9]+)?)", details_text)
        if not match:
            return None
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return None


    def build_payment_history(logs):
        """One row per Razorpay order, latest status wins. Logs are newest-first
        (see database/audit.get_audit_logs), so the FIRST time we see an order_id
        for a given action family is its most recent state."""
        orders = {}
        unlinked_failures = []

        for row in logs:
            if len(row) < 4:
                continue
            timestamp, action, details, status = row
            action = str(action)
            details = str(details)
            status = str(status)

            order_id = _extract_order_id(details)

            if action == "Razorpay Order Created":
                orders.setdefault(order_id, {}).setdefault("order_id", order_id)
                orders[order_id].setdefault("created_at", timestamp)
                orders[order_id].setdefault("amount", _extract_amount(details))
                orders[order_id].setdefault("session", _session_from_details(details))
                orders[order_id].setdefault("outcome", "Awaiting payment")
                orders[order_id].setdefault("reason", "Order created, payment not yet completed.")
                orders[order_id].setdefault("last_update", timestamp)

            elif action in ("Payment Verified", "Order Completed") and order_id:
                entry = orders.setdefault(order_id, {"order_id": order_id})
                if "outcome" not in entry or entry.get("outcome") != "Verified":
                    entry["outcome"] = "Verified"
                    entry["reason"] = "Signature, amount, and capture status all confirmed."
                    entry["last_update"] = timestamp

            elif action == "Payment Failed" and order_id:
                entry = orders.setdefault(order_id, {"order_id": order_id})
                entry.setdefault("outcome", "Failed")
                entry.setdefault("reason", "Payment verification failed (see backend response).")
                entry.setdefault("last_update", timestamp)

            elif action == "Payment Verification Failed":
                reason = details
                if order_id:
                    entry = orders.setdefault(order_id, {"order_id": order_id})
                    entry.setdefault("outcome", "Failed")
                    entry.setdefault("reason", reason)
                    entry.setdefault("last_update", timestamp)
                else:
                    unlinked_failures.append({"time": timestamp, "reason": reason})

            elif action == "Razorpay Order Creation Failed":
                unlinked_failures.append({"time": timestamp, "reason": details})

            elif action == "Payment Service Error":
                unlinked_failures.append({"time": timestamp, "reason": details})

            elif action == "Payment Status Check Failed" and order_id:
                entry = orders.setdefault(order_id, {"order_id": order_id})
                entry.setdefault("outcome", "Status check error")
                entry.setdefault("reason", details)
                entry.setdefault("last_update", timestamp)

        return list(orders.values()), unlinked_failures


    def _session_from_details(details_text):
        if "[Session:" in details_text:
            try:
                return details_text.split("[Session:", 1)[1].split("]", 1)[0].strip()
            except (IndexError, AttributeError):
                return ""
        return ""


    payment_orders, payment_unlinked_failures = build_payment_history(command_logs)

    total_payment_orders = len(payment_orders)
    verified_orders = [o for o in payment_orders if o.get("outcome") == "Verified"]
    failed_orders = [o for o in payment_orders if o.get("outcome") in ("Failed", "Status check error")]
    pending_orders = [o for o in payment_orders if o.get("outcome") == "Awaiting payment"]

    payment_success_rate = (
        len(verified_orders) / total_payment_orders * 100 if total_payment_orders else 0
    )
    payment_failure_rate = (
        len(failed_orders) / total_payment_orders * 100 if total_payment_orders else 0
    )

    ph1, ph2, ph3, ph4 = st.columns(4)
    with ph1:
        st.metric("Payment Attempts", f"{total_payment_orders}")
    with ph2:
        st.metric("Payment Success Rate", f"{payment_success_rate:.0f}%")
    with ph3:
        st.metric("Failed / Unresolved", f"{len(failed_orders)}")
    with ph4:
        st.metric("Blocked Before Payment", f"{blocked_count}")

    if payment_orders:
        history_rows = []
        for order in sorted(payment_orders, key=lambda o: o.get("last_update", o.get("created_at", "")), reverse=True):
            outcome = order.get("outcome", "Unknown")
            badge = {
                "Verified": "✅ Verified",
                "Failed": "❌ Failed",
                "Status check error": "⚠️ Error",
                "Awaiting payment": "⏳ Awaiting payment",
            }.get(outcome, outcome)

            history_rows.append(
                {
                    "Order ID": order.get("order_id", "—"),
                    "Status": badge,
                    "Amount": f"₹{order['amount']:,.0f}" if order.get("amount") else "—",
                    "Session": order.get("session", "—"),
                    "Reason": order.get("reason", "—"),
                    "Created": order.get("created_at", "—"),
                }
            )

        st.dataframe(history_rows, width="stretch", hide_index=True, height=260)

        if failed_orders or payment_unlinked_failures:
            st.markdown("##### 🔍 Failure Reason Breakdown")

            reason_bucket = {}

            def _bucket(reason_text):
                text = str(reason_text).lower()
                if "signature" in text:
                    return "Invalid/tampered signature"
                if "amount" in text:
                    return "Amount mismatch"
                if "captured" in text or "status" in text:
                    return "Payment not captured"
                if "connect" in text or "timeout" in text or "cannot connect" in text:
                    return "Backend/network error"
                if "unknown or expired" in text:
                    return "Unknown or expired order"
                return "Other"

            for order in failed_orders:
                key = _bucket(order.get("reason", ""))
                reason_bucket[key] = reason_bucket.get(key, 0) + 1
            for item in payment_unlinked_failures:
                key = _bucket(item.get("reason", ""))
                reason_bucket[key] = reason_bucket.get(key, 0) + 1

            if reason_bucket:
                st.bar_chart(reason_bucket)

            with st.expander("View raw failure messages"):
                for order in failed_orders:
                    st.write(f"**{order.get('order_id', '—')}** — {order.get('reason', '—')}")
                for item in payment_unlinked_failures:
                    st.write(f"**{item.get('time', '—')}** — {item.get('reason', '—')}")
    else:
        st.info("No payment attempts recorded yet. Complete a checkout above to populate this history.")
