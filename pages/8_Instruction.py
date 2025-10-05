import streamlit as st
from db_functions import get_plans_by_user, update_plan_instructions
from utils import ensure_plan_selected
from config import get_ai_manager
import json

st.markdown("""
    <style>
        /* General dark background and text */
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

        /* Containers */
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
            background-color: #1a1d23;
            border: 1px solid #2e3440;
            border-radius: 12px;
            padding: 1em;
            margin-bottom: 1em;
        }
            
        header[data-testid="stHeader"] {
            background-color: #0e1117 !important; 
            color: #f5f5f5 !important;           
        }

        header[data-testid="stHeader"] {
            box-shadow: none !important;
        }

        /* Make the container for the back button invisible */
        .back-button-container > div {
            background-color: transparent !important;
            border: none !important;
        }

        /* Style for copyable code/latex blocks */
        [data-testid="stCodeBlock"], [data-testid="stLatex"] {
            background-color: #262730; /* A medium-dark grey */
            border-radius: 8px;
            padding: 1em;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Edit Instructions", layout="wide")

# --- Setup ---
pid = ensure_plan_selected()
uid = st.session_state.get('user_id', 1)
ai_manager = get_ai_manager()
if not ai_manager.initialize():
    st.error("AI could not be initialized.")
    st.stop()

# --- Data Fetching ---
def get_current_plan():
    all_plans = get_plans_by_user(uid)
    return next((plan for plan in all_plans if plan['pid'] == pid), None)

current_plan = get_current_plan()
if not current_plan:
    st.error("Plan not found.")
    st.stop()

# --- State Management ---
if 'instruction_last_pid' not in st.session_state or st.session_state.instruction_last_pid != pid:
    st.session_state.instruction_last_pid = pid
    st.session_state.draft_instructions = current_plan['special_instructions'] or ""
    st.session_state.instruction_messages = []

# --- UI ---
title_col, back_button_col = st.columns([0.8, 0.2])
with title_col:
    st.title("📝 Edit Special Instructions")
with back_button_col:
    st.markdown('<div class="back-button-container">', unsafe_allow_html=True)
    if st.button("◀ Back", use_container_width=True):
        st.switch_page("pages/2_Plan_Details.py")
    st.markdown('</div>', unsafe_allow_html=True)

st.info("Refine the instructions for the AI. These will be used when generating or adjusting your plan.", icon="💡")
st.divider()

col1, col2 = st.columns([0.5, 0.5], gap="large")

# --- Left Column: Instructions Editor ---
with col1:
    st.header("Current Instructions")
    
    # The text area's value is controlled by the session state
    st.session_state.draft_instructions = st.text_area(
        "Instructions", 
        value=st.session_state.draft_instructions, 
        height=300,
        label_visibility="collapsed"
    )

    save_col, revert_col = st.columns(2)
    with save_col:
        if st.button("💾 Save Changes", use_container_width=True, type="primary"):
            update_plan_instructions(uid, pid, st.session_state.draft_instructions)
            st.toast("✅ Instructions saved successfully!")
    with revert_col:
        if st.button("↩️ Revert Changes", use_container_width=True):
            st.session_state.draft_instructions = current_plan['special_instructions'] or ""
            st.toast("Changes reverted.")
            st.rerun()

# --- Right Column: Chat Interface ---
with col2:
    st.header("AI Assistant")

    for message in st.session_state.instruction_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("How should we change the instructions?"):
        st.session_state.instruction_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤖 Refining instructions..."):
                full_prompt = f"""
                You are an assistant helping a user refine special instructions for an AI-powered learning plan generator.
                The user's request is: '{prompt}'

                Here are the current instructions:
                ---
                {st.session_state.draft_instructions}
                ---

                Based on the user's request, please generate the new, complete set of special instructions.
                Your response should ONLY be the text of the new instructions, with no other conversational text, formatting, or explanations.
                """
                
                new_instructions = ai_manager.generate_content(full_prompt)
                if new_instructions:
                    st.session_state.draft_instructions = new_instructions
                    st.session_state.instruction_messages.append({"role": "assistant", "content": "I've updated the instructions on the left. You can edit them further or click 'Save Changes'."})
                    st.rerun()
                else:
                    error_msg = "Sorry, I couldn't generate a response. Please try again."
                    st.session_state.instruction_messages.append({"role": "assistant", "content": error_msg})
                    st.error(error_msg)