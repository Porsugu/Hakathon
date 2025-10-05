"""
Practice Exercises Module for Personal Learning OS
Handles AI-powered practice exercise generation
"""
from typing import Dict, Optional
from api_manager import get_api_manager
import streamlit as st

def generate_practice_exercises(topic: str, exercise_type: str) -> Optional[Dict]:
    """Generate practice exercises based on topic and type"""
    api_manager = get_api_manager()

    if not api_manager.model:
        return None

    if exercise_type == "Quiz":
        prompt = f"""Create 3 multiple-choice quiz questions about: {topic}

For each question provide:
1. Clear, specific question
2. 4 answer options (A, B, C, D)
3. Correct answer letter
4. Brief explanation

Keep questions practical and test real understanding.
Format as clear text, not JSON."""

    elif exercise_type == "Problems":
        prompt = f"""Create 2 practical problem-solving exercises about: {topic}

For each problem provide:
1. Clear problem description
2. Example input/output (if applicable)
3. Step-by-step solution approach
4. Complete solution with explanation

Focus on hands-on, practical problems."""

    else:  # Examples
        prompt = f"""Create 2 practical examples demonstrating: {topic}

For each example provide:
1. Real-world scenario
2. Step-by-step implementation
3. Code with comments (if applicable)
4. Expected outcome
5. One variation or extension

Make examples practical and relevant."""

    response = api_manager.make_request(prompt, f"practice_{exercise_type.lower()}")

    if response:
        return {"content": response, "type": exercise_type}
    return None
