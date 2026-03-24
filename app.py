from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import json
import datetime
from utils import load_menus, search_meals, suggest_healthier, predict_meal_from_image
from auth import login_screen, sign_up_screen


if "screen" not in st.session_state:
    st.session_state["screen"] = "login"

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Routing
if st.session_state["logged_in"]:
    st.title("🎉 Logged In!")
else:
    if st.session_state["screen"] == "login":
        login_screen()
        st.stop()   

    elif st.session_state["screen"] == "signup":
        sign_up_screen()
        st.stop()   


col_logo, col_title, col_spacer = st.columns([1, 3, 1])

with col_logo:
    st.image("Clemson_logo.jpg", width=200)

with col_title:
    st.markdown("""
    <div class="tigerplate-title" style="text-align:center;">
        TigerPlate
    </div>
    """, unsafe_allow_html=True)



st.markdown("""
<style>

/* ----------------------------------------------
   GLOBAL
---------------------------------------------- */

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #FFFFFF !important;
    color: #2D2A24 !important;
}

/* MAIN CONTENT BACKGROUND */
.block-container {
    background-color: #FFFFFF !important;
    padding-top: 1rem;
}

/* ----------------------------------------------
   SIDEBAR
---------------------------------------------- */

[data-testid="stSidebar"] {
    background-color: #522D80 !important; /* Clemson off-white */
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #F56600 !important; /* Clemson orange */
    font-weight: 800;
}

/* Sidebar labels */
[data-testid="stSidebar"] label {
    color: #5A2A83 !important; /* Clemson purple */
    font-weight: 600;
}

/* ----------------------------------------------
   BUTTONS
---------------------------------------------- */

.stButton>button {
    background-color: #F56600 !important;  /* Clemson Orange */
    color: white !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.1rem !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
}

.stButton>button:hover {
    background-color: #D45500 !important;
}

/* ----------------------------------------------
   METRICS
---------------------------------------------- */

[data-testid="stMetricValue"] {
    color: #5A2A83 !important;      /* Purple */
    font-weight: 900 !important;
    font-size: 1.5rem !important;
}

[data-testid="stMetricLabel"] {
    color: #2D2A24 !important;
    font-weight: 600 !important;
}

/* ----------------------------------------------
   CLEMSON HEADER (CUSTOM)
---------------------------------------------- */

.tigerplate-header {
    width: 100%;
    text-align: center;
    padding: 2rem 0 1.5rem 0;
    background: linear-gradient(90deg, #F56600, #D45500);
    border-radius: 10px;
    margin-bottom: 25px;
    position: relative;
}

.tigerplate-title {
    font-size: 3rem;
    font-weight: 900;
    color: white;
    margin-top: 0.5rem;
}

.tiger-paw {
    width: 50px;
    filter: drop-shadow(0px 0px 6px rgba(0,0,0,0.25));
}

/* ----------------------------------------------
   TIGER PAW WATERMARK (Page Background)
---------------------------------------------- */

body::before {
    content: "";
    position: fixed;
    right: 3%;
    bottom: 5%;
    width: 260px;
    height: 260px;
    background-image: url('https://upload.wikimedia.org/wikipedia/en/thumb/8/8c/Clemson_Tigers_logo.svg/1200px-Clemson_Tigers_logo.svg.png');
    background-size: contain;
    background-repeat: no-repeat;
    opacity: 0.05; /* subtle watermark */
    pointer-events: none;
    z-index: 0;
}

/* ----------------------------------------------
   HEADERS
---------------------------------------------- */

h1, h2, h3, h4 {
    color: #F56600 !important;
    font-weight: 800 !important;
}

/* Divider */
hr {
    border-top: 2px solid #F56600 !important;
}
</style>
""", unsafe_allow_html=True)


# Page config
st.set_page_config(page_title="TigerPlate ", layout="wide")

# Title
st.title("Tiger Plate")
st.markdown("Find healthier meal alternatives from your dining hall menus")

# Load menus with caching
@st.cache_data
def get_menus():
    return load_menus()

menu_df = get_menus()

# Sidebar
st.sidebar.header("🔍 Meal Options")

# Dining hall selector
dining_hall = st.sidebar.selectbox(
    "Select Dining Hall:",
    ["All Dining Halls", "core", "douthit", "shilletter"],
    index=0
)

# Meal time filter
meal_time = st.sidebar.selectbox(
    "Meal Time:",
    ["All Meals", "breakfast", "lunch", "dinner"],
    index=0
)

search_query = st.sidebar.text_input("Search for a meal:", placeholder="e.g., scrambled eggs")

st.sidebar.header("🍽️ Meal Builder")

# Initialize a persistent list in session_state
if "meal" not in st.session_state:
    st.session_state.meal = []

# Input box for new food item
new_food = st.sidebar.text_input(
    "Enter a food to add:",
    placeholder="e.g., scrambled eggs"
)

# Button to add item
if st.sidebar.button("Add Food"):
    if new_food.strip():             # avoid empty items
        st.session_state.meal.append(new_food.strip())
        st.sidebar.success(f"Added: {new_food}")
    else:
        st.sidebar.error("Please enter a food name.")

# Display current meal
st.sidebar.subheader("Your Meal:")
if st.session_state.meal:
    for item in st.session_state.meal:
        st.sidebar.write(f"• {item}")
else:
    st.sidebar.write("No foods added yet.")

# Finish meal button
if st.sidebar.button("Finish Meal"):
    st.session_state.finish_meal = True
else:
    st.session_state.finish_meal = False

# Image input options
st.sidebar.subheader("📸 Image Options")
image_option = st.sidebar.radio(
    "Choose how to add an image:",
    ["Upload Image", "Take Photo"],
    label_visibility="collapsed"
)

if image_option == "Take Photo":
    camera_image = st.sidebar.camera_input("Take a picture of your meal")
    upload_image = None
else:
    upload_image = st.sidebar.file_uploader(
        "Upload an image of your meal", 
        type=["jpg", "png", "jpeg"]
    )
    camera_image = None

# User goals
st.sidebar.subheader("🎯 Daily Goals")
goal_calories = st.sidebar.number_input("Calories", value=2000)
goal_protein = st.sidebar.number_input("Protein (g)", value=100)
goal_fat = st.sidebar.number_input("Fat (g)", value=70)

# Filter by dining hall if selected
if dining_hall != "All Dining Halls":
    filtered_df = menu_df[menu_df['hall'] == dining_hall]
else:
    filtered_df = menu_df

# Filter by meal time if selected
if meal_time != "All Meals":
    filtered_df = filtered_df[filtered_df['meal'] == meal_time]

# Display data load status
if menu_df.empty:
    st.error("⚠️ No menu data found. Make sure CSV files are in the same directory as the app.")
else:
    filter_text = []
    if dining_hall != "All Dining Halls":
        filter_text.append(f"{dining_hall}")
    if meal_time != "All Meals":
        filter_text.append(f"{meal_time}")
    
    if filter_text:
        st.success(f"✅ Showing {len(filtered_df)} items from {' - '.join(filter_text)}")
    else:
        st.success(f"✅ Loaded {len(menu_df)} items from all dining halls")

# --- Calculate Meal Builder Nutrition ---
if st.session_state.meal:
    from utils import calculate_meal_nutrition

    totals = calculate_meal_nutrition(st.session_state.meal, filtered_df)

    st.sidebar.subheader("📊 Meal Nutrition Totals")

    st.sidebar.write(f"🔥 **Calories:** {totals['calories']} cal")
    st.sidebar.write(f"🥩 **Protein:** {totals['protein_g']} g")
    st.sidebar.write(f"🍞 **Carbs:** {totals['carbs_g']} g")
    st.sidebar.write(f"🧈 **Fat:** {totals['fat_g']} g")

    # Optional detailed breakdown
    with st.sidebar.expander("See breakdown"):
        for item in totals["matched_items"]:
            st.write(
                f"• **{item['item_name']}** — {item.get('calories', 0)} cal, "
                f"{item.get('protein_g', 0)}g protein, {item.get('carbs_g', 0)}g carbs, {item.get('fat_g', 0)}g fat"
            )

# Meal log file
LOG_FILE = "meal_log.json"

def log_meal(meal):
    data = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    meal["timestamp"] = datetime.datetime.utcnow().isoformat()
    data.append(meal)
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_today_meals():
    if not os.path.exists(LOG_FILE):
        return []
    today = datetime.datetime.utcnow().date().isoformat()
    with open(LOG_FILE, "r") as f:
        meals = json.load(f)
    return [m for m in meals if m["timestamp"].startswith(today)]

# Main app logic
if search_query:
    st.subheader(f"🔎 Results for '{search_query}'")
    
    results = search_meals(filtered_df, search_query)
    
    if results:
        # Display search results
        for i, r in enumerate(results, 1):
            # Format macro info if available
            macro_info = ""
            if 'protein_g' in r and 'carbs_g' in r and 'fat_g' in r:
                macro_info = f" — 🥩 {r['protein_g']}g protein, 🍞 {r['carbs_g']}g carbs, 🧈 {r['fat_g']}g fat"
            
            meal_badge = ""
            if 'meal' in r:
                meal_emoji = {"breakfast": "🌅", "lunch": "🌞", "dinner": "🌙"}.get(r['meal'], "")
                meal_badge = f" {meal_emoji}" if meal_emoji else ""
            
            st.write(f"**{i}. {r['item_name']}**{meal_badge} — 🔥 {r['calories']} cal{macro_info} — 📍 {r['hall']}")
        
        # Show healthier alternatives for top result
        st.divider()
        st.subheader("💚 Healthier Alternatives")
        
        healthier = suggest_healthier(filtered_df, results[0]['item_name'])
        
        if healthier:
            for i, h in enumerate(healthier, 1):
                calories_saved = results[0]['calories'] - h['calories']
                
                # Format macro info
                macro_info = ""
                if 'protein_g' in h and 'carbs_g' in h and 'fat_g' in h:
                    macro_info = f" — 🥩 {h['protein_g']}g protein, 🍞 {h['carbs_g']}g carbs, 🧈 {h['fat_g']}g fat"
                
                meal_badge = ""
                if 'meal' in h:
                    meal_emoji = {"breakfast": "🌅", "lunch": "🌞", "dinner": "🌙"}.get(h['meal'], "")
                    meal_badge = f" {meal_emoji}" if meal_emoji else ""
                
                st.write(
                    f"**{i}. {h['item_name']}**{meal_badge} — 🔥 {h['calories']} cal{macro_info} — 📍 {h['hall']} "
                    f"✅ *(Save {calories_saved} calories)*"
                )
        else:
            st.info("No lower-calorie alternatives found for this meal.")
    else:
        st.warning(f"No results found for '{search_query}'. Try a different search term.")

elif upload_image or camera_image:
    # Use whichever image source is available
    image_source = camera_image if camera_image else upload_image
    
    st.subheader("📸 Analyzing your meal...")
    
    # Save uploaded image temporarily
    temp_path = "temp_image.jpg"
    with open(temp_path, "wb") as f:
        f.write(image_source.getbuffer())
    
    # Display the uploaded image
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(image_source, caption="Your Meal", width="stretch")
    
    with col2:
        # Get predictions from Gemini (now with menu context)
        with st.spinner("Identifying meal..."):
            predictions = predict_meal_from_image(temp_path, None)
        
        if predictions:
            st.success("✅ Meal identified!")
            for p in predictions:
                st.write(f"**Detected:** {p['label']} (Confidence: {p['confidence']*100:.0f}%)")
            
            # Try to find the exact match in our menu
            detected_name = predictions[0]['label']
            exact_match = search_meals(filtered_df, detected_name, top_n=1)
            
            if exact_match:
                st.info(f"📍 Found in menu: **{exact_match[0]['item_name']}** — {exact_match[0]['calories']} cal")
                
                # Health score
                st.subheader("💡 Health Score")
                nutrition_info = exact_match[0]
                calories = nutrition_info.get("calories", 0)
                protein = nutrition_info.get("protein_g", 0)
                fat = nutrition_info.get("fat_g", 0)
                score = max(0, min(100, int(100 - calories/30 + protein*2 - fat*1.5)))
                explanation = f"Calories: {calories}, Protein: {protein}g, Fat: {fat}g — balanced for a healthy meal."
                st.metric("Health Score", f"{score}/100")
                st.write(f"💬 {explanation}")

                # Log button
                if st.button("➕ Log this meal"):
                    meal_data = {
                        "item_name": detected_name,
                        "calories": calories,
                        "protein_g": protein,
                        "fat_g": fat,
                    }
                    log_meal(meal_data)
                    st.success("Meal logged ✅")

                # Show healthier alternatives
                st.divider()
                st.subheader("💚 Healthier Alternatives")
                
                healthier = suggest_healthier(filtered_df, exact_match[0]['item_name'])
                
                if healthier:
                    for i, h in enumerate(healthier, 1):
                        calories_saved = exact_match[0]['calories'] - h['calories']
                        
                        # Format macro info
                        macro_info = ""
                        if 'protein_g' in h and 'carbs_g' in h and 'fat_g' in h:
                            macro_info = f" — 🥩 {h['protein_g']}g protein, 🍞 {h['carbs_g']}g carbs, 🧈 {h['fat_g']}g fat"
                        
                        meal_badge = ""
                        if 'meal' in h:
                            meal_emoji = {"breakfast": "🌅", "lunch": "🌞", "dinner": "🌙"}.get(h['meal'], "")
                            meal_badge = f" {meal_emoji}" if meal_emoji else ""
                        
                        st.write(
                            f"**{i}. {h['item_name']}**{meal_badge} — 🔥 {h['calories']} cal{macro_info} — 📍 {h['hall']} "
                            f"✅ *(Save {calories_saved} calories)*"
                        )
                else:
                    st.info("No lower-calorie alternatives found for this meal.")
            else:
                st.warning(
                    f"⚠️ Could not find exact match for '{detected_name}' in menu. Try searching manually below."
                )
                
                # Show a search box for manual correction
                manual_search = st.text_input("Search manually:", key="manual_search")
                if manual_search:
                    manual_results = search_meals(filtered_df, manual_search, top_n=3)
                    if manual_results:
                        st.write("**Suggestions:**")
                        for i, r in enumerate(manual_results, 1):
                            st.write(f"{i}. {r['item_name']} — {r['calories']} cal — {r['hall']}")
            
            # Show today's totals vs goals
            today_meals = get_today_meals()
            if today_meals:
                total_cal = sum(m.get("calories",0) for m in today_meals)
                total_protein = sum(m.get("protein_g",0) for m in today_meals)
                total_fat = sum(m.get("fat_g",0) for m in today_meals)
                st.divider()
                st.subheader("📊 Today's Progress")
                st.write(f"Calories: {total_cal}/{goal_calories}")
                st.write(f"Protein: {total_protein}/{goal_protein} g")
                st.write(f"Fat: {total_fat}/{goal_fat} g")
                
                if total_cal > goal_calories:
                    st.warning(f"⚠️ Over daily calorie goal by {total_cal - goal_calories}")
                else:
                    st.success(f"✅ Under daily calorie goal by {goal_calories - total_cal}")
                
        else:
            st.error("❌ Could not identify the meal. Make sure GEMINI_API_KEY is set, or try a clearer image.")
    
    # Clean up temp file
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except:
        pass

else:
    # Welcome screen
    st.info("👈 **Get started:** Search for a meal, upload an image, or take a photo in the sidebar!")
    
    st.markdown("""
    ### How it works:
    1. **Filter your options**: Select dining hall and meal time
    2. **Search by name**: Type a meal name (e.g., "scrambled eggs") to see nutrition info
    3. **Upload an image**: Choose a photo from your device
    4. **Take a photo**: Use your camera to snap a pic of your meal (mobile-friendly!)
    5. **Get alternatives**: Discover healthier options with better nutrition
    6. **Meal Builder**: Build your own meals by adding as many foods as you would like
    
    ### Features:
    - 🔍 Search across multiple dining halls
    - 📊 Complete nutrition info (calories, protein, carbs, fat)
    - 🤖 AI-powered image recognition with smart matching
    - 💡 Smart recommendations based on meal type and nutrition
    - 🕐 Filter by meal time (breakfast/lunch/dinner)
    - 🏫 Filter by dining hall location
    - 🍜 Meal Builder 
    

    """)
    
    # Show sample of available meals
    if not filtered_df.empty:
        st.divider()
        st.subheader("📋 Sample Menu Items")
        
        # Prepare sample columns
        sample_cols = ['item_name', 'calories', 'hall']
        if 'protein_g' in filtered_df.columns:
            sample_cols.append('protein_g')
        if 'meal' in filtered_df.columns:
            sample_cols.append('meal')
            
        sample = filtered_df.sample(min(10, len(filtered_df)))[sample_cols]
        st.dataframe(sample, use_container_width=True, hide_index=True)
