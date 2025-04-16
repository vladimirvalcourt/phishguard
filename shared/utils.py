from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
import json
from urllib.parse import urlparse
from difflib import SequenceMatcher

# Email validation patterns
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
URL_PATTERN = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

# Common phishing indicators
PHISHING_KEYWORDS = {
    'urgency': [
        'urgent', 'immediate', 'action required', 'account suspended',
        'limited time', 'expires soon', 'act now', 'deadline'
    ],
    'threat': [
        'suspicious activity', 'security alert', 'unauthorized access',
        'unusual sign-in', 'security breach', 'account compromised'
    ],
    'action': [
        'verify your account', 'confirm your identity', 'validate your account',
        'click here', 'login now', 'update your information'
    ],
    'reward': [
        'you won', 'congratulations', 'prize', 'reward',
        'gift card', 'free offer', 'exclusive deal'
    ]
}

# Common legitimate domains for comparison
LEGITIMATE_DOMAINS = [
    'paypal.com', 'google.com', 'microsoft.com', 'apple.com',
    'amazon.com', 'facebook.com', 'twitter.com', 'linkedin.com'
]

def validate_email(email: str) -> bool:
    """Validate email format."""
    return bool(re.match(EMAIL_PATTERN, email))

def extract_urls(text: str) -> List[str]:
    """Extract all URLs from text."""
    return re.findall(URL_PATTERN, text)

def analyze_domain_similarity(domain: str) -> Tuple[bool, Optional[str]]:
    """Analyze domain for similarity with legitimate domains to detect typosquatting."""
    for legit_domain in LEGITIMATE_DOMAINS:
        similarity = SequenceMatcher(None, domain, legit_domain).ratio()
        if similarity > 0.8 and domain != legit_domain:
            return True, legit_domain
    return False, None

def analyze_urls(text: str) -> List[Dict[str, any]]:
    """Analyze URLs in text for suspicious patterns."""
    urls = extract_urls(text)
    analysis = []
    
    for url in urls:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            is_suspicious, similar_to = analyze_domain_similarity(domain)
            
            result = {
                'url': url,
                'domain': domain,
                'is_suspicious': is_suspicious,
                'reasons': []
            }
            
            if is_suspicious:
                result['reasons'].append(f"Similar to legitimate domain: {similar_to}")
            if not parsed.scheme.startswith('https'):
                result['reasons'].append("Non-secure protocol (HTTP)")
            if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', domain):
                result['reasons'].append("IP address in URL")
            
            analysis.append(result)
        except Exception:
            analysis.append({
                'url': url,
                'is_suspicious': True,
                'reasons': ["Invalid URL format"]
            })
    
    return analysis

def calculate_risk_score(features: Dict[str, any]) -> Tuple[float, List[str]]:
    """Calculate risk score and generate risk factors based on extracted features."""
    weights = {
        'urgency_keywords': 0.25,
        'threat_keywords': 0.25,
        'action_keywords': 0.2,
        'reward_keywords': 0.15,
        'suspicious_urls': 0.4,
        'suspicious_sender': 0.3,
        'poor_formatting': 0.15,
        'sensitive_requests': 0.35
    }
    
    score = 0.0
    risk_factors = []
    
    # Calculate keyword-based scores
    for category, keywords in PHISHING_KEYWORDS.items():
        feature_name = f"{category}_keywords"
        if feature_name in features and features[feature_name]:
            score += weights[feature_name]
            risk_factors.append(f"Contains {category}-related suspicious keywords")
    
    # Add URL-based scores
    if 'suspicious_urls' in features and features['suspicious_urls']:
        score += weights['suspicious_urls']
        for url_analysis in features['suspicious_urls']:
            if url_analysis['is_suspicious']:
                risk_factors.extend(url_analysis['reasons'])
    
    # Add other feature scores
    if features.get('suspicious_sender', False):
        score += weights['suspicious_sender']
        risk_factors.append("Suspicious sender email format")
    
    if features.get('poor_formatting', False):
        score += weights['poor_formatting']
        risk_factors.append("Poor email formatting")
    
    if features.get('sensitive_requests', False):
        score += weights['sensitive_requests']
        risk_factors.append("Requests for sensitive information")
    
    return min(1.0, score), risk_factors

def format_timestamp(timestamp: datetime) -> str:
    """Format datetime object to string."""
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS and other injection attacks."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove special characters
    text = re.sub(r'[\\\"\'\{\}\[\]\;\`]', '', text)
    return text.strip()

def generate_report(analysis_result: Dict) -> str:
    """Generate a human-readable report from analysis results."""
    report = {
        'timestamp': format_timestamp(datetime.now()),
        'risk_level': 'High' if analysis_result['is_phishing'] else 'Low',
        'confidence': f"{analysis_result['confidence']:.2%}",
        'risk_factors': analysis_result['risk_factors'],
        'recommendations': [
            'Forward suspicious emails to your IT department',
            'Do not click on any links or download attachments',
            'Verify sender identity through alternative channels',
            'Enable two-factor authentication on your accounts'
        ]
    }
    
    return json.dumps(report, indent=2)