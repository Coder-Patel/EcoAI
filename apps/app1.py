import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import json

# Custom CSS to ensure text is visible everywhere
st.markdown("""
<style>
    /* Ensure all text is black for better visibility */
    .stTextInput, .stSelectbox, .stMultiselect, .stNumberInput, .stDateInput, .stTimeInput {
        color: black !important;
    }
    .css-1djdyxw {
        color: black !important;
    }
    input, textarea, [contenteditable] {
        color: white !important;
    }
    /* Make sure labels above input fields are visible */
    label, .st-be, .st-c0 {
        color: white !important;
        font-weight: bold !important;
        font-size: 20px !important;
    }
    .stMarkdown {
        color: white !important;
    }
    div[data-testid="stForm"] {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    .eco-card {
        background-color: #f0f9f0;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #4CAF50;
        color: black !important;  /* Add this line */
    }
    .eco-card h4, .eco-card p {
        color: black !important;  /* Add this line */
    }
    .challenge-card {
        background-color: #fff8e1;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 4px solid #FFC107;
    }
    .challenge-card h4, .challenge-card p {
        color: black !important;  /* Add this line */
    }
    .milestone-card {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 4px solid #2196F3;
    }
    .badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
        margin-right: 5px;
        margin-bottom: 5px;
        background-color: #4CAF50;
        color: black;
    }
    .travel-progress {
        height: 30px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    /* Style for placeholder text */
    ::placeholder {
        color: #808080 !important;
        opacity: 0.5 !important;
    }
    /* Ensure form labels are visible */
    p, span, label, .stTextInput > div > div > label {
        color: white !important;
    }
    /* Input field labels need strong contrast */
    .stTextInput > label, .stSelectbox > label, .stNumberInput > label {
        color: black !important;
        font-weight: bold !important;
    }
    /* Style for form fields */
    .form-field {
        background-color: #2e3136;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .form-field label {
        color: white !important;
        font-weight: bold;
        margin-bottom: 5px;
        display: block;
    }
</style>
""", unsafe_allow_html=True)

# Your Gemini API key - hard coded so users don't need to enter it
GEMINI_API_KEY = "AIzaSyASnBJDcTM4puEQSrNLJPPRMgAA0wUzeIU"  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)

# Define transportation modes and their carbon footprint (g CO2 per km)
transport_emissions = {
    'Car (Gasoline)': 192,
    'Car (Diesel)': 171,
    'Car (Hybrid)': 111,
    'Electric Vehicle': 53,
    'Motorcycle': 103,
    'Bus': 105,
    'Train/Subway': 41,
    'Tram/Light Rail': 35, 
    'Carpool (4 people)': 48,
    'Bicycle': 0,
    'Walking': 0,
    'E-scooter': 26,
    'Ferry': 120
}

# Function to generate eco-friendly suggestions using Gemini
def generate_suggestions(travel_data, carbon_footprint):
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Prepare the prompt with detailed travel data
        prompt = f"""
        As an eco-friendly transportation planner, analyze the following user's travel data and provide personalized suggestions for more sustainable transportation options:

        Current weekly travel habits:
        {travel_data}
        
        Current estimated carbon footprint: {carbon_footprint} kg CO2 per week
        
        Please provide:
        1. 3-5 specific recommendations to reduce the carbon footprint
        2. Suggested eco-friendly alternative routes for the most carbon-intensive trips
        3. One weekly challenge to help build more sustainable travel habits
        4. An estimate of potential carbon savings if recommendations are followed (as a percentage)
        
        Format the output in a concise, actionable way that motivates the user to make eco-friendly changes.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating suggestions: {str(e)}"

# Function to add travel data
def auto_save_on_action():
    """Automatically save progress if auth is available"""
    if 'auth' in st.session_state and 'user' in st.session_state:
        progress_data = {
            'travel_data': st.session_state.travel_data,
            'carbon_footprint': st.session_state.carbon_footprint,
            'eco_points': st.session_state.eco_points,
            'badges': st.session_state.badges,
            'milestones': st.session_state.milestones,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.auth.save_progress(st.session_state.user, "transport", json.dumps(progress_data))

def add_travel_data(start_point, end_point, distance, frequency, mode):
    # Calculate weekly carbon footprint
    weekly_distance = distance * frequency
    carbon_per_km = transport_emissions.get(mode, 0)
    weekly_carbon = (weekly_distance * carbon_per_km) / 1000  # Convert to kg
    
    travel_entry = {
        'start_point': start_point,
        'end_point': end_point,
        'distance': distance,
        'frequency': frequency,
        'mode': mode,
        'weekly_distance': weekly_distance,
        'weekly_carbon': weekly_carbon
    }
    
    st.session_state.travel_data.append(travel_entry)
    st.session_state.carbon_footprint += weekly_carbon
    
    # Update milestones if using eco-friendly options
    if mode == 'Bicycle':
        st.session_state.milestones['bike_distance'] += weekly_distance
        award_milestone_badges('bike')
    elif mode == 'Walking':
        st.session_state.milestones['walk_distance'] += weekly_distance
        award_milestone_badges('walk')
    elif mode == 'Carpool (4 people)':
        st.session_state.milestones['carpool_distance'] += weekly_distance
        award_milestone_badges('carpool')
    elif mode in ['Bus', 'Train/Subway', 'Tram/Light Rail']:
        st.session_state.milestones['public_transit_distance'] += weekly_distance
        award_milestone_badges('public_transit')
    elif mode == 'Electric Vehicle':
        st.session_state.milestones['ev_distance'] += weekly_distance
        award_milestone_badges('ev')
    
    # Award eco points based on transportation mode
    if mode in ['Bicycle', 'Walking']:
        st.session_state.eco_points += int(weekly_distance * 5)  # 5 points per km
    elif mode in ['Bus', 'Train/Subway', 'Tram/Light Rail', 'Carpool (4 people)']:
        st.session_state.eco_points += int(weekly_distance * 3)  # 3 points per km
    elif mode == 'Electric Vehicle':
        st.session_state.eco_points += int(weekly_distance * 2)  # 2 points per km
    else:
        st.session_state.eco_points += int(weekly_distance * 0.5)  # 0.5 points per km

    auto_save_on_action()

# Function to award badges for milestones
def award_milestone_badges(transport_type):
    milestones = {
        'bike': [
            {'distance': 10, 'badge': '🚲 First 10 Miles Biked'},
            {'distance': 50, 'badge': '🚲 Cycling Enthusiast (50 miles)'},
            {'distance': 100, 'badge': '🚲 Cycling Pro (100 miles)'}
        ],
        'walk': [
            {'distance': 5, 'badge': '👟 First 5 Miles Walked'},
            {'distance': 25, 'badge': '👟 Walking Enthusiast (25 miles)'},
            {'distance': 50, 'badge': '👟 Walking Pro (50 miles)'}
        ],
        'carpool': [
            {'distance': 20, 'badge': '🚗 First 20 Miles Carpooled'},
            {'distance': 75, 'badge': '🚗 Carpool Champion (75 miles)'},
            {'distance': 150, 'badge': '🚗 Carpool Master (150 miles)'}
        ],
        'transit': [
            {'distance': 30, 'badge': '🚆 First 30 Miles on Public Transit'},
            {'distance': 100, 'badge': '🚆 Transit Explorer (100 miles)'},
            {'distance': 200, 'badge': '🚆 Transit Expert (200 miles)'}
        ],
        'ev': [
            {'distance': 50, 'badge': '⚡ First 50 Miles in an EV'},
            {'distance': 150, 'badge': '⚡ EV Enthusiast (150 miles)'},
            {'distance': 300, 'badge': '⚡ EV Champion (300 miles)'}
        ]
    }
    
    current_distance = st.session_state.milestones[f'{transport_type}_distance']
    
    for milestone in milestones.get(transport_type, []):
        if current_distance >= milestone['distance'] and milestone['badge'] not in st.session_state.badges:
            st.session_state.badges.append(milestone['badge'])
            st.session_state.eco_points += 50  # Bonus points for achieving milestone

# Function to get active challenges
def get_available_challenges():
    challenges = [
        {
            'title': 'Walk to Work Week',
            'description': 'Replace at least 3 car trips with walking this week',
            'points': 100,
            'icon': '👟'
        },
        {
            'title': 'Carpool Month',
            'description': 'Share at least 5 rides with others this month',
            'points': 150,
            'icon': '🚗'
        },
        {
            'title': 'Public Transit Explorer',
            'description': 'Use public transit for at least 4 trips this week',
            'points': 120,
            'icon': '🚆'
        },
        {
            'title': 'Zero Carbon Weekend',
            'description': 'Use only carbon-free transportation (walking, biking) for an entire weekend',
            'points': 200,
            'icon': '🌱'
        },
        {
            'title': 'New Route Pioneer',
            'description': 'Discover and use 3 new eco-friendly routes to regular destinations',
            'points': 180,
            'icon': '🧭'
        }
    ]
    return challenges

# Function to join challenge
def join_challenge(challenge):
    if challenge not in st.session_state.active_challenges:
        st.session_state.active_challenges.append(challenge)
        return True
    return False

# Function to complete challenge (simulated)
def complete_challenge(challenge_index):
    challenge = st.session_state.active_challenges.pop(challenge_index)
    st.session_state.completed_challenges.append(challenge)
    st.session_state.eco_points += challenge['points']
    
    # Add a badge for completing challenge
    badge_name = f"{challenge['icon']} {challenge['title']} Completed"
    if badge_name not in st.session_state.badges:
        st.session_state.badges.append(badge_name)

    auto_save_on_action()

# Function to add travel buddy
def add_travel_buddy(name, common_route):
    buddy = {
        'name': name,
        'common_route': common_route,
        'points': random.randint(50, 200),
        'eco_trips': random.randint(3, 15)
    }
    st.session_state.travel_buddies.append(buddy)

def init_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        reset_session_state()
    elif 'last_user' not in st.session_state or st.session_state.last_user != st.session_state.user:
        # Reset data if user changed
        reset_session_state()
        st.session_state.last_user = st.session_state.user

def reset_session_state():
    """Reset all session state variables to default values"""
    st.session_state.travel_data = []
    st.session_state.carbon_footprint = 0
    st.session_state.eco_points = 0
    st.session_state.active_challenges = []
    st.session_state.completed_challenges = []
    st.session_state.milestones = {
        'bike_distance': 0,
        'walk_distance': 0,
        'carpool_distance': 0,
        'public_transit_distance': 0,
        'ev_distance': 0
    }
    st.session_state.badges = []
    st.session_state.travel_buddies = []
    st.session_state.suggestion_history = []

def main(auth=None):
    """Main function for the transportation app"""
    # Initialize session state
    init_session_state()
    
    # Load saved data if auth is provided
    if auth and 'user' in st.session_state:
        try:
            saved_data = auth.get_user_progress(st.session_state.user, "transport")
            if not saved_data.empty:
                latest_data = saved_data.iloc[-1]['data']
                data = json.loads(latest_data)
                # Update session state with saved data
                st.session_state.travel_data = data.get('travel_data', [])
                st.session_state.carbon_footprint = data.get('carbon_footprint', 0)
                st.session_state.eco_points = data.get('eco_points', 0)  # Add this
                st.session_state.badges = data.get('badges', [])
                st.session_state.milestones = data.get('milestones', st.session_state.milestones)
        except Exception as e:
            st.error(f"Error loading saved data: {str(e)}")

    def save_progress():
        """Save progress if auth is available"""
        if auth and 'user' in st.session_state:
            progress_data = {
                'travel_data': st.session_state.travel_data,
                'carbon_footprint': st.session_state.carbon_footprint,
                'eco_points': st.session_state.eco_points,
                'badges': st.session_state.badges,
                'milestones': st.session_state.milestones
            }
            # Save locally only
            auth.save_progress(st.session_state.user, "transport", json.dumps(progress_data))
            st.success("Progress saved!")

    # Add save button in sidebar only if auth is available
    if auth:
        st.sidebar.markdown("---")
        if st.sidebar.button("💾 Save Progress"):
            save_progress()

    # Automatically save progress after significant actions if auth is available
    def auto_save_on_action():
        if auth and 'user' in st.session_state:
            save_progress()

    # Main app layout
    st.title("🌿 Eco-Friendly Transportation Planner")

    # Sidebar for stats
    with st.sidebar:
        st.header("Your Stats")
        st.metric("Eco Points", st.session_state.eco_points)
        st.metric("Carbon Footprint", f"{st.session_state.carbon_footprint:.2f} kg CO2/week")
        
        # Display badges
        if st.session_state.badges:
            st.subheader("Your Badges")
            for badge in st.session_state.badges:
                st.markdown(f'<div class="badge">{badge}</div>', unsafe_allow_html=True)

    # Create tabs for different functions
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Travel Log", "Suggestions", "Challenges", "Milestones", "Travel Buddies"])

    # Tab 1: Travel Log
    with tab1:
        st.header("Log Your Travel")
        
        # Move form to the top
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<label style='color:white; font-weight:bold;'>Starting Point</label>", unsafe_allow_html=True)
            start_point = st.text_input("", placeholder="e.g. Home", key="start_point_input")
            
            st.markdown("<label style='color:white; font-weight:bold;'>Distance (miles)</label>", unsafe_allow_html=True)
            distance = st.number_input("", min_value=0.1, value=5.0, step=0.1, key="distance_input")
        
        with col2:
            st.markdown("<label style='color:white; font-weight:bold;'>Destination</label>", unsafe_allow_html=True)
            end_point = st.text_input("", placeholder="e.g. Office", key="end_point_input")
            
            st.markdown("<label style='color:white; font-weight:bold;'>Weekly Frequency</label>", unsafe_allow_html=True)
            frequency = st.number_input("", min_value=1, value=5, step=1, key="frequency_input")
        
        st.markdown("<label style='color:white; font-weight:bold;'>Transportation Mode</label>", unsafe_allow_html=True)
        mode = st.selectbox("", options=list(transport_emissions.keys()), key="mode_input")
        
        if st.button("Add Travel Data"):
            if start_point and end_point:
                add_travel_data(start_point, end_point, distance, frequency, mode)
                st.success("Travel data added successfully!")
            else:
                st.error("Please fill in both starting point and destination.")
        
        # Display travel log in the middle
        if st.session_state.travel_data:
            st.subheader("Your Travel Log")
            
            for i, trip in enumerate(st.session_state.travel_data):
                st.markdown(f"""
                <div class="eco-card">
                    <h4>{trip['start_point']} to {trip['end_point']}</h4>
                    <p>Distance: {trip['distance']} miles | Frequency: {trip['frequency']} times/week</p>
                    <p>Mode: {trip['mode']}</p>
                    <p>Weekly carbon: {trip['weekly_carbon']:.2f} kg CO2</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Move chart to the bottom
        if st.session_state.travel_data:
            st.markdown("---")  # Add a separator
            st.subheader("Carbon Footprint Breakdown")
            
            # Update carbon footprint breakdown chart
            def update_carbon_chart():
                carbon_by_mode = {}
                for trip in st.session_state.travel_data:
                    mode = trip['mode']
                    carbon_by_mode[mode] = carbon_by_mode.get(mode, 0) + trip['weekly_carbon']
                
                fig, ax = plt.subplots(figsize=(10, 6))
                modes = list(carbon_by_mode.keys())
                carbon_values = list(carbon_by_mode.values())
                
                # Define colors for the pie chart
                colors = plt.cm.Greens(np.linspace(0.3, 0.8, len(modes)))
                
                wedges, texts, autotexts = ax.pie(
                    carbon_values, 
                    labels=modes,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colors
                )
                
                # Ensure the text is visible
                for text in texts:
                    text.set_color('black')
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                ax.axis('equal')
                plt.title('Weekly Carbon Footprint by Transportation Mode')
                return fig
            
            # Display the chart
            st.pyplot(update_carbon_chart())

    # Tab 2: Suggestions
    with tab2:
        st.header("Eco-Friendly Suggestions")
        
        if not st.session_state.travel_data:
            st.info("Add travel data in the Travel Log tab to get personalized suggestions.")
        else:
            if st.button("Generate Eco-Friendly Suggestions"):
                with st.spinner("Generating eco-friendly suggestions with Gemini 1.5 Pro..."):
                    # Prepare travel data for the API
                    travel_summary = "\n".join([
                        f"- Trip from {trip['start_point']} to {trip['end_point']}: {trip['distance']} miles, {trip['frequency']} times/week, using {trip['mode']} ({trip['weekly_carbon']:.2f} kg CO2/week)"
                        for trip in st.session_state.travel_data
                    ])
                    
                    suggestions = generate_suggestions(travel_summary, st.session_state.carbon_footprint)
                    st.session_state.suggestion_history.append({
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'content': suggestions
                    })
            
            # Display suggestion history
            if st.session_state.suggestion_history:
                st.subheader("Latest Suggestion")
                st.markdown(st.session_state.suggestion_history[-1]['content'])
                
                if len(st.session_state.suggestion_history) > 1:
                    with st.expander("View Previous Suggestions"):
                        for i, suggestion in enumerate(reversed(st.session_state.suggestion_history[:-1])):
                            st.markdown(f"**{suggestion['timestamp']}**")
                            st.markdown(suggestion['content'])
                            st.divider()

    # Tab 3: Challenges
    with tab3:
        st.header("Eco Challenges")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Available Challenges")
            challenges = get_available_challenges()
            
            for i, challenge in enumerate(challenges):
                if challenge not in st.session_state.active_challenges and challenge not in st.session_state.completed_challenges:
                    st.markdown(f"""
                    <div class="challenge-card">
                        <h4>{challenge['icon']} {challenge['title']}</h4>
                        <p>{challenge['description']}</p>
                        <p>Reward: {challenge['points']} eco-points</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Join Challenge", key=f"join_{i}"):
                        if join_challenge(challenge):
                            st.success(f"You joined the {challenge['title']} challenge!")
                            st.rerun()
        
        with col2:
            st.subheader("Your Active Challenges")
            if not st.session_state.active_challenges:
                st.info("You haven't joined any challenges yet.")
            else:
                for i, challenge in enumerate(st.session_state.active_challenges):
                    st.markdown(f"""
                    <div class="challenge-card">
                        <h4>{challenge['icon']} {challenge['title']}</h4>
                        <p>{challenge['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Simulating challenge progress
                    progress = random.uniform(0.1, 0.9)
                    st.progress(progress)
                    
                    if st.button(f"Mark as Completed", key=f"complete_{i}"):
                        complete_challenge(i)
                        st.success(f"Congratulations! You completed the {challenge['title']} challenge and earned {challenge['points']} eco-points!")
                        st.rerun()
            
            st.divider()
            
            st.subheader("Completed Challenges")
            if not st.session_state.completed_challenges:
                st.info("You haven't completed any challenges yet.")
            else:
                for challenge in st.session_state.completed_challenges:
                    st.markdown(f"""
                    <div class="challenge-card">
                        <h4>{challenge['icon']} {challenge['title']} ✅</h4>
                        <p>Earned: {challenge['points']} eco-points</p>
                    </div>
                    """, unsafe_allow_html=True)

    # Tab 4: Milestones
    with tab4:
        st.header("Travel Milestones")
        
        milestones_data = [
            {"name": "Biking", "distance": st.session_state.milestones['bike_distance'], "icon": "🚲", "color": "#4CAF50", "goals": [10, 50, 100]},
            {"name": "Walking", "distance": st.session_state.milestones['walk_distance'], "icon": "👟", "color": "#2196F3", "goals": [5, 25, 50]},
            {"name": "Carpooling", "distance": st.session_state.milestones['carpool_distance'], "icon": "🚗", "color": "#FFC107", "goals": [20, 75, 150]},
            {"name": "Public Transit", "distance": st.session_state.milestones['public_transit_distance'], "icon": "🚆", "color": "#9C27B0", "goals": [30, 100, 200]},
            {"name": "Electric Vehicle", "distance": st.session_state.milestones['ev_distance'], "icon": "⚡", "color": "#FF5722", "goals": [50, 150, 300]}
        ]
        
        for milestone in milestones_data:
            st.subheader(f"{milestone['icon']} {milestone['name']} Distance")
            
            # Find the next goal
            current = milestone['distance']
            next_goal = None
            for goal in milestone['goals']:
                if current < goal:
                    next_goal = goal
                    break
            
            if next_goal:
                progress = current / next_goal
                st.markdown(f"<p>{current:.1f} / {next_goal} miles</p>", unsafe_allow_html=True)
                
                # Custom progress bar
                st.markdown(
                    f"""
                    <div class="travel-progress" style="background-color: #e0e0e0;">
                        <div style="width: {min(progress * 100, 100)}%; height: 100%; background-color: {milestone['color']}; 
                            border-radius: 5px; text-align: center; line-height: 30px; color: white; 
                            font-weight: bold;">
                            {min(progress * 100, 100):.1f}%
                        </div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                st.markdown(f"Next milestone: **{next_goal} miles**")
            else:
                st.success(f"Congratulations! You've achieved all milestones for {milestone['name']}!")
                st.markdown(f"Total distance: **{current:.1f} miles**")
            
            st.divider()
        
        # Environmental impact visualization
        st.subheader("Your Environmental Impact")
        
        # Calculate carbon savings
        total_eco_miles = sum([
            st.session_state.milestones['bike_distance'],
            st.session_state.milestones['walk_distance'],
            st.session_state.milestones['carpool_distance'] * 0.75,  # 75% reduction compared to solo driving
            st.session_state.milestones['public_transit_distance'] * 0.7,  # 70% reduction compared to solo driving
            st.session_state.milestones['ev_distance'] * 0.6  # 60% reduction compared to gasoline car
        ])
        
        carbon_saved = total_eco_miles * 0.192  # Assuming savings compared to average car (192g CO2/km)
        trees_equivalent = carbon_saved / 20  # Approximate - each tree absorbs about 20kg CO2 per year
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Carbon Saved", f"{carbon_saved:.2f} kg CO2")
        
        with col2:
            st.metric("Equivalent to Trees Planted", f"{trees_equivalent:.1f} trees")
        
        # Tree visualization
        st.markdown("### Trees Equivalent")
        tree_html = ""
        for i in range(min(int(trees_equivalent), 20)):  # Limit to 20 trees max for display
            tree_html += "🌳 "
        
        st.markdown(f"<h1 style='line-height: 1.5'>{tree_html}</h1>", unsafe_allow_html=True)

    # Tab 5: Travel Buddies
    with tab5:
        st.header("Travel Buddies")
        
        # Add new buddy
        with st.expander("Add Travel Buddy"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<label style='color:white; font-weight:bold;'>Buddy Name</label>", unsafe_allow_html=True)
                buddy_name = st.text_input("", key="buddy_name_input")
            with col2:
                st.markdown("<label style='color:white; font-weight:bold;'>Common Route</label>", unsafe_allow_html=True)
                common_route = st.text_input("", placeholder="e.g. 'Home to Office'", key="common_route_input")
            
            if st.button("Add Buddy") and buddy_name and common_route:
                add_travel_buddy(buddy_name, common_route)
                st.success(f"Added {buddy_name} as your travel buddy!")
        
        # Display buddies
        if not st.session_state.travel_buddies:
            st.info("You haven't added any travel buddies yet.")
        else:
            st.subheader("Your Travel Buddies")
            
            col1, col2 = st.columns(2)
            
            for i, buddy in enumerate(st.session_state.travel_buddies):
                with col1 if i % 2 == 0 else col2:
                    st.markdown(f"""
                    <div class="milestone-card">
                        <h4>{buddy['name']}</h4>
                        <p>Common route: {buddy['common_route']}</p>
                        <p>Eco Points: {buddy['points']}</p>
                        <p>Eco-friendly trips: {buddy['eco_trips']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Team challenge
            st.subheader("Team Challenge")
            
            team_challenge = {
                'title': 'Green Commuters of the Month',
                'description': 'Collectively complete 50 eco-friendly trips this month',
                'current': sum(buddy['eco_trips'] for buddy in st.session_state.travel_buddies),
                'target': 50,
                'reward': 500
            }
            
            progress = team_challenge['current'] / team_challenge['target']

            st.markdown(f"### 🏆 {team_challenge['title']}")
            st.markdown(team_challenge['description'])
            st.markdown(f"<p>{team_challenge['current']} / {team_challenge['target']} eco-friendly trips</p>", unsafe_allow_html=True)
            
            # Custom progress bar
            st.markdown(
                f"""
                <div class="travel-progress" style="background-color: #e0e0e0;">
                    <div style="width: {min(progress * 100, 100)}%; height: 100%; background-color: #FFC107; 
                        border-radius: 5px; text-align: center; line-height: 30px; color: white; 
                        font-weight: bold;">
                        {min(progress * 100, 100):.1f}%
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            st.markdown(f"Reward: **{team_challenge['reward']} eco-points**")
            
            if team_challenge['current'] >= team_challenge['target']:
                st.success(f"Congratulations! Your team has completed the {team_challenge['title']} challenge!")
            else:
                st.info(f"Keep going! You need {team_challenge['target'] - team_challenge['current']} more eco-friendly trips to complete this challenge.")
            
            # Carpool matching
            st.subheader("Carpool Matching")
            st.markdown("Find potential carpool matches based on your travel routes")
            
            if st.button("Find Matches"):
                # Simulate finding matches
                with st.spinner("Finding potential carpool matches..."):
                    time.sleep(2)
                    
                    # Show simulated matches
                    st.success("Found 3 potential carpool matches!")
                    
                    matches = [
                        {"name": "Alex", "route": "Downtown to Business Park", "schedule": "Mon-Fri, 8AM-5PM", "compatibility": "85%"},
                        {"name": "Jamie", "route": "Suburb to City Center", "schedule": "Mon-Wed, 9AM-6PM", "compatibility": "72%"},
                        {"name": "Taylor", "route": "Riverside to Shopping District", "schedule": "Tue-Fri, 8:30AM-5:30PM", "compatibility": "68%"}
                    ]
                    
                    for match in matches:
                        st.markdown(f"""
                        <div class="milestone-card">
                            <h4>{match['name']}</h4>
                            <p>Route: {match['route']}</p>
                            <p>Schedule: {match['schedule']}</p>
                            <p>Compatibility: {match['compatibility']}</p>
                            <button style="background-color: #4CAF50; color: white; border: none; padding: 5px 10px; 
                                    border-radius: 5px; cursor: pointer;">
                                Contact {match['name']}
                            </button>
                        </div>
                        """, unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    main()  # Run standalone without auth
    st.markdown("""
<div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
    <h3 style="color: black !important; font-size: 20px !important; font-weight: bold !important;">Welcome to the Eco-Friendly Transportation Planner! 🌿</h3>
    <p style="color: black !important;">This app helps you make greener transportation choices and reduce your carbon footprint.</p>
    <p style="color: black !important;">Get started by logging your travel data in the <b>Travel Log</b> tab, then explore eco-friendly suggestions powered by Gemini 1.5 Pro!</p>
</div>
""", unsafe_allow_html=True)