import pandas as pd
import os
from PIL import Image
import io

# Gemini Vision imports
from google.generativeai import client as genai

# Configure Gemini API key from environment
GEN_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEN_API_KEY)


# ---------- CSV / Menu Utilities ----------

def load_all_menus(csv_paths=None):
    """Load multiple CSVs into a single DataFrame"""
    if csv_paths is None:
        csv_paths = [
            "ai_meal_optimizer/core.csv",
            "ai_meal_optimizer/schiletter.csv",
            "ai_meal_optimizer/douthit.csv"
        ]
    dfs = []
    for path in csv_paths:
        if os.path.exists(path):
            dfs.append(pd.read_csv(path))
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame(columns=["item_name", "calories", "protein", "carbs", "fat"])


def find_meal(menu_df, query, top_n=5):
    """Find meals matching query"""
    menu_df["match_score"] = menu_df["item_name"].str.lower().apply(lambda x: query.lower() in x)
    results = menu_df[menu_df["match_score"]].copy()
    return results.head(top_n)


def suggest_healthy(menu_df, n=3):
    """Suggest the n lowest-calorie items"""
    if menu_df.empty:
        return []
    return menu_df.sort_values("calories").head(n)["item_name"].tolist()


# ---------- AI / Gemini Vision ----------

def predict_top_3_gemini(image_file, menu_list):
    """
    Send the image to Gemini Vision to identify top 3 menu items.
    Fallback to first 3 items if AI fails.
    """
    try:
        image_bytes = image_file.read()
        image_stream = io.BytesIO(image_bytes)

        prompt = f"Identify which of these menu items this image is: {', '.join(menu_list)}. Return top 3 items."

        response = genai.images.generate(
            model="gemini-vision",
            prompt=prompt,
            image=image_stream
        )

        # Assuming response['candidates'] has text predictions
        top_3 = [cand['text'] for cand in response.get('candidates', [])][:3]

        if not top_3:
            top_3 = menu_list[:3]  # fallback
    except Exception as e:
        print(f"Gemini AI error: {e}")
        top_3 = menu_list[:3]  # fallback
    return top_3
