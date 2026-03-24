import pandas as pd
import os
import base64
from typing import List, Dict, Optional
#from google import genai
import google.generativeai as genai


def load_menus() -> pd.DataFrame:
    """
    Load and combine menu CSVs from multiple dining halls.

    Returns:
        pd.DataFrame with columns: item_name, calories, hall, meal
    """
    csv_files = ["core.csv", "douthit.csv", "shiletter.csv"]
    dataframes = []

    for file in csv_files:
        if os.path.exists(file):
            df = pd.read_csv(file)
            # Strip whitespace from column names
            df.columns = df.columns.str.strip()
            dataframes.append(df)
        else:
            print(f"Warning: {file} not found")

    if not dataframes:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=["item_name", "calories", "hall", "meal"])

    # Combine all dataframes
    combined_df = pd.concat(dataframes, ignore_index=True)

    # Strip whitespace from item_name
    if "item_name" in combined_df.columns:
        combined_df["item_name"] = combined_df["item_name"].str.strip()

    # Keep only necessary columns
    columns_to_keep = ["item_name", "calories", "hall", "meal"]

    # Add optional columns if they exist
    if "protein_g" in combined_df.columns:
        columns_to_keep.append("protein_g")
    if "carbs_g" in combined_df.columns:
        columns_to_keep.append("carbs_g")
    if "fat_g" in combined_df.columns:
        columns_to_keep.append("fat_g")

    combined_df = combined_df[columns_to_keep]

    # Remove rows with missing calories
    combined_df = combined_df.dropna(subset=["calories"])

    # Remove duplicates based on item_name only (keep first occurrence)
    combined_df = combined_df.drop_duplicates(subset=["item_name"], keep="first")

    return combined_df


def search_meals(menu_df: pd.DataFrame, query: str, top_n: int = 5) -> List[Dict]:
    """
    Search for meals matching the query string.
    Returns unique items only - no duplicates in results.

    Args:
        menu_df: DataFrame with meal data
        query: Search string
        top_n: Number of results to return

    Returns:
        List of dictionaries with item_name, calories, hall, and macros if available
    """
    if menu_df.empty:
        return []

    query = query.lower().strip()

    # Create a copy to avoid modifying original
    search_df = menu_df.copy()

    # Create a relevance score
    search_df["score"] = (
        search_df["item_name"].str.lower().apply(lambda x: 100 if query in x else 0)
    )

    # Filter results
    results = search_df[search_df["score"] > 0].copy()

    # Remove any duplicates in search results
    results = results.drop_duplicates(subset=["item_name"], keep="first")

    # Sort and limit
    results = results.sort_values(by="score", ascending=False).head(top_n)

    # Prepare return columns
    return_cols = ["item_name", "calories", "hall"]
    if "protein_g" in results.columns:
        return_cols.append("protein_g")
    if "carbs_g" in results.columns:
        return_cols.append("carbs_g")
    if "fat_g" in results.columns:
        return_cols.append("fat_g")
    if "meal" in results.columns:
        return_cols.append("meal")

    # Return as list of dictionaries
    return results[return_cols].to_dict("records")


def suggest_healthier(
    menu_df: pd.DataFrame, meal_name: str, top_n: int = 3
) -> List[Dict]:
    """
    Suggest healthier alternatives using a multi-factor health score.
    Considers calories, protein, fat, and meal similarity for realistic suggestions.
    Excludes the original meal from suggestions.

    Args:
        menu_df: DataFrame with meal data
        meal_name: Name of the meal to find alternatives for
        top_n: Number of alternatives to return

    Returns:
        List of dictionaries with item_name, calories, hall, and macros if available
    """
    if menu_df.empty:
        return []

    # Find the meal
    meal = menu_df[menu_df["item_name"].str.lower() == meal_name.lower()]

    if meal.empty:
        return []

    meal_calories = meal.iloc[0]["calories"]
    meal_item_name = meal.iloc[0]["item_name"].lower()

    # Check if we have macro data
    has_macros = "protein_g" in menu_df.columns and "fat_g" in menu_df.columns

    # Filter candidates (only lower calorie options, but not too low)
    # EXCLUDE the original meal from alternatives
    min_calories = max(50, meal_calories * 0.3)  # At least 30% of original or 50 cal
    candidates = menu_df[
        (menu_df["calories"] < meal_calories)
        & (menu_df["calories"] >= min_calories)
        & (menu_df["item_name"].str.lower() != meal_item_name)  # Exclude original meal
    ].copy()

    if candidates.empty:
        return []

    # Remove duplicates
    candidates = candidates.drop_duplicates(subset=["item_name"], keep="first")

    if has_macros:
        # Calculate health score with macros
        meal_protein = meal.iloc[0].get("protein_g", 0)
        meal_fat = meal.iloc[0].get("fat_g", 0)

        # Health score factors:
        # 1. Calorie reduction (normalized to 0-100)
        candidates["calorie_score"] = (
            (meal_calories - candidates["calories"]) / meal_calories * 100
        )

        # 2. Protein quality (protein per calorie ratio)
        candidates["protein_ratio"] = candidates["protein_g"] / (
            candidates["calories"] + 1
        )
        candidates["protein_score"] = candidates["protein_ratio"] * 1000  # Scale up

        # 3. Fat penalty (lower is better)
        candidates["fat_score"] = -candidates["fat_g"] * 2

        # 4. Meal similarity bonus (same category = more realistic)
        def get_meal_category(name):
            name = name.lower()
            if any(word in name for word in ["burger", "sandwich", "wrap"]):
                return "sandwich"
            elif any(word in name for word in ["pizza", "slice"]):
                return "pizza"
            elif any(word in name for word in ["salad", "lettuce", "spinach"]):
                return "salad"
            elif any(
                word in name for word in ["chicken", "beef", "pork", "turkey", "ham"]
            ):
                return "protein"
            elif any(word in name for word in ["fries", "potato", "chips"]):
                return "sides"
            elif any(word in name for word in ["cookie", "brownie", "cake", "dessert"]):
                return "dessert"
            elif any(word in name for word in ["yogurt", "oatmeal", "cereal", "eggs"]):
                return "breakfast"
            else:
                return "other"

        meal_category = get_meal_category(meal_item_name)
        candidates["category"] = candidates["item_name"].apply(get_meal_category)
        candidates["similarity_score"] = candidates["category"].apply(
            lambda x: 30 if x == meal_category else 0
        )

        # Combined health score
        candidates["health_score"] = (
            candidates["calorie_score"] * 0.4  # 40% weight on calories
            + candidates["protein_score"] * 0.3  # 30% weight on protein
            + candidates["fat_score"] * 0.1  # 10% weight on fat
            + candidates["similarity_score"] * 0.2  # 20% weight on similarity
        )

    else:
        # Fallback: just use calories if no macro data
        candidates["health_score"] = meal_calories - candidates["calories"]

    # Sort by health score and get top results
    healthier = candidates.nlargest(top_n, "health_score")

    # Prepare return columns
    return_cols = ["item_name", "calories", "hall"]
    if "protein_g" in healthier.columns:
        return_cols.append("protein_g")
    if "carbs_g" in healthier.columns:
        return_cols.append("carbs_g")
    if "fat_g" in healthier.columns:
        return_cols.append("fat_g")
    if "meal" in healthier.columns:
        return_cols.append("meal")

    return healthier[return_cols].to_dict("records")


def find_best_match(menu_df: pd.DataFrame, detected_food: str) -> Optional[str]:
    """
    Find the best matching menu item for a detected food name.
    Uses fuzzy matching to handle variations in naming.

    Args:
        menu_df: DataFrame with menu items
        detected_food: The food name detected by Gemini

    Returns:
        Best matching menu item name or None
    """
    if menu_df is None or menu_df.empty:
        return None

    detected_lower = detected_food.lower().strip()

    # Remove common articles and words
    detected_lower = (
        detected_lower.replace("the ", "").replace("a ", "").replace("an ", "")
    )

    # First try exact match
    exact_match = menu_df[menu_df["item_name"].str.lower() == detected_lower]
    if not exact_match.empty:
        return exact_match.iloc[0]["item_name"]

    # Try partial matches
    # Split detected food into words
    words = detected_lower.split()

    # Score each menu item based on word matches
    best_match = None
    best_score = 0

    for _, row in menu_df.iterrows():
        item_name = row["item_name"].lower()
        score = 0

        # Check if detected food is substring of menu item
        if detected_lower in item_name:
            score = 100
        # Check if menu item is substring of detected food
        elif item_name in detected_lower:
            score = 90
        else:
            # Count matching words
            for word in words:
                if len(word) > 2 and word in item_name:  # Ignore very short words
                    score += 20

            # Bonus for matching all words
            if all(word in item_name for word in words if len(word) > 2):
                score += 30

        if score > best_score and score >= 20:  # Require at least some match
            best_score = score
            best_match = row["item_name"]

    print(f"Best match for '{detected_food}': '{best_match}' (score: {best_score})")
    return best_match


def predict_meal_from_image(image_path: str, menu_df: pd.DataFrame = None):
    """
    Use Gemini Vision API to identify the food in an image.
    This version ignores menu_df entirely and returns ONLY the model output.
    """

    try:
        import streamlit as st
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not set")
        import streamlit as st
        st.error("API key not found")
        return []
    else:
        import streamlit as st
        st.info(f"API key found, length: {len(api_key)}")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    try:
        # Load image
        import PIL.Image
        img = PIL.Image.open(image_path)

        prompt = """You are a food recognition expert.
Identify the main food item in this image. 
Return ONLY the food name in lowercase with no extra words.
If the food item appears to be a combination of multiple foods 
into a single meal Return ONLY the your interpretation of the meal and its contents."""

        response = model.generate_content([prompt, img])

        # Extract pure text result
        result_text = response.text.strip().lower()

        return [{
            "label": result_text,
            "confidence": 0.92,
            "raw_detection": result_text,
        }]

    except Exception as e:
        import streamlit as st
        st.error(f"Gemini API error: {e}")
        import traceback
        traceback.print_exc()
        return []


        detected_text = result_text
        original_detected = result_text

        # Try menu fuzzy-matching
        if menu_df is not None:
            best_match = find_best_match(menu_df, detected_text)
            if best_match:
                print(f"Matched to menu item: '{best_match}'")
                detected_text = best_match
            else:
                print(f"No menu match found for: '{original_detected}'")

            return [
                    {
                    "label": detected_text,
                        "confidence": 0.92,
                        "raw_detection": original_detected,
            }
        ]
    

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        import traceback

        traceback.print_exc()
        return []
    

def calculate_meal_nutrition(food_list, menu_df):
    total = {
        "calories": 0,
        "protein_g": 0,
        "carbs_g": 0,
        "fat_g": 0,
        "matched_items": []  # store detailed matches
    }

    for food in food_list:
        # Try to find the food in the menu (case-insensitive partial match)
        matches = menu_df[menu_df["item_name"].str.contains(food, case=False)]

        if not matches.empty:
            item = matches.iloc[0].to_dict()
            total["matched_items"].append(item)

            total["calories"] += item.get("calories", 0)
            total["protein_g"] += item.get("protein_g", 0)
            total["carbs_g"] += item.get("carbs_g", 0)
            total["fat_g"] += item.get("fat_g", 0)

    return total
    
    