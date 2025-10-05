import streamlit as st
from db_functions import add_plan
import json
from config import config
from config import get_ai_manager

st.markdown("""
    <style>
        /* General background and text */
        .stApp {
            background-color: #0e1117;
            color: #f5f5f5;
        }
        h1, h2, h3, h4, h5, h6, p, span, div {
            color: #f5f5f5 !important;
        }

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #1a1d23;
            color: #f5f5f5;
        }

        /* Buttons */
        div.stButton > button {
            background-color: #0078ff;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.6em 1em;
            font-weight: 600;
            transition: 0.2s ease-in-out;
        }
        div.stButton > button:hover {
            background-color: #0056b3;
            transform: scale(1.05);
        }

        /* Info boxes */
        .stAlert {
            background-color: #1f2937 !important;
            color: #e5e7eb !important;
            border: none;
        }

        /* Progress bar */
        [data-testid="stProgress"] > div > div {
            background-color: #0078ff !important;
        }

        /* Containers */
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
            background-color: #1a1d23;
            border: 1px solid #2e3440;
            border-radius: 12px;
            padding: 1em;
            margin-bottom: 1em;
        }
            
        section[data-testid="stSidebar"] .stAlert {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }

        section[data-testid="stSidebar"] .stAlert p {
            color: #f5f5f5 !important;
        }
        
        div.stAlert {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }

        div.stAlert p {
            color: #f5f5f5 !important;
        }
            
        header[data-testid="stHeader"] {
            background-color: #0e1117 !important; 
            color: #f5f5f5 !important;           
        }

        header[data-testid="stHeader"] .css-1v0mbdj {
            color: #f5f5f5 !important;
        }

        header[data-testid="stHeader"] {
            box-shadow: none !important;
        }

        /* Style for copyable code/latex blocks */
        [data-testid="stCodeBlock"], [data-testid="stLatex"] {
            background-color: #262730; /* A medium-dark grey */
            border-radius: 8px;
            padding: 1em;
        }
        
    </style>
""", unsafe_allow_html=True)

# Set up the page
st.set_page_config(page_title="Add Learning Plan", layout="wide")

# --- AI Manager ---
ai_manager = get_ai_manager()
if not ai_manager.initialize():
    st.error("AI could not be initialized. Check your secrets or environment variables.")
    st.stop()


def generate_learning_plan_json(target, time_in_days):
    """
    Generates a structured learning plan in JSON format using an AI model.
    """
    prompt = f"""
    Create a daily learning plan for a user who wants to learn '{target}' in {time_in_days} days.
    Your response must be a valid JSON array.
    Each element in the array should be an object representing a single day's plan.
    Each daily object must have the following keys:
    - "day": An integer representing the day number (from 1 to {time_in_days}).
    - "topic": A concise string for the main topic of the day.
    - "details": A string providing a brief description of tasks or concepts for the day.
    - "status": A string, which must be initialized to "pending".

    Do not include any text or markdown formatting outside of the JSON array itself.
    Example for 1 day:
    [
      {{
        "day": 1,
        "topic": "Introduction to Python",
        "details": "Learn basic syntax, variables, and data types.",
        "status": "pending"
      }}
    ]
    """
    response = ai_manager.generate_content(prompt)
    if not response:
        raise Exception("AI returned no content")
    cleaned_response = response.replace("```json", "").replace("```", "").strip()
    return cleaned_response


# Main content
st.title("Add a New Learning Plan")

# Input fields
st.info("Define your learning goal and the number of days you want to commit. Our AI will generate a customized day-by-day plan for you.")
learning_target = st.text_input("What do you want to learn?", placeholder="e.g., 'Python for Data Science' or 'the basics of Guitar'")
learning_time = st.number_input("Learning Time (in days)", min_value=1, step=1)
special_instructions = st.text_area("Special Instructions (Optional)", placeholder="e.g., 'Focus on practical examples', 'Avoid complex theory at the beginning'")

# Add Plan button
if st.button("Submit"):
    if learning_target and learning_time:
        # Fetch user ID (for demonstration purposes, using a static user ID)
        if 'user_id' not in st.session_state:
            st.session_state['user_id'] = 1 # Placeholder
        uid = st.session_state['user_id']

        with st.spinner("🤖 Our AI is crafting your personalized learning plan..."):
            try:
                # Generate the plan using the AI model
                daily_content_json = generate_learning_plan_json(learning_target, learning_time)
                
                # Validate that the response is valid JSON
                json.loads(daily_content_json)

                # Add the plan to the database
                add_plan(uid, learning_target, daily_content_json, special_instructions)

                st.success("Your new learning plan has been created successfully!")
                st.balloons()
                st.page_link("main.py", label="View My Plans", icon="🏠")
            except Exception as e:
                st.error(f"An error occurred while generating the plan: {e}")
    else:
        st.error("Please fill in all fields.")