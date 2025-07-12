import streamlit as st
from utils import init_app
import sys
import os
import json
import pandas as pd
from datetime import datetime
import time


# Page config must be the first Streamlit command
st.set_page_config(
    page_title="EcoWise Living Platform",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add the apps directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import app modules directly
from apps.app1 import main as transport_main
from apps.app2 import main as energy_main
from apps.app2 import init_energy_session_state
from apps.app3 import main as water_main
from apps.app4 import main as food_main
from apps.app5 import main as waste_main

# Initialize the application
auth, model = init_app()

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False
if 'model' not in st.session_state:
    st.session_state.model = model

def calculate_eco_score(username, progress):
    """Calculate overall eco score based on all activities"""
    scores = {
        'transport': 0,
        'energy': 0,
        'water': 0,
        'food': 0,
        'waste': 0
    }
    
    try:
        # Calculate individual feature scores
        for feature in scores.keys():
            feature_data = progress[progress['feature'] == feature]
            if not feature_data.empty:
                latest_data = json.loads(feature_data.iloc[-1]['data'])
                
                if feature == 'transport':
                    scores[feature] = latest_data.get('eco_points', 0)
                elif feature == 'energy':
                    scores[feature] = latest_data.get('energy_points', 0)
                elif feature == 'water':
                    scores[feature] = latest_data.get('water_points', 0)
                elif feature == 'food':
                    scores[feature] = latest_data.get('food_points', 0)
                elif feature == 'waste':
                    scores[feature] = latest_data.get('waste_points', 0)
    except Exception as e:
        print(f"Error calculating eco score: {e}")
    
    # Calculate weighted average
    weights = {'transport': 0.25, 'energy': 0.25, 'water': 0.2, 'food': 0.15, 'waste': 0.15}
    total_score = sum(scores[k] * weights[k] for k in scores.keys())
    return round(total_score)

def calculate_metrics(username, progress):
    """Calculate all dashboard metrics"""
    metrics = {
        'carbon_saved': 0,
        'water_saved': 0,
        'energy_saved': 0
    }
    
    # Calculate carbon savings
    transport_data = progress[progress['feature'] == 'transport']
    food_data = progress[progress['feature'] == 'food']
    
    if not transport_data.empty:
        latest_transport = json.loads(transport_data.iloc[-1]['data'])
        metrics['carbon_saved'] += latest_transport.get('carbon_footprint', 0)
    
    if not food_data.empty:
        latest_food = json.loads(food_data.iloc[-1]['data'])
        metrics['carbon_saved'] += latest_food.get('carbon_saved', 0)
    
    # Calculate water savings
    water_data = progress[progress['feature'] == 'water']
    if not water_data.empty:
        latest_water = json.loads(water_data.iloc[-1]['data'])
        metrics['water_saved'] = latest_water.get('water_saved', 0)
    
    # Calculate energy savings
    energy_data = progress[progress['feature'] == 'energy']
    if not energy_data.empty:
        latest_energy = json.loads(energy_data.iloc[-1]['data'])
        recommendations = latest_energy.get('recommendations', {})
        metrics['energy_saved'] = recommendations.get('estimated_carbon_reduction', 0)
    
    return metrics

def main():
    # Add this before authentication UI
    st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h1 style='color: #1e88e5;'>🌍 Eco Action</h1>
            <p style='font-size: 1.2em; color: #ffffff;'>Make your life more efficient and sustainable</p>
        </div>
    """, unsafe_allow_html=True)

    # Authentication UI
    if not st.session_state.user:
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        
        if not st.session_state.show_signup:
            st.subheader("Login")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    success, message = auth.login_user(username, password)
                    if success:
                        st.session_state.user = username
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            
            if st.button("Create Account"):
                st.session_state.show_signup = True
                st.rerun()
        else:
            st.subheader("Create Account")
            with st.form("signup_form"):
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                submit = st.form_submit_button("Sign Up")
                
                if submit:
                    if not all([new_username, new_password, name, email]):
                        st.error("Please fill in all fields")
                    else:
                        success, message = auth.register_user(new_username, new_password, name, email)
                        if success:
                            st.success("Account created successfully! Please login.")
                            time.sleep(1)
                            st.session_state.show_signup = False
                            st.rerun()
                        else:
                            st.error(message)
            
            if st.button("Back to Login"):
                st.session_state.show_signup = False
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    # Sidebar navigation
    st.sidebar.title("🌍 EcoWise Living")
    
    # User info in sidebar
    st.sidebar.markdown(f"Welcome, {st.session_state.user}!")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()
    
    # Navigation
    page = st.sidebar.radio(
        "Choose Feature",
        ["Dashboard", "Transportation", "Energy", "Water", "Food", "Waste"]
    )

    # Page routing
    if page == "Dashboard":
        show_dashboard()
    elif page == "Transportation":
        transport_main(auth)
    elif page == "Energy":
        from apps.app2 import init_energy_session_state
        init_energy_session_state()
        energy_main(auth)
    elif page == "Water":
        water_main(auth)
    elif page == "Food":
        food_main(auth)
    elif page == "Waste":
        waste_main(auth)

def show_dashboard():
    st.title("Your Sustainability Dashboard")
    
    try:
        # Read from local progress file
        progress_file = "data/progress.csv"
        if os.path.exists(progress_file):
            progress = pd.read_csv(progress_file)
            # Filter for current user
            progress = progress[progress['username'] == st.session_state.user]
        else:
            # Create empty DataFrame if file doesn't exist
            progress = pd.DataFrame(columns=['username', 'feature', 'data', 'timestamp'])
        
        # Calculate metrics with error handling
        try:
            eco_score = calculate_eco_score(st.session_state.user, progress)
            metrics = calculate_metrics(st.session_state.user, progress)
        except Exception as e:
            eco_score = 0
            metrics = {'carbon_saved': 0, 'water_saved': 0, 'energy_saved': 0}
            print(f"Error calculating metrics: {e}")
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Eco Score", f"{eco_score}")
        with col2:
            st.metric("Carbon Saved", f"{metrics['carbon_saved']:.1f} kg")
        with col3:
            st.metric("Water Saved", f"{metrics['water_saved']:.1f} gal")
        with col4:
            st.metric("Energy Saved", f"{metrics['energy_saved']:.1f} kWh")
        
        # Feature progress section
        st.subheader("Feature Progress")
        features = ["Transportation", "Energy", "Water", "Food", "Waste"]
        
        for feature in features:
            feature_data = progress[progress['feature'] == feature.lower()]
            progress_value = 0.0
            
            if not feature_data.empty:
                try:
                    latest_data = json.loads(feature_data.iloc[-1]['data'])
                    progress_value = latest_data.get('completion_percentage', 0) / 100
                except:
                    progress_value = 0.0
                    
            st.progress(progress_value)
            st.caption(f"{feature}: {int(progress_value*100)}% complete")
            
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        st.info("Start your sustainability journey by using the features above!")

if __name__ == "__main__":
    main()