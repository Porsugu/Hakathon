import streamlit as st
from db_functions import get_plans_by_user, update_plan_content
from utils import ensure_plan_selected
import google.generativeai as genai
import json

st.set_page_config(page_title="Adjust Plan", layout="wide")

# --- Check for selected plan ---
pid = ensure_plan_selected()
uid = st.session_state.get('user_id', 1)

# --- AI Configuration (using hardcoded key as in other files) ---
try:
    genai.configure(api_key="AIzaSyDJpS-vOpOQXdsWQG5iKunReCHqG4OZdOg")
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"AI Model could not be configured: {e}")
    st.stop()

# --- Function to fetch the current plan ---W
def get_current_plan():
    all_plans = get_plans_by_user(uid)
    return next((plan for plan in all_plans if plan['pid'] == pid), None)

# --- Initialize session state for chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Page Title ---
st.title("🛠️ Adjust Your Learning Plan")
st.info("Use the chat on the right to ask the AI to modify your plan. For example: 'Make day 3 easier' or 'Add a day about testing'.")
st.divider()

# --- Layout ---
col1, col2 = st.columns([0.5, 0.5], gap="large")

# --- Left Column: Display Current Plan ---
with col1:
    st.header("Current Plan")
    plan_data = get_current_plan()
    if plan_data:
        try:
            daily_content = json.loads(plan_data['daily_content'])
            for day in daily_content:
                with st.expander(f"**Day {day['day']}: {day['topic']}**"):
                    st.markdown(f"**Details:** {day['details']}")
                    st.markdown(f"**Status:** `{day['status']}`")
        except (json.JSONDecodeError, TypeError):
            st.error("Could not load plan details.")
    else:
        st.error("Could not find the selected plan.")

# --- Right Column: Chat Interface ---
with col2:
    st.header("Chat with AI Assistant")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("How should I adjust the plan?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                # Construct a detailed prompt for the AI
                current_plan_json = plan_data['daily_content']
                full_prompt = f"""
                A user wants to adjust their learning plan.
                Their request is: '{prompt}'
                
                Here is the current plan in JSON format:
                {current_plan_json}
                
                Please generate a new, updated plan based on the user's request.
                Your response MUST be only the updated JSON array, with no other text or markdown.
                The JSON structure for each day must contain 'day', 'topic', 'details', and 'status' keys.
                """
                
                response = model.generate_content(full_prompt)
                cleaned_response = response.text.strip().replace("```json", "").replace("```", "")

                try:
                    # Validate and update the database
                    json.loads(cleaned_response) # Check if it's valid JSON
                    update_plan_content(pid, cleaned_response)
                    st.success("Plan updated successfully! The new plan is shown on the left.")
                    st.rerun() # Rerun the script to show the updated plan
                except (json.JSONDecodeError, Exception) as e:
                    error_message = f"Sorry, I couldn't update the plan. The AI returned an invalid format. Please try a different request. Error: {e}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})