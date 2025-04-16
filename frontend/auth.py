import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import requests
import json
from datetime import datetime
from shared.logger import logger

# API endpoint
API_URL = "https://phishguard-mcuv.onrender.com"

def register_user(email, password):
    """Register a new user"""
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return {"success": True, "message": "Registration successful! Please log in."}
        else:
            return {"success": False, "message": response.json().get("detail", "Registration failed")}
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {str(e)}")
        logger.error(f"Auth error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}

def login_user(email, password):
    """Login a user"""
    try:
        response = requests.post(
            f"{API_URL}/auth/token",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "token": data["access_token"],
                "token_type": data["token_type"]
            }
        else:
            return {"success": False, "message": response.json().get("detail", "Login failed")}
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {str(e)}")
        logger.error(f"Auth error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}

def get_user_info(token):
    """Get user information"""
    try:
        response = requests.get(
            f"{API_URL}/auth/me",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        
        if response.status_code == 200:
            return {"success": True, "user": response.json()}
        else:
            return {"success": False, "message": response.json().get("detail", "Failed to get user info")}
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {str(e)}")
        logger.error(f"Auth error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}

def display_login_page():
    """Display the login page"""
    st.title("🛡️ PhishGuard - Login")
    
    # Check if already logged in
    if "token" in st.session_state:
        st.success("You are already logged in!")
        if st.button("Logout"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()
        return
    
    # Create tabs for login and registration
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        
        # Login form
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    result = login_user(email, password)
                    if result["success"]:
                        # Store token in session state
                        st.session_state["token"] = result["token"]
                        st.session_state["token_type"] = result["token_type"]
                        
                        # Get user info
                        user_info = get_user_info(result["token"])
                        if user_info["success"]:
                            st.session_state["user"] = user_info["user"]
                        
                        st.success("Login successful!")
                        st.experimental_rerun()
                    else:
                        st.error(result["message"])
    
    with tab2:
        st.subheader("Create a New Account")
        
        # Registration form
        with st.form("register_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Register")
            
            if submit:
                if not email or not password or not confirm_password:
                    st.error("Please fill in all fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    result = register_user(email, password)
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])

def display_user_profile():
    """Display the user profile page"""
    st.title("🛡️ PhishGuard - Your Profile")
    
    # Check if logged in
    if "token" not in st.session_state:
        st.warning("Please log in to view your profile")
        return
    
    # Get user info if not already in session state
    if "user" not in st.session_state:
        user_info = get_user_info(st.session_state["token"])
        if user_info["success"]:
            st.session_state["user"] = user_info["user"]
        else:
            st.error(user_info["message"])
            return
    
    user = st.session_state["user"]
    subscription = user["subscription"]
    
    # Display user info
    st.subheader("Account Information")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Account Created:** {user['created_at']}")
    
    # Display subscription info
    st.subheader("Subscription Details")
    st.write(f"**Current Plan:** {subscription['plan'].capitalize()}")
    
    if subscription["plan"] == "free":
        st.write(f"**Scans Used:** {subscription['scans_used']} of {subscription['scan_limit']}")
        st.progress(min(1.0, subscription['scans_used'] / subscription['scan_limit']))
        
        # Upgrade button
        if st.button("Upgrade to Pro"):
            st.session_state["page"] = "subscription"
            st.experimental_rerun()
    else:
        st.write("**Scans Available:** Unlimited")
        st.write(f"**Status:** {subscription['status'].capitalize()}")
        
        # Manage subscription button
        if st.button("Manage Subscription"):
            st.session_state["page"] = "subscription"
            st.experimental_rerun()
    
    # Logout button
    if st.button("Logout"):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

if __name__ == "__main__":
    display_login_page()