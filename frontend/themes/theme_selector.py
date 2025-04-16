import streamlit as st
from frontend.themes.modern import apply_modern_theme
from frontend.themes.cyber import apply_cyber_theme
from frontend.themes.friendly import apply_friendly_theme

def initialize_theme_selector():
    if 'theme' not in st.session_state:
        st.session_state.theme = 'modern'

def apply_selected_theme():
    theme_map = {
        'modern': apply_modern_theme,
        'cyber': apply_cyber_theme,
        'friendly': apply_friendly_theme
    }
    
    # Apply the selected theme
    theme_map[st.session_state.theme]()

def display_theme_selector():
    initialize_theme_selector()
    
    # Create a container for the theme selector
    with st.sidebar:
        st.title('🎨 Theme Options')
        selected_theme = st.radio(
            'Choose your preferred look:',
            options=['modern', 'cyber', 'friendly'],
            format_func=lambda x: {
                'modern': '🎯 Modern Minimalist',
                'cyber': '🔒 Cybersecurity Dark',
                'friendly': '🌟 Friendly & Playful'
            }[x],
            key='theme'
        )
        
        st.markdown('---')
        st.markdown('''
        ### Theme Details:
        
        **Modern Minimalist**
        Clean and professional design with subtle animations
        
        **Cybersecurity Dark**
        Dark theme with neon accents and tech vibes
        
        **Friendly & Playful**
        Approachable design with rounded shapes
        ''')