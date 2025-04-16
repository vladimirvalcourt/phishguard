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

# Additional custom CSS for theme-independent styles
st.markdown("""
<style>
    .main > div {
        padding: 2rem;
        border-radius: 10px;
        background: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        padding: 0.5rem;
        background-color: #0d6efd;
        color: white;
    }
    .risk-high {
        color: #dc3545;
        font-weight: bold;
    }
    .risk-low {
        color: #198754;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Custom CSS for UI Polish
st.markdown(
    '''
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .css-1d391kg {padding-top: 2rem;}
        .phishguard-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .phishguard-logo {
            width: 48px;
            border-radius: 10px;
        }
        .phishguard-risk-card {
            background: #fffbe6;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px #f0f0f0;
            margin-bottom: 20px;
        }
    </style>
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
    
    # Check if user is logged in (DISABLED FOR TESTING)
    # if "token" not in st.session_state:
    #     st.warning("Please log in to analyze emails")
    #     st.info("Free tier: 5 scans/month | Pro tier: $9/month for unlimited scans")
    #     if st.button("Login / Register"):
    #         st.session_state["page"] = "login"
    #         st.experimental_rerun()
    #     return
    
    # Get user subscription status
    user = st.session_state.get("user", {})
    subscription = user.get("subscription", {})
    
    # Display subscription info
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Plan:** {subscription.get('plan', 'Free').capitalize()}")
    with col2:
        if subscription.get('plan') == "free":
            st.markdown(f"**Scans remaining:** {subscription.get('scans_remaining', 0)}/{subscription.get('scan_limit', 5)}")
        else:
            st.markdown("**Scans remaining:** Unlimited")
    
    st.markdown("""
    Hey there! 👋 Got an email that seems a bit off? Drop it below and I'll help you figure out 
    if it's real or trying to trick you. I'm like your personal email detective! 🔍
    """)
    
    # Check if user can perform a scan
    can_scan = subscription.get('scans_remaining', 0) > 0 or subscription.get('plan') == "pro"
    
    if not can_scan:
        # st.error("You've reached your monthly scan limit. Upgrade to Pro for unlimited scans!")
        # if st.button("Upgrade to Pro"):
        #     st.info("Pro upgrade coming soon!")
        # TODO: Re-enable this when Pro tier is available
        pass
    
    with st.form("email_analysis_form"):
        col1, col2 = st.columns(2)
        with col1:
            sender = st.text_input("📧 Who's it from?", placeholder="paste the sender's email here")
        with col2:
            subject = st.text_input("📝 What's it about?", placeholder="paste the subject line here")
        
        body = st.text_area(
            "📄 What does the email say?",
            placeholder="Copy and paste the whole email message here...",
            height=200
        )
        
        submitted = st.form_submit_button("Analyze Email")
        
        if submitted:
            if sender and subject and body:
                with st.spinner("🕵️ Looking for anything suspicious..."):
                    # Add token to request
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
                        
                        # Update user info after scan
                        st.session_state.pop("user", None)  # Force refresh of user info on next page load
            else:
                st.warning("Oops! Please fill in all the boxes above so I can help you check this email 😊")
    
    # Display some tips
    with st.expander("📚 Quick Tips to Spot Fake Emails"):
        st.markdown("""
        ### 🚩 Red Flags to Watch For:
        * Oops! Lots of typos and weird grammar
        * "URGENT!!!" or "Your account will be deleted!"
        * Email address looks almost right but not quite (like amaz0n.com)
        * Sketchy links that want you to "verify" something
        * Asking for passwords or credit card info (legit companies don't do this!)
        
        ### 🛡️ Stay Safe:
        * When in doubt, don't click!
        * Call the company directly if you're unsure
        * Trust your gut - if it feels weird, it probably is
        """)

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
        # Optionally add History button if you have a history page
        # if st.button("📜 History"):
        #     st.session_state["page"] = "history"
        #     st.experimental_rerun()

    # Display the appropriate page based on navigation state
    if st.session_state["page"] == "home":
        display_home_page()
    # elif st.session_state["page"] == "history":
    #     display_history_page()  # Only if you have this implemented
    # elif st.session_state["page"] == "login":
    #     display_login_page()
    # elif st.session_state["page"] == "profile":
    #     display_user_profile()
    # elif st.session_state["page"] == "subscription":
    #     display_subscription_page()

if __name__ == "__main__":
    main()