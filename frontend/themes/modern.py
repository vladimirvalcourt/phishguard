import streamlit as st

def apply_modern_theme():
    st.markdown("""
    <style>
        /* Modern Minimalist Theme */
        .main > div {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: #ffffff;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            border-radius: 16px;
        }
        
        /* Typography */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            color: #1a1a1a;
            letter-spacing: -0.5px;
        }
        
        p {
            font-family: 'Inter', sans-serif;
            color: #4a4a4a;
            line-height: 1.6;
        }
        
        /* Buttons */
        .stButton>button {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 500;
            transition: transform 0.2s ease;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            color: #4f46e5 !important;
        }
        
        /* Risk Indicators */
        .risk-high {
            color: #ef4444;
            font-weight: 600;
            padding: 0.5rem;
            border-left: 4px solid #ef4444;
            background: rgba(239, 68, 68, 0.1);
        }
        
        .risk-low {
            color: #10b981;
            font-weight: 600;
            padding: 0.5rem;
            border-left: 4px solid #10b981;
            background: rgba(16, 185, 129, 0.1);
        }
        
        /* Form Fields */
        .stTextInput>div>div>input {
            border-radius: 8px;
            border: 2px solid #e5e7eb;
            padding: 0.75rem;
            transition: border-color 0.2s ease;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: #4f46e5;
            box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .main > div > div {
            animation: fadeIn 0.5s ease-out;
        }
    </style>
    
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)