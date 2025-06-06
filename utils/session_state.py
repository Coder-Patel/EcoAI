import streamlit as st
import pandas as pd
from datetime import datetime

def init_all_session_states():
    """Initialize all session states for the application"""
    # Energy Module
    if "historical_data" not in st.session_state:
        st.session_state.historical_data = pd.DataFrame()
    if "energy_score" not in st.session_state:
        st.session_state.energy_score = 0
    if "total_savings" not in st.session_state:
        st.session_state.total_savings = 0
    
    # Authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
        
    # Other modules initialization can be added here