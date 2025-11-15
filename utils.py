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
    
    # Remove duplicates based on item_name only (keep first occurrence)
    # This ensures users see variety, not the same item repeated
    combined_df = combined_df.drop_duplicates(
        subset=['item_name'],
        keep='first'
    )
    
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
    
    # Create a relevance score
    menu_df['score'] = menu_df['item_name'].str.lower().apply(
        lambda x: 100 if query in x else 0
    )
    
    # Filter results
    results = menu_df[menu_df['score'] > 0].copy()
    
    # Remove any duplicates in search results (shouldn't happen, but just in case)
    results = results.drop_duplicates(subset=['item_name'], keep='first')
    
    # Sort and limit
    results = results.sort_values(by='score', ascending=False).head(top_n)
    
    # Prepare return columns
    return_cols = ['item_name', 'calories', 'hall']
    if 'protein_g' in results.columns:
        return_cols.append('protein_g')
    if 'carbs_g' in results.columns:
        return_cols.append('carbs_g')
    if 'fat_g' in results.columns:
        return_cols.append('fat_g')
    if 'meal' in results.columns:
        return_cols.append('meal')
    
    # Return as list of dictionaries
    return results[return_cols].to_dict('records')


def suggest_healthier(menu_df: pd.DataFrame, meal_name: str, top_n: int = 3) -> List[Dict]:
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
    meal = menu_df[menu_df['item_name'].str.lower() == meal_name.lower()]
    
    if meal.empty:
        return []
    
    meal_calories = meal.iloc[0]['calories']
    meal_item_name = meal.iloc[0]['item_name'].lower()
    
    # Check if we have macro data
    has_macros = 'protein_g' in menu_df.columns and 'fat_g' in menu_df.columns
    
    # Filter candidates (only lower calorie options, but not too low)
    # EXCLUDE the original meal from alternatives
    min_calories = max(50, meal_calories * 0.3)  # At least 30% of original or 50 cal
    candidates = menu_df[
        (menu_df['calories'] < meal_calories) & 
        (menu_df['calories'] >= min_calories) &
        (menu_df['item_name'].str.lower() != meal_item_name)  # Exclude original meal
    ].copy()
    
    if candidates.empty:
        return []
    
    # Remove duplicates
    candidates = candidates.drop_duplicates(subset=['item_name'], keep='first')
    
    if has_macros:
        # Calculate health score with macros
        meal_protein = meal.iloc[0].get('protein_g', 0)
        meal_fat = meal.iloc[0].get('fat_g', 0)
        
        # Health score factors:
        # 1. Calorie reduction (normalized to 0-100)
        candidates['calorie_score'] = (meal_calories - candidates['calories']) / meal_calories * 100
        
        # 2. Protein quality (protein per calorie ratio)
        candidates['protein_ratio'] = candidates['protein_g'] / (candidates['calories'] + 1)
        candidates['protein_score'] = candidates['protein_ratio'] * 1000  # Scale up
        
        # 3. Fat penalty (lower is better)
        candidates['fat_score'] = -candidates['fat_g'] * 2
        
        # 4. Meal similarity bonus (same category = more realistic)
        def get_meal_category(name):
            name = name.lower()
            if any(word in name for word in ['burger', 'sandwich', 'wrap']):
                return 'sandwich'
            elif any(word in name for word in ['pizza', 'slice']):
                return 'pizza'
            elif any(word in name for word in ['salad', 'lettuce', 'spinach']):
                return 'salad'
            elif any(word in name for word in ['chicken', 'beef', 'pork', 'turkey', 'ham']):
                return 'protein'
            elif any(word in name for word in ['fries', 'potato', 'chips']):
                return 'sides'
            elif any(word in name for word in ['cookie', 'brownie', 'cake', 'dessert']):
                return 'dessert'
            elif any(word in name for word in ['yogurt', 'oatmeal', 'cereal', 'eggs']):
                return 'breakfast'
            else:
                return 'other'
        
        meal_category = get_meal_category(meal_item_name)
        candidates['category'] = candidates['item_name'].apply(get_meal_category)
        candidates['similarity_score'] = candidates['category'].apply(
            lambda x: 30 if x == meal_category else 0
        )
        
        # Combined health score
        candidates['health_score'] = (
            candidates['calorie_score'] * 0.4 +  # 40% weight on calories
            candidates['protein_score'] * 0.3 +  # 30% weight on protein
            candidates['fat_score'] * 0.1 +      # 10% weight on fat
            candidates['similarity_score'] * 0.2  # 20% weight on similarity
        )
        
    else:
        # Fallback: just use calories if no macro data
        candidates['health_score'] = (meal_calories - candidates['calories'])
    
    # Sort by health score and get top results
    healthier = candidates.nlargest(top_n, 'health_score')
    
    # Prepare return columns
    return_cols = ['item_name', 'calories', 'hall']
    if 'protein_g' in healthier.columns:
        return_cols.append('protein_g')
    if 'carbs_g' in healthier.columns:
        return_cols.append('carbs_g')
    if 'fat_g' in healthier.columns:
        return_cols.append('fat_g')
    if 'meal' in healthier.columns:
        return_cols.append('meal')
    
    return healthier[return_cols].to_dict('records')


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
    if menu_df.empty:
        return None
    
    detected_lower = detected_food.lower().strip()
    
    # First try exact match
    exact_match = menu_df[menu_df['item_name'].str.lower() == detected_lower]
    if not exact_match.empty:
        return exact_match.iloc[0]['item_name']
    
    # Try partial matches
    # Split detected food into words
    words = detected_lower.split()
    
    # Score each menu item based on word matches
    best_match = None
    best_score = 0
    
    for _, row in menu_df.iterrows():
        item_name = row['item_name'].lower()
        score = 0
        
        # Check if all words from detected food are in menu item
        if detected_lower in item_name:
            score = 100
        else:
            # Count matching words
            for word in words:
                if word in item_name:
                    score += 10
        
        if score > best_score and score >= 10:  # Require at least one word match
            best_score = score
            best_match = row['item_name']
    
    return best_match


def predict_meal_from_image(image_path: str) -> List[Dict]:
    """
    Use Gemini Vision API to identify meals from an image.
    Now includes fuzzy matching to connect detected food to CSV menu items.
    
    Args:
        image_path: Path to the image file
        menu_df: DataFrame of menu items for better matching
        
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
        
        # Build a list of available menu items to help Gemini
        menu_context = ""
        if menu_df is not None and not menu_df.empty:
            sample_items = menu_df['item_name'].head(50).tolist()
            menu_context = f"\n\nAvailable menu items include: {', '.join(sample_items[:30])}"
        
        # Gemini API endpoint (updated URL format)
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": f"""You are a food recognition expert for college dining halls. 
Identify this meal and return ONLY the exact menu item name or the most similar match.

Be specific but flexible - if you see:
- A burger → say "cheeseburger" or "burger"
- Pizza → say "cheese pizza" or "pepperoni pizza"
- Eggs → say "scrambled eggs"
- Fries → say "french fries"
- Chicken → specify if grilled, fried, or baked

{menu_context}

Return ONLY the item name in lowercase, no extra words, punctuation, or explanations."""
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
            url,
            headers=headers,
            json=payload
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Parse Gemini response
        if 'candidates' in result and len(result['candidates']) > 0:
            detected_text = result['candidates'][0]['content']['parts'][0]['text'].strip().lower()
            
            # Try to find best match in menu
            if menu_df is not None:
                best_match = find_best_match(menu_df, detected_text)
                if best_match:
                    detected_text = best_match
            
            return [{
                'label': detected_text,
                'confidence': 0.92
            }]
        
        return []
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return []