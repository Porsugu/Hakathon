"""
Plan Generation Module for Personal Learning OS
Handles chunked plan generation with proper error handling and UI display
"""
import time
from typing import List, Optional
from datetime import datetime
from api_manager import get_api_manager
from models import LearningPlan, DailyMission, get_db_session
import re
import streamlit as st

def generate_learning_plan_chunked(target: str, days: int, difficulty: str = 'intermediate') -> Optional[str]:
    """Generate learning plan in chunks to avoid token limits"""
    api_manager = get_api_manager()

    if not api_manager.model:
        return None

    # Determine optimal chunk size based on total days
    if days <= 4:
        chunk_size = days  # Single chunk for small plans
    elif days <= 8:
        chunk_size = 2     # 2-day chunks
    else:
        chunk_size = 3     # 3-day chunks for larger plans

    chunks = []
    start = 1
    while start <= days:
        end = min(start + chunk_size - 1, days)
        chunks.append((start, end))
        start = end + 1

    collected_content = []

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, (start_day, end_day) in enumerate(chunks):
        chunk_days = end_day - start_day + 1

        status_text.text(f"Generating days {start_day}-{end_day} ({i+1}/{len(chunks)})")

        prompt = f"""Create a detailed {chunk_days}-day learning plan for: {target}

Difficulty level: {difficulty}
Target audience: Self-directed learner
Time commitment: 2-3 hours per day

IMPORTANT: Include ONLY days {start_day} through {end_day}.

For each day, provide:
- Day X: [Clear topic title]
- Learning objectives (3-4 specific goals)
- Key concepts to master
- Practical exercises
- Time breakdown

Format each day clearly with "Day X:" at the start.
Keep responses focused and concise."""

        chunk_content = api_manager.make_request(prompt, f"plan_chunk_{start_day}_{end_day}")

        if chunk_content:
            collected_content.append(chunk_content)
            status_text.text(f"✅ Generated days {start_day}-{end_day}")
        else:
            status_text.text(f"❌ Failed to generate days {start_day}-{end_day}")
            progress_bar.progress(1.0)
            return None

        # Update progress
        progress = (i + 1) / len(chunks)
        progress_bar.progress(progress)

        # Wait between chunks to respect rate limits
        if i < len(chunks) - 1:  # Don't wait after last chunk
            time.sleep(2)

    progress_bar.progress(1.0)
    status_text.text("✅ Plan generation complete!")

    # Clean up progress indicators after a moment
    time.sleep(1)
    progress_bar.empty()
    status_text.empty()

    return "\n\n".join(collected_content)

def parse_plan_content(content: str, plan_id: int) -> List[DailyMission]:
    """Parse AI-generated plan content into mission objects with improved parsing"""
    missions = []
    lines = content.split('\n')
    current_mission = None

    for line in lines:
        line = line.strip()

        # Look for day headers with improved regex
        day_match = re.match(r'^Day\s+(\d+)\s*:?\s*(.+)', line, re.IGNORECASE)
        if day_match:
            # Save previous mission if exists
            if current_mission:
                missions.append(current_mission)

            # Create new mission
            day_num = int(day_match.group(1))
            title = day_match.group(2).strip()

            current_mission = DailyMission(
                plan_id=plan_id,
                day_number=day_num,
                mission_title=title,
                mission_description="",
                detailed_content="",
                status='pending'
            )

        elif current_mission and line:
            # Add content to current mission
            if line.startswith(('Objectives:', 'Key Concepts:', 'Practice:', 'Time:', 'Learning objectives:', 'Key concepts:')):
                current_mission.detailed_content += f"\n\n**{line}**"
            elif line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.')):
                current_mission.detailed_content += f"\n{line}"
            else:
                # Add to description if it's substantial content
                if len(line) > 10:  # Only add meaningful content
                    current_mission.mission_description += f" {line}"

    # Don't forget the last mission
    if current_mission:
        missions.append(current_mission)

    # Sort missions by day number to ensure proper order
    missions.sort(key=lambda x: x.day_number)

    return missions

def create_learning_plan(target: str, days: int, difficulty: str = 'intermediate') -> Optional[LearningPlan]:
    """Create a complete learning plan with missions"""
    db = get_db_session()

    # Create the plan record first
    plan = LearningPlan(
        learning_target=target,
        total_days=days,
        difficulty_level=difficulty,
        created_date=datetime.now()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    # Generate plan content using chunked approach
    plan_content = generate_learning_plan_chunked(target, days, difficulty)

    if plan_content:
        # Parse and create missions
        missions = parse_plan_content(plan_content, plan.id)

        if missions:
            # Verify we have missions for all days
            mission_days = {m.day_number for m in missions}
            expected_days = set(range(1, days + 1))

            if mission_days != expected_days:
                st.warning(f"⚠️ Some days may be missing. Generated: {sorted(mission_days)}, Expected: {sorted(expected_days)}")

            # Save all missions
            for mission in missions:
                db.add(mission)
            db.commit()

            st.success(f"✅ Successfully created plan with {len(missions)} daily missions!")
            return plan
        else:
            st.error("❌ Failed to parse plan content into missions")
            db.delete(plan)
            db.commit()
            return None
    else:
        st.error("❌ Failed to generate plan content")
        db.delete(plan)
        db.commit()
        return None

def get_current_plan() -> Optional[LearningPlan]:
    """Get the most recent learning plan"""
    db = get_db_session()
    plans = db.query(LearningPlan).order_by(LearningPlan.created_date.desc()).all()
    return plans[0] if plans else None

def get_missions_for_plan(plan_id: int) -> List[DailyMission]:
    """Get all missions for a plan, sorted by day"""
    db = get_db_session()
    return db.query(DailyMission).filter(
        DailyMission.plan_id == plan_id
    ).order_by(DailyMission.day_number).all()
