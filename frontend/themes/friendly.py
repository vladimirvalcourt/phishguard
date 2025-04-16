import streamlit as st

def apply_friendly_theme():
    st.markdown("""
    <style>
        /* Friendly Theme */
        .main > div {
            background: #f0f9ff;
            border-radius: 24px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(100, 100, 255, 0.1);
        }
        
        /* Typography */
        h1, h2, h3 {
            font-family: 'Quicksand', sans-serif;
            color: #2563eb;
            font-weight: 700;
        }
        
        p {
            font-family: 'Quicksand', sans-serif;
            color: #475569;
            line-height: 1.8;
            font-size: 1.1rem;
        }
        
        /* Buttons */
        .stButton>button {
            background: #2563eb;
            color: white;
            font-family: 'Quicksand', sans-serif;
            font-weight: 700;
            padding: 1rem;
            border-radius: 100px;
            border: none;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            transform: scale(1.02);
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3);
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            font-family: 'Quicksand', sans-serif;
            font-weight: 700;
            color: #2563eb !important;
        }
        
        /* Risk Indicators */
        .risk-high {
            color: #dc2626;
            background: #fee2e2;
            border-radius: 16px;
            padding: 1rem;
            font-family: 'Quicksand', sans-serif;
            font-weight: 700;
            margin: 1rem 0;
        }
        
        .risk-low {
            color: #059669;
            background: #d1fae5;
            border-radius: 16px;
            padding: 1rem;
            font-family: 'Quicksand', sans-serif;
            font-weight: 700;
            margin: 1rem 0;
        }
        
        /* Form Fields */
        .stTextInput>div>div>input {
            font-family: 'Quicksand', sans-serif;
            border: 2px solid #e2e8f0;
            border-radius: 100px;
            padding: 1rem;
            transition: all 0.3s ease;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
        }
        
        /* Card-like containers */
        .element-container {
            background: white;
            border-radius: 20px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            transition: transform 0.3s ease;
        }
        
        .element-container:hover {
            transform: translateY(-2px);
        }
        
        /* Animations */
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }
        
        .stImage {
            animation: float 4s ease-in-out infinite;
        }
    </style>
    
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)