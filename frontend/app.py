import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import requests
import json
from datetime import datetime

# Import our custom modules
from frontend.auth import display_login_page, display_user_profile
from frontend.subscription import display_subscription_page
from frontend.themes.theme_selector import display_theme_selector, apply_selected_theme, initialize_theme_selector

# Configure the page
st.set_page_config(
    page_title="PhishGuard - AI Email Protection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize theme in session state before applying
initialize_theme_selector()
apply_selected_theme()

# Display theme selector in sidebar
display_theme_selector()

# --- Million Dollar SaaS UI Polish ---
st.markdown(
    '''
    <style>
        body {
            background: linear-gradient(135deg, #e0e7ff 0%, #f5f7fa 100%);
        }
        .main > div {
            padding: 2.5rem 2rem;
            border-radius: 18px;
            background: #fff;
            box-shadow: 0 8px 32px rgba(44, 62, 80, 0.07);
            max-width: 700px;
            margin: 2rem auto;
        }
        .phishguard-header {
            display: flex;
            align-items: center;
            gap: 1.25rem;
            margin-bottom: 2rem;
        }
        .phishguard-logo {
            width: 56px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(44, 62, 80, 0.10);
        }
        h1, h2, h3, .stMarkdown h1, .stMarkdown h2 {
            font-family: 'Inter', 'Quicksand', sans-serif !important;
            color: #1a237e;
            letter-spacing: -0.5px;
        }
        .stTextInput input, .stTextArea textarea {
            background: #f4f6fb;
            border-radius: 8px;
            border: 1.5px solid #c3dafe;
            font-size: 1.1rem;
            padding: 0.75rem;
            color: #1a237e;
        }
        .stButton>button {
            width: 100%;
            padding: 0.75rem;
            border-radius: 8px;
            background: linear-gradient(90deg, #6366f1 0%, #0ea5e9 100%);
            color: white;
            font-weight: 600;
            font-size: 1.1rem;
            box-shadow: 0 2px 8px rgba(44, 62, 80, 0.10);
            transition: background 0.2s;
        }
        .stButton>button:hover {
            background: linear-gradient(90deg, #0ea5e9 0%, #6366f1 100%);
        }
        .phishguard-risk-card {
            background: linear-gradient(90deg, #f3e8ff 0%, #e0f2fe 100%);
            padding: 28px 24px;
            border-radius: 16px;
            box-shadow: 0 4px 16px #e0e7ff;
            margin-bottom: 28px;
            border: 1.5px solid #c3dafe;
        }
        .risk-high {
            color: #e11d48;
            font-weight: bold;
            font-size: 1.15rem;
        }
        .risk-low {
            color: #059669;
            font-weight: bold;
            font-size: 1.15rem;
        }
        .stMetric {
            background: #f4f6fb;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        .stExpanderHeader {
            font-size: 1.1rem;
            font-weight: 600;
            color: #6366f1;
        }
        .stAlert, .stSuccess, .stError {
            border-radius: 10px;
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Quicksand:wght@400;600;700&display=swap" rel="stylesheet">
    ''',
    unsafe_allow_html=True
)

# API endpoint
API_URL = "http://localhost:8001"

def analyze_email(subject: str, body: str, sender: str, token: str = None) -> dict:
    """Send email content to API for analysis."""
    data = {
        "subject": subject,
        "body": body,
        "sender": sender
    }
    
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.post(
            f"{API_URL}/analyze",
            json=data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error during analysis: {str(e)}")
        return None

def display_results(analysis: dict):
    """Show analysis results in a friendly, easy-to-understand way."""
    # Give the overall verdict with a friendly tone
    if analysis["is_phishing"]:
        st.error("🚨 Hold up! This looks like a scam email!")
        st.markdown(f"<p class='risk-high'>{analysis['summary']}</p>", unsafe_allow_html=True)
    else:
        st.success("✅ Good news! This email checks out!")
        st.markdown(f"<p class='risk-low'>{analysis['summary']}</p>", unsafe_allow_html=True)
    
    # Show key findings in a simple way
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risk_level = "Yikes!" if analysis['confidence'] > 0.7 else "Hmm..." if analysis['confidence'] > 0.4 else "Looking good!"
        st.metric(
            label="Sketchy Score",
            value=f"{analysis['confidence']:.0%}",
            delta=risk_level
        )
    
    with col2:
        suspicious_count = len([url for url in analysis['suspicious_urls'] if url['is_suspicious']])
        st.metric(
            label="Fishy Links Found",
            value=suspicious_count
        )
    
    with col3:
        # Count how many GPT-detected factors are in the risk factors
        gpt_factors = [factor for factor in analysis['risk_factors'] if factor.startswith("GPT detected")]
        st.metric(
            label="Red Flags Spotted",
            value=len(analysis['risk_factors']),
            delta=f"{len(gpt_factors)} from AI" if gpt_factors else None
        )
    
    # Break down any suspicious links we found
    if analysis['suspicious_urls']:
        st.subheader("🔍 Let's Look at Those Links...")
        for url in analysis['suspicious_urls']:
            if url['is_suspicious']:
                with st.expander(f"🚫 Watch out for: {url['domain']}"):
                    st.markdown("**They want you to click:** " + url['url'])
                    st.markdown("**Why it's suspicious:**")
                    for reason in url['reasons']:
                        st.warning(f"⚠️ {reason}")
    
    # List out the warning signs we spotted
    if analysis["risk_factors"]:
        st.subheader("🚩 Here's What Caught My Eye...")
        for factor in analysis["risk_factors"]:
            st.warning(factor)
    
    # Add a learn more section
    with st.expander("📚 Learn More About Phishing"):
        st.markdown("""
        ### How to Protect Yourself
        1. **Never** share sensitive information through email
        2. **Check** the sender's email address carefully
        3. **Hover** over links before clicking them
        4. **Be wary** of urgent or threatening language
        5. **Look** for spelling and grammar mistakes
        
        ### Common Phishing Tactics
        - Creating a sense of urgency
        - Impersonating legitimate companies
        - Using similar-looking domains
        - Requesting sensitive information
        - Offering too-good-to-be-true deals
        """)

def display_home_page():
    st.title("🛡️ PhishGuard - Your Email Bodyguard")
    st.subheader("Let's Check If That Email Is Legit!")
    st.markdown("""
    <div style='font-size:1.15rem; color:#475569; margin-bottom:2.5rem;'>
        Paste a suspicious email below. PhishGuard will analyze it for <b>phishing risks</b> and highlight any red flags.<br>
        <span style='color:#6366f1;'>Your privacy is protected – we never store your emails.</span>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("email_analysis_form"):
        col1, col2 = st.columns(2)
        with col1:
            sender = st.text_input("📧 Sender Email", placeholder="e.g. ceo@company.com")
        with col2:
            subject = st.text_input("📝 Subject", placeholder="e.g. Urgent: Account Verification Needed")
        body = st.text_area(
            "📄 Email Content",
            placeholder="Paste the full email message here...",
            height=220
        )
        submitted = st.form_submit_button("🔍 Analyze Email")
        if submitted:
            if sender and subject and body:
                with st.spinner("🕵️‍♂️ Scanning for phishing signals..."):
                    analysis = analyze_email(subject, body, sender, st.session_state.get("token", None))
                    if analysis:
                        st.markdown(
                            f"""
                            <div class='phishguard-risk-card'>
                                <h3 style='color:#d9534f;'>Risk Score: {analysis.get('confidence', 'N/A')}</h3>
                                <p>{analysis.get('summary', '')}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        display_results(analysis)
                        st.balloons()
                        st.success("Analysis complete! Stay safe out there 🚀")
            else:
                st.warning("Please fill in <b>all</b> fields above to analyze the email.", unsafe_allow_html=True)
    
    with st.expander("📚 Quick Tips to Spot Fake Emails"):
        st.markdown("""
        <div style='font-size:1.08rem;'>
        <b>🚩 Red Flags:</b><br>
        • Typos, weird grammar, or urgent threats<br>
        • Sender's address looks off (e.g. amaz0n.com)<br>
        • Links asking you to verify info<br>
        • Requests for passwords or payment<br>
        </div>
        <div style='font-size:1.08rem; margin-top:0.5rem;'>
        <b>🛡️ Pro Tips:</b><br>
        • Don't click suspicious links<br>
        • Call the company if unsure<br>
        • Trust your instincts – if it feels weird, it probably is
        </div>
        """, unsafe_allow_html=True)

def main():
    # Initialize session state for navigation
    if "page" not in st.session_state:
        st.session_state["page"] = "home"
    
    # Create sidebar for navigation
    with st.sidebar:
        st.markdown("""
        <div class='phishguard-header'>
            <img src='https://raw.githubusercontent.com/vladimirvalcourt/phishguard/main/frontend/dashboard/phishguard-logo.png' class='phishguard-logo' alt='PhishGuard Logo' />
            <div>
                <h2 style='margin-bottom:0;'>PhishGuard</h2>
                <span style='font-size:0.9rem;color:#888;'>AI-powered email security</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        st.title("Navigation")
        if st.button("🏠 Home"):
            st.session_state["page"] = "home"
            st.experimental_rerun()

    # Display the appropriate page based on navigation state
    if st.session_state["page"] == "home":
        display_home_page()

if __name__ == "__main__":
    main()