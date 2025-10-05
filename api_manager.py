"""
API Manager for Personal Learning OS
Handles all Gemini API interactions with proper rate limiting and error handling
"""
import time
import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
from typing import Optional
from models import APIUsage, get_db_session
import asyncio
import threading
from queue import Queue
import os

class APIManager:
    """Manages Gemini API calls with rate limiting and error handling"""

    def __init__(self):
        self.last_request_time = 0
        self.request_count = 0
        self.daily_token_limit = 50000
        self.requests_per_minute = 15  # Conservative limit for free tier
        self.min_request_interval = 4  # 4 seconds between requests for safety
        self.request_queue = Queue()
        self.model = self._init_model()

    def _init_model(self):
        """Initialize Gemini model with production configuration"""
        try:
            # Try to get API key from secrets first, then environment
            api_key = None
            if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
                api_key = st.secrets['GEMINI_API_KEY']
            else:
                api_key = os.getenv('GEMINI_API_KEY')

            if not api_key:
                st.error("🔑 Gemini API key not found!")
                return None

            genai.configure(api_key=api_key)

            # Use gemini-2.5-flash for better rate limits and reliability
            model = genai.GenerativeModel(
                'gemini-2.5-flash',
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=1024,  # Reduced to avoid token limits
                )
            )

            return model

        except Exception as e:
            st.error(f"❌ Gemini API initialization failed: {str(e)}")
            return None

    def can_make_request(self) -> bool:
        """Check if we can make an API request based on rate limits"""
        current_time = time.time()

        # Check minimum interval between requests
        if current_time - self.last_request_time < self.min_request_interval:
            return False

        # Check requests per minute
        db = get_db_session()
        minute_ago = datetime.now() - timedelta(minutes=1)
        recent_requests = db.query(APIUsage).filter(
            APIUsage.timestamp >= minute_ago
        ).count()

        if recent_requests >= self.requests_per_minute:
            return False

        return True

    def wait_for_rate_limit(self):
        """Wait until we can make a request"""
        while not self.can_make_request():
            time.sleep(1)

    def record_request(self, endpoint_type: str, success: bool = True, tokens: int = 0):
        """Record API usage for monitoring"""
        try:
            db = get_db_session()
            usage = APIUsage(
                endpoint_type=endpoint_type,
                tokens_used=tokens,
                success=str(success).lower(),
                timestamp=datetime.now()
            )
            db.add(usage)
            db.commit()

            self.last_request_time = time.time()
            self.request_count += 1
        except Exception as e:
            print(f"Failed to record API usage: {e}")

    def make_request(self, prompt: str, endpoint_type: str) -> Optional[str]:
        """Make a rate-limited request to Gemini API"""
        if not self.model:
            return None

        # Wait for rate limit
        self.wait_for_rate_limit()

        try:
            # Try primary request
            with st.spinner(f"🤖 AI is working on your {endpoint_type}..."):
                response = self.model.generate_content(prompt)

                # Safely extract text from several possible response shapes
                def _extract_text(resp):
                    # Try common quick accessors used by various client versions
                    try:
                        # common accessor
                        text = getattr(resp, 'text', None)
                        if text:
                            return text
                    except Exception:
                        pass

                    # Try common candidate/generation list shapes
                    try:
                        # response.candidates -> candidate.text or candidate.content
                        candidates = getattr(resp, 'candidates', None) or getattr(resp, 'generations', None)
                        if candidates and len(candidates) > 0:
                            first = candidates[0]
                            # candidate may be a dict-like or object
                            text = None
                            if isinstance(first, dict):
                                text = first.get('text') or first.get('content') or first.get('output')
                            else:
                                text = getattr(first, 'text', None) or getattr(first, 'content', None) or getattr(first, 'output', None)
                            if text:
                                return text
                    except Exception:
                        pass

                    # Some clients expose `result` or `output_text`
                    try:
                        text = getattr(resp, 'result', None) or getattr(resp, 'output_text', None)
                        if isinstance(text, str) and text:
                            return text
                    except Exception:
                        pass

                    # As a last resort, inspect repr for debugging (not returned to user)
                    return None

                text = _extract_text(response)

                # If we didn't get usable text, attempt a single quick retry (sometimes transient)
                if not text:
                    # record a failed attempt for monitoring
                    self.record_request(endpoint_type, False)

                    # Log debug info to console for developers
                    try:
                        print("API response had no text parts. Response repr:", repr(response))
                    except Exception:
                        print("API response had no text parts and could not be repr()-ed.")

                    # Try one retry with a conservative backoff
                    time.sleep(1)
                    try:
                        retry_resp = self.model.generate_content(prompt)
                        text = _extract_text(retry_resp)
                        if text:
                            self.record_request(endpoint_type, True, len(text))
                            return text
                        else:
                            self.record_request(endpoint_type, False)
                            return None
                    except Exception as e:
                        # If retry fails, continue to outer exception handler
                        raise

                # Normal successful path
                self.record_request(endpoint_type, True, len(text))
                return text

        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "limit" in error_msg.lower():
                st.error("⏱️ API quota exceeded. Please wait or upgrade your plan.")
            else:
                # Provide a clearer message if the response had no parts (common client error)
                if "quick accessor" in error_msg.lower() or "no parts" in error_msg.lower() or "finish_reason" in error_msg.lower():
                    st.error("❌ API Error: Model returned an empty response (no parts). This can happen if the model aborted generation or a content filter blocked the output. The request has been recorded; try again or reduce the requested output length.")
                else:
                    st.error(f"❌ API Error: {error_msg}")

            self.record_request(endpoint_type, False)
            return None

# Global API manager instance
@st.cache_resource
def get_api_manager():
    return APIManager()
