
import streamlit as st
import google.generativeai as genai

# This system stores the API key in session state only, to have it persist, use setup,py

def validate_api_key(api_key):
    """Validate the Gemini API key by making a test call"""
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty"

    try:
        # Configure and test the API key
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Make a simple test call
        response = model.generate_content("Say 'API key is valid'")
        if response and response.text:
            return True, "API key validated successfully!"
        else:
            return False, "Invalid API key or no response from Gemini"

    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
            return False, "Invalid API key. Please check your key and try again."
        elif "PERMISSION_DENIED" in error_msg:
            return False, "API key doesn't have permission to access Gemini. Please check your API key permissions."
        elif "quota" in error_msg.lower():
            return False, "API quota exceeded. Please check your Gemini API usage limits."
        else:
            return False, f"Error validating API key: {error_msg}"

def show_login_page():
    """Display the API key login page"""

    # Page config
    st.set_page_config(
        page_title="🚀 Learning OS - Setup",
        page_icon="🚀",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS for a better looking login page
    st.markdown("""
    <style>
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .stTextInput > div > div > input {
        background-color: #f8f9fa;
    }

    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
        margin: 1rem 0;
    }

    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Main container
    with st.container():
        # Header
        st.title("🚀 Learning OS")
        st.subheader("Welcome! Let's get started")
        st.markdown("---")

        # Introduction
        st.markdown("""
        ### Setup Your AI Tutor

        To use this AI-powered learning platform, you'll need a **Gemini API key** from Google.

        **How to get your API key:**
        1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
        2. Sign in with your Google account
        3. Click "Create API Key"
        4. Copy the generated key and paste it below
        """)

        # API Key input form
        with st.form("api_key_form", clear_on_submit=False):
            api_key = st.text_input(
                "Enter your Gemini API Key:",
                type="password",
                placeholder="Enter your API key here...",
                help="Your API key will be stored securely in your session"
            )

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submit_button = st.form_submit_button(
                    "🔓 Validate & Continue",
                    use_container_width=True,
                    type="primary"
                )

        # Handle form submission
        if submit_button:
            if not api_key:
                st.error("❌ Please enter your API key")
            else:
                # Show validation progress
                with st.spinner("🔍 Validating your API key..."):
                    is_valid, message = validate_api_key(api_key)

                if is_valid:
                    # Store the API key in session state
                    st.session_state['gemini_api_key'] = api_key.strip()
                    st.session_state['api_key_validated'] = True

                    # Show success message
                    st.success(f"✅ {message}")
                    st.balloons()  # Fun celebration effect

                    # Auto redirect after a brief delay
                    st.markdown("**Redirecting to your Learning OS...**")
                    st.rerun()

                else:
                    # Show error message
                    st.error(f"❌ {message}")

        # Footer with helpful links
        st.markdown("---")
        st.markdown("""
        **Need help?**
        - [Get Gemini API Key](https://aistudio.google.com/app/apikey) 
        - [Gemini API Documentation](https://ai.google.dev/docs)
        - Contact support if you continue having issues
        """)

# Main logic
def main():
    # Initialize session state
    if 'api_key_validated' not in st.session_state:
        st.session_state['api_key_validated'] = False

    # Check if API key is validated
    if not st.session_state.get('api_key_validated', False):
        show_login_page()
    else:
        # Redirect to main app
        st.switch_page("main.py")  # This should redirect to your main app

if __name__ == "__main__":
    main()
