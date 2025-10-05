"""
Personal Learning OS - Main Application
Modular production-ready learning management system
"""
import streamlit as st
import time
from datetime import datetime

# Import our modular components
from models import get_db_session
from api_manager import get_api_manager
from plan_generator import create_learning_plan, get_current_plan, get_missions_for_plan
from learning import generate_learning_content, save_learning_progress
from practice import generate_practice_exercises
from chat import generate_free_learning_response, save_explanation, get_saved_explanations
from ui_styles import get_custom_css, render_header, render_stat_box

# Configure Streamlit
st.set_page_config(
    page_title="Personal Learning OS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'current_function': 'dashboard',
        'current_plan': None,
        'chat_messages': [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def render_stats():
    """Render learning statistics dashboard"""
    plan = get_current_plan()
    if plan:
        missions = get_missions_for_plan(plan.id)
        completed = len([m for m in missions if m.status == 'completed'])
        total = len(missions)
        current_day = len([m for m in missions if m.status in ['completed', 'current']]) or 1

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(render_stat_box("Current Day", str(current_day), plan.difficulty_level), unsafe_allow_html=True)

        with col2:
            st.markdown(render_stat_box("Progress", f"{completed}/{total}", plan.learning_target[:20]), unsafe_allow_html=True)

        with col3:
            progress_percent = int((completed/total)*100) if total > 0 else 0
            st.markdown(render_stat_box("Complete", f"{progress_percent}%", "missions"), unsafe_allow_html=True)

        with col4:
            saved_count = len(get_saved_explanations())
            st.markdown(render_stat_box("Saved", str(saved_count), "explanations"), unsafe_allow_html=True)

def function_plan():
    """Plan creation interface"""
    st.header("📋 Create Learning Plan")

    # Check API status
    api_manager = get_api_manager()
    if not api_manager.model:
        st.error("❌ Cannot create plans without Gemini API.")
        return

    with st.form("create_plan_form"):
        col1, col2 = st.columns(2)

        with col1:
            learning_target = st.text_input(
                "🎯 What do you want to learn?",
                placeholder="e.g., Python Programming, Web Development"
            )
            days = st.slider("📅 Duration (days)", min_value=3, max_value=21, value=7)

        with col2:
            difficulty = st.selectbox(
                "🎚️ Difficulty Level",
                ["beginner", "intermediate", "advanced"],
                index=1
            )
            st.info("💡 Plans are generated in chunks to handle API limits.")

        submitted = st.form_submit_button("🚀 Generate AI Learning Plan", use_container_width=True)

        if submitted and learning_target:
            plan = create_learning_plan(learning_target.strip(), days, difficulty)
            if plan:
                st.session_state.current_plan = plan
                st.balloons()
                st.rerun()

    # Display current plan
    plan = get_current_plan()
    if plan:
        st.markdown("---")
        st.markdown("### 📚 Your Learning Plan")

        missions = get_missions_for_plan(plan.id)

        if missions:
            for mission in missions:
                status_emoji = "✅" if mission.status == "completed" else "🟡" if mission.status == "current" else "⏳"

                with st.expander(f"{status_emoji} Day {mission.day_number}: {mission.mission_title}"):
                    if mission.mission_description:
                        st.markdown(f"**Description:** {mission.mission_description}")
                    if mission.detailed_content:
                        st.markdown("**Details:**")
                        st.markdown(mission.detailed_content)

def function_learn():
    """Learning interface"""
    st.header("📖 AI-Powered Learning")

    plan = get_current_plan()
    if not plan:
        st.warning("⚠️ Please create a learning plan first!")
        return

    missions = get_missions_for_plan(plan.id)
    current_mission = None

    # Find current mission
    for mission in missions:
        if mission.status == 'current':
            current_mission = mission
            break

    if not current_mission:
        for mission in missions:
            if mission.status == 'pending':
                current_mission = mission
                db = get_db_session()
                mission.status = 'current'
                db.commit()
                break

    if current_mission:
        st.markdown(f"### 🎯 Day {current_mission.day_number}: {current_mission.mission_title}")

        if st.button("🚀 GIVE ME RIGHT HERE RIGHT NOW", use_container_width=True):
            instruction = generate_learning_content(current_mission.mission_title)

            if instruction:
                st.markdown("---")
                st.markdown("### 🧠 Your Learning Content")
                st.markdown(instruction)

                # Save progress and advance
                save_learning_progress(plan.id, current_mission.day_number, instruction[:1000])

                current_mission.status = 'completed'
                db = get_db_session()

                # Find next mission
                for mission in missions:
                    if mission.day_number == current_mission.day_number + 1:
                        mission.status = 'current'
                        break

                db.commit()
                st.success("✅ Mission completed!")
    else:
        st.success("🎉 All missions completed!")

def function_practice():
    """Practice interface"""
    st.header("💪 Practice Exercises")

    plan = get_current_plan()
    if not plan:
        st.warning("⚠️ Create a plan first!")
        return

    missions = get_missions_for_plan(plan.id)
    completed = [m for m in missions if m.status == 'completed']

    if not completed:
        st.info("Complete some missions first!")
        return

    col1, col2 = st.columns(2)
    with col1:
        topic = st.selectbox("Topic:", [m.mission_title for m in completed])
    with col2:
        ex_type = st.radio("Type:", ["Quiz", "Problems", "Examples"])

    if st.button("Generate Exercises", use_container_width=True):
        exercises = generate_practice_exercises(topic, ex_type)
        if exercises:
            st.markdown("---")
            st.markdown(exercises["content"])

def function_chat():
    """Chat interface"""
    st.header("💬 AI Chat")

    # Display chat history
    for i, message in enumerate(st.session_state.chat_messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant" and "saved" not in message:
                if st.button("💾 Save", key=f"save_{i}"):
                    query = message.get("query", "Chat question")
                    save_explanation(query, message["content"])
                    st.success("✅ Saved!")
                    message["saved"] = True
                    st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask anything..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = generate_free_learning_response(prompt)
            if response:
                st.markdown(response)
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": response,
                    "query": prompt
                })

def function_review():
    """Review interface"""
    st.header("📖 Review")

    explanations = get_saved_explanations()
    if not explanations:
        st.info("No saved content yet.")
        return

    for exp in explanations[:10]:
        with st.expander(f"{exp.user_query[:50]}..."):
            st.markdown(f"**Q:** {exp.user_query}")
            st.markdown(f"**A:** {exp.ai_explanation}")

def main():
    """Main application"""
    init_session_state()

    # Header
    api_manager = get_api_manager()
    st.markdown(render_header(api_manager.model is not None), unsafe_allow_html=True)
    render_stats()

    # Navigation
    st.sidebar.title("Navigation")
    functions = {
        "📊 Dashboard": "dashboard",
        "📋 Plan": "plan",
        "📖 Learn": "learn", 
        "💪 Practice": "practice",
        "💬 Chat": "chat",
        "📖 Review": "review"
    }

    selected = st.sidebar.radio("Choose:", list(functions.keys()))
    st.session_state.current_function = functions[selected]

    # Route to function
    if st.session_state.current_function == "plan":
        function_plan()
    elif st.session_state.current_function == "learn":
        function_learn()
    elif st.session_state.current_function == "practice":
        function_practice()
    elif st.session_state.current_function == "chat":
        function_chat()
    elif st.session_state.current_function == "review":
        function_review()
    else:  # dashboard
        plan = get_current_plan()
        if plan:
            st.header("📊 Dashboard")
            st.success(f"Active plan: {plan.learning_target}")
            if st.button("Continue Learning"):
                st.session_state.current_function = "learn"
                st.rerun()
        else:
            st.header("🚀 Welcome!")
            if st.button("Create Plan"):
                st.session_state.current_function = "plan"
                st.rerun()

if __name__ == "__main__":
    main()
