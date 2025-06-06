import streamlit as st
import pandas as pd
import numpy as np
import datetime
import json
import os
import random
import google.generativeai as genai
from PIL import Image
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime, timedelta, date 

# Waste Management Constants
FOOD_CATEGORIES = {
    'Fruit & Vegetables': 0.5,
    'Paper & Cardboard': 1.0,
    'Plastic': 2.5,
    'Glass': 1.5,
    'Metal': 1.8,
    'Electronics': 5.0,
    'Organic Waste': 0.8
}

WASTE_REDUCTION_TIPS = {
    'Beginner': [
        "Start using reusable shopping bags",
        "Begin basic recycling of paper and plastic",
        "Use a reusable water bottle"
    ],
    'Intermediate': [
        "Start composting kitchen scraps",
        "Buy items in bulk to reduce packaging",
        "Repair items instead of replacing them"
    ],
    'Advanced': [
        "Create a zero-waste kitchen",
        "Start a community recycling program",
        "Implement a household composting system"
    ]
}

# Update the custom CSS section
st.markdown("""
<style>
    /* Modern theme colors */
    :root {
        --primary-color: #2ecc71;
        --secondary-color: #27ae60;
        --background-dark: #1a1a1a;
        --card-bg: #2d2d2d;
        --accent: #3498db;
        --error: #e74c3c;
        --success: #2ecc71;
    }

    /* Main container */
    .stApp {
        background-color: var(--background-dark);
        color: #ecf0f1;
    }

    /* Modern card design */
    .card {
        background: linear-gradient(145deg, #2d2d2d, #333333);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
    }
    .card:hover {
        transform: translateY(-5px);
    }

    /* Animated buttons */
    .stButton > button {
        background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6em 1.2em;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }

    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        border-radius: 10px;
    }

    /* Metrics */
    .metric-container {
        background: linear-gradient(145deg, #2d2d2d, #333333);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: var(--primary-color);
    }
    .metric-label {
        color: #bdc3c7;
        font-size: 0.9em;
    }

    /* Badges */
    .badge {
        background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
        color: white;
        padding: 0.5em 1em;
        border-radius: 20px;
        font-size: 0.8em;
        display: inline-block;
        margin: 0.2em;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade-in {
        animation: fadeIn 0.5s ease-out;
    }

    /* Level indicators */
    .level-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    .level-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #495057;
        transition: background-color 0.3s ease;
    }
    .level-dot.active {
        background-color: var(--primary-color);
    }

    /* Custom select boxes */
    .stSelectbox > div > div {
        background-color: #2d2d2d;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
    }
    
    /* Custom number inputs */
    .stNumberInput > div > div > input {
        background-color: #2d2d2d;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Configure Gemini API
# Note: In a production environment, store this in environment variables
API_KEY = "AIzaSyASnBJDcTM4puEQSrNLJPPRMgAA0wUzeIU"  # Replace with your actual API key
genai.configure(api_key=API_KEY)

# Set up the model
model = genai.GenerativeModel('gemini-1.5-pro')

# Helper functions
def get_current_level(points):
    if points < 100:
        return "Waste Reducer"
    elif points < 300:
        return "Recycler"
    elif points < 600:
        return "Sustainability Pro"
    else:
        return "Zero Waste Champion"

def update_level():
    st.session_state.user_data['level'] = get_current_level(st.session_state.user_data['points'])

def initialize_bingo_board():
    tasks = [
        "Compost for a full week",
        "Use zero plastic bags this week",
        "Visit a local recycling center",
        "Upcycle an item instead of trashing it",
        "Use a reusable water bottle all week",
        "Take shorter showers to save water",
        "Shop at a bulk food store",
        "Fix something instead of replacing it",
        "Donate unused items",
        "Make a zero-waste meal",
        "Use cloth napkins instead of paper",
        "Start a compost bin",
        "Properly recycle electronics",
        "Use reusable containers for takeout",
        "Create a recycling station at home",
        "Make DIY cleaning supplies",
        "Use public transportation or bike",
        "Purchase second-hand items",
        "Avoid single-use plastics for a day",
        "Plant a native species plant",
        "Collect rainwater for plants",
        "Switch to digital documents",
        "Turn off lights when not in use",
        "Use reusable bags for produce",
        "Repurpose glass jars"
    ]
    
    # Shuffle and select 25 tasks
    random.shuffle(tasks)
    selected_tasks = tasks[:25]
    
    # Create a 5x5 bingo board
    board = {}
    for i in range(25):
        board[i] = {"task": selected_tasks[i], "completed": False}
        
    return board

def initialize_scavenger_hunt():
    tasks = [
        {"task": "Find and use a local recycling drop-off point", "completed": False, "points": 20},
        {"task": "Purchase a reusable water bottle", "completed": False, "points": 15},
        {"task": "Take a photo of yourself using a compost bin", "completed": False, "points": 25},
        {"task": "Visit a second-hand store", "completed": False, "points": 15},
        {"task": "Find a local farmers market", "completed": False, "points": 20},
        {"task": "Identify a bulk food store", "completed": False, "points": 15},
        {"task": "Attend a local environmental event", "completed": False, "points": 30},
        {"task": "Start a small herb garden", "completed": False, "points": 25},
        {"task": "Find a place to donate used items", "completed": False, "points": 15},
        {"task": "Learn about local recycling guidelines", "completed": False, "points": 20}
    ]
    return tasks

def add_points(amount):
    """Add points to user's total and update level"""
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {}
    if 'points' not in st.session_state.user_data:
        st.session_state.user_data['points'] = 0
        
    st.session_state.user_data['points'] += amount
    update_level()
    
    # Show notification
    st.toast(f"🎉 Earned {amount} points!")

def check_for_bingo():
    """Check for completed bingo lines and award points"""
    if 'user_data' not in st.session_state or 'bingo_board' not in st.session_state.user_data:
        return False
        
    board = st.session_state.user_data['bingo_board']
    bingo_found = False

    # Check rows
    for row in range(5):
        if all(board[row * 5 + col]['completed'] for col in range(5)):
            bingo_found = True
            break

    # Check columns
    if not bingo_found:
        for col in range(5):
            if all(board[row * 5 + col]['completed'] for row in range(5)):
                bingo_found = True
                break

    # Check diagonals
    if not bingo_found:
        if all(board[i * 6]['completed'] for i in range(5)):  # Top-left to bottom-right
            bingo_found = True
        elif all(board[i * 4 + 4]['completed'] for i in range(5)):  # Top-right to bottom-left
            bingo_found = True

    if bingo_found:
        if 'completed_bingos' not in st.session_state.user_data:
            st.session_state.user_data['completed_bingos'] = 0
        st.session_state.user_data['completed_bingos'] += 1
        add_points(100)
        return True

    return False

def check_waste_achievements():
    """Check and award achievements based on waste reduction"""
    user_data = st.session_state.user_data
    
    # Check recycling streak
    if len(user_data['recycling_history']) >= 4 and all(x > 0 for x in user_data['recycling_history'][-4:]):
        if "Consistent Recycler" not in user_data['badges']:
            user_data['badges'].append("Consistent Recycler")
            add_points(50)
            st.success("🏆 Achievement Unlocked: Consistent Recycler!")
    
    # Check composting progress
    if sum(user_data['composting_history'][-4:]) > 10:
        if "Composting Champion" not in user_data['badges']:
            user_data['badges'].append("Composting Champion")
            add_points(75)
            st.success("🏆 Achievement Unlocked: Composting Champion!")

def render_recycling_bingo():
    st.subheader("Recycling Bingo")
    
    # Display board in a 5x5 grid
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    for row in range(5):
        cols = st.columns(5)
        for col in range(5):
            idx = row * 5 + col
            task = st.session_state.user_data['bingo_board'][idx]
            with cols[col]:
                if task['completed']:
                    st.markdown(f"<div style='padding: 10px; background-color: #2ecc71; border-radius: 5px; text-align: center; min-height: 100px;'><s>{task['task']}</s></div>", unsafe_allow_html=True)
                else:
                    if st.button(task['task'], key=f"bingo_{idx}"):
                        st.session_state.user_data['bingo_board'][idx]['completed'] = True
                        if check_for_bingo():
                            st.balloons()
                            st.success("🎉 BINGO! You've earned 100 points!")

def render_scavenger_hunt():
    st.subheader("Eco Scavenger Hunt")
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    for i, task in enumerate(st.session_state.user_data['scavenger_hunt']):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(task['task'])
        with col2:
            st.write(f"{task['points']} points")
        with col3:
            if not task['completed']:
                if st.button("Complete", key=f"task_{i}"):
                    task['completed'] = True
                    add_points(task['points'])
                    st.success(f"🎉 Task completed! Earned {task['points']} points!")
            else:
                st.write("✅ Done")
    st.markdown("</div>", unsafe_allow_html=True)

def render_waste_analysis():
    st.subheader("Waste Analysis & Insights")
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        total_recycling = sum(st.session_state.user_data['recycling_history'][-4:]) if st.session_state.user_data['recycling_history'] else 0
        st.metric("Monthly Recycling", f"{total_recycling:.1f} kg")
    with col2:
        total_composting = sum(st.session_state.user_data['composting_history'][-4:]) if st.session_state.user_data['composting_history'] else 0
        st.metric("Monthly Composting", f"{total_composting:.1f} kg")
    with col3:
        if st.session_state.user_data['trash_history']:
            current_trash = sum(st.session_state.user_data['trash_history'][-4:])/4
            # Add check for zero division
            if st.session_state.user_data['weekly_trash'] > 0:
                reduction = ((st.session_state.user_data['weekly_trash'] - current_trash) / 
                            st.session_state.user_data['weekly_trash'] * 100)
                st.metric("Waste Reduction", f"{reduction:.1f}%", 
                         delta="↓ Good" if reduction > 0 else "↑ Need improvement")
            else:
                st.metric("Waste Reduction", "0%", 
                         delta="No baseline data")
        else:
            st.metric("Waste Reduction", "0%", 
                     delta="No historical data")

def render_waste_management_form():
    st.title("♻️ Waste Management & Recycling Insights")
    
    tabs = st.tabs(["Track Waste", "Set Goals", "View Insights", "Get Tips"])
    
    with tabs[0]:
        with st.form("waste_tracking"):
            col1, col2 = st.columns(2)
            
            with col1:
                recycling = st.number_input("Recycling (kg)", min_value=0.0, step=0.5)
                composting = st.number_input("Composting (kg)", min_value=0.0, step=0.5)
                waste_category = st.selectbox("Waste Category", list(FOOD_CATEGORIES.keys()))
            
            with col2:
                trash = st.number_input("General Waste (kg)", min_value=0.0, step=0.5)
                reusable_items = st.multiselect("Reusable Items Used", 
                    ["Shopping Bags", "Water Bottle", "Coffee Cup", "Food Containers"])
            
            if st.form_submit_button("Log Waste"):
                # Update history
                st.session_state.user_data['recycling_history'].append(recycling)
                st.session_state.user_data['composting_history'].append(composting)
                st.session_state.user_data['trash_history'].append(trash)
                
                # Award points
                points = calculate_waste_points(recycling, composting, trash, len(reusable_items))
                add_points(points)
                
                # Check for achievements
                check_waste_achievements()
                st.success(f"Waste data logged successfully! Earned {points} points!")
                
                # Auto-save progress
                auto_save_on_action()
    
    with tabs[1]:
        st.subheader("Monthly Goals")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Recycling Goal", 
                     f"{st.session_state.monthly_goal['recycling']} kg",
                     f"{calculate_goal_progress('recycling')}% complete")
        with col2:
            st.metric("Composting Goal",
                     f"{st.session_state.monthly_goal['composting']} kg",
                     f"{calculate_goal_progress('composting')}% complete")

    # View Insights Tab
    with tabs[2]:
        st.subheader("Your Waste Management Insights")
        
        # Show metrics in cards
        col1, col2, col3 = st.columns(3)
        with col1:
            total_recycling = sum(st.session_state.user_data['recycling_history'][-4:]) if st.session_state.user_data['recycling_history'] else 0
            st.metric("Monthly Recycling", f"{total_recycling:.1f} kg", 
                     delta="↑ 15%" if total_recycling > 0 else None)
        
        with col2:
            total_composting = sum(st.session_state.user_data['composting_history'][-4:]) if st.session_state.user_data['composting_history'] else 0
            st.metric("Monthly Composting", f"{total_composting:.1f} kg",
                     delta="↑ 20%" if total_composting > 0 else None)
        
        with col3:
            if st.session_state.user_data['trash_history']:
                current_trash = sum(st.session_state.user_data['trash_history'][-4:])/4
                # Add check for zero division
                if st.session_state.user_data['weekly_trash'] > 0:
                    reduction = ((st.session_state.user_data['weekly_trash'] - current_trash) / 
                                st.session_state.user_data['weekly_trash'] * 100)
                    st.metric("Waste Reduction", f"{reduction:.1f}%", 
                             delta="↓ Good" if reduction > 0 else "↑ Need improvement")
                else:
                    st.metric("Waste Reduction", "0%", 
                             delta="No baseline data")
            else:
                st.metric("Waste Reduction", "0%", 
                         delta="No historical data")

        # Progress Charts
        if st.session_state.user_data['recycling_history']:
            st.subheader("Recycling Progress")
            recycling_data = pd.DataFrame({
                'Week': range(1, len(st.session_state.user_data['recycling_history']) + 1),
                'Amount (kg)': st.session_state.user_data['recycling_history']
            })
            st.line_chart(recycling_data.set_index('Week'))

        # Waste Composition Breakdown
        st.subheader("Waste Composition")
        waste_types = {
            'Recyclables': total_recycling,
            'Compost': total_composting,
            'General Waste': st.session_state.user_data['weekly_trash'] * 4
        }
        
        fig = px.pie(values=list(waste_types.values()), 
                    names=list(waste_types.keys()),
                    title="Monthly Waste Distribution")
        st.plotly_chart(fig)

    # Get Tips Tab
    with tabs[3]:
        st.subheader("Personalized Waste Reduction Tips")
        
        # Get user's waste management profile
        user_profile = {
            'weekly_trash': st.session_state.user_data['weekly_trash'],
            'recycling_habit': st.session_state.user_data.get('recycling_habit', 'Sometimes'),
            'composting_habit': st.session_state.user_data.get('composting_habit', 'Never'),
            'plastic_usage': st.session_state.user_data.get('plastic_usage', 'Moderate')
        }
        
        if st.button("Get New Tips"):
            with st.spinner("Generating personalized recommendations..."):
                recommendations = get_waste_recommendations(user_profile)
                if recommendations:
                    tips = recommendations.split('\n')
                    for tip in tips:
                        if tip.strip():
                            st.markdown(f"🌱 {tip.strip()}")
                else:
                    st.warning("Unable to generate tips at the moment. Here are some general tips:")
                    st.markdown("""
                    * Start a compost bin for food scraps and yard waste
                    * Use reusable shopping bags and containers
                    * Properly sort recyclables to avoid contamination
                    * Buy items with minimal packaging
                    * Repair items instead of replacing them when possible
                    """)
        
        # Quick Reference Guide
        st.subheader("Quick Reference Guide")
        with st.expander("Recycling Guide"):
            st.markdown("""
            ♻️ **Common Recyclables:**
            * Paper and cardboard
            * Glass bottles and jars
            * Metal cans and containers
            * Plastic bottles and containers (check numbers)
            * Clean aluminum foil
            """)
            
        with st.expander("Composting Guide"):
            st.markdown("""
            🌱 **Compostable Items:**
            * Fruit and vegetable scraps
            * Coffee grounds and filters
            * Tea bags
            * Eggshells
            * Yard trimmings
            """)
            
        with st.expander("Waste Reduction Tips"):
            st.markdown("""
            📝 **Daily Habits:**
            * Carry reusable water bottles and coffee cups
            * Pack lunch in reusable containers
            * Say no to single-use plastics
            * Shop with reusable bags
            * Buy in bulk to reduce packaging
            """)

def calculate_goal_progress(goal_type):
    """Calculate progress towards monthly goals"""
    if goal_type == 'recycling':
        total = sum(st.session_state.user_data['recycling_history'][-4:]) if st.session_state.user_data['recycling_history'] else 0
        goal = st.session_state.monthly_goal['recycling']
    elif goal_type == 'composting':
        total = sum(st.session_state.user_data['composting_history'][-4:]) if st.session_state.user_data['composting_history'] else 0
        goal = st.session_state.monthly_goal['composting']
    elif goal_type == 'trash_reduction':
        if st.session_state.user_data['trash_history']:
            initial = st.session_state.user_data['weekly_trash']
            current = sum(st.session_state.user_data['trash_history'][-4:]) / 4
            reduction = ((initial - current) / initial) * 100
            return min(int(reduction), 100)
        return 0
    
    if goal <= 0:
        return 0
    return min(int((total / goal) * 100), 100)

def get_waste_recommendations(user_data):
    """Generate personalized waste reduction recommendations"""
    try:
        prompt = f"""
        Analyze this user's waste management data and provide personalized recommendations:
        Weekly trash: {user_data['weekly_trash']} kg
        Recycling habit: {user_data['recycling_habit']}
        Composting habit: {user_data['composting_habit']}
        Plastic usage: {user_data['plastic_usage']}
        
        Provide 3 specific, actionable recommendations to:
        1. Reduce overall waste
        2. Improve recycling habits
        3. Start or enhance composting
        
        Format as a bulleted list.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating recommendations: {str(e)}"

def calculate_waste_points(recycling, composting, trash, reusable_items):
    """Calculate points based on waste management activities"""
    points = 0
    
    # Points for recycling
    if recycling > 0:
        points += int(recycling * 10)  # 10 points per kg recycled
    
    # Points for composting
    if composting > 0:
        points += int(composting * 15)  # 15 points per kg composted
    
    # Points for reducing trash
    if trash < 5:  # Reward low trash amounts
        points += 25
    elif trash < 10:
        points += 10
        
    # Points for using reusable items
    points += reusable_items * 5  # 5 points per reusable item used
    
    return points

def render_sidebar():
    st.sidebar.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h2 style='color: #2ecc71;'>🌿 Your Progress</h2>
        </div>
    """, unsafe_allow_html=True)

    # Level and points display
    st.sidebar.markdown(f"""
        <div class='metric-container'>
            <div class='metric-value'>{st.session_state.user_data['level']}</div>
            <div class='metric-label'>Current Level</div>
        </div>
    """, unsafe_allow_html=True)

    # Progress bar with animation
    progress = min(st.session_state.user_data['points'] / 1000, 1.0)
    st.sidebar.markdown(f"""
        <div class='level-indicator'>
            <div class='level-dot {"active" if progress >= 0.25 else ""}'></div>
            <div class='level-dot {"active" if progress >= 0.5 else ""}'></div>
            <div class='level-dot {"active" if progress >= 0.75 else ""}'></div>
            <div class='level-dot {"active" if progress >= 1.0 else ""}'></div>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.header("Activities")
    if st.sidebar.button("Waste Management Details"):
        st.session_state.show_bingo = False
        st.session_state.show_scavenger = False
        st.session_state.show_analysis = False

    if st.sidebar.button("Recycling Bingo"):
        if 'bingo_board' not in st.session_state.user_data or not st.session_state.user_data['bingo_board']:
            st.session_state.user_data['bingo_board'] = initialize_bingo_board()
        st.session_state.show_bingo = True
        st.session_state.show_scavenger = False
        st.session_state.show_analysis = False

    if st.sidebar.button("Eco Scavenger Hunt"):
        if 'scavenger_hunt' not in st.session_state.user_data or not st.session_state.user_data['scavenger_hunt']:
            st.session_state.user_data['scavenger_hunt'] = initialize_scavenger_hunt()
        st.session_state.show_bingo = False
        st.session_state.show_scavenger = True
        st.session_state.show_analysis = False

    st.sidebar.header("Monthly Goals")
    with st.sidebar.expander("Set Monthly Goals"):
        st.session_state.monthly_goal['recycling'] = st.slider(
            "Recycling Goal (kg)", 
            0, 
            50,
            int(st.session_state.monthly_goal['recycling'])
        )

        st.session_state.monthly_goal['composting'] = st.slider(
            "Composting Goal (kg)", 
            0, 
            30,
            int(st.session_state.monthly_goal['composting'])
        )

        st.session_state.monthly_goal['trash_reduction'] = st.slider(
            "Trash Reduction Goal (%)",
            0,
            100,
            int(st.session_state.monthly_goal['trash_reduction'])
        )

def save_progress():
    """Save progress if auth is available"""
    if 'auth' in globals() and auth and 'user' in st.session_state:  # Changed condition
        progress_data = {
            'waste_log': st.session_state.user_data['waste_log'],
            'recycling_points': st.session_state.user_data['recycling_points'],
            'badges': st.session_state.user_data['badges'],
            'challenges': st.session_state.user_data['active_challenges'],
            'points': st.session_state.user_data['points'],
            'level': st.session_state.user_data['level']
        }
        auth.save_progress(st.session_state.user, "waste", json.dumps(progress_data))
        st.success("Progress saved!")

def auto_save_on_action():
    """Automatically save progress if auth is available"""
    if 'auth' in st.session_state and 'user' in st.session_state:
        progress_data = {
            'points': st.session_state.user_data.get('points', 0),
            'level': st.session_state.user_data.get('level', 'Waste Reducer'),
            'activities': st.session_state.user_data.get('activities', []),  # Use get() with default
            'recycling_history': st.session_state.user_data.get('recycling_history', []),
            'composting_history': st.session_state.user_data.get('composting_history', []),
            'trash_history': st.session_state.user_data.get('trash_history', []),
            'badges': st.session_state.user_data.get('badges', []),
            'bingo_board': st.session_state.user_data.get('bingo_board', {}),
            'scavenger_hunt': st.session_state.user_data.get('scavenger_hunt', []),
            'monthly_goal': st.session_state.monthly_goal,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.auth.save_progress(st.session_state.user, "waste", json.dumps(progress_data))

def render_main_app():
    render_sidebar()
    if st.session_state.show_bingo:
        render_recycling_bingo()
    elif st.session_state.show_scavenger:
        render_scavenger_hunt()
    elif st.session_state.show_analysis:
        render_waste_analysis()
    else:
        render_waste_management_form()

def init_session_state():
    """Initialize session state variables"""
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {
            'level': 'Waste Reducer',  
            'points': 0,
            'activities': [],  # Initialize empty activities list
            'challenges': [],
            'completed_challenges': [],
            'badges': [],
            'streak': 0,
            'last_activity_date': None,
            'recycling_history': [],
            'composting_history': [],
            'trash_history': [],
            'weekly_trash': 0,
            'bingo_board': {},
            'scavenger_hunt': []
        }
    
    # Add 'activities' to required keys
    required_keys = {
        'recycling_history': [],
        'composting_history': [],
        'trash_history': [],
        'weekly_trash': 0,
        'badges': [],
        'level': 'Waste Reducer',
        'points': 0,
        'activities': []  # Add activities to required keys
    }
    
    for key, default_value in required_keys.items():
        if key not in st.session_state.user_data:
            st.session_state.user_data[key] = default_value

    # Initialize monthly goals if not present
    if 'monthly_goal' not in st.session_state:
        st.session_state.monthly_goal = {
            'recycling': 0,
            'composting': 0,
            'trash_reduction': 0
        }

    # Initialize other required session state variables
    if 'show_bingo' not in st.session_state:
        st.session_state.show_bingo = False
    if 'show_scavenger' not in st.session_state:
        st.session_state.show_scavenger = False
    if 'show_analysis' not in st.session_state:
        st.session_state.show_analysis = False

def main(auth=None):
    """Main function for waste management"""
    init_session_state()
    
    # Add save button in sidebar if auth is provided
    if auth is not None:  # Changed condition
        st.sidebar.markdown("---")
        if st.sidebar.button("💾 Save Progress"):
            save_progress()

    # Run the main app
    render_main_app()

if __name__ == "__main__":
    main(None)  # Pass None when running standalone, pass auth when running in combined app