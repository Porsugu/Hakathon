import streamlit as st
import api_log

def render_api_key_sidebar():
    """Render API key management in the sidebar - reusable component"""
    with st.sidebar:
        # Add API key management in sidebar (compact inline UI)
        if st.button("Change API Key"):
            st.session_state['show_change_api_key_box'] = True

        # Ensure flag exists
        if 'show_change_api_key_box' not in st.session_state:
            st.session_state['show_change_api_key_box'] = False

        if st.session_state.get('show_change_api_key_box'):
            # Compact inline form (textbox + tick/submit + cancel buttons)
            with st.form("change_api_key_form", clear_on_submit=False, border=False):  # Use form without border to avoid double container effect
                # Input field
                new_key = st.text_input("New Gemini API Key", placeholder="Enter new API key", type="password", key="new_gemini_key", label_visibility="collapsed")
                
                # Button row (Cancel and Submit)
                col_cancel, col_submit = st.columns([1, 1], gap="small")
                with col_cancel:
                    cancel_pressed = st.form_submit_button("❌", help="Cancel")
                with col_submit:
                    submit_pressed = st.form_submit_button("✅", help="Save API Key")

                # Handle button actions
                if cancel_pressed:
                    st.session_state['show_change_api_key_box'] = False
                    st.rerun()

                if submit_pressed:
                    if not new_key:
                        st.error("Please enter an API key before saving.")
                    else:
                        with st.spinner("Validating API key..."):
                            is_valid, message = api_log.validate_api_key(new_key)
                            if is_valid:
                                st.session_state['gemini_api_key'] = new_key.strip()
                                st.session_state['api_key_validated'] = True
                                st.session_state['show_change_api_key_box'] = False
                                st.success("✅ API key updated and validated.")
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")

        # Show masked API key if available
        if 'gemini_api_key' in st.session_state:
            masked_key = f"{st.session_state['gemini_api_key'][:8]}...{st.session_state['gemini_api_key'][-4:]}"
            st.caption(f"🔑 API Key: {masked_key}")

def get_sidebar_css():
    """Get the CSS for fixing sidebar button hover effects"""
    return """
    /* Form submit button styling in sidebar - FIXED */
    section[data-testid="stSidebar"] .stFormSubmitButton button {
        background-color: #0078ff !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        padding: 0.4rem 0.6rem !important;
        min-width: 2.5rem !important;
        height: 2.5rem !important;
        font-weight: 700 !important;
        border: none !important;
    }

    section[data-testid="stSidebar"] .stFormSubmitButton button:hover {
        background-color: #0056b3 !important;
        transform: none !important;
    }

    /* Fix for white rectangle on form submit button hover */
    section[data-testid="stSidebar"] .stFormSubmitButton button:hover::before,
    section[data-testid="stSidebar"] .stFormSubmitButton button:focus::before {
        display: none !important;
    }

    /* Remove any hover background effects */
    section[data-testid="stSidebar"] .stFormSubmitButton button:hover {
        background-color: #0056b3 !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* Remove pseudo-elements that might create white rectangles */
    section[data-testid="stSidebar"] .stFormSubmitButton button::before,
    section[data-testid="stSidebar"] .stFormSubmitButton button::after {
        content: none !important;
        display: none !important;
    }

    /* Remove form borders to prevent double container effect */
    section[data-testid="stSidebar"] [data-testid="stForm"] {
        border: 0px !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Style the text input in the API key form */
    section[data-testid="stSidebar"] .stFormSubmitButton div .stTextInput > div > div {
        margin: 0 !important;
        padding: 0 !important;
    }
    """
