import pandas as pd
from rapidfuzz import process
import os
import random

# Load menu with fallback if CSV missing or empty
def load_menu(csv_path="clemson_food.csv"):
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            if df.empty:
                print("CSV is empty. Using mock menu.")
                return load_menu_mock()
            return df
        except Exception as e:
            print(f"Error reading CSV: {e}. Using mock menu.")
            return load_menu_mock()
    else:
        print("CSV not found. Using mock menu.")
        return load_menu_mock()

# Mock menu fallback
def load_menu_mock():
    data = {
        "item_name": ["Chicken Sandwich", "Veggie Burger", "Pasta Primavera", "Salad Bowl", "Beef Taco"],
        "calories": [500, 400, 350, 200, 450],
        "protein": [30, 20, 15, 5, 25],
        "carbs": [50, 45, 60, 20, 40],
        "fat": [20, 10, 5, 2, 15]
    }
    return pd.DataFrame(data)

# Text search function
def find_meal(query, menu_df):
    results = process.extract(query, menu_df['item_name'], limit=5)
    return results

# Demo Top 3 AI predictions (replace with Gemini/OpenAI API later)
def predict_top_3(menu_df):
    menu_list = menu_df['item_name'].tolist()
    if len(menu_list) <= 3:
        return menu_list
    return random.sample(menu_list, 3)

def predict_top_3(menu_df):
    import random
    menu_list = menu_df['item_name'].tolist()
    if len(menu_list) <= 3:
        return menu_list
    return random.sample(menu_list, 3)