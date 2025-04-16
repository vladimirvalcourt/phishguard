# Database module for PhishGuard
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import logging
from shared.logger import logger

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phishguard.db')

def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        scan_count INTEGER DEFAULT 0,
        last_scan_date TIMESTAMP
    )
    ''')
    
    # Create subscriptions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        stripe_customer_id TEXT,
        stripe_subscription_id TEXT,
        plan_type TEXT NOT NULL,
        status TEXT NOT NULL,
        current_period_start TIMESTAMP,
        current_period_end TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create scan_history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scan_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        email_subject TEXT,
        is_phishing BOOLEAN,
        confidence REAL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# User management functions
def create_user(email: str, password_hash: str) -> int:
    """Create a new user and return the user ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, password_hash)
        )
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        # Email already exists
        return None
    finally:
        conn.close()

def get_user_by_email(email: str) -> Dict:
    """Get user by email"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None

def get_user_by_id(user_id: int) -> Dict:
    """Get user by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None

# Subscription management functions
def create_subscription(user_id: int, stripe_customer_id: str, 
                       stripe_subscription_id: str, plan_type: str, 
                       status: str, period_start: datetime, period_end: datetime) -> int:
    """Create a new subscription for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """INSERT INTO subscriptions 
           (user_id, stripe_customer_id, stripe_subscription_id, plan_type, status, 
            current_period_start, current_period_end) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, stripe_customer_id, stripe_subscription_id, plan_type, 
         status, period_start, period_end)
    )
    
    subscription_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return subscription_id

def update_subscription(subscription_id: int, status: str, 
                       period_start: datetime = None, period_end: datetime = None) -> bool:
    """Update an existing subscription"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    update_fields = ["status = ?", "status"]
    params = [status]
    
    if period_start:
        update_fields.append("current_period_start = ?")
        params.append(period_start)
    
    if period_end:
        update_fields.append("current_period_end = ?")
        params.append(period_end)
    
    params.append(subscription_id)
    
    cursor.execute(
        f"UPDATE subscriptions SET {', '.join(update_fields)} WHERE id = ?",
        params
    )
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def get_user_subscription(user_id: int) -> Dict:
    """Get the active subscription for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    )
    
    subscription = cursor.fetchone()
    conn.close()
    
    if subscription:
        return dict(subscription)
    return None

# Scan tracking functions
def record_scan(user_id: int, email_subject: str, is_phishing: bool, confidence: float) -> bool:
    """Record a scan in the history and update user's scan count"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Record the scan in history
        cursor.execute(
            """INSERT INTO scan_history 
               (user_id, email_subject, is_phishing, confidence) 
               VALUES (?, ?, ?, ?)""",
            (user_id, email_subject, is_phishing, confidence)
        )
        
        # Update user's scan count and last scan date
        cursor.execute(
            """UPDATE users 
               SET scan_count = scan_count + 1, last_scan_date = CURRENT_TIMESTAMP 
               WHERE id = ?""",
            (user_id,)
        )
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error recording scan: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_user_scan_count(user_id: int) -> int:
    """Get the number of scans a user has performed"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT scan_count FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result['scan_count']
    return 0

def get_user_scan_history(user_id: int, limit: int = 10) -> List[Dict]:
    """Get the scan history for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT * FROM scan_history 
           WHERE user_id = ? 
           ORDER BY scan_date DESC LIMIT ?""",
        (user_id, limit)
    )
    
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return history

# Initialize the database when this module is imported
init_db()