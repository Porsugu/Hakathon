import streamlit as st

def ensure_plan_selected():
    """
    A robust function to check for a selected plan ID.
    It checks session state first, then falls back to URL query parameters.
    If no plan ID is found, it stops the app with a user-friendly error.
    """
    # If session state is lost, try to restore it from the URL query parameter.
    if 'current_plan_id' not in st.session_state and "pid" in st.query_params:
        try:
            st.session_state.current_plan_id = int(st.query_params["pid"])
        except (ValueError, TypeError):
            # Handle cases where the URL parameter is invalid.
            st.error("Invalid Plan ID in the URL.")
            st.page_link("main.py", label="Go to Homepage", icon="🏠")
            st.stop()

    if 'current_plan_id' not in st.session_state:
        st.error("No plan selected. Please go back to the homepage and select a plan.")
        st.page_link("main.py", label="Go to Homepage", icon="🏠")
        st.stop()
    
    return st.session_state['current_plan_id']