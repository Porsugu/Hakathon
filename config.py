import os
import streamlit as st


class Config:
    """Centralized configuration helper for API keys and constants."""

    GEMINI_MODEL = "gemini-2.5-flash"

    def initialize(self):
        """
        Locate and return the GEMINI API key.

        Search order:
        1. streamlit secrets (st.secrets)
        2. environment variable GEMINI_API_KEY
        3. local file `mykey.env` (loaded via python-dotenv)

        Returns:
          (True, api_key) on success
          (False, error_message) on failure
        """
        # 1) Streamlit secrets (good for Streamlit Cloud)
        try:
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                return True, st.secrets["GEMINI_API_KEY"]
        except Exception:
            # In some contexts st.secrets might not be available; ignore and continue
            pass

        # 2) Environment variable
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            return True, api_key

        # No fallback to local mykey.env to avoid accidental committed secrets.
        return False, (
            "GEMINI_API_KEY not found. Set it in Streamlit secrets (recommended) or as an environment variable. "
            "See .streamlit/secrets.example.toml for a template."
        )


# singleton-style instance used by other modules
config = Config()


########### AI Manager (moved from ai_utils.py) ###########
import google.generativeai as genai
import time
import json


class AIManager:
    """Manages AI model initialization and common operations"""

    def __init__(self):
        self.model = None
        self.is_initialized = False
        self.last_request_time = 0
        self.min_request_interval = 2  # seconds between requests

    def initialize(self):
        try:
            success, api_key = config.initialize()
            if not success:
                st.error(f"❌ AI Configuration Error: {api_key}")
                return False

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(config.GEMINI_MODEL)
            self.is_initialized = True
            return True
        except Exception as e:
            st.error(f"❌ Failed to initialize AI model: {str(e)}")
            return False

    def rate_limit_check(self):
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def generate_content(self, prompt, show_spinner=False, spinner_text=None):
        if not self.is_initialized:
            if not self.initialize():
                return None

        try:
            self.rate_limit_check()
            if show_spinner:
                # Allow callers to provide a custom spinner_text; fall back to the old message
                text = spinner_text if spinner_text is not None else "🤖 AI is thinking..."
                with st.spinner(text):
                    response = self.model.generate_content(prompt)
            else:
                # Do not show a spinner here by default. Pages should provide their own
                # user-facing messages where needed so each page can have a unique message.
                response = self.model.generate_content(prompt)

            if response and getattr(response, 'text', None):
                return response.text.strip()
            else:
                st.error("❌ AI returned empty response. Please try again.")
                return None

        except Exception as e:
            st.error(f"❌ AI Error: {str(e)}")
            return None


@st.cache_resource
def get_ai_manager():
    return AIManager()

