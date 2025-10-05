"""
Learning Content Module for Personal Learning OS
Handles AI-powered learning content generation and progress tracking
"""
from typing import List, Optional
from datetime import datetime
from api_manager import get_api_manager
from models import LearningProgress, get_db_session
import streamlit as st

def generate_learning_content(mission_title: str, previous_content: List[str] = None) -> Optional[str]:
    """Generate detailed learning content for a specific mission"""
    api_manager = get_api_manager()

    if not api_manager.model:
        return None

    context = ""
    if previous_content:
        context = f"Previous learning context: {'; '.join(previous_content[-2:])}"

    prompt = f"""Create comprehensive learning content for: {mission_title}

{context}

Provide a focused tutorial that includes:
1. Clear explanation of key concepts with examples
2. Step-by-step walkthrough or tutorial
3. Practical examples with code (if applicable)
4. Common mistakes to avoid
5. 2-3 hands-on exercises
6. Summary of key points

Keep it concise but thorough. Use markdown formatting.
Focus on practical, actionable content that helps learners build skills."""

    return api_manager.make_request(prompt, "learning_content")

def save_learning_progress(plan_id: int, day: int, content: str, score: int = 100):
    """Save learning progress to database"""
    db = get_db_session()
    progress = LearningProgress(
        plan_id=plan_id,
        day_number=day,
        content_taught=content[:1000],  # Limit stored content
        completion_score=score,
        timestamp=datetime.now()
    )
    db.add(progress)
    db.commit()
    return progress

def get_learning_progress(plan_id: int) -> List[LearningProgress]:
    """Get learning progress for a plan"""
    db = get_db_session()
    return db.query(LearningProgress).filter(
        LearningProgress.plan_id == plan_id
    ).order_by(LearningProgress.day_number).all()
