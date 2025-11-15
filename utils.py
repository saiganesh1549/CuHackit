import pandas as pd
import os
import requests
import base64
from typing import List, Dict, Optional

def load_menus() -> pd.DataFrame:
    """
    Load and combine menu CSVs from multiple dining halls.
    
    Returns:
        pd.DataFrame with columns: item_name, calories, hall, meal
    """
    csv_files = ['core.csv', 'douthit.csv', 'shilletter.csv']
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
        return pd.DataFrame(columns=['item_name', 'calories', 'hall', 'meal'])
    
    # Combine all dataframes
    combined_df = pd.concat(dataframes, ignore_index=True)
    
    # Strip whitespace from item_name
    if 'item_name' in combined_df.columns:
        combined_df['item_name'] = combined_df['item_name'].str.strip()
    
    # Keep only necessary columns
    columns_to_keep = ['item_name', 'calories', 'hall', 'meal']
    
    # Add optional columns if they exist
    if 'protein_g' in combined_df.columns:
        columns_to_keep.append('protein_g')
    if 'carbs_g' in combined_df.columns:
        columns_to_keep.append('carbs_g')
    if 'fat_g' in combined_df.columns:
        columns_to_keep.append('fat_g')
    
    combined_df = combined_df[columns_to_keep]
    
    # Remove rows with missing calories
    combined_df = combined_df.dropna(subset=['calories'])
    
    return combined_df


def search_meals(menu_df: pd.DataFrame, query: str, top_n: int = 5) -> List[Dict]:
    """
    Search for meals matching the query string.
    
    Args:
        menu_df: DataFrame with meal data
        query: Search string
        top_n: Number of results to return
        
    Returns:
        List of dictionaries with item_name, calories, hall
    """
    if menu_df.empty:
        return []
    
    query = query.lower().strip()
    
    # Create a relevance score
    menu_df['score'] = menu_df['item_name'].str.lower().apply(
        lambda x: 100 if query in x else 0
    )
    
    # Filter and sort results
    results = menu_df[menu_df['score'] > 0].sort_values(
        by='score', ascending=False
    ).head(top_n)
    
    # Return as list of dictionaries
    return results[['item_name', 'calories', 'hall']].to_dict('records')


def suggest_healthier(menu_df: pd.DataFrame, meal_name: str, top_n: int = 3) -> List[Dict]:
    """
    Suggest healthier alternatives with lower calories.
    
    Args:
        menu_df: DataFrame with meal data
        meal_name: Name of the meal to find alternatives for
        top_n: Number of alternatives to return
        
    Returns:
        List of dictionaries with item_name, calories, hall
    """
    if menu_df.empty:
        return []
    
    # Find the meal
    meal = menu_df[menu_df['item_name'].str.lower() == meal_name.lower()]
    
    if meal.empty:
        return []
    
    meal_calories = meal.iloc[0]['calories']
    
    # Find meals with lower calories
    healthier = menu_df[menu_df['calories'] < meal_calories].sort_values(
        by='calories', ascending=True
    ).head(top_n)
    
    return healthier[['item_name', 'calories', 'hall']].to_dict('records')


def predict_meal_from_image(image_path: str) -> List[Dict]:
    """
    Use Gemini Vision API to identify meals from an image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        List of dictionaries with label and confidence
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("Warning: GEMINI_API_KEY not set")
        return []
    
    try:
        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Gemini API endpoint (correct endpoint for vision)
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": "Identify this food item. Return only the name of the dish, nothing else."
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_data
                        }
                    }
                ]
            }]
        }
        
        response = requests.post(
            f"{url}?key={api_key}",
            headers=headers,
            json=payload
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Parse Gemini response
        if 'candidates' in result and len(result['candidates']) > 0:
            text = result['candidates'][0]['content']['parts'][0]['text']
            # Return as prediction format
            return [{
                'label': text.strip(),
                'confidence': 0.92  # Gemini doesn't provide confidence scores
            }]
        
        return []
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return []