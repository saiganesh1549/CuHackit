import streamlit as st
from ai_meal_optimizer.utils import load_all_menus, find_meal, suggest_healthy, predict_top_3_gemini

st.set_page_config(page_title="AI Campus Meal Optimizer")

# ---------- Load Data ----------
menu_df = load_all_menus()

# ---------- App Header ----------
st.title("AI Campus Meal Optimizer")
st.write("Search for meals or scan a photo to identify your meal!")

# ---------- Search by Name ----------
st.subheader("Search meals by name")
query = st.text_input("Type your meal query:")

if query:
    results = find_meal(menu_df, query)
    if not results.empty:
        st.write("Top meal matches:")
        st.table(results[["item_name", "calories", "protein", "carbs", "fat"]])
    else:
        st.write("No matching meals found.")

# ---------- Scan Meal Image ----------
st.subheader("Scan your meal")
image_file = st.file_uploader("Upload a photo of your meal", type=["png", "jpg", "jpeg"])

if image_file:
    menu_list = menu_df["item_name"].tolist()
    top_suggestions = predict_top_3_gemini(image_file, menu_list)
    st.write("Top AI predictions for your meal:")
    st.write(top_suggestions)

    healthy_suggestions = suggest_healthy(menu_df)
    st.write("Healthy suggestions:")
    st.write(healthy_suggestions)



