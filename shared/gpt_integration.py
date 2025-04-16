import os
from openai import OpenAI
from typing import Dict, List, Optional, Any
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI API
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-3.5-turbo")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "500"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def should_use_gpt(risk_score: float, risk_factors: List[str]) -> bool:
    """
    Determine if we should use GPT for enhanced analysis based on risk score and factors.
    
    This function implements a cost-efficient approach to using the GPT API:
    - For clearly safe emails (very low risk score), we skip GPT analysis
    - For clearly dangerous emails (very high risk score), we skip GPT analysis
    - For borderline cases where we're uncertain, we use GPT for enhanced analysis
    
    Args:
        risk_score: The calculated risk score from basic analysis (0.0 to 1.0)
        risk_factors: List of identified risk factors from basic analysis
        
    Returns:
        bool: True if GPT analysis should be used, False otherwise
    """
    # Skip GPT for very low risk emails (clearly safe)
    if risk_score < 0.2:
        return False
    
    # Skip GPT for very high risk emails (clearly dangerous)
    if risk_score > 0.8:
        return False
    
    # For borderline cases, use GPT if we have few risk factors
    # This helps when we're uncertain and need more insights
    if 0.2 <= risk_score <= 0.8 and len(risk_factors) < 3:
        return True
    
    # Use GPT if we have a moderate risk score
    # This is the "gray area" where AI can help the most
    if 0.4 <= risk_score <= 0.6:
        return True
    
    return False


def analyze_email_with_gpt(
    subject: str, 
    body: str, 
    sender: str, 
    existing_risk_factors: List[str]
) -> Dict[str, Any]:
    """
    Analyze email content using GPT to identify additional phishing indicators.
    
    Args:
        subject: Email subject line
        body: Email body content
        sender: Email sender address
        existing_risk_factors: Risk factors already identified by basic analysis
        
    Returns:
        Dict containing:
            - success: Whether the GPT analysis was successful
            - additional_risk_factors: List of new risk factors identified by GPT
            - error: Error message if analysis failed
    """
    try:
        # Prepare the prompt for GPT
        prompt = f"""
        Analyze this email for phishing indicators. Identify any suspicious elements not in the existing risk factors.
        
        Subject: {subject}
        From: {sender}
        Body: {body}
        
        Existing risk factors: {', '.join(existing_risk_factors)}
        
        Provide ONLY new suspicious elements in this format:
        1. [Specific suspicious element with brief explanation]
        2. [Another suspicious element with brief explanation]
        
        If you find nothing new, respond with "No additional suspicious elements found."
        """
        
        # Call the OpenAI API
        if not api_key:
            logger.warning("OpenAI API key not found. Skipping GPT analysis.")
            return {"success": False, "additional_risk_factors": [], "error": "API key not configured"}
        
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "system", "content": "You are a cybersecurity expert specializing in phishing detection."},
                     {"role": "user", "content": prompt}],
            max_tokens=MAX_TOKENS,
            temperature=0.3  # Lower temperature for more focused, analytical responses
        )
        
        # Process the response
        gpt_analysis = response.choices[0].message.content.strip()
        
        # Extract new risk factors
        additional_factors = []
        if "No additional suspicious elements found" not in gpt_analysis:
            # Split by numbered list items and filter out empty lines
            for line in gpt_analysis.split("\n"):
                # Look for numbered list items or bullet points
                if (line.strip() and (line.strip()[0].isdigit() and ". " in line or 
                                      line.strip().startswith("- "))):
                    # Clean up the line and add "GPT detected" prefix
                    factor = line.strip()
                    # Remove the number/bullet and any leading/trailing whitespace
                    factor = factor.split(".", 1)[1].strip() if ". " in factor else factor[2:].strip()
                    additional_factors.append(f"GPT detected: {factor}")
        
        return {
            "success": True,
            "additional_risk_factors": additional_factors,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Error in GPT analysis: {str(e)}")
        return {
            "success": False,
            "additional_risk_factors": [],
            "error": str(e)
        }