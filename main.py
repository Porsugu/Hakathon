# Home.py
import streamlit as st
import api_log
import os
from db_functions import get_plans_by_user, delete_plan
import json
from change_api import render_api_key_sidebar, get_sidebar_css

# --- API Key Validation Check --- 
# could be set up using setup.py / api_log.py
def check_api_key_validation():
    """Check if API key has been validated; if not, try to load from secrets or env and
    otherwise render the login UI inline.
    """
    # 1) session already validated
    if st.session_state.get('api_key_validated', False):
        return

    # 2) Check Streamlit secrets (secrets.toml) first
    try:
        if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets and st.secrets['GEMINI_API_KEY']:
            st.session_state['gemini_api_key'] = st.secrets['GEMINI_API_KEY']
            st.session_state['api_key_validated'] = True
            return
    except Exception:
        # st.secrets may not be available in some contexts; ignore and continue
        pass

    # 3) Check environment variable as fallback
    env_key = os.environ.get('GEMINI_API_KEY')
    if env_key:
        st.session_state['gemini_api_key'] = env_key
        st.session_state['api_key_validated'] = True
        return

    # 4) Otherwise, render the login UI inline
    api_log.show_login_page()
    st.stop()

# Check API key validation first
check_api_key_validation()

# --- Sidebar Lock Control ---
# This boolean controls whether the sidebar can be opened.
# When set to False, the button to open the sidebar will be hidden.
allow_sidebar = False

# --- CSS Styles ---
css_styles = """
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

        /* Vertically align content in columns */
        [data-testid="stHorizontalBlock"] {
            align-items: center;
        }

        /* CSS for truncating long plan titles */
        .card-title {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Style for copyable code/latex blocks */
        [data-testid="stCodeBlock"], [data-testid="stLatex"] {
            background-color: #262730; /* A medium-dark grey */
            border-radius: 8px;
            padding: 1em;
        }
        
        /* Add the fixed sidebar CSS */
        {get_sidebar_css()}
"""

if not allow_sidebar:
    # This CSS finds the button that opens the sidebar (the hamburger menu) and hides it.
    css_styles += """
        button[title="Open navigation"] {
            display: none !important;
        }
"""

css_styles += """
    </style>
"""

st.markdown(css_styles, unsafe_allow_html=True)

st.title("🚀 Your Learning OS")
st.sidebar.success("Select a page above to get started.")

# --- User Authentication Placeholder ---
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = 1  # Static user ID for demonstration

# --- Display Existing Plans ---
st.header("My Learning Plans")

uid = st.session_state['user_id']

# --- ADDED THIS BUTTON ---
# This creates a clear, visible button to navigate to the Add Plan page.
if st.button("Add New Plan"):
    st.switch_page("pages/1_Add_Plan.py")
st.divider()
# --- END OF ADDITION ---

# --- Logic to handle page switching after a plan is selected ---
# This ensures the URL is updated *before* we switch pages.
if st.session_state.get("plan_to_view"):
    # Reset the flag to False before switching to prevent an infinite redirect loop.
    st.session_state.plan_to_view = False
    st.switch_page("pages/2_Plan_Details.py")

my_plans = get_plans_by_user(uid)

if not my_plans:
    # --- IMPROVED THIS SECTION ---
    st.info("You don't have any learning plans yet. Click the button above to create one!")
    # --- END OF IMPROVEMENT ---
else:
    # --- Pagination Logic for single plan view ---
    if 'plan_page_index' not in st.session_state:
        st.session_state.plan_page_index = 0

    total_plans = len(my_plans)
    # Ensure index is valid if plans are deleted
    if st.session_state.plan_page_index >= total_plans:
        st.session_state.plan_page_index = max(0, total_plans - 1)

    current_index = st.session_state.plan_page_index
    plan = my_plans[current_index]

    # --- Display Single Plan Card with Side Navigation ---
    left_nav_col, card_col, right_nav_col = st.columns([1, 8, 1])

    with left_nav_col:
        if st.button("◀", key="left_arrow", use_container_width=True, disabled=(current_index == 0)):
            st.session_state.plan_page_index -= 1
            st.rerun()

    with card_col:
        with st.container(border=True, height=300):
                # Use markdown to apply custom class and title attribute for hover effect
                st.markdown(f'<h2 class="card-title" title="{plan["plan_name"]}">{plan["plan_name"]}</h2>', unsafe_allow_html=True)
                try:
                    content = json.loads(plan['daily_content'])
                    total_days = len(content)
                    completed_days = sum(1 for day in content if day.get('status') == 'completed')
                    progress = completed_days / total_days if total_days > 0 else 0
                    st.progress(progress, text=f"{completed_days} / {total_days} Days Completed")
                except (json.JSONDecodeError, TypeError):
                    st.warning("Could not display progress.")

                st.caption(f"Created: {plan['created_at'].split(' ')[0]}")

                view_col, delete_col = st.columns(2)
                with view_col:
                    if st.button("View", key=f"view_{plan['pid']}", use_container_width=True):
                        st.session_state['current_plan_id'] = plan['pid']
                        st.session_state['plan_to_view'] = True
                        st.query_params["pid"] = plan['pid']
                        st.rerun()
                with delete_col:
                    if st.button("Delete", key=f"delete_{plan['pid']}", use_container_width=True, type="secondary"):
                        delete_plan(uid, plan['pid'])
                        st.toast(f"Plan '{plan['plan_name']}' deleted successfully!")
                        st.rerun()

    with right_nav_col:
        if st.button("▶", key="right_arrow", use_container_width=True, disabled=(current_index >= total_plans - 1)):
            st.session_state.plan_page_index += 1
            st.rerun()
            
# render_api_key_sidebar()