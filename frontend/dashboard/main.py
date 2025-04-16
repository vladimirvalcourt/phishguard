import streamlit as st
import pandas as pd
import requests
import os
from frontend.auth import display_login_page
from frontend.subscription import display_subscription_page
from frontend.themes.theme_selector import display_theme_selector

BACKEND_URL = os.getenv("PHISHGUARD_BACKEND_URL", "http://localhost:8000")

# --- Sidebar Navigation ---
st.sidebar.image("/Volumes/Vladhard/PhishGuard/frontend/themes/phishguard_logo.png", width=150)
st.sidebar.title("PhishGuard")
st.sidebar.markdown("## Navigation")
nav = st.sidebar.radio(
    "Go to",
    ("Dashboard", "History", "Subscription", "Support")
)

# --- Top Bar ---
st.markdown(
    """
    <div style='display: flex; justify-content: space-between; align-items: center;'>
        <h2 style='color:#204080;'>Dashboard</h2>
        <div>
            <span style='margin-right:20px;'>🔔</span>
            <span>👤 User</span>
        </div>
    </div>
    <hr>
    """,
    unsafe_allow_html=True
)

# --- Main Dashboard Content ---
if nav == "Dashboard":
    st.subheader("Analyze a Suspicious Email")
    uploaded_file = st.file_uploader("Upload an email file (.eml, .msg, .txt)", type=["eml", "msg", "txt"])
    analysis_result = None
    if uploaded_file is not None:
        files = {"email_file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        try:
            response = requests.post(f"{BACKEND_URL}/phishing/analyze", files=files)
            if response.status_code == 200:
                analysis_result = response.json()
                st.success("Analysis complete!")
            else:
                st.error(f"Analysis failed: {response.text}")
        except Exception as e:
            st.error(f"Could not connect to backend: {e}")

    if analysis_result:
        st.markdown(f"**Risk Score:** {analysis_result.get('risk_score', 'N/A')}")
        st.markdown(f"**Summary:** {analysis_result.get('summary', 'No summary')}")

# --- Subscription Section ---
elif nav == "Subscription":
    st.header("Subscription & Billing")
    st.markdown("""
    **Current Plan:** Free (MVP)
    # Upgrade to Pro for unlimited scans and advanced features. (REMOVED for MVP)
    """)
    # if st.button("Upgrade to Pro (Stripe Test)"):
    #     st.markdown("Redirecting to Stripe checkout...")
    #     st.experimental_set_query_params(redirect="stripe")
    #     st.markdown("<meta http-equiv='refresh' content='0; url=https://buy.stripe.com/test_4gwcOq9jL1qI4jC4gg' />", unsafe_allow_html=True)
    st.info("For demo purposes, this uses Stripe's test environment.")

# --- Recent Analyses Table ---
elif nav == "History":
    st.subheader("Recent Analyses")
    try:
        resp = requests.get(f"{BACKEND_URL}/phishing/history?limit=5")
        if resp.status_code == 200:
            data = resp.json().get("history", [])
        else:
            data = []
    except Exception:
        data = []
    if not data:
        # Fallback example data
        data = [
            {"Date": "2025-04-15", "Sender": "phisher@bad.com", "Subject": "Urgent action required!", "Risk Score": 95, "Report": "View"},
            {"Date": "2025-04-14", "Sender": "boss@company.com", "Subject": "Monthly update", "Risk Score": 5, "Report": "View"},
        ]
    df = pd.DataFrame(data)
    st.table(df)

# --- Feedback & Accessibility ---
st.info("Need help? Visit the Support page or contact us.")

# --- Responsive and accessible design is built-in with Streamlit ---
