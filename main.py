# Home.py
import streamlit as st
from db_functions import get_plans_by_user, delete_plan
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
        
    </style>
""", unsafe_allow_html=True)

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
    # Use columns for a cleaner layout
    cols = st.columns(3)
    for i, plan in enumerate(my_plans):
        col_index = i % 3
        with cols[col_index]:
            with st.container(border=True):
                st.subheader(plan['plan_name'])
                
                # Calculate and display progress from the JSON content
                try:
                    content = json.loads(plan['daily_content'])
                    total_days = len(content)
                    completed_days = sum(1 for day in content if day.get('status') == 'completed')
                    progress = completed_days / total_days if total_days > 0 else 0
                    
                    st.progress(progress, text=f"{completed_days} / {total_days} Days Completed")
                except (json.JSONDecodeError, TypeError):
                    st.warning("Could not display progress.")
                
                st.caption(f"Created: {plan['created_at'].split(' ')[0]}")

                # Place buttons on separate rows for a cleaner look
                if st.button("View Plan", key=f"view_{plan['pid']}", use_container_width=True):
                    # Step 1: Set the session state and query params. This will trigger a rerun.
                    st.session_state['current_plan_id'] = plan['pid']
                    st.session_state['plan_to_view'] = True
                    st.query_params["pid"] = plan['pid']
                    # On the next run, the logic at the top of the script will handle the page switch.
                    st.rerun()
                
                if st.button("Delete", key=f"delete_{plan['pid']}", use_container_width=True, type="secondary"):
                    delete_plan(uid, plan['pid'])
                    st.toast(f"Plan '{plan['plan_name']}' deleted successfully!")
                    st.rerun()