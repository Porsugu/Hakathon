"""
Chat and Explanations Module for Personal Learning OS
Handles free learning chat and saved explanations
"""
from typing import List, Optional
from datetime import datetime
from api_manager import get_api_manager
from models import SavedExplanation, get_db_session
import streamlit as st

def generate_free_learning_response(query: str) -> Optional[str]:
    """Generate response for free learning chat"""
    api_manager = get_api_manager()

    if not api_manager.model:
        return None

    prompt = f"""As an expert tutor, provide a comprehensive answer to: {query}

Your response should:
1. Directly answer the question with clear explanations
2. Provide concrete examples when helpful
3. Break down complex concepts into simple parts
4. Include practical applications or use cases
5. Be encouraging and educational

Keep the response focused and helpful. Use markdown formatting for better readability."""

    return api_manager.make_request(prompt, "free_learning")

def save_explanation(query: str, explanation: str, tags: str = "", difficulty: str = "intermediate"):
    """Save explanation to database"""
    db = get_db_session()
    saved = SavedExplanation(
        user_query=query,
        ai_explanation=explanation,
        tags=tags,
        difficulty_level=difficulty,
        saved_date=datetime.now()
    )
    db.add(saved)
    db.commit()
    return saved

def get_saved_explanations() -> List[SavedExplanation]:
    """Get all saved explanations"""
    db = get_db_session()
    return db.query(SavedExplanation).order_by(
        SavedExplanation.saved_date.desc()
    ).all()

def delete_explanation(explanation_id: int):
    """Delete a saved explanation"""
    db = get_db_session()
    explanation = db.query(SavedExplanation).filter(
        SavedExplanation.id == explanation_id
    ).first()
    if explanation:
        db.delete(explanation)
        db.commit()
        return True
    return False
