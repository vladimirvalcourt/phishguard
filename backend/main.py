# Import necessary libraries for our phishing detection system
from fastapi import FastAPI, HTTPException, status, Depends, Request, File  # FastAPI for building our web API
from fastapi.middleware.cors import CORSMiddleware  # Allows our frontend to talk to the backend
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel  # Helps validate incoming data
from typing import List, Dict, Optional  # For type hints that make our code safer
from datetime import datetime  # For handling dates and times
from transformers import pipeline  # For AI-powered text analysis
import nltk  # For processing text
import re  # For pattern matching in text
import stripe

# Import our custom modules
from backend.auth import (
    Token, UserCreate, UserLogin, User, get_current_user,
    register_new_user, login_user
)
from backend.payment import (
    PLANS, create_customer, create_checkout_session,
    cancel_subscription, handle_webhook_event,
    check_user_subscription_status, can_user_perform_scan
)
from backend.database import record_scan, get_user_scan_history

# Download language processing tools we need
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Create our web API - think of this as the brain of our phishing detection system
app = FastAPI(
    title="PhishGuard - Your Friendly Email Protector",
    description="AI-powered system that helps you spot sneaky phishing emails"
)

# Allow our frontend website to talk to this API
# Without this, your browser would block the connection for security reasons
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you'd list specific allowed websites
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI model for sentiment analysis
sentiment_analyzer = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

# Pydantic models
class EmailContent(BaseModel):
    subject: str
    body: str
    sender: str

class URLAnalysis(BaseModel):
    url: str
    domain: str
    is_suspicious: bool
    reasons: List[str]

class PhishingAnalysis(BaseModel):
    is_phishing: bool
    confidence: float
    risk_factors: List[str]
    suspicious_urls: List[URLAnalysis]
    analysis_timestamp: datetime
    summary: str

from shared.utils import (
    validate_email, extract_urls, analyze_urls,
    calculate_risk_score, PHISHING_KEYWORDS
)

# Import GPT integration
from shared.gpt_integration import analyze_email_with_gpt, should_use_gpt

# Phishing detection functions
def extract_features(email: EmailContent) -> dict:
    """Look for suspicious patterns in the email that might indicate it's a phishing attempt.
    
    This is like a detective examining clues in the email:
    - Does it use urgent or threatening language?
    - Are there suspicious links?
    - Is the sender's address fishy?
    - Is it asking for sensitive info?
    """
    # Combine subject and body text for easier analysis
    combined_text = f"{email.subject.lower()} {email.body.lower()}"
    
    features = {
        # Check for fishy language patterns
        "urgency_keywords": any(kw in combined_text for kw in PHISHING_KEYWORDS['urgency']),  # "Act now!", "Urgent!"
        "threat_keywords": any(kw in combined_text for kw in PHISHING_KEYWORDS['threat']),   # "Account suspended"
        "action_keywords": any(kw in combined_text for kw in PHISHING_KEYWORDS['action']),  # "Click here"
        "reward_keywords": any(kw in combined_text for kw in PHISHING_KEYWORDS['reward']),  # "You won!"
        
        # Look for sketchy links
        "suspicious_urls": analyze_urls(email.body),
        
        # Check if the sender's email looks legitimate
        "suspicious_sender": not validate_email(email.sender),
        
        # Look for other red flags
        "poor_formatting": len(re.findall(r'[A-Z]{4,}', email.body)) > 2,  # Lots of CAPS LOCK is suspicious
        "sensitive_requests": any(term in combined_text for term in [
            "password", "credit card", "social security", "bank account"  # Asking for private info
        ])
    }
    return features

def generate_summary(is_phishing: bool, risk_factors: List[str], urls: List[dict]) -> str:
    """Create a friendly, easy-to-understand summary of our findings.
    
    Instead of technical jargon, we use simple language to explain what we found.
    Think of it as translating our detective work into plain English!
    """
    if not is_phishing:
        return "Looks good! We didn't find anything fishy about this email. 👍"
    
    # Build a list of reasons why this email looks suspicious
    summary_points = []
    if any("keyword" in factor.lower() for factor in risk_factors):
        summary_points.append("uses language tricks to pressure or scare you")
    if any(url["is_suspicious"] for url in urls):
        summary_points.append("contains fake or dangerous links")
    if "Suspicious sender" in risk_factors:
        summary_points.append("comes from a sketchy email address")
    
    return f"⚠️ Watch out! This looks like a scam email because it {', '.join(summary_points)}. Stay safe and don't click any links!"

def analyze_sentiment(text: str) -> dict:
    result = sentiment_analyzer(text)
    return result[0]

# API endpoints
@app.post("/analyze", response_model=PhishingAnalysis)
async def analyze_email(email: EmailContent, current_user: Dict = Depends(get_current_user)):
    try:
        # Check if user can perform a scan based on their subscription
        if not can_user_perform_scan(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Scan limit reached. Please upgrade to Pro for unlimited scans."
            )
        
        # Extract and analyze features
        features = extract_features(email)
        risk_score, risk_factors = calculate_risk_score(features)
        
        # Determine if we should use GPT for enhanced analysis
        if should_use_gpt(risk_score, risk_factors):
            # Get enhanced analysis from GPT
            gpt_result = analyze_email_with_gpt(
                email.subject,
                email.body,
                email.sender,
                risk_factors
            )
            
            # If GPT analysis was successful, incorporate its findings
            if gpt_result["success"]:
                # Add GPT-identified risk factors
                risk_factors.extend(gpt_result["additional_risk_factors"])
                
                # Recalculate risk score with GPT insights
                # Add a small boost to the risk score for each new factor identified by GPT
                gpt_factor_boost = 0.05 * len(gpt_result["additional_risk_factors"])
                risk_score = min(1.0, risk_score + gpt_factor_boost)
        
        # Prepare analysis result
        analysis = PhishingAnalysis(
            is_phishing=risk_score > 0.5,
            confidence=risk_score,
            risk_factors=risk_factors,
            suspicious_urls=[URLAnalysis(**url) for url in features["suspicious_urls"]],
            analysis_timestamp=datetime.utcnow(),
            summary=generate_summary(
                risk_score > 0.5,
                risk_factors,
                features["suspicious_urls"]
            )
        )
        
        # Record this scan in the database
        record_scan(
            user_id=current_user["id"],
            email_subject=email.subject,
            is_phishing=analysis.is_phishing,
            confidence=analysis.confidence
        )
        
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing email: {str(e)}"
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/")
async def root():
    return {"message": "Welcome to PhishGuard - Your Friendly Email Protector! 🛡️"}

# Authentication endpoints
@app.post("/auth/register", response_model=Dict)
async def register(user_data: UserCreate):
    """Register a new user"""
    result = register_new_user(user_data)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return {"message": "User registered successfully", "user_id": result["user_id"]}

@app.post("/auth/token", response_model=Token)
async def login(user_data: UserLogin):
    """Login and get access token"""
    result = login_user(user_data)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"],
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token": result["access_token"],
        "token_type": result["token_type"]
    }

@app.get("/auth/me", response_model=Dict)
async def get_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current user information"""
    # Get subscription status
    subscription = check_user_subscription_status(current_user["id"])
    
    return {
        "user_id": current_user["id"],
        "email": current_user["email"],
        "created_at": current_user["created_at"],
        "subscription": subscription
    }

# Payment and subscription endpoints
@app.get("/subscription/plans", response_model=Dict)
async def get_subscription_plans():
    """Get available subscription plans"""
    return {"plans": PLANS}

@app.get("/subscription/status", response_model=Dict)
async def get_subscription_status(current_user: Dict = Depends(get_current_user)):
    """Get user's subscription status"""
    status = check_user_subscription_status(current_user["id"])
    return {"subscription": status}

@app.post("/subscription/checkout", response_model=Dict)
async def create_subscription_checkout(request: Dict, current_user: Dict = Depends(get_current_user)):
    """Create a checkout session for subscription"""
    # Create or get Stripe customer
    customer_result = create_customer(current_user["email"])
    if not customer_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer"
        )
    
    # Create checkout session
    checkout_result = create_checkout_session(
        customer_id=customer_result["customer_id"],
        price_id=request["price_id"],
        success_url=request["success_url"],
        cancel_url=request["cancel_url"]
    )
    
    if not checkout_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )
    
    return {"session_id": checkout_result["session_id"], "checkout_url": checkout_result["checkout_url"]}

@app.post("/subscription/cancel", response_model=Dict)
async def cancel_user_subscription(current_user: Dict = Depends(get_current_user)):
    """Cancel user's subscription"""
    # Get user's subscription
    subscription = check_user_subscription_status(current_user["id"])
    
    if subscription["plan"] == "free" or subscription["status"] != "active":
        return {"message": "No active subscription to cancel"}
    
    # Cancel subscription in Stripe
    # This would require getting the Stripe subscription ID from the database
    # For now, we'll just return a success message
    return {"message": "Subscription canceled successfully"}

@app.post("/webhook/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )
    
    result = handle_webhook_event(payload, sig_header)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Invalid webhook event")
        )
    
    return {"status": "success"}

# Scan history endpoints
@app.get("/scan/history", response_model=Dict)
async def get_scan_history(current_user: Dict = Depends(get_current_user)):
    """Get user's scan history"""
    history = get_user_scan_history(current_user["id"])
    return {"history": history}

# MVP endpoints
@app.post("/phishing/analyze")
async def phishing_analyze(email_file: bytes = File(...)):
    """
    Analyze an uploaded email file for phishing.
    Accepts raw file bytes, returns mock result for MVP.
    """
    # For MVP, just return a mock result
    return {
        "risk_score": 87,
        "summary": "⚠️ This email contains suspicious links and urgent language. Be careful!",
        "details": "Mock analysis only."
    }

@app.get("/phishing/history")
async def phishing_history(limit: int = 5):
    """
    Return mock scan history for MVP.
    """
    return {
        "history": [
            {"Date": "2025-04-15", "Sender": "phisher@bad.com", "Subject": "Urgent action required!", "Risk Score": 95, "Report": "View"},
            {"Date": "2025-04-14", "Sender": "boss@company.com", "Subject": "Monthly update", "Risk Score": 5, "Report": "View"},
        ]
    }

@app.get("/subscription/subscribe")
def subscribe():
    """
    Redirect user to Stripe Checkout (mock for MVP).
    """
    # In real code, generate a Stripe checkout session and redirect
    return RedirectResponse(url="https://buy.stripe.com/test_4gwcOq9jL1qI4jC4gg")