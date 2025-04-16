# Payment module for PhishGuard using Stripe
import os
import stripe
from datetime import datetime
from typing import Dict, Optional, Any
from dotenv import load_dotenv
from shared.logger import logger

# Import database functions
from backend.database import (
    get_user_by_id, get_user_subscription,
    create_subscription, update_subscription
)

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Subscription plans with Stripe price IDs
PLANS = {
    "free": {
        "name": "Free Tier",
        "price": 0,
        "scan_limit": 5,  # 5 scans per month
        "stripe_price_id": None,  # Free plan has no Stripe price ID
        "features": ["Basic phishing detection", "Email analysis reports"]
    },
    "pro": {
        "name": "Pro Tier",
        "price": 9,  # $9 per month
        "scan_limit": float('inf'),  # Unlimited scans
        "stripe_price_id": "price_H5ggYwtDq9DGrp",  # Replace with your actual Stripe price ID
        "features": [
            "Advanced phishing detection", 
            "Unlimited email scans", 
            "Priority GPT analysis", 
            "Detailed threat reports",
            "24/7 Email Support"
        ]
    }
}

# Stripe API functions
def create_customer(email: str, name: str = None) -> Dict:
    """Create a new customer in Stripe"""
    try:
        customer = stripe.Customer.create(
            email=email,
            name=name
        )
        return {
            "success": True,
            "customer_id": customer.id
        }
    except Exception as e:
        logger.error(f"Error creating Stripe customer: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def create_checkout_session(customer_id: str, price_id: str, success_url: str, cancel_url: str) -> Dict:
    """Create a Stripe checkout session for subscription"""
    try:
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return {
            "success": True,
            "session_id": checkout_session.id,
            "checkout_url": checkout_session.url
        }
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def cancel_subscription(subscription_id: str) -> Dict:
    """Cancel a Stripe subscription"""
    try:
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        return {
            "success": True,
            "subscription": subscription
        }
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def handle_webhook_event(payload: bytes, signature: str) -> Dict:
    """Handle Stripe webhook events"""
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, STRIPE_WEBHOOK_SECRET
        )
        
        # Handle the event based on its type
        if event.type == "checkout.session.completed":
            # Payment was successful, activate the subscription
            session = event.data.object
            handle_successful_payment(session)
        
        elif event.type == "customer.subscription.updated":
            # Subscription was updated
            subscription = event.data.object
            handle_subscription_updated(subscription)
        
        elif event.type == "customer.subscription.deleted":
            # Subscription was canceled or expired
            subscription = event.data.object
            handle_subscription_canceled(subscription)
        
        return {"success": True}
    
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        # TODO: Optionally notify admin or retry event
        return {"success": False, "error": str(e)}

# Webhook event handlers
def handle_successful_payment(session: Dict) -> None:
    """Handle successful payment and activate subscription"""
    # Extract customer and subscription IDs
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    
    if not customer_id or not subscription_id:
        logger.error("Missing customer or subscription ID in session")
        return
    
    # Get subscription details from Stripe
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Get the user ID from metadata or lookup by customer ID
        # This would require storing the user_id in the checkout session metadata
        user_id = session.get("client_reference_id")
        
        if not user_id:
            logger.error("Missing user ID in session metadata")
            return
        
        # Create subscription record in database
        create_subscription(
            user_id=int(user_id),
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            plan_type="pro",  # Assuming Pro plan for now
            status=subscription.status,
            period_start=datetime.fromtimestamp(subscription.current_period_start),
            period_end=datetime.fromtimestamp(subscription.current_period_end)
        )
        
        logger.info(f"Subscription activated for user {user_id}")
    
    except Exception as e:
        logger.error(f"Error activating subscription: {str(e)}")

def handle_subscription_updated(subscription: Dict) -> None:
    """Handle subscription update events"""
    subscription_id = subscription.get("id")
    status = subscription.get("status")
    
    if not subscription_id or not status:
        logger.error("Missing subscription ID or status")
        return
    # Update subscription in database by Stripe ID
    try:
        update_subscription(
            stripe_subscription_id=subscription_id,
            status=status
        )
        logger.info(f"Subscription {subscription_id} updated to status {status}")
    except Exception as e:
        logger.error(f"Error updating subscription in DB: {str(e)}")

def handle_subscription_canceled(subscription: Dict) -> None:
    """Handle subscription cancellation events"""
    subscription_id = subscription.get("id")
    
    if not subscription_id:
        logger.error("Missing subscription ID")
        return
    # Update subscription in database by Stripe ID
    try:
        update_subscription(
            stripe_subscription_id=subscription_id,
            status="canceled"
        )
        logger.info(f"Subscription {subscription_id} canceled")
    except Exception as e:
        logger.error(f"Error updating subscription in DB: {str(e)}")

# User subscription functions
def check_user_subscription_status(user_id: int) -> Dict:
    """Check a user's subscription status"""
    # Get user from database
    user = get_user_by_id(user_id)
    if not user:
        return {
            "plan": "none",
            "status": "inactive",
            "scan_limit": 0,
            "scans_used": 0,
            "scans_remaining": 0
        }
    
    # Get subscription from database
    subscription = get_user_subscription(user_id)
    
    # Default to free tier if no subscription
    if not subscription or subscription["status"] != "active":
        plan_type = "free"
        status = "active"
    else:
        plan_type = subscription["plan_type"]
        status = subscription["status"]
    
    # Get plan details
    plan = PLANS.get(plan_type, PLANS["free"])
    
    # Get scan count
    scans_used = user["scan_count"]
    
    # Calculate scans remaining
    if plan_type == "pro":
        scans_remaining = float('inf')
    else:
        scans_remaining = max(0, plan["scan_limit"] - scans_used)
    
    return {
        "plan": plan_type,
        "status": status,
        "scan_limit": plan["scan_limit"],
        "scans_used": scans_used,
        "scans_remaining": scans_remaining,
        "features": plan["features"]
    }

def can_user_perform_scan(user_id: int) -> bool:
    """Check if a user can perform a scan based on their subscription"""
    subscription_status = check_user_subscription_status(user_id)
    
    # If user has remaining scans or is on pro plan, they can scan
    return subscription_status["scans_remaining"] > 0 or subscription_status["plan"] == "pro"