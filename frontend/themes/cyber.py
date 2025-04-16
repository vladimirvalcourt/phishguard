import streamlit as st

def apply_cyber_theme():
    st.markdown("""
    <style>
        /* Cyber Dark Theme */
        body {
            background: #0a0a1f;
            color: #e0e0ff;
        }
        
        .main > div {
            background: linear-gradient(180deg, #12122a 0%, #0a0a1f 100%);
            border: 1px solid #2a2a5a;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 0 20px rgba(82, 255, 168, 0.1);
        }
        
        /* Typography */
        h1, h2, h3 {
            font-family: 'JetBrains Mono', monospace;
            color: #52ffa8;
            text-shadow: 0 0 10px rgba(82, 255, 168, 0.3);
        }
        
        p {
            font-family: 'JetBrains Mono', monospace;
            color: #b4b4ff;
            line-height: 1.6;
        }
        
        /* Buttons */
        .stButton>button {
            background: transparent;
            border: 2px solid #52ffa8;
            color: #52ffa8;
            font-family: 'JetBrains Mono', monospace;
            padding: 0.75rem;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 2px;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background: #52ffa8;
            color: #0a0a1f;
            box-shadow: 0 0 20px rgba(82, 255, 168, 0.4);
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            font-family: 'JetBrains Mono', monospace;
            color: #52ffa8 !important;
            text-shadow: 0 0 10px rgba(82, 255, 168, 0.3);
        }
        
        /* Risk Indicators */
        .risk-high {
            color: #ff5252;
            background: rgba(255, 82, 82, 0.1);
            border: 1px solid #ff5252;
            border-radius: 6px;
            padding: 1rem;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .risk-low {
            color: #52ffa8;
            background: rgba(82, 255, 168, 0.1);
            border: 1px solid #52ffa8;
            border-radius: 6px;
            padding: 1rem;
            font-family: 'JetBrains Mono', monospace;
        }
        
        /* Form Fields */
        .stTextInput>div>div>input {
            background: #12122a;
            border: 1px solid #2a2a5a;
            color: #e0e0ff;
            border-radius: 6px;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: #52ffa8;
            box-shadow: 0 0 10px rgba(82, 255, 168, 0.2);
        }
        
        /* Animations */
        @keyframes scanline {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100%); }
        }
        
        .main > div::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: rgba(82, 255, 168, 0.2);
            animation: scanline 2s linear infinite;
            pointer-events: none;
        }
    </style>
    
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)