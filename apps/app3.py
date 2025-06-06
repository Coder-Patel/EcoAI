import streamlit as st
import pandas as pd
import json
import random
import datetime
import os
import google.generativeai as genai
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px

# Set your Gemini API key here
GEMINI_API_KEY = "AIzaSyASnBJDcTM4puEQSrNLJPPRMgAA0wUzeIU"  # Replace with your actual API key

def init_session_state():
    """Initialize session state variables"""
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {
            'level': 'Water Watcher',  
            'points': 0,
            'activities': [],
            'challenges': [],
            'completed_challenges': [],  # Add this key
            'badges': [],
            'water_saved': 0,
            'streak': 0,
            'last_activity_date': None,
            'conservation_tips': [],
            'goals': {
                'daily_target': 0,
                'weekly_target': 0,
                'monthly_target': 0
            },
            'spin_available': False,
            'history': [],
            'last_login': None
        }
    else:
        # Ensure all required keys exist
        required_keys = {
            'level': 'Water Watcher',
            'points': 0,
            'activities': [],
            'challenges': [],
            'completed_challenges': [],  # Add this key
            'badges': [],
            'water_saved': 0,
            'streak': 0,
            'spin_available': False,
            'last_activity_date': None,
            'history': []
        }
        
        for key, default_value in required_keys.items():
            if key not in st.session_state.user_data:
                st.session_state.user_data[key] = default_value

def main(auth=None):
    """
    Main function for the water conservation app
    Args:
        auth: Authentication object passed from main app, None when running standalone
    """
    # Initialize session state
    init_session_state()
    
    # Load saved data if auth is provided and user is logged in
    if auth and 'user' in st.session_state:
        saved_data = auth.get_user_progress(st.session_state.user, "water")
        if not saved_data.empty:
            latest_data = saved_data.iloc[-1]['data']
            data = json.loads(latest_data)
            st.session_state.user_data.update(data)  # Update existing data

    if 'daily_log' not in st.session_state:
        st.session_state.daily_log = False

    if 'api_configured' not in st.session_state:
        st.session_state.api_configured = False

    # Gemini API configuration
    def configure_genai_api():
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-pro')
            st.session_state.api_configured = True
            st.session_state.model = model
            return True
        except Exception as e:
            st.error(f"Error configuring Gemini API: {e}")
            return False

    # Configure API on app startup
    if not st.session_state.api_configured:
        configure_genai_api()

    # Water usage benchmarks (in gallons)
    WATER_USAGE = {
        'shower': {'standard': 17.2, 'efficient': 8.0},  # 8-min shower
        'bath': {'standard': 30.0, 'efficient': 20.0},
        'toilet_flush': {'standard': 1.6, 'efficient': 0.8},
        'dishwashing_by_hand': {'standard': 27.0, 'efficient': 8.0},
        'dishwasher': {'standard': 6.0, 'efficient': 4.0},
        'laundry': {'standard': 40.0, 'efficient': 25.0},
        'watering_garden': {'standard': 60.0, 'efficient': 30.0},
        'washing_car': {'standard': 100.0, 'efficient': 40.0},
        'brushing_teeth': {'standard': 4.0, 'efficient': 0.5},  # running water vs cup
    }

    # Levels configuration
    LEVELS = [
        {"name": "Water Watcher", "requirement": 0, "description": "Starting your water conservation journey"},
        {"name": "Flow Reducer", "requirement": 50, "description": "Making consistent water-saving choices"},
        {"name": "H2O Hero", "requirement": 150, "description": "Becoming a water conservation champion"},
        {"name": "Hydration Guardian", "requirement": 300, "description": "Mastering water-saving techniques"},
        {"name": "Aqua Savior", "requirement": 500, "description": "Leading by example in water conservation"},
        {"name": "Water Wizard", "requirement": 1000, "description": "Ultimate water conservation master"}
    ]

    # Badge configuration
    BADGES = [
        {"name": "First Save", "requirement": "First water-saving activity"},
        {"name": "Week Warrior", "requirement": "7-day streak"},
        {"name": "Challenge Champion", "requirement": "Complete 5 challenges"},
        {"name": "Big Saver", "requirement": "Save 100 gallons total"},
        {"name": "Eco Enthusiast", "requirement": "Log activities for 30 days"},
    ]

    # Daily challenges pool
    DAILY_CHALLENGES = [
        {"name": "5-Minute Shower", "description": "Take a shower in 5 minutes or less", "points": 15, "water_saved": 5},
        {"name": "Leaky Faucet Hunter", "description": "Check and fix any leaky faucets in your home", "points": 20, "water_saved": 10},
        {"name": "Full Load Only", "description": "Only run full loads of laundry or dishes today", "points": 15, "water_saved": 15},
        {"name": "Bucket Brigade", "description": "Use a bucket to collect water while waiting for shower to warm up", "points": 10, "water_saved": 2},
        {"name": "Sprinkler Supervisor", "description": "Adjust sprinkler system to reduce waste or water plants in the morning", "points": 25, "water_saved": 20},
        {"name": "Rainwater Collector", "description": "Set up a simple rainwater collection system", "points": 30, "water_saved": 30},
        {"name": "Mindful Dishwashing", "description": "Use a dishpan instead of running water", "points": 20, "water_saved": 15},
        {"name": "Rain Collector", "description": "Set up a container to collect rainwater", "points": 25, "water_saved": 20},
        {"name": "Shower Master", "description": "Use a timer for your shower today", "points": 15, "water_saved": 8},
        {"name": "Leak Detective", "description": "Check all faucets and pipes for leaks", "points": 20, "water_saved": 10}
    ]

    # Conservation tips for each activity
    CONSERVATION_TIPS = {
        'shower': "Try using a shower timer and low-flow showerhead. Aim for 5-minute showers.",
        'bath': "Consider switching to showers or reusing bath water for plants.",
        'toilet_flush': "Install a dual-flush system or place a water displacement device in the tank.",
        'dishwashing_by_hand': "Use a dishpan instead of running water continuously.",
        'dishwasher': "Only run full loads and use eco-mode when available.",
        'laundry': "Collect full loads and use cold water when possible.",
        'watering_garden': "Water early morning or late evening, use mulch to retain moisture.",
        'washing_car': "Use a bucket and sponge instead of running hose.",
        'brushing_teeth': "Use a cup of water instead of running tap."
    }

    # Function to calculate water bill savings
    def calculate_water_savings(gallons_saved):
        # Average water rate per gallon (you can adjust this)
        RATE_PER_GALLON = 0.004
        return round(gallons_saved * RATE_PER_GALLON, 2)

    # Function to update level based on water saved
    def update_level():
        current_water_saved = st.session_state.user_data['water_saved']
        
        for level in reversed(LEVELS):
            if current_water_saved >= level["requirement"]:
                if st.session_state.user_data['level'] != level["name"]:
                    st.session_state.user_data['level'] = level["name"]
                    st.success(f"Level Up! You are now a {level['name']}!")
                break

    # Function to update streak
    def update_streak():
        today = datetime.now().date()
        last_login = st.session_state.user_data['last_login']
        
        if last_login:
            last_login_date = datetime.strptime(last_login, "%Y-%m-%d").date()
            
            if today == last_login_date + timedelta(days=1):
                st.session_state.user_data['streak'] += 1
                if st.session_state.user_data['streak'] == 7:
                    award_badge("Week Warrior")
            elif today > last_login_date:
                st.session_state.user_data['streak'] = 1
        else:
            st.session_state.user_data['streak'] = 1
        
        st.session_state.user_data['last_login'] = today.strftime("%Y-%m-%d")

    # Function to check and award badges
    def award_badge(badge_name):
        if badge_name not in st.session_state.user_data['badges']:
            st.session_state.user_data['badges'].append(badge_name)
            st.balloons()
            st.success(f"You earned the '{badge_name}' badge!")

    # Function to add new water-saving activity
    def add_activity(activity_type, duration=None, count=None, is_efficient=False):
        water_used_standard = 0
        water_used_efficient = 0
        activity_data = {}
        
        if activity_type in WATER_USAGE:
            if duration is not None:  # For duration-based activities
                water_used_standard = WATER_USAGE[activity_type]['standard'] * (duration / 8 if activity_type == 'shower' else duration)
                water_used_efficient = WATER_USAGE[activity_type]['efficient'] * (duration / 8 if activity_type == 'shower' else duration)
            elif count is not None:  # For count-based activities
                water_used_standard = WATER_USAGE[activity_type]['standard'] * count
                water_used_efficient = WATER_USAGE[activity_type]['efficient'] * count
            else:  # For single activities
                water_used_standard = WATER_USAGE[activity_type]['standard']
                water_used_efficient = WATER_USAGE[activity_type]['efficient']
            
            water_used = water_used_efficient if is_efficient else water_used_standard
            water_saved = water_used_standard - water_used if is_efficient else 0
            
            activity_data = {
                'type': activity_type,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'water_used': round(water_used, 2),
                'water_saved': round(water_saved, 2),
                'is_efficient': is_efficient
            }
            
            st.session_state.user_data['activities'].append(activity_data)
            st.session_state.user_data['water_saved'] += water_saved
            
            # Award points for water-saving activities
            if water_saved > 0:
                points_earned = int(water_saved * 2)  # 2 points per gallon saved
                st.session_state.user_data['points'] += points_earned
                
                # Check for spin eligibility
                if st.session_state.user_data['points'] >= 100 and not st.session_state.user_data['spin_available']:
                    st.session_state.user_data['spin_available'] = True
                
                # Log to history
                st.session_state.user_data['history'].append({
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'water_saved': round(water_saved, 2),
                    'points_earned': points_earned
                })
                
                # Award badge for first save
                if len(st.session_state.user_data['activities']) == 1:
                    award_badge("First Save")
                
                # Check for Big Saver badge
                if st.session_state.user_data['water_saved'] >= 100:
                    award_badge("Big Saver")
            
            update_level()
            return activity_data
        
        return None

    # Function to get water-saving recommendations from Gemini
    def get_recommendations(activities):
        if not st.session_state.api_configured:
            return "Error: Gemini API is not configured properly."
        
        activities_summary = ""
        total_water_used = 0
        
        for activity in activities[-10:]:
            activities_summary += f"- {activity['type']}: {activity['water_used']} gallons (Efficient: {activity['is_efficient']})\n"
            total_water_used += activity['water_used']
        
        prompt = f"""
        As a Water Conservation Advisor, analyze the following water usage data and provide detailed recommendations:
        
        Recent Activities:
        {activities_summary}
        
        Total water usage: {total_water_used} gallons
        
        Please provide:
        1. 3-5 specific, actionable water-saving recommendations
        2. Estimated gallons saved per recommendation
        3. Potential cost savings based on average water rates
        4. Long-term conservation strategies
        5. Seasonal adjustments for water usage
        
        Focus on practical, achievable changes that can make a significant impact.
        Include specific tips for the user's most water-intensive activities.
        """
        
        try:
            response = st.session_state.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error getting recommendations: {e}"

    # Function to generate a daily challenge
    def generate_challenge():
        if not st.session_state.user_data['challenges']:
            available_challenges = [c for c in DAILY_CHALLENGES if c["name"] not in st.session_state.user_data['completed_challenges']]
            if available_challenges:
                challenge = random.choice(available_challenges)
                st.session_state.user_data['challenges'] = [challenge]
                return challenge
        return st.session_state.user_data['challenges'][0] if st.session_state.user_data['challenges'] else None

    # Function to complete a challenge
    def complete_challenge():
        if st.session_state.user_data['challenges']:
            challenge = st.session_state.user_data['challenges'][0]
            st.session_state.user_data['points'] += challenge['points']
            st.session_state.user_data['water_saved'] += challenge['water_saved']
            st.session_state.user_data['completed_challenges'].append(challenge['name'])
            st.session_state.user_data['challenges'] = []
            
            # Check for Challenge Champion badge
            if len(st.session_state.user_data['completed_challenges']) >= 5:
                award_badge("Challenge Champion")
            
            st.success(f"Challenge completed! You earned {challenge['points']} points and saved {challenge['water_saved']} gallons.")
            update_level()

    # Function for the water saver wheel
    def spin_wheel():
        if st.session_state.user_data['spin_available']:
            rewards = [
                {"name": "25 Bonus Points", "value": 25, "type": "points"},
                {"name": "50 Bonus Points", "value": 50, "type": "points"},
                {"name": "100 Bonus Points", "value": 100, "type": "points"},
                {"name": "Eco Warrior Badge", "value": "Eco Warrior", "type": "badge"},
                {"name": "Water Master Badge", "value": "Water Master", "type": "badge"},
                {"name": "10 Gallon Bonus", "value": 10, "type": "water"},
                {"name": "20 Gallon Bonus", "value": 20, "type": "water"},
            ]
            
            reward = random.choice(rewards)
            
            if reward["type"] == "points":
                st.session_state.user_data['points'] += reward["value"]
                message = f"You won {reward['value']} bonus points!"
            elif reward["type"] == "badge":
                if reward["value"] not in st.session_state.user_data['badges']:
                    st.session_state.user_data['badges'].append(reward["value"])
                message = f"You won the {reward['value']} badge!"
            elif reward["type"] == "water":
                st.session_state.user_data['water_saved'] += reward["value"]
                message = f"You won a {reward['value']} gallon water saving bonus!"
            
            st.session_state.user_data['spin_available'] = False
            update_level()
            
            return message
        
        return "No spin available. You need 100 points to spin the wheel."

    # Function to save progress
    def save_progress():
        if auth and 'user' in st.session_state:
            progress_data = {
                'activities': st.session_state.user_data['activities'],
                'water_saved': st.session_state.user_data['water_saved'],
                'level': st.session_state.user_data['level'],
                'streak': st.session_state.user_data['streak'],
                'badges': st.session_state.user_data['badges'],
                'challenges': st.session_state.user_data['challenges'],
                'points': st.session_state.user_data['points']
            }
            # Save locally
            auth.save_progress(st.session_state.user, "water", json.dumps(progress_data))
        else:
            st.warning("Progress saving is only available when running as part of the main app.")

    # App layout and functionality
    st.title("💧 Water Conservation Advisor")

    # Sidebar for user stats and gamification
    with st.sidebar:
        st.header("Your Profile")
        
        # API status indicator
        if st.session_state.api_configured:
            st.success("Gemini AI Connected")
        else:
            st.error("Gemini AI Not Connected")
        
        # User stats
        st.subheader(f"Level: {st.session_state.user_data['level']}")
        st.progress(min(1.0, st.session_state.user_data['water_saved'] / LEVELS[-1]["requirement"]))
        
        st.metric("Water Saved", f"{st.session_state.user_data['water_saved']:.1f} gallons")
        st.metric("Points", st.session_state.user_data['points'])
        st.metric("Streak", f"{st.session_state.user_data['streak']} days")
        
        # Badges
        if st.session_state.user_data['badges']:
            st.subheader("Your Badges")
            for badge in st.session_state.user_data['badges']:
                st.success(badge)
        
        # Water Saver Wheel
        st.subheader("Water Saver Wheel")
        if st.session_state.user_data['spin_available']:
            if st.button("Spin the Wheel"):
                result = spin_wheel()
                st.balloons()
                st.success(result)
        else:
            st.write(f"Earn {100 - (st.session_state.user_data['points'] % 100)} more points to spin")

        # Add save button in sidebar
        if auth:
            st.sidebar.markdown("---")
            if st.sidebar.button("💾 Save Progress"):
                save_progress()

    # Main content area
    tabs = st.tabs(["Log Water Usage", "Daily Challenge", "Recommendations", "Analytics"])

    with tabs[0]:
        st.header("Log Your Water Usage")
        
        activity_type = st.selectbox(
            "Select Activity",
            options=list(WATER_USAGE.keys()),
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        # Dynamically adjust input fields based on activity type
        if activity_type in ['shower', 'bath', 'dishwashing_by_hand', 'watering_garden']:
            duration = st.slider(f"Duration (minutes)", 1, 60, 10)
            is_efficient = st.checkbox("Used water-saving method")
            
            if st.button("Log Activity"):
                result = add_activity(activity_type, duration=duration, is_efficient=is_efficient)
                if result:
                    st.success(f"Logged {activity_type} for {duration} minutes")
                    if is_efficient:
                        st.info(f"You saved {result['water_saved']:.1f} gallons by using efficient methods!")
                update_streak()
        
        elif activity_type in ['toilet_flush', 'dishwasher', 'laundry', 'washing_car', 'brushing_teeth']:
            count = st.number_input(f"Number of times", 1, 20, 1)
            is_efficient = st.checkbox("Used water-saving method")
            
            if st.button("Log Activity"):
                result = add_activity(activity_type, count=count, is_efficient=is_efficient)
                if result:
                    st.success(f"Logged {count} {activity_type}")
                    if is_efficient:
                        st.info(f"You saved {result['water_saved']:.1f} gallons by using efficient methods!")
                update_streak()

    with tabs[1]:
        st.header("Daily Challenge")
        
        challenge = generate_challenge()
        
        if challenge:
            st.subheader(challenge["name"])
            st.write(challenge["description"])
            st.write(f"Reward: {challenge['points']} points + {challenge['water_saved']} gallons saved")
            
            if st.button("Mark as Completed"):
                complete_challenge()
        else:
            st.write("All challenges completed for today. Check back tomorrow!")

    with tabs[2]:
        st.header("Your Water-Saving Recommendations")
        
        if st.button("Get Personalized Recommendations"):
            if st.session_state.api_configured and st.session_state.user_data['activities']:
                with st.spinner("Generating recommendations with Gemini..."):
                    recommendations = get_recommendations(st.session_state.user_data['activities'])
                    st.markdown(recommendations)
            elif not st.session_state.api_configured:
                st.warning("Gemini API connection issue. Please contact the administrator.")
            elif not st.session_state.user_data['activities']:
                st.warning("Log some water usage activities first to get personalized recommendations")

    with tabs[3]:
        st.header("Water Usage Analytics")
        
        if st.session_state.user_data['activities']:
            # Prepare data for charts
            df_activities = pd.DataFrame(st.session_state.user_data['activities'])
            
            # Convert timestamp to datetime
            df_activities['timestamp'] = pd.to_datetime(df_activities['timestamp'])
            df_activities['date'] = df_activities['timestamp'].dt.date
            
            # Daily water usage chart
            daily_usage = df_activities.groupby('date')['water_used'].sum().reset_index()
            
            st.subheader("Daily Water Usage")
            fig1 = px.bar(daily_usage, x='date', y='water_used', 
                         labels={'water_used': 'Gallons Used', 'date': 'Date'},
                         title="Daily Water Consumption")
            st.plotly_chart(fig1)
            
            # Activity breakdown chart
            activity_breakdown = df_activities.groupby('type')['water_used'].sum().reset_index()
            
            st.subheader("Water Usage by Activity")
            fig2 = px.pie(activity_breakdown, values='water_used', names='type',
                         title="Water Usage Distribution by Activity")
            st.plotly_chart(fig2)
            
            # Water saved over time
            if any(df_activities['water_saved'] > 0):
                daily_saved = df_activities.groupby('date')['water_saved'].sum().reset_index()
                daily_saved = daily_saved[daily_saved['water_saved'] > 0]
                
                st.subheader("Water Saved Over Time")
                fig3 = px.line(daily_saved, x='date', y='water_saved',
                              labels={'water_saved': 'Gallons Saved', 'date': 'Date'},
                              title="Daily Water Savings")
                st.plotly_chart(fig3)
            
            # Efficiency comparison
            if len(df_activities) > 5:
                st.subheader("Standard vs. Efficient Usage")
                
                efficient_count = len(df_activities[df_activities['is_efficient']])
                standard_count = len(df_activities) - efficient_count
                
                efficient_data = df_activities[df_activities['is_efficient']]['water_used'].sum()
                standard_data = df_activities[~df_activities['is_efficient']]['water_used'].sum()
                
                comparison_data = pd.DataFrame({
                    'method': ['Standard', 'Efficient'],
                    'activities': [standard_count, efficient_count],
                    'water_used': [standard_data, efficient_data]
                })
                
                fig4 = px.bar(comparison_data, x='method', y='water_used',
                             labels={'water_used': 'Gallons Used', 'method': 'Method'},
                             title="Standard vs. Efficient Water Usage")
                st.plotly_chart(fig4)
            
            # Add water savings impact
            if st.session_state.user_data['water_saved'] > 0:
                st.subheader("Your Conservation Impact")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Water Saved", 
                             f"{st.session_state.user_data['water_saved']:.1f} gallons")
                
                with col2:
                    money_saved = calculate_water_savings(st.session_state.user_data['water_saved'])
                    st.metric("Estimated Money Saved", 
                             f"${money_saved:.2f}")
                
                with col3:
                    trees_equivalent = st.session_state.user_data['water_saved'] / 100
                    st.metric("Environmental Impact", 
                             f"{trees_equivalent:.1f} trees worth of water")
                
                # Add conservation tips based on usage patterns
                st.subheader("Personalized Conservation Tips")
                if len(df_activities) > 0:
                    most_used = df_activities.groupby('type')['water_used'].sum().idxmax()
                    st.info(f"💡 Tip for your highest water usage activity ({most_used}): "
                           f"{CONSERVATION_TIPS[most_used]}")
        else:
            st.info("Log some water usage activities to see analytics here")

    # Add a save/load system
    st.sidebar.subheader("Data Management")

    if st.sidebar.button("Save Data"):
        data_json = json.dumps(st.session_state.user_data)
        st.sidebar.download_button(
            label="Download Your Data",
            data=data_json,
            file_name="water_conservation_data.json",
            mime="application/json"
        )

    uploaded_file = st.sidebar.file_uploader("Load Previous Data", type="json")
    if uploaded_file is not None:
        try:
            uploaded_data = json.load(uploaded_file)
            st.session_state.user_data = uploaded_data
            st.sidebar.success("Data loaded successfully!")
        except Exception as e:
            st.sidebar.error(f"Error loading data: {e}")

    # Reset button for testing
    if st.sidebar.button("Reset All Data"):
        st.session_state.user_data = {
            'activities': [],
            'water_saved': 0,
            'level': "Water Watcher",
            'streak': 0,
            'last_login': None,
            'points': 0,
            'badges': [],
            'challenges': [],
            'completed_challenges': [],
            'spin_available': False,
            'history': []
        }
        st.sidebar.success("All data reset!")

if __name__ == "__main__":
    main()  # Run standalone without auth