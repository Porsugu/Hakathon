import streamlit as st
from db_functions import add_plan
import google.generativeai as genai
import json
import os

# Set up the page
st.set_page_config(page_title="Add Learning Plan", layout="wide")

# --- AI Configuration ---
# WARNING: Hardcoding keys is not secure. Use st.secrets for production.
genai.configure(api_key="AIzaSyDJpS-vOpOQXdsWQG5iKunReCHqG4OZdOg")


def generate_learning_plan_json(target, time_in_days):
    """
    Generates a structured learning plan in JSON format using an AI model.
    """
    # Switched to 'gemini-pro' as it's a stable and widely available model,
    # which resolves the "404 not found" error for 'gemini-1.5-flash'.
    # Using 'gemini-1.0-pro' as a more specific and stable model identifier
    # to resolve the 404 error for 'gemini-pro'.
    model = genai.GenerativeModel('gemini-2.5-flash')

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
    response = model.generate_content(prompt)
    # Clean up the response to ensure it's just the JSON
    cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
    return cleaned_response


# Main content
st.title("Add a New Learning Plan")

# Input fields
st.info("Define your learning goal and the number of days you want to commit. Our AI will generate a customized day-by-day plan for you.")
learning_target = st.text_input("What do you want to learn?", placeholder="e.g., 'Python for Data Science' or 'the basics of Guitar'")
learning_time = st.number_input("Learning Time (in days)", min_value=1, step=1)

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
                add_plan(uid, learning_target, daily_content_json)

                st.success("Your new learning plan has been created successfully!")
                st.balloons()
                st.page_link("main.py", label="View My Plans", icon="🏠")
            except Exception as e:
                st.error(f"An error occurred while generating the plan: {e}")
    else:
        st.error("Please fill in all fields.")