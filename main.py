# Home.py
import streamlit as st
from db_functions import get_plans_by_user
import json

# Page configuration should be the first Streamlit command
st.set_page_config(page_title="Learning OS", layout="wide", initial_sidebar_state="expanded")

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
if st.button("➕ Add New Plan"):
    st.switch_page("pages/1_Add_Plan.py")
st.divider()
# --- END OF ADDITION ---

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