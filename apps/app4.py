import streamlit as st
import pandas as pd
import datetime
import random
import json
import os
from PIL import Image
import google.generativeai as genai
from datetime import date, timedelta

# Setup for Gemini - using a hardcoded API key
def configure_gemini():
    # Use a hardcoded API key (replace with your actual key)
    api_key = "AIzaSyASnBJDcTM4puEQSrNLJPPRMgAA0wUzeIU"
    if api_key:
        genai.configure(api_key=api_key)
        return True
    return False

# Constants and data
FOOD_CATEGORIES = {
    "Vegetables": 0.5,
    "Fruits": 1.0,
    "Grains & Legumes": 1.2,
    "Dairy": 6.0,
    "Eggs": 4.5,
    "Fish": 5.0,
    "Poultry": 6.0,
    "Pork": 7.0,
    "Beef & Lamb": 20.0,
    "Processed Foods": 8.0,
    "Plant-based Alternatives": 2.0
}

SOURCING_OPTIONS = {
    "Local Farm (< 50 miles)": 0.7,
    "Regional (50-250 miles)": 1.0,
    "National": 1.5,
    "International": 2.0
}

PRODUCTION_METHOD = {
    "Organic": 0.8,
    "Conventional": 1.0,
    "Regenerative": 0.7,
    "Unknown": 1.1
}

BADGES = {
    "Plant Pioneer": "Logged 5 plant-based meals",
    "Local Hero": "Logged 5 locally sourced meals",
    "Meat-Free Monday Champion": "Completed 4 meat-free Mondays",
    "Seasonal Savvy": "Used seasonal ingredients in 10 meals",
    "Carbon Cutter": "Reduced carbon footprint by 25% in a week",
    "Recipe Explorer": "Tried 5 suggested eco-friendly recipes",
    "Streak Master": "Maintained a 7-day green meal streak",
    "Organic Observer": "Logged 10 organic items",
    "Challenge Champion": "Completed a monthly recipe challenge",
    "Plant-Based Pro": "Log 20 plant-based meals",
    "Seasonal Explorer": "Use ingredients from each season",
    "Zero Waste Chef": "Log 10 meals using leftover ingredients",
    "Local Food Champion": "Log 15 meals with locally sourced ingredients",
    "Creative Cook": "Participate in 3 recipe challenges"
}

SEASONAL_EVENTS = {
    "Spring": {
        "name": "Spring Green Revolution",
        "description": "Embrace fresh, local spring produce in your meals",
        "period": "March 21 - June 20",
        "theme": "Fresh Spring Vegetables",
        "bonus_ingredients": ["Asparagus", "Peas", "Spring Greens"],
        "challenge": "Create 5 meals using seasonal spring produce"
    },
    "Summer": {
        "name": "Summer Eco Grills",
        "description": "Master sustainable grilling with plant-based alternatives",
        "period": "June 21 - September 22",
        "theme": "Sustainable Grilling",
        "bonus_ingredients": ["Zucchini", "Corn", "Bell Peppers"],
        "challenge": "Make 5 plant-based grill recipes"
    },
    "Fall": {
        "name": "Fall for Plant-Based",
        "description": "Explore autumn vegetables and plant-based comfort foods",
        "period": "September 23 - December 20"
    },
    "Winter": {
        "name": "Winter Sustainability Challenge",
        "description": "Create eco-friendly warming meals and reduce food waste",
        "period": "December 21 - March 20"
    }
}

# Initialize session state
def init_session_state():
    """Initialize all session state variables for meal tracking"""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.user_data = {
            "meals": [],
            "badges": [],
            "challenges_completed": [],
            "current_streak": 0,
            "longest_streak": 0,
            "last_meal_date": None,
            "total_carbon_saved": 0,
            "recipe_challenge_progress": 0
        }
        
        # Initialize seasonal points directly in session state
        st.session_state.seasonal_points = {
            f"{get_current_season()}_{date.today().year}": 0
        }
        
        # Initialize current challenge
        st.session_state.current_challenge = {
            "name": "Spring Plant-Based Plates",
            "description": "Create meals featuring seasonal spring vegetables as the star ingredient",
            "deadline": (date.today() + timedelta(days=30)).isoformat(),
            "completed": False
        }

    # Ensure all required keys exist
    required_keys = {
        "meals": [],
        "badges": [],
        "challenges_completed": [],
        "current_streak": 0,
        "longest_streak": 0,
        "last_meal_date": None,
        "total_carbon_saved": 0,
        "recipe_challenge_progress": 0
    }

    # Initialize or update missing keys
    if 'user_data' not in st.session_state:
        st.session_state.user_data = required_keys
    else:
        for key, default_value in required_keys.items():
            if key not in st.session_state.user_data:
                st.session_state.user_data[key] = default_value

    # Ensure seasonal_points exists
    if 'seasonal_points' not in st.session_state:
        st.session_state.seasonal_points = {
            f"{get_current_season()}_{date.today().year}": 0
        }

    # Ensure current challenge exists
    if 'current_challenge' not in st.session_state:
        st.session_state.current_challenge = {
            "name": "Spring Plant-Based Plates",
            "description": "Create meals featuring seasonal spring vegetables as the star ingredient",
            "deadline": (date.today() + timedelta(days=30)).isoformat(),
            "completed": False
        }

    # Initialize tab state if not exists
    if 'tab' not in st.session_state:
        st.session_state.tab = "log_meal"

# Carbon footprint calculation
def calculate_carbon_footprint(food_category, portion_size, sourcing, production):
    base_carbon = FOOD_CATEGORIES[food_category]
    sourcing_multiplier = SOURCING_OPTIONS[sourcing]
    production_multiplier = PRODUCTION_METHOD[production]
    
    return base_carbon * portion_size * sourcing_multiplier * production_multiplier

# Streak management
def update_streak(meal_date):
    if not st.session_state.user_data["last_meal_date"]:
        st.session_state.user_data["current_streak"] = 1
    else:
        last_date = datetime.datetime.strptime(st.session_state.user_data["last_meal_date"], "%Y-%m-%d").date()
        current_date = datetime.datetime.strptime(meal_date, "%Y-%m-%d").date()
        
        if (current_date - last_date).days == 1:
            st.session_state.user_data["current_streak"] += 1
        elif (current_date - last_date).days > 1:
            st.session_state.user_data["current_streak"] = 1
            
    if st.session_state.user_data["current_streak"] > st.session_state.user_data["longest_streak"]:
        st.session_state.user_data["longest_streak"] = st.session_state.user_data["current_streak"]
    
    st.session_state.user_data["last_meal_date"] = meal_date
    
    # Award streak badge if applicable
    if st.session_state.user_data["current_streak"] >= 7 and "Streak Master" not in st.session_state.user_data["badges"]:
        st.session_state.user_data["badges"].append("Streak Master")
        return "Streak Master"
    
    return None

# Badge check
def check_for_badges(user_data):
    """Enhanced badge checking function"""
    new_badges = []
    meals = user_data["meals"]
    
    # Plant Pioneer
    plant_based_count = sum(1 for meal in meals if meal["category"] in ["Vegetables", "Fruits", "Grains & Legumes", "Plant-based Alternatives"])
    if plant_based_count >= 5 and "Plant Pioneer" not in user_data["badges"]:
        user_data["badges"].append("Plant Pioneer")
        new_badges.append("Plant Pioneer")
    
    # Local Hero
    local_meals = sum(1 for meal in meals if meal["sourcing"] == "Local Farm (< 50 miles)")
    if local_meals >= 5 and "Local Hero" not in user_data["badges"]:
        user_data["badges"].append("Local Hero")
        new_badges.append("Local Hero")
    
    # Meat-Free Monday
    monday_meals = [meal for meal in meals if datetime.datetime.strptime(meal["date"], "%Y-%m-%d").weekday() == 0]
    meat_free_mondays = sum(1 for meal in monday_meals if meal["category"] not in ["Beef & Lamb", "Pork", "Poultry", "Fish"])
    if meat_free_mondays >= 4 and "Meat-Free Monday Champion" not in user_data["badges"]:
        user_data["badges"].append("Meat-Free Monday Champion")
        new_badges.append("Meat-Free Monday Champion")
    
    # Organic Observer
    organic_items = sum(1 for meal in meals if meal["production"] == "Organic")
    if organic_items >= 10 and "Organic Observer" not in user_data["badges"]:
        user_data["badges"].append("Organic Observer")
        new_badges.append("Organic Observer")
        
    # Plant-Based Pro check
    plant_based_meals = sum(1 for meal in meals 
                          if meal["category"] in ["Vegetables", "Fruits", "Plant-based Alternatives"])
    if plant_based_meals >= 20 and "Plant-Based Pro" not in user_data["badges"]:
        user_data["badges"].append("Plant-Based Pro")
        new_badges.append("Plant-Based Pro")
    
    # Seasonal Explorer check
    current_season = get_current_season()
    seasonal_meals = sum(1 for meal in meals 
                        if any(ingredient in meal["description"] 
                              for ingredient in SEASONAL_EVENTS[current_season]["bonus_ingredients"]))
    if seasonal_meals >= 5 and "Seasonal Explorer" not in user_data["badges"]:
        user_data["badges"].append("Seasonal Explorer")
        new_badges.append("Seasonal Explorer")
    
    # Zero Waste Chef check
    zero_waste_meals = sum(1 for meal in meals 
                          if "leftover" in meal["description"].lower())
    if zero_waste_meals >= 10 and "Zero Waste Chef" not in user_data["badges"]:
        user_data["badges"].append("Zero Waste Chef")
        new_badges.append("Zero Waste Chef")
    
    return new_badges

def get_current_season():
    today = date.today()
    # Determine current season based on date
    if date(today.year, 3, 21) <= today <= date(today.year, 6, 20):
        return "Spring"
    elif date(today.year, 6, 21) <= today <= date(today.year, 9, 22):
        return "Summer"
    elif date(today.year, 9, 23) <= today <= date(today.year, 12, 20):
        return "Fall"
    else:
        return "Winter"

def update_seasonal_leaderboard(meal_data):
    """Enhanced seasonal points calculation"""
    points = 0
    current_season = get_current_season()
    season_data = SEASONAL_EVENTS[current_season]
    
    # Base points
    if meal_data["category"] in ["Vegetables", "Fruits", "Plant-based Alternatives"]:
        points += 10
    
    # Seasonal bonus points
    if any(ingredient.lower() in meal_data["description"].lower() 
           for ingredient in season_data["bonus_ingredients"]):
        points += 15
    
    # Local sourcing bonus
    if meal_data["sourcing"] == "Local Farm (< 50 miles)":
        points += 10
    
    # Organic/Regenerative bonus
    if meal_data["production"] in ["Organic", "Regenerative"]:
        points += 5
    
    return points

# Get sustainable recipe recommendations using Gemini 1.5 Pro
def get_recipe_recommendations(meal_data):
    if not configure_gemini():
        return "Unable to connect to Gemini API. Please contact the administrator."
    
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = f"""
        As a sustainable food expert, recommend 3 eco-friendly recipes based on the following meal preferences:
        
        Food categories the user likes: {meal_data['category']}
        Sourcing preference: {meal_data['sourcing']}
        Production method preference: {meal_data['production']}
        
        For each recipe, provide:
        1. Recipe name
        2. Brief description (1-2 sentences)
        3. Main ingredients
        4. Environmental benefit (how this recipe is sustainable)
        
        Prioritize seasonal, local, plant-forward recipes with low carbon footprint.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error getting recommendations: {str(e)}"

# Get sustainability tips using Gemini 1.5 Pro
def get_sustainability_tips(meal_history):
    if not configure_gemini():
        return "Unable to connect to Gemini API. Please contact the administrator."
    
    if not meal_history:
        return "Log more meals to get personalized sustainability tips."
        
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Extract relevant data for analysis
        categories = [meal["category"] for meal in meal_history]
        sourcing = [meal["sourcing"] for meal in meal_history]
        production = [meal["production"] for meal in meal_history]
        carbon_footprints = [meal["carbon_footprint"] for meal in meal_history]
        
        prompt = f"""
        As a sustainable nutrition expert, analyze this meal history and provide 3-5 personalized sustainability tips:
        
        Food categories consumed: {categories}
        Sourcing methods: {sourcing}
        Production methods: {production}
        Carbon footprint range: {min(carbon_footprints)} to {max(carbon_footprints)} kg CO2e
        
        Based on this data, provide actionable sustainability tips that would help this person:
        1. Reduce their food carbon footprint
        2. Make more sustainable food choices
        3. Improve the environmental impact of their diet
        
        Focus on practical, specific suggestions rather than general advice.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error getting sustainability tips: {str(e)}"

# UI Components
def meal_logging_tab():
    st.header("Log Your Meal")
    
    col1, col2 = st.columns(2)
    
    with col1:
        meal_name = st.text_input("Meal Name", "")
        meal_date = st.date_input("Date", datetime.datetime.now()).isoformat()
        meal_category = st.selectbox("Main Food Category", list(FOOD_CATEGORIES.keys()))
        portion_size = st.slider("Portion Size (servings)", 0.5, 3.0, 1.0, 0.5)
    
    with col2:
        meal_description = st.text_area("Meal Description (ingredients, etc.)", "")
        sourcing = st.selectbox("Food Sourcing", list(SOURCING_OPTIONS.keys()))
        production = st.selectbox("Production Method", list(PRODUCTION_METHOD.keys()))
    
    if st.button("Calculate & Log Meal"):
        if not meal_name:
            st.error("Please enter a meal name")
            return
            
        carbon_footprint = calculate_carbon_footprint(meal_category, portion_size, sourcing, production)
        
        # Alternative option carbon footprint for comparison
        alt_category = "Plant-based Alternatives" if meal_category in ["Beef & Lamb", "Pork", "Poultry"] else meal_category
        alt_sourcing = "Local Farm (< 50 miles)" if sourcing != "Local Farm (< 50 miles)" else sourcing
        alt_carbon = calculate_carbon_footprint(alt_category, portion_size, alt_sourcing, production)
        
        carbon_saved = max(0, carbon_footprint - alt_carbon)
        
        meal_data = {
            "name": meal_name,
            "date": meal_date,
            "category": meal_category,
            "description": meal_description,
            "portion_size": portion_size,
            "sourcing": sourcing,
            "production": production,
            "carbon_footprint": carbon_footprint,
            "potential_saving": carbon_saved
        }
        
        st.session_state.user_data["meals"].append(meal_data)
        st.session_state.user_data["total_carbon_saved"] += carbon_saved
        
        # Update streak
        badge_earned = update_streak(meal_date)
        
        # Check for new badges
        new_badges = check_for_badges(st.session_state.user_data)
        if badge_earned:
            new_badges.append(badge_earned)
        
        # Check if meal contributes to current challenge
        if (meal_category in ["Vegetables", "Fruits", "Plant-based Alternatives"] and 
            sourcing in ["Local Farm (< 50 miles)", "Regional (50-250 miles)"]):
            st.session_state.user_data["recipe_challenge_progress"] += 1
            
            if (st.session_state.user_data["recipe_challenge_progress"] >= 5 and 
                not st.session_state.current_challenge["completed"]):
                st.session_state.current_challenge["completed"] = True
                st.session_state.user_data["challenges_completed"].append(st.session_state.current_challenge["name"])
                if "Challenge Champion" not in st.session_state.user_data["badges"]:
                    st.session_state.user_data["badges"].append("Challenge Champion")
                    new_badges.append("Challenge Champion")
        
        # Update seasonal leaderboard
        seasonal_points = update_seasonal_leaderboard(meal_data)
        if seasonal_points > 0:
            st.success(f"🌟 Earned {seasonal_points} seasonal points!")
        
        st.success(f"Meal logged! Carbon footprint: {carbon_footprint:.2f} kg CO2e")
        st.info(f"Seasonal points earned: {seasonal_points}")
        
        # Get recommendations using Gemini
        with st.spinner("Getting eco-friendly recipe recommendations..."):
            recommendations = get_recipe_recommendations(meal_data)
            st.subheader("Eco-Friendly Recipe Recommendations")
            st.markdown(recommendations)
        
        if new_badges:
            st.balloons()
            st.success(f"🎉 New badge(s) earned: {', '.join(new_badges)}")
            for badge in new_badges:
                st.info(f"**{badge}**: {BADGES[badge]}")

def dashboard_tab():
    st.header("Your Sustainability Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Stats")
        st.metric("Current Green Streak", f"{st.session_state.user_data['current_streak']} days")
        st.metric("Longest Streak", f"{st.session_state.user_data['longest_streak']} days")
        st.metric("Meals Logged", f"{len(st.session_state.user_data['meals'])}")
        st.metric("Carbon Saved", f"{st.session_state.user_data['total_carbon_saved']:.2f} kg CO2e")
        
        st.subheader("Current Challenge")
        st.info(f"**{st.session_state.current_challenge['name']}**")
        st.write(st.session_state.current_challenge['description'])
        st.progress(min(1.0, st.session_state.user_data["recipe_challenge_progress"] / 5))
        st.write(f"Progress: {st.session_state.user_data['recipe_challenge_progress']}/5 meals")
        st.write(f"Deadline: {st.session_state.current_challenge['deadline']}")
        
    with col2:
        st.subheader("Your Badges")
        if not st.session_state.user_data["badges"]:
            st.write("No badges earned yet. Keep logging sustainable meals!")
        else:
            for badge in st.session_state.user_data["badges"]:
                st.success(f"**{badge}**: {BADGES[badge]}")
                
        st.subheader("Challenges Completed")
        if not st.session_state.user_data["challenges_completed"]:
            st.write("No challenges completed yet. Keep going!")
        else:
            for challenge in st.session_state.user_data["challenges_completed"]:
                st.write(f"✅ {challenge}")
    
    if st.session_state.user_data["meals"]:
        st.subheader("Your Meal History")
        meal_df = pd.DataFrame(st.session_state.user_data["meals"])
        st.dataframe(meal_df[["date", "name", "category", "carbon_footprint"]])
        
        st.subheader("Personalized Sustainability Tips")
        with st.spinner("Generating personalized tips..."):
            tips = get_sustainability_tips(st.session_state.user_data["meals"])
            st.markdown(tips)
    
    st.subheader("Seasonal Leaderboard")
    if 'seasonal_points' in st.session_state:
        leaderboard = pd.DataFrame.from_dict(st.session_state.seasonal_points, orient='index', columns=['Points'])
        leaderboard.index.name = 'Season'
        st.dataframe(leaderboard.sort_values(by='Points', ascending=False))
    else:
        st.write("No seasonal points earned yet. Log meals to participate!")
    
    st.subheader("🌟 Seasonal Challenge")
    current_season = get_current_season()
    season_data = SEASONAL_EVENTS[current_season]
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### {season_data['name']}")
        st.write(season_data['description'])
        st.write(f"**Active Period:** {season_data['period']}")
        
        # Display seasonal points
        season_key = f"{current_season}_{date.today().year}"
        seasonal_points = st.session_state.seasonal_points.get(season_key, 0)
        st.metric("Your Seasonal Points", seasonal_points)
        
    with col2:
        st.markdown("### Seasonal Achievements")
        if seasonal_points >= 500:
            st.success("🏆 Seasonal Champion")
        elif seasonal_points >= 250:
            st.success("🥈 Seasonal Expert")
        elif seasonal_points >= 100:
            st.success("🥉 Seasonal Enthusiast")
        
        # Progress to next achievement
        next_threshold = 100 if seasonal_points < 100 else 250 if seasonal_points < 250 else 500
        progress = min(1.0, seasonal_points / next_threshold)
        st.progress(progress)
        st.write(f"Progress to next achievement: {seasonal_points}/{next_threshold} points")

def analytics_tab():
    if not st.session_state.user_data["meals"]:
        st.info("Log some meals to see your analytics!")
        return
        
    st.header("Your Sustainability Analytics")
    
    meals_df = pd.DataFrame(st.session_state.user_data["meals"])
    
    # Carbon footprint by category
    st.subheader("Carbon Footprint by Food Category")
    category_carbon = meals_df.groupby("category")["carbon_footprint"].sum().sort_values(ascending=False)
    st.bar_chart(category_carbon)
    
    # Carbon footprint by sourcing
    st.subheader("Carbon Footprint by Sourcing Method")
    sourcing_carbon = meals_df.groupby("sourcing")["carbon_footprint"].sum().sort_values(ascending=False)
    st.bar_chart(sourcing_carbon)
    
    # Time series of carbon footprint
    st.subheader("Carbon Footprint Over Time")
    meals_df["date"] = pd.to_datetime(meals_df["date"])
    time_carbon = meals_df.groupby("date")["carbon_footprint"].mean()
    st.line_chart(time_carbon)
    
    # Carbon saving potential
    st.subheader("Your Carbon Saving Potential")
    total_carbon = meals_df["carbon_footprint"].sum()
    total_potential_saving = meals_df["potential_saving"].sum()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Carbon Footprint", f"{total_carbon:.2f} kg CO2e")
    with col2:
        st.metric("Potential Additional Savings", f"{total_potential_saving:.2f} kg CO2e", delta=f"-{(total_potential_saving/total_carbon*100):.1f}%")
    
    # Distribution of food categories
    st.subheader("Your Food Category Distribution")
    category_counts = meals_df["category"].value_counts()
    st.bar_chart(category_counts)

def render_challenges_section():
    """Display current recipe challenges"""
    st.subheader("🎯 Recipe Challenges")
    current_season = get_current_season()
    season_data = SEASONAL_EVENTS[current_season]
    
    st.markdown(f"""
    ### Current Challenge: {season_data['name']}
    **Theme:** {season_data['theme']}
    **Bonus Ingredients:** {', '.join(season_data['bonus_ingredients'])}
    **Challenge:** {season_data['challenge']}
    """)
    
    # Challenge progress
    progress = min(1.0, st.session_state.user_data["recipe_challenge_progress"] / 5)
    st.progress(progress)
    st.write(f"Progress: {st.session_state.user_data['recipe_challenge_progress']}/5 recipes")

# Main app
def main(auth=None):
    """Main function for the food app"""
    st.title("🥗 EcoWise Food Planner")
    
    # Add custom CSS to make the title white
    st.markdown("""
        <style>
        .stTitle {
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    init_session_state()
    
    # Configure Gemini at startup
    configure_gemini()
    
    # Load saved data if auth is provided and user is logged in
    if auth and 'user' in st.session_state:
        saved_data = auth.get_user_progress(st.session_state.user, "food")
        if not saved_data.empty:
            latest_data = saved_data.iloc[-1]['data']
            data = json.loads(latest_data)
            # Update session state with saved data
            st.session_state.user_data = {
                'meals': data.get('meals', []),
                'badges': data.get('badges', []),
                'challenges_completed': data.get('challenges_completed', []),
                'current_streak': data.get('current_streak', 0),
                'longest_streak': data.get('longest_streak', 0),
                'last_meal_date': data.get('last_meal_date', None),
                'total_carbon_saved': data.get('total_carbon_saved', 0),
                'recipe_challenge_progress': data.get('recipe_challenge_progress', 0)
            }
            st.session_state.seasonal_points = data.get('seasonal_points', {})

    #st.write("Track your meals, reduce your carbon footprint, and make sustainable food choices!")
    
    # Navigation
    tab1, tab2, tab3 = st.tabs(["Log Meal", "Dashboard", "Analytics"])
    
    with tab1:
        meal_logging_tab()
    
    with tab2:
        dashboard_tab()
    
    with tab3:
        analytics_tab()
    
    # Sidebar elements
    st.sidebar.header("About Healthy Eats")
    st.sidebar.write("""
    Healthy Eats helps you make more sustainable dietary choices 
    by tracking your meals and providing personalized recommendations 
    to reduce your carbon footprint.
    
    Join challenges, earn badges, and track your progress towards 
    a more sustainable diet!
    """)
    
    def save_progress():
        if auth and 'user' in st.session_state:
            progress_data = {
                'meals': st.session_state.user_data['meals'],
                'badges': st.session_state.user_data['badges'],
                'challenges_completed': st.session_state.user_data['challenges_completed'],
                'current_streak': st.session_state.user_data['current_streak'],
                'total_carbon_saved': st.session_state.user_data['total_carbon_saved'],
                'seasonal_points': st.session_state.seasonal_points
            }
            # Save locally
            auth.save_progress(st.session_state.user, "food", json.dumps(progress_data))
            st.success("Progress saved!")

    # Add save button in sidebar only if auth is available
    if auth:
        if st.sidebar.button("💾 Save Progress"):
            save_progress()
    
    # Reset button (for testing)
    if st.sidebar.button("🔄 Reset App Data"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

if __name__ == "__main__":
    main()  # Run standalone without auth