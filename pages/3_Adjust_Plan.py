import streamlit as st
from db_functions import get_plans_by_user, update_plan_content
from utils import ensure_plan_selected
from config import get_ai_manager
import json

st.markdown("""
    <style>
        /* Keep expanded expander header and content dark */
        details[open] > summary {
            background-color: #1a1d23 !important;
            color: #f5f5f5 !important;
        }
        details[open] {
            background-color: #1a1d23 !important;
            color: #f5f5f5 !important;
        }
            
        /* General dark background and text */
        .stApp {
            background-color: #0e1117;
            color: #f5f5f5;
        }
        h1, h2, h3, h4, h5, h6, p, span, div {
            color: #f5f5f5 !important;
        }

        /* Top bar */
        header[data-testid="stHeader"] {
            background-color: #0e1117 !important;
            color: #f5f5f5 !important;
            box-shadow: none !important;
        }
        header[data-testid="stHeader"] .css-1v0mbdj {
            color: #f5f5f5 !important;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1a1d23 !important;
            color: #f5f5f5 !important;
        }
        section[data-testid="stSidebar"] .stAlert {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }
        section[data-testid="stSidebar"] .stAlert p {
            color: #f5f5f5 !important;
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

        /* Info / Error / Success Boxes */
        .stAlert {
            border: none !important;
            background-color: transparent !important;
            color: #f5f5f5 !important;
            box-shadow: none !important;
        }

        /* Expanders (Days) */
        details {
            background-color: #1a1d23 !important;
            border: 1px solid #2e3440 !important;
            border-radius: 8px !important;
            margin-bottom: 8px !important;
        }

        /* Progress bars */
        [data-testid="stProgress"] > div > div {
            background-color: #0078ff !important;
        }

        /* Chat input box */
        div[data-testid="stChatInput"] textarea {
            color: #f5f5f5 !important;
        }

        /* Chat messages */
        div[data-testid="stChatMessage"] {
            background-color: #1a1d23 !important;
            border-radius: 12px !important;
            padding: 1em !important;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        /* Keep expanded expander header and content dark */
        details[open] > summary {
            background-color: #1a1d23 !important;
            color: #f5f5f5 !important;
        }
        details[open] {
            background-color: #1a1d23 !important;
            color: #f5f5f5 !important;
        }
            
        /* General dark background and text */
        .stApp {
            background-color: #0e1117;
            color: #f5f5f5;
        }
        h1, h2, h3, h4, h5, h6, p, span, div {
            color: #f5f5f5 !important;
        }

        /* Top bar */
        header[data-testid="stHeader"] {
            background-color: #0e1117 !important;
            color: #f5f5f5 !important;
            box-shadow: none !important;
        }
        header[data-testid="stHeader"] .css-1v0mbdj {
            color: #f5f5f5 !important;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1a1d23 !important;
            color: #f5f5f5 !important;
        }
        section[data-testid="stSidebar"] .stAlert {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }
        section[data-testid="stSidebar"] .stAlert p {
            color: #f5f5f5 !important;
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

        /* Info / Error / Success Boxes */
        .stAlert {
            border: none !important;
            background-color: transparent !important;
            color: #f5f5f5 !important;
            box-shadow: none !important;
        }

        /* Expanders (Days) */
        details {
            background-color: #1a1d23 !important;
            border: 1px solid #2e3440 !important;
            border-radius: 8px !important;
            margin-bottom: 8px !important;
        }

        /* Progress bars */
        [data-testid="stProgress"] > div > div {
            background-color: #0078ff !important;
        }

        /* Chat input box */
        div[data-testid="stChatInput"] textarea {
            color: #f5f5f5 !important;
        }

        /* Chat messages */
        div[data-testid="stChatMessage"] {
            background-color: #1a1d23 !important;
            border-radius: 12px !important;
            padding: 1em !important;
        }

        /* Style for copyable code/latex blocks */
        [data-testid="stCodeBlock"], [data-testid="stLatex"] {
            background-color: #262730; /* A medium-dark grey */
            border-radius: 8px;
            padding: 1em;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Adjust Plan", layout="wide")

# --- Check for selected plan ---
pid = ensure_plan_selected()
pid = ensure_plan_selected()
uid = st.session_state.get('user_id', 1)

# --- AI Configuration ---
ai_manager = get_ai_manager()
if not ai_manager.initialize():
    st.error("AI could not be initialized. Check your secrets or environment variables.")
    st.stop()

# --- Function to fetch the current plan ---W
def get_current_plan():
    all_plans = get_plans_by_user(uid)
    return next((plan for plan in all_plans if plan['pid'] == pid), None)

# --- Initialize session state for chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Page Title ---
title_col, back_button_col = st.columns([0.8, 0.2])
with title_col:
    st.title("🛠️ Adjust Your Learning Plan")
with back_button_col:
    st.markdown('<div class="back-button-container">', unsafe_allow_html=True)
    if st.button("◀ Back", use_container_width=True):
        st.switch_page("pages/2_Plan_Details.py")
    st.markdown('</div>', unsafe_allow_html=True)

st.info("Use the chat on the right to ask the AI to modify your plan. For example: 'Make day 3 easier' or 'Add a day about testing'.", icon="💡")
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
                IMPORTANT: All backslashes `\` inside the JSON string values must be properly escaped (as `\\`).
                The JSON structure for each day must contain 'day', 'topic', 'details', and 'status' keys.
                """
                
                response_text = ai_manager.generate_content(full_prompt)
                # new
                if not response_text:
                    error_message = "Sorry, I couldn't get a response from the AI. Please try again."
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
                else:
                    cleaned_response = response_text.strip().replace("```json", "").replace("```", "")

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