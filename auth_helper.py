
# auth_helper.py - Helper functions for authentication
import streamlit as st

def require_api_key():
    """
    Decorator-like function that ensures API key is validated before page loads.
    Call this at the beginning of every page that requires API access.
    """
    if not st.session_state.get('api_key_validated', False):
        st.error("🔒 Please validate your API key first.")
        if st.button("Go to Login"):
            st.switch_page("main.py")
        st.stop()

def get_validated_api_key():
    """
    Returns the validated API key from session state.
    Returns None if not validated.
    """
    if st.session_state.get('api_key_validated', False):
        return st.session_state.get('gemini_api_key')
    return None

def logout():
    """
    Clear the API key validation and redirect to login.
    """
    st.session_state['api_key_validated'] = False
    if 'gemini_api_key' in st.session_state:
        del st.session_state['gemini_api_key']
    st.switch_page("main.py")
