import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from random import randint  # Change this line
import datetime
import re  # Add this import
import google.generativeai as genai
from PIL import Image
import json

st.markdown("""
    <div style='text-align: center; padding: 20px;'>
    </div>
""", unsafe_allow_html=True)

# Update the custom CSS section with modern styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1e88e5;
        --secondary-color: #4CAF50;
        --background-dark: #1a1a1a;
        --card-bg: #2d2d2d;
        --text-light: #ffffff;
        --text-dark: #333333;
        --accent-color: #ffd700;
    }

    /* Main container styling */
    .main {
        background-color: var(--background-dark);
        color: var(--text-light);
        padding: 20px;
    }

    /* Modern button styling */
    .stButton > button {
        background: linear-gradient(45deg, var(--primary-color), #1565c0);
        color: white;
        font-weight: 600;
        padding: 0.6em 1.2em;
        border: none;
        border-radius: 8px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }

    /* Enhanced tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--card-bg);
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: var(--text-light);
        border: 1px solid var(--primary-color);
        border-radius: 8px;
        padding: 8px 16px;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, var(--primary-color), #1565c0);
        border: none;
    }

    /* Modern card design */
    .modern-card {
        background: linear-gradient(145deg, #2d2d2d, #363636);
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        border: 1px solid rgba(255,255,255,0.1);
    }

    /* Enhanced metric cards */
    .metric-card {
        background: linear-gradient(145deg, #2d2d2d, #363636);
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid rgba(255,255,255,0.1);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }

    /* Achievement badges */
    .achievement-badge {
        background: linear-gradient(145deg, #2d2d2d, #363636);
        border-radius: 12px;
        padding: 15px;
        margin: 8px;
        text-align: center;
        border: 1px solid var(--accent-color);
        transition: all 0.3s ease;
    }
    .achievement-badge:hover {
        transform: scale(1.05);
    }
    .locked-badge {
        filter: grayscale(100%);
        opacity: 0.5;
        border: 1px solid rgba(255,255,255,0.1);
    }

    /* Form styling */
    div[data-testid="stForm"] {
        background-color: var(--card-bg);
        padding: 25px;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.1);
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background-color: #363636;
        color: var(--text-light) !important;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 8px;
    }

    /* Select boxes */
    .stSelectbox > div > div {
        background-color: #363636;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 8px;
    }

    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        border-radius: 10px;
    }

    /* Tooltips */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        background-color: var(--card-bg);
        color: var(--text-light);
        text-align: center;
        padding: 5px 10px;
        border-radius: 6px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }

    /* Animation for loading states */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    .loading {
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# Configure Gemini API
def configure_genai(api_key):
    genai.configure(api_key=api_key)

# Function to get appliance recommendations from Gemini 1.5 Pro
def get_energy_recommendations(user_data, appliance_data):
    """Get detailed energy recommendations from Gemini"""
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = f"""
        As an AI energy efficiency expert, analyze the household's energy usage and provide detailed recommendations. 
        Please respond ONLY with a valid JSON object.
        
        User Details:
        - Household Size: {user_data['household_size']} members
        - Location: {user_data['city']}, {user_data['country']}
        - Current Month: {user_data['month']}
        - Weather: {user_data['precipitation']} precipitation
        - Monthly Bill: {user_data['currency']} {user_data['monthly_bill']}

        Appliance Details:
        {appliance_data}

        Required JSON structure:
        {{
            "analysis": {{
                "total_consumption": <number>,
                "regional_comparison": <string>,
                "peak_usage": <string>,
                "carbon_footprint": <number>
            }},
            "appliance_analysis": [
                {{
                    "name": <string>,
                    "current_consumption": <number>,
                    "current_cost": <number>,
                    "potential_savings_kwh": <number>,
                    "potential_savings_money": <number>,
                    "optimization_steps": [<string>, ...],
                    "upgrade_suggestions": <string>,
                    "roi_months": <number>
                }}
            ],
            "recommendations": [
                {{
                    "title": <string>,
                    "description": <string>,
                    "implementation_cost": <number>,
                    "annual_savings_kwh": <number>,
                    "annual_savings_money": <number>,
                    "payback_period_months": <number>,
                    "difficulty": <string>,
                    "priority": <string>
                }}
            ],
            "renewable_suggestions": [
                {{
                    "technology": <string>,
                    "initial_cost": <number>,
                    "annual_production": <number>,
                    "annual_savings": <number>,
                    "payback_period_years": <number>,
                    "incentives_available": <string>
                }}
            ],
            "target_kwh": <number>,
            "target_money": <number>,
            "estimated_carbon_reduction": <number>
        }}"""

        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Extract JSON content
        json_match = re.search(r'(\{[\s\S]*\})', result)
        if not json_match:
            st.error("Failed to generate valid recommendations")
            return None
            
        json_str = json_match.group(1)
        # Clean up any potential formatting issues
        json_str = json_str.replace('\n', ' ').replace('\r', '')
        
        try:
            recommendations = json.loads(json_str)
            # Validate required fields
            required_fields = ["analysis", "appliance_analysis", "recommendations", 
                             "renewable_suggestions", "target_kwh", "target_money", 
                             "estimated_carbon_reduction"]
            
            if all(field in recommendations for field in required_fields):
                return recommendations
            else:
                st.error("Invalid recommendations format - missing required fields")
                return None
                
        except json.JSONDecodeError as e:
            st.error(f"Error parsing recommendations: {str(e)}")
            return None

    except Exception as e:
        st.error(f"Error generating recommendations: {str(e)}")
        return None

# Function to update user level based on points
def update_user_level():
    points = st.session_state.points
    if points >= 1000:
        st.session_state.user_level = "Energy Expert"
    elif points >= 500:
        st.session_state.user_level = "Power Saver"
    elif points >= 200:
        st.session_state.user_level = "Eco Enthusiast"
    else:
        st.session_state.user_level = "Energy Novice"

# Function to simulate energy savings over time
def generate_simulation_data(start_consumption, recommendations):
    """Generate simulated energy consumption data"""
    data = []
    today = datetime.date.today()
    consumption = start_consumption
    
    # Calculate total potential savings from recommendations
    total_savings = sum(rec.get("savings_kwh", 0) for rec in recommendations.get("recommendations", []))
    
    # Generate 12 months of data
    for i in range(12):
        month_date = today + datetime.timedelta(days=30*i)
        month_name = month_date.strftime("%b")
        
        # Gradually reduce consumption based on recommendations (more aggressive at start)
        if i < 3:
            reduction = total_savings * 0.2 * (i+1)  # 20%, 40%, 60% of potential savings
        else:
            reduction = total_savings * min(0.8 + (i-3)*0.03, 0.95)  # 80% to 95% of potential savings
            
        new_consumption = max(start_consumption - reduction, start_consumption * 0.5)  # Don't go below 50% of original
        
        data.append({
            "month": month_name,
            "consumption": new_consumption,
            "baseline": start_consumption
        })
        consumption = new_consumption
        
    return pd.DataFrame(data)

def update_streaks_and_badges():
    """Update user streaks and award badges based on activity"""
    today = datetime.datetime.now().date()
    
    if 'last_activity_date' not in st.session_state:
        st.session_state.last_activity_date = today
    elif st.session_state.last_activity_date != today:
        if (today - st.session_state.last_activity_date).days == 1:
            st.session_state.streaks += 1
            # Award streak-based badges
            if st.session_state.streaks >= 7 and not st.session_state.badges["Night Saver"]:
                st.session_state.badges["Night Saver"] = True
                st.success("🌙 You've unlocked the Night Saver badge!")
            elif st.session_state.streaks >= 30 and not st.session_state.badges["Eco Warrior"]:
                st.session_state.badges["Eco Warrior"] = True
                st.success("🌍 You've unlocked the Eco Warrior badge!")
        else:
            st.session_state.streaks = 1
        st.session_state.last_activity_date = today

def check_weekend_challenge():
    """Check and award weekend challenge completion"""
    today = datetime.datetime.now()
    if today.weekday() in [5, 6]:  # Saturday or Sunday
        if 'weekend_savings' not in st.session_state:
            st.session_state.weekend_savings = 0
        
        # Simulate weekend energy savings
        current_consumption = st.session_state.monthly_targets.get('current', 0)
        if current_consumption < st.session_state.monthly_targets.get('target', 0) * 0.8:
            st.session_state.weekend_savings += 1
            if st.session_state.weekend_savings >= 4 and not st.session_state.badges["Weekend Off"]:
                st.session_state.badges["Weekend Off"] = True
                st.session_state.points += 100
                st.success("🎉 Weekend Challenge completed! You've earned the Weekend Off badge!")
                return True
    return False

def calculate_energy_rewards(previous_consumption, current_consumption):
    """Calculate points and badges based on energy savings"""
    if previous_consumption and current_consumption:
        savings_percentage = ((previous_consumption - current_consumption) / previous_consumption) * 100
        points_earned = int(savings_percentage * 10)  # 10 points per % saved
        
        if savings_percentage >= 20 and not st.session_state.badges["Power Optimizer"]:
            st.session_state.badges["Power Optimizer"] = True
            points_earned += 200
            st.success("⚡ You've unlocked the Power Optimizer badge!")
        
        st.session_state.points += points_earned
        return points_earned
    return 0

def init_energy_session_state():
    """Initialize all session state variables for energy module"""
    # Basic variables
    if "initialized" not in st.session_state:
        st.session_state.initialized = True

    # Energy specific variables
    if "appliances" not in st.session_state:
        st.session_state.appliances = []
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = None
    if "user_level" not in st.session_state:
        st.session_state.user_level = "Energy Novice"
    if "points" not in st.session_state:
        st.session_state.points = 0
    if "streaks" not in st.session_state:
        st.session_state.streaks = 0
    if "quiz_completed" not in st.session_state:
        st.session_state.quiz_completed = False
    if "historical_data" not in st.session_state:
        st.session_state.historical_data = pd.DataFrame()
    if "monthly_targets" not in st.session_state:
        st.session_state.monthly_targets = {'current': 0, 'target': 0}
    if "badges" not in st.session_state:
        st.session_state.badges = {
            "Weekend Off": False,
            "Night Saver": False,
            "Power Optimizer": False,
            "Green Champion": False,
            "Eco Warrior": False,
            "Energy Genius": False
        }

def auto_save_on_action():
    """Automatically save progress if auth is available"""
    if 'auth' in st.session_state and 'user' in st.session_state:
        progress_data = {
            'appliances': st.session_state.appliances,
            'recommendations': st.session_state.recommendations,
            'points': st.session_state.points,
            'user_level': st.session_state.user_level,
            'badges': st.session_state.badges,
            'historical_data': st.session_state.historical_data.to_dict() if isinstance(st.session_state.historical_data, pd.DataFrame) else {},
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.auth.save_progress(st.session_state.user, "energy", json.dumps(progress_data))

def main(auth=None):
    """Main function for the energy app"""
    # Initialize session state at the start
    init_energy_session_state()
    
    # Load saved data if auth is provided and user is logged in
    if auth and 'user' in st.session_state:
        try:
            saved_data = auth.get_user_progress(st.session_state.user, "energy")
            if not saved_data.empty:
                latest_data = json.loads(saved_data.iloc[-1]['data'])
                # Update session state with user-specific data
                st.session_state.appliances = latest_data.get('appliances', [])
                st.session_state.recommendations = latest_data.get('recommendations', None)
                st.session_state.points = latest_data.get('points', 0)
                st.session_state.user_level = latest_data.get('user_level', "Energy Novice")
                st.session_state.badges = latest_data.get('badges', {
                    "Weekend Off": False,
                    "Night Saver": False,
                    "Power Optimizer": False,
                    "Green Champion": False,
                    "Eco Warrior": False,
                    "Energy Genius": False
                })
                if isinstance(latest_data.get('historical_data'), dict):
                    st.session_state.historical_data = pd.DataFrame(latest_data['historical_data'])
        except Exception as e:
            st.error(f"Error loading saved data: {str(e)}")

    # Mark initialization as complete
    st.session_state.initialized = True

    # Move header before tabs
    st.title("⚡ Energy Efficiency Advisor")
    
    # Create tabs after header
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Input Data", "📊 Analysis & Recommendations", "📈 Progress Tracking", "🎮 Energy Quiz"])

    # Function to save progress
    def save_progress():
        if auth and 'user' in st.session_state:
            progress_data = {
                'appliances': st.session_state.appliances,
                'recommendations': st.session_state.recommendations,
                'points': st.session_state.points,
                'user_level': st.session_state.user_level,
                'badges': st.session_state.badges,
                'historical_data': st.session_state.historical_data.to_dict() if isinstance(st.session_state.historical_data, pd.DataFrame) else {}
            }
            # Save locally
            auth.save_progress(st.session_state.user, "energy", json.dumps(progress_data))
            st.success("Progress saved!")

    # Add save button in sidebar only if auth is available
    if auth:
        st.sidebar.markdown("---")
        if st.sidebar.button("💾 Save Progress"):
            save_progress()

    # Auto-save function for important actions
    def auto_save_on_action():
        if auth and 'user' in st.session_state:
            save_progress()

    # Tab 1: Input Data
    with tab1:
        # Remove the duplicate header
        with st.form(key="user_info_form"):
            st.subheader("Household Information")
            
            col1, col2 = st.columns(2)
            with col1:
                household_size = st.number_input("Household Size (number of people)", min_value=1, max_value=20, value=4)
                country = st.text_input("Country", value="India")
                precipitation = st.selectbox("Precipitation Level", options=["Low", "Moderate", "High"], index=1)
            
            with col2:
                city = st.text_input("City", value="New Delhi")
                month = st.selectbox("Month", options=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], index=datetime.datetime.now().month - 1)
                currency = st.text_input("Currency Symbol", value="₹")
            
            monthly_bill = st.number_input(f"Monthly Energy Bill ({currency})", min_value=0, value=3000)
            
            submit_button = st.form_submit_button(label="Generate Energy Recommendations")
            
            if submit_button:
                if not st.session_state.appliances:
                    st.error("Please add at least one appliance before generating recommendations.")
                else:
                    with st.spinner("Analyzing your energy usage..."):
                        # Prepare user data
                        user_data = {
                            "household_size": household_size,
                            "city": city,
                            "country": country,
                            "month": month,
                            "precipitation": precipitation,
                            "monthly_bill": monthly_bill,
                            "currency": currency
                        }
                        
                        # Format appliance data for the prompt
                        appliance_text = ""
                        for app in st.session_state.appliances:
                            appliance_text += f"- {app['name']}: {app['power_rating']} kW, {app['star_rating']} efficiency, {app['hours_per_day']} hours per {app['usage_type'].lower()}, {app['age_years']} years old\n"
                        
                        # Get recommendations
                        recommendations = get_energy_recommendations(user_data, appliance_text)
                        
                        if recommendations:
                            st.session_state.recommendations = recommendations
                            
                            # Set monthly targets if available
                            if "target_kwh" in recommendations:
                                st.session_state.monthly_targets = {
                                    'current': 0,
                                    'target': recommendations["target_kwh"]
                                }
                            
                            # Add points and update level
                            st.session_state.points += 50
                            st.session_state.streaks += 1
                            update_user_level()
                            
                            # Unlock a badge if applicable
                            if not st.session_state.badges["Power Optimizer"]:
                                st.session_state.badges["Power Optimizer"] = True
                                
                            st.success("Analysis complete! Check the 'Analysis & Recommendations' tab.")
                            # Auto-save if available
                            if 'auth' in st.session_state and 'user' in st.session_state:
                                auto_save_on_action()
            elif submit_button and not auth:
                st.error("Please enter your Gemini API Key in the sidebar to generate recommendations.")

        # Move appliance form outside the main user info form
        st.subheader("Appliance Information")
        
        # Add appliance inputs
        col1, col2 = st.columns(2)
        with col1:
            appliance_name = st.text_input("Appliance Name")
            power_rating = st.number_input("Power Rating (kW)", min_value=0.0, step=0.1, value=1.5)
            hours_per_day = st.number_input("Usage Hours per Day", min_value=0.0, max_value=24.0, step=0.5, value=6.0)

        with col2:
            star_rating = st.selectbox("Energy Efficiency (Star Rating)", 
                options=["1-Star", "2-Star", "3-Star", "4-Star", "5-Star"], 
                index=2)
            usage_type = st.selectbox("Usage Pattern", 
                options=["Daily", "Weekly", "Monthly"], 
                index=0)
            age_years = st.number_input("Appliance Age (years)", 
                min_value=0, 
                max_value=30, 
                value=3)

        # Add appliance button (outside any form)
        if st.button("Add Appliance"):
            if appliance_name:
                new_appliance = {
                    "name": appliance_name,
                    "power_rating": power_rating,
                    "star_rating": star_rating,
                    "hours_per_day": hours_per_day,
                    "usage_type": usage_type,
                    "age_years": age_years
                }
                if 'appliances' not in st.session_state:
                    st.session_state.appliances = []
                st.session_state.appliances.append(new_appliance)
                st.success(f"Added {appliance_name} to your appliance list!")
            else:
                st.error("Please enter an appliance name")

        # Display existing appliances
        if st.session_state.appliances:
            st.subheader("Your Appliances")
            for i, app in enumerate(st.session_state.appliances):
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    st.markdown(f"""
                    **{app['name']}** ({app['star_rating']}) - {app['power_rating']} kW, 
                    {app['hours_per_day']} hours/{app['usage_type'].lower()}, Age: {app['age_years']} years
                    """)
                with col2:
                    if st.button("🗑️", key=f"remove_{i}"):
                        st.session_state.appliances.pop(i)
                        # Clear recommendations when appliances change
                        st.session_state.recommendations = None
                        # Auto-save if available
                        if 'auth' in st.session_state and 'user' in st.session_state:
                            auto_save_on_action()
                        st.rerun()

            # Update the Remove All Appliances button section
            if st.button("Remove All Appliances"):
                st.session_state.appliances = []
                st.session_state.recommendations = None
                st.session_state.historical_data = pd.DataFrame()
                st.session_state.monthly_targets = {
                    'current': 0,
                    'target': 0
                }
                # Auto-save if available
                if 'auth' in st.session_state and 'user' in st.session_state:
                    auto_save_on_action()
                st.rerun()

    # Tab 2: Analysis & Recommendations
    with tab2:
        if st.session_state.recommendations:
            st.header("Your Energy Analysis")
            
            # Add Save Recommendations button at the top
            if st.button("💾 Save These Recommendations"):
                # Generate simulation data based on recommendations
                base_consumption = randint(300, 500)  # Remove random. prefix
                simulation_data = generate_simulation_data(base_consumption, st.session_state.recommendations)
                st.session_state.historical_data = simulation_data
                
                # Auto-save if auth is available
                if auth and 'user' in st.session_state:
                    save_progress()
                    st.success("Recommendations and progress data saved successfully!")
                else:
                    st.success("Simulation data generated successfully!")
            
            # Analysis Overview Card
            st.markdown("""
            <div class='modern-card'>
                <h3>📊 Energy Consumption Analysis</h3>
                <ul>
                    <li><strong>Total Consumption:</strong> {total_consumption} kWh/month</li>
                    <li><strong>Regional Comparison:</strong> {regional_comparison}</li>
                    <li><strong>Peak Usage Time:</strong> {peak_usage}</li>
                    <li><strong>Carbon Footprint:</strong> {carbon_footprint} kg CO₂/month</li>
                </ul>
            </div>
            """.format(
                total_consumption="{:.1f}".format(st.session_state.recommendations["analysis"]["total_consumption"]),
                regional_comparison=st.session_state.recommendations["analysis"]["regional_comparison"],
                peak_usage=st.session_state.recommendations["analysis"]["peak_usage"],
                carbon_footprint="{:.1f}".format(st.session_state.recommendations["analysis"]["carbon_footprint"])
            ), unsafe_allow_html=True)

            # Per-Appliance Analysis
            st.subheader("📱 Appliance-wise Breakdown")
            for app in st.session_state.recommendations["appliance_analysis"]:
                with st.expander(f"{app['name']} Analysis"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Current Usage", f"{app['current_consumption']:.1f} kWh")
                        st.metric("Monthly Cost", f"₹{app['current_cost']:.2f}")
                    with col2:
                        st.metric("Potential Savings", f"{app['potential_savings_kwh']:.1f} kWh")
                        st.metric("Cost Savings", f"₹{app['potential_savings_money']:.2f}")
                    
                    st.markdown("#### Optimization Steps:")
                    for step in app['optimization_steps']:
                        st.markdown(f"• {step}")
                    
                    st.info(f"💡 **Upgrade Suggestion:** {app['upgrade_suggestions']}")
                    st.caption(f"Return on Investment: {app['roi_months']} months")

            # Recommendations Section
            st.subheader("🎯 Recommended Actions")
            for rec in st.session_state.recommendations["recommendations"]:
                with st.container():
                    st.markdown(f"""
                    <div class='modern-card'>
                        <h3>{rec['title']}</h3>
                        <p>{rec['description']}</p>
                        <table>
                            <tr>
                                <td><strong>Implementation Cost:</strong></td>
                                <td>₹{rec['implementation_cost']:,.2f}</td>
                            </tr>
                            <tr>
                                <td><strong>Annual Energy Savings:</strong></td>
                                <td>{rec['annual_savings_kwh']:,.1f} kWh</td>
                            </tr>
                            <tr>
                                <td><strong>Annual Cost Savings:</strong></td>
                                <td>₹{rec['annual_savings_money']:,.2f}</td>
                            </tr>
                            <tr>
                                <td><strong>Payback Period:</strong></td>
                                <td>{rec['payback_period_months']} months</td>
                            </tr>
                        </table>
                        <p><strong>Priority:</strong> <span class="badge">{rec['difficulty']}</span></p>
                    </div>
                    """, unsafe_allow_html=True)

            # Renewable Energy Options
            st.subheader("🌞 Renewable Energy Solutions")
            for renewable in st.session_state.recommendations["renewable_suggestions"]:
                with st.container():
                    st.markdown(f"""
                    <div class='modern-card'>
                        <h3>{renewable['technology']}</h3>
                        <table>
                            <tr>
                                <td><strong>Initial Investment:</strong></td>
                                <td>₹{renewable['initial_cost']:,.2f}</td>
                            </tr>
                            <tr>
                                <td><strong>Annual Production:</strong></td>
                                <td>{renewable['annual_production']:,.1f} kWh</td>
                            </tr>
                            <tr>
                                <td><strong>Annual Savings:</strong></td>
                                <td>₹{renewable['annual_savings']:,.2f}</td>
                            </tr>
                            <tr>
                                <td><strong>Payback Period:</strong></td>
                                <td>{renewable['payback_period_years']:.1f} years</td>
                            </tr>
                        </table>
                        <p><strong>Available Incentives:</strong> {renewable['incentives_available']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Please enter your household and appliance information in the Input Data tab to get personalized recommendations.")

    # Tab 3: Progress Tracking
    with tab3:
        st.header("Track Your Energy Savings")
        
        # Fix the condition check for historical_data
        if not isinstance(st.session_state.historical_data, list) and hasattr(st.session_state.historical_data, 'empty') and not st.session_state.historical_data.empty:
            # Display progress towards target
            data = st.session_state.historical_data
            current_month_idx = min(2, len(data) - 1)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<div class='metric-card'>", unsafe_allow_html=True)
                start_consumption = data.iloc[0]["baseline"]
                current_consumption = data.iloc[current_month_idx]["consumption"]
                savings_pct = ((start_consumption - current_consumption) / start_consumption) * 100
                st.metric("Current Savings", f"{savings_pct:.1f}% reduction")
                
                # Ensure monthly_targets exists before updating
                if 'monthly_targets' not in st.session_state:
                    st.session_state.monthly_targets = {'current': 0, 'target': 0}
                st.session_state.monthly_targets["current"] = start_consumption - current_consumption
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col2:
                st.markdown(f"<div class='metric-card'>", unsafe_allow_html=True)
                if st.session_state.monthly_targets["target"] > 0:
                    progress = min(st.session_state.monthly_targets["current"] / st.session_state.monthly_targets["target"], 1.0)
                    st.markdown(f"### Target Progress: {progress*100:.1f}%")
                    st.progress(progress)
                    remaining = max(0, st.session_state.monthly_targets["target"] - st.session_state.monthly_targets["current"])
                    st.markdown(f"{remaining:.1f} kWh remaining to reach your monthly target")
                else:
                    st.markdown("No target set yet")
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Energy consumption chart
            st.subheader("Energy Consumption Over Time")
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # Plot baseline as a dashed line
            ax.plot(data["month"], data["baseline"], 'k--', label="Baseline")
            
            # Plot consumption with gradient color (from red to green)
            consumption_line = ax.plot(data["month"], data["consumption"], marker='o', linewidth=3, label="Your Consumption")
            
            # Add shaded savings area
            ax.fill_between(data["month"], data["baseline"], data["consumption"], alpha=0.3, color='green')
            
            # Add projections with lighter color
            if current_month_idx < len(data) - 1:
                ax.plot(data["month"][current_month_idx+1:], data["consumption"][current_month_idx+1:], 
                        'o-', alpha=0.5, linewidth=2, color='blue', label="Projected")
            
            ax.set_xlabel("Month")
            ax.set_ylabel("Energy Consumption (kWh)")
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.legend()
            
            # Calculate total projected savings for the title
            total_savings = sum(data["baseline"] - data["consumption"])
            ax.set_title(f"Energy Consumption Trend (Projected Annual Savings: {total_savings:.0f} kWh)")
            
            st.pyplot(fig)
            
            # Achievements and milestones
            st.subheader("Your Energy Saving Milestones")
            
            milestone_cols = st.columns(3)
            with milestone_cols[0]:
                st.markdown(f"<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Consecutive Days", f"{st.session_state.streaks}")
                st.markdown("</div>", unsafe_allow_html=True)
                
            with milestone_cols[1]:
                st.markdown(f"<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("CO₂ Reduction", f"{total_savings * 0.4:.1f} kg")  # Approximate CO2 per kWh
                st.markdown("</div>", unsafe_allow_html=True)
                
            with milestone_cols[2]:
                st.markdown(f"<div class='metric-card'>", unsafe_allow_html=True)
                trees_saved = (total_savings * 0.4) / 20  # Approximate kg CO2 absorbed by a tree annually
                st.metric("Equivalent Trees", f"{trees_saved:.1f}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Log Night Savings", key="log_night"):
                    if not st.session_state.badges["Night Saver"]:
                        st.session_state.badges["Night Saver"] = True
                        st.session_state.points += 50
                        update_user_level()
                        st.success("🌙 Night Savings logged! You earned 50 points and unlocked the Night Saver badge!")
                    else:
                        st.info("You've already earned the Night Saver badge.")
                        
            with col2:
                if st.button("Share Progress"):
                    st.session_state.points += 25
                    update_user_level()
                    st.success("🌟 Progress shared! You earned 25 points!")
                    
        else:
            st.info("No energy tracking data available yet. Generate recommendations and save them to start tracking your progress.")

    # Tab 4: Energy Quiz
    with tab4:
        st.header("Energy Efficiency Quiz")
        st.markdown("Test your knowledge and earn points by answering these questions correctly!")
        
        if not st.session_state.quiz_completed:
            with st.form(key="energy_quiz"):
                st.markdown("### Question 1")
                q1 = st.radio(
                    "Which appliance typically consumes the most energy in a household?",
                    ["Refrigerator", "Television", "Air Conditioner", "Ceiling Fan"]
                )
                
                st.markdown("### Question 2")
                q2 = st.radio(
                    "What does the 'star rating' on appliances indicate?",
                    ["Manufacturing quality", "Energy efficiency", "Water resistance", "Warranty period"]
                )
                
                st.markdown("### Question 3")
                q3 = st.radio(
                    "Which of these actions would save the most energy?",
                    ["Turning off lights when not in use", "Upgrading to a 5-star refrigerator from a 2-star model", 
                     "Unplugging chargers when not in use", "Using a laptop instead of a desktop computer"]
                )
                
                st.markdown("### Question 4")
                q4 = st.radio(
                    "What is the most energy-efficient temperature setting for an air conditioner?",
                    ["16-18°C", "19-21°C", "22-24°C", "25-27°C"]
                )
                
                st.markdown("### Question 5")
                q5 = st.radio(
                    "Which renewable energy source has the highest efficiency for residential use in most regions?",
                    ["Solar panels", "Wind turbines", "Geothermal heat pumps", "Micro-hydropower"]
                )
                
                submit_quiz = st.form_submit_button("Submit Answers")
                
                if submit_quiz:
                    # Check answers (correct answers: AC, Energy efficiency, Upgrade refrigerator, 24-26°C, Solar)
                    score = 0
                    if q1 == "Air Conditioner": score += 1
                    if q2 == "Energy efficiency": score += 1
                    if q3 == "Upgrading to a 5-star refrigerator from a 2-star model": score += 1
                    if q4 == "25-27°C": score += 1
                    if q5 == "Solar panels": score += 1
                    
                    st.session_state.quiz_completed = True
                    points_earned = score * 20
                    st.session_state.points += points_earned
                    update_user_level()
                    
                    # Unlock badge if perfect score
                    if score == 5 and not st.session_state.badges["Energy Genius"]:
                        st.session_state.badges["Energy Genius"] = True
                        
                    st.success(f"Quiz completed! You got {score}/5 correct and earned {points_earned} points!")
                    
                    if score == 5:
                        st.balloons()
                        st.markdown("### 🏆 Perfect Score! You're an Energy Expert!")
        else:
            st.success("You've already completed this week's quiz!")
            
            # Show when the next quiz will be available
            import random
            days_remaining = random.randint(1, 6)
            st.info(f"Next quiz will be available in {days_remaining} days. Check back for more points!")
            
            if st.button("Reset Quiz (Demo Only)"):
                st.session_state.quiz_completed = False
                st.success("Quiz reset! You can take it again.")

if __name__ == "__main__":
    main()  # Run standalone without auth