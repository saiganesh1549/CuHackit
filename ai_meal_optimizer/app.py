import streamlit as st
from PIL import Image
import pandas as pd
from utils import load_menu, find_meal, predict_top_3

st.set_page_config(page_title="AI Campus Meal Optimizer", layout="centered")
st.title("AI Campus Meal Optimizer")
st.write("Search for meals or scan a photo to identify your meal!")

# --- Load menu ---
menu_df = load_menu()  # safe: uses mock if CSV missing/empty

# --- Text search ---
st.subheader("Search meals by name")
query = st.text_input("Type your meal query:")

if query:
    results = find_meal(query, menu_df)
    st.subheader("Top meal matches")
    st.write(results)

# --- Scan meal photo ---
st.subheader("Scan your meal")
uploaded_image = st.file_uploader("Upload a photo of your meal", type=["png", "jpg", "jpeg"])

if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, caption="Uploaded meal")

    st.write("Identifying meal...")

    # --- Demo AI Top 3 predictions ---
    top_suggestions = predict_top_3(menu_df)

    st.subheader("Top 3 predicted meals from menu")
    for meal in top_suggestions:
        st.write(f"**{meal}**")
        meal_info = menu_df[menu_df['item_name'] == meal]
        st.dataframe(meal_info)


