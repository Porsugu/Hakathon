import streamlit as st
from db_functions import get_plans_by_user
from utils import ensure_plan_selected
import json

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
            
        /* Remove background from progress bar label */
        [data-testid="stProgress"] [data-testid="stMarkdownContainer"] {
            background: transparent !important;
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

        /* Make the container for the back button invisible */
        .back-button-container > div {
            background-color: transparent !important;
            border: none !important;
        }

        /* Make the container for the title bar invisible */
        .title-bar-container > div > div > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
        }

        /* Style for copyable code/latex blocks */
        [data-testid="stCodeBlock"], [data-testid="stLatex"] {
            background-color: #262730; /* A medium-dark grey */
            border-radius: 8px;
            padding: 1em;
        }
        
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Plan Dashboard", layout="wide")

# --- Helper function to create a clickable card ---
def card(title, icon):
    with st.container(border=True):
        st.markdown(f"### {icon} {title}")
        clicked = st.button("Go", key=f"go_{title.lower().replace(' ', '_')}", use_container_width=True)
    return clicked

# --- Check for selected plan and display header ---
pid = ensure_plan_selected()
uid = st.session_state.get('user_id', 1) # Default to 1 if not found

# Fetch all plans and find the current one by pid
all_plans = get_plans_by_user(uid)
current_plan = next((plan for plan in all_plans if plan['pid'] == pid), None)

if not current_plan:
    st.error("Plan not found. It might have been deleted.")
    st.page_link("main.py", label="Go to Homepage", icon="🏠")
    st.stop()

title_col, back_button_col = st.columns([0.8, 0.2])
with title_col:
    st.title(f"Plan: {current_plan['plan_name']}")
with back_button_col:
    st.markdown('<div class="back-button-container">', unsafe_allow_html=True)
    if st.button("◀ Back", use_container_width=True):
        st.switch_page("main.py")
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("Select an option below to manage your learning plan.")
st.divider()

# --- Display the action cards ---
col1, col2, col3 = st.columns(3)

with col1:
    if card("Adjust Plan", "🛠️"):
        st.query_params["pid"] = pid
        st.switch_page("pages/3_Adjust_Plan.py")

with col2:
    if card("Learn Today", "📖"):
        st.query_params["pid"] = pid
        st.switch_page("pages/4_Learn_Today.py")

with col3:
    if card("Review", "🧠"):
        st.query_params["pid"] = pid
        st.switch_page("pages/5_Review.py")

col4, col5, col6 = st.columns(3)

with col4:
    if card("Exercise", "✍️"):
        st.query_params["pid"] = pid
        st.switch_page("pages/6_Exercise.py")

with col5:
    if card("Ask Something", "❓"):
        st.query_params["pid"] = pid
        st.switch_page("pages/7_Ask.py")

with col6:
    if card("Instruction", "📝"):
        st.query_params["pid"] = pid
        st.switch_page("pages/8_Instruction.py")