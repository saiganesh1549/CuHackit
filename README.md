# CuHackit
Jin, Sai, and CJ's CuHackit Repo
# 🍽 AI Meal Optimizer

![Python](https://img.shields.io/badge/python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/streamlit-v1.28-green?logo=streamlit)
![License](https://img.shields.io/badge/license-MIT-yellow)

Welcome to **AI Meal Optimizer** – your intelligent dining assistant for campus meals!  
Search meals, check nutrition info, get AI predictions from images, and find healthier alternatives – all in a clean, modern interface.

---


## 🏆 Features

- **Search Meals:** Quickly find meals across all dining halls.  
- **Dining Hall Filter:** Filter by Core, Douthit, or Shilletter.  
- **Meal Nutritional Info:** Calories, protein, carbs, fat for every meal.  
- **AI Image Prediction:** Upload a photo of your meal for AI predictions (Gemini API).  
- **Healthier Alternatives:** Suggest lower-calorie meals.  
- **Multi-Hall CSV Integration:** Combines all hall menus into one dataset.  
- **Clean, Professional UI:** Streamlit interface with sidebar filters, columns, and expandable cards.  

---

## 📂 File Structure

ai_meal_optimizer/
├── app.py # Main Streamlit app
├── utils.py # Helper functions
├── core.csv # Core dining hall menu
├── douthit.csv # Douthit dining hall menu
├── schilletter.csv # Shilletter dining hall menu
├── requirements.txt # Python dependencies
└── README.md

yaml
Copy code

---

## 🛠 Installation

1. Clone the repo:  

bash
git clone https://github.com/CuHackit/ai_meal_optimizer.git
cd ai_meal_optimizer
Create a virtual environment:

bash
Copy code
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Set up Gemini API key:

bash
Copy code
export GEMINI_API_KEY="your_api_key_here"  # macOS/Linux
setx GEMINI_API_KEY "your_api_key_here"    # Windows
🚀 Running the App
bash
Copy code
streamlit run ai_meal_optimizer/app.py
Sidebar options:

Filter by dining hall

Search meals

Upload meal images for AI predictions

Main display:

Meal info cards

Expandable healthier alternatives

Optional placeholder images

💡 Usage Examples
Search for a meal:

Enter "chicken" in the sidebar search

Results show calories, macronutrients, and hall location

Upload meal image:

Upload meal.jpg

AI predicts meal with confidence scores

Healthier alternatives:

Expand “Healthier alternatives” card to see lower-calorie options

⚡ Future Improvements
Add real meal images for each item

Visualize nutritional breakdown with charts

Save favorite meals

Add a weekly meal planner

Improve AI predictions with a custom-trained model
