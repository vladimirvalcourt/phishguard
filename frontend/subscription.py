import streamlit as st
import requests
import json
from datetime import datetime
from shared.logger import logger

# API endpoint
API_URL = "https://phishguard-mcuv.onrender.com"

def get_subscription_plans():
    """Get available subscription plans from API"""
    try:
        response = requests.get(
            f"{API_URL}/subscription/plans",
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()["plans"]
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching subscription plans: {str(e)}")
        logger.error(f"Subscription API error: {str(e)}")
        return None

def get_user_subscription(token):
    """Get user's subscription status"""
    try:
        response = requests.get(
            f"{API_URL}/subscription/status",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        response.raise_for_status()
        return response.json()["subscription"]
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching subscription status: {str(e)}")
        logger.error(f"Subscription API error: {str(e)}")
        return None

def create_checkout_session(token, price_id, success_url, cancel_url):
    """Create a Stripe checkout session"""
    try:
        response = requests.post(
            f"{API_URL}/subscription/checkout",
            json={
                "price_id": price_id,
                "success_url": success_url,
                "cancel_url": cancel_url
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating checkout session: {str(e)}")
        logger.error(f"Subscription API error: {str(e)}")
        return None

def cancel_subscription(token):
    """Cancel user's subscription"""
    try:
        response = requests.post(
            f"{API_URL}/subscription/cancel",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error canceling subscription: {str(e)}")
        logger.error(f"Subscription API error: {str(e)}")
        return None

def display_subscription_page():
    """Display the subscription page"""
    st.title("🛡️ PhishGuard Subscription Plans")
    st.markdown("""
        <style>
        .pricing-card {
            border: 1px solid #e6e6e6;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
        }
        .pricing-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transform: translateY(-5px);
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Check if user is logged in
    if "token" not in st.session_state:
        st.warning("Please log in to manage your subscription")
        return
    
    # Get user's subscription status
    subscription = get_user_subscription(st.session_state["token"])
    if not subscription:
        st.error("Unable to fetch subscription information")
        return
    
    # Get available plans
    plans = get_subscription_plans()
    if not plans:
        st.error("Unable to fetch subscription plans")
        return
    
    # Display current subscription
    st.subheader("Your Current Plan")
    
    current_plan = subscription["plan"]
    plan_name = plans[current_plan]["name"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Current Plan",
            value=plan_name
        )
    
    with col2:
        if current_plan == "free":
            st.metric(
                label="Scans Remaining",
                value=subscription["scans_remaining"]
            )
        else:
            st.metric(
                label="Scans Available",
                value="Unlimited"
            )
    
    # Display plan comparison
    st.subheader("Available Plans")
    
    # Create columns for each plan
    cols = st.columns(len(plans))
    
    # Display each plan
    for i, (plan_id, plan) in enumerate(plans.items()):
        with cols[i]:
            st.markdown(f"### {plan['name']}")
            st.markdown(f"**${plan['price']}/month**")
            
            # List features
            for feature in plan["features"]:
                st.markdown(f"✅ {feature}")
            
            # Show appropriate button based on current subscription
            if plan_id == current_plan:
                st.success("Current Plan")
            elif plan_id == "free":
                st.info("Free Plan")
            else:
                # Subscribe button for paid plans
                if st.button(f"Upgrade to {plan['name']}", key=f"upgrade_{plan_id}", type="primary"):
                    # Create checkout session
                    checkout = create_checkout_session(
                        token=st.session_state["token"],
                        price_id=plan['stripe_price_id'],
                        success_url="http://localhost:8501/subscription?success=true",
                        cancel_url="http://localhost:8501/subscription?canceled=true"
                    )
                    
                    if checkout and "checkout_url" in checkout:
                        # Redirect to Stripe checkout
                        st.markdown(f"""<meta http-equiv="refresh" content="0;URL='{checkout['checkout_url']}'" />""", unsafe_allow_html=True)
    
    # Cancellation section (only show for paid plans)
    if current_plan != "free":
        st.subheader("Cancel Subscription")
        st.warning("Warning: Canceling your subscription will downgrade you to the Free plan at the end of your billing period.")
        
        if st.button("Cancel Subscription"):
            result = cancel_subscription(st.session_state["token"])
            if result:
                st.success(result["message"])
                st.experimental_rerun()

if __name__ == "__main__":
    display_subscription_page()