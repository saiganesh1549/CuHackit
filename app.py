import streamlit as st
import os
from utils import load_menus, search_meals, suggest_healthier, predict_meal_from_image

# Page config
st.set_page_config(page_title="AI Meal Optimizer", layout="wide")

# Title
st.title("🍽️ AI Meal Optimizer")
st.markdown("Find healthier meal alternatives from your dining hall menus")

# Load menus with caching
@st.cache_data
def get_menus():
    return load_menus()

menu_df = get_menus()

# Display data load status
if menu_df.empty:
    st.error("⚠️ No menu data found. Make sure CSV files are in the same directory as the app.")
else:
    st.success(f"✅ Loaded {len(menu_df)} items from dining halls")

# Sidebar
st.sidebar.header("🔍 Meal Options")
search_query = st.sidebar.text_input("Search for a meal:", placeholder="e.g., scrambled eggs")
upload_image = st.sidebar.file_uploader(
    "Or upload an image of your meal", 
    type=["jpg", "png", "jpeg"]
)

# Main app logic
if search_query:
    st.subheader(f"🔎 Results for '{search_query}'")
    
    results = search_meals(menu_df, search_query)
    
    if results:
        # Display search results
        for i, r in enumerate(results, 1):
            st.write(f"**{i}. {r['meal']}** — {r['calories']} cal — 📍 {r['meal_location']}")
        
        # Show healthier alternatives for top result
        st.divider()
        st.subheader("💚 Healthier Alternatives")
        
        healthier = suggest_healthier(menu_df, results[0]['meal_name'])
        
        if healthier:
            for i, h in enumerate(healthier, 1):
                calories_saved = results[0]['calories'] - h['calories']
                st.write(
                    f"**{i}. {h['meal_name']}** — {h['calories']} cal — 📍 {h['meal_location']} "
                    f"*(Save {calories_saved} calories)*"
                )
        else:
            st.info("No lower-calorie alternatives found for this meal.")
    else:
        st.warning(f"No results found for '{search_query}'. Try a different search term.")

elif upload_image:
    st.subheader("📸 Analyzing your meal...")
    
    # Save uploaded image temporarily
    temp_path = "temp_image.jpg"
    with open(temp_path, "wb") as f:
        f.write(upload_image.getbuffer())
    
    # Display the uploaded image
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(upload_image, caption="Uploaded Image", use_container_width=True)
    
    with col2:
        # Get predictions from Gemini
        with st.spinner("Identifying meal..."):
            predictions = predict_meal_from_image(temp_path)
        
        if predictions:
            st.success("✅ Meal identified!")
            for p in predictions:
                st.write(f"**Detected:** {p['label']} (Confidence: {p['confidence']*100:.0f}%)")
            
            # Suggest healthier alternatives
            st.divider()
            st.subheader("💚 Healthier Alternatives")
            
            healthier = suggest_healthier(menu_df, predictions[0]['label'])
            
            if healthier:
                for i, h in enumerate(healthier, 1):
                    st.write(
                        f"**{i}. {h['meal_name']}** — {h['calories']} cal — 📍 {h['meal_location']}"
                    )
            else:
                st.info(
                    f"No exact match found for '{predictions[0]['label']}' in our menu database. "
                    "Try searching manually or upload a clearer image."
                )
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
    st.info("👈 **Get started:** Search for a meal or upload an image in the sidebar!")
    
    st.markdown("""
    ### How it works:
    1. **Search by name**: Type a meal name (e.g., "scrambled eggs") to see nutrition info
    2. **Upload an image**: Take a photo of your meal and let AI identify it
    3. **Get alternatives**: Discover healthier options with fewer calories
    
    ### Features:
    - 🔍 Search across multiple dining halls
    - 📊 Compare calorie counts instantly
    - 🤖 AI-powered image recognition (requires GEMINI_API_KEY)
    - 💡 Smart recommendations for healthier choices
    """)
    
    # Show sample of available meals
    if not menu_df.empty:
        st.divider()
        st.subheader("📋 Sample Menu Items")
        sample = menu_df.sample(min(10, len(menu_df)))[['meal_name', 'calories', 'meal_location']]
        st.dataframe(sample, use_container_width=True, hide_index=True)