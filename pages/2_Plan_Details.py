import streamlit as st
from db_functions import get_plans_by_user
from utils import ensure_plan_selected
import json

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

st.title(f"Plan: {current_plan['plan_name']}")
st.caption("Select an option below to manage your learning plan.")
st.divider()

# --- Display the four action cards ---
col1, col2, col3, col4, col5 = st.columns(5)

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

with col4:
    if card("Exercise", "✍️"):
        st.query_params["pid"] = pid
        st.switch_page("pages/6_Exercise.py")

with col5:
    if card("Ask Something", "❓"):
        st.query_params["pid"] = pid
        st.switch_page("pages/7_Ask.py")