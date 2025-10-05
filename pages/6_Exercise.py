import streamlit as st
from db_functions import get_knowledge_items_by_plan, get_plans_by_user
from utils import ensure_plan_selected
import google.generativeai as genai
import json
import random

st.set_page_config(page_title="Exercise", layout="wide")

# --- Check for selected plan ---
pid = ensure_plan_selected()
uid = st.session_state.get('user_id', 1)

# --- AI Configuration ---
try:
    genai.configure(api_key="AIzaSyDJpS-vOpOQXdsWQG5iKunReCHqG4OZdOg")
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"AI Model could not be configured: {e}")
    st.stop()

# --- Fetch Data ---
knowledge_items = get_knowledge_items_by_plan(uid, pid)
all_plans = get_plans_by_user(uid)
current_plan = next((plan for plan in all_plans if plan['pid'] == pid), None)
plan_name = current_plan['plan_name'] if current_plan else "Exercise"

st.title(f"✍️ Exercise: {plan_name}")


# --- Handle No Items ---
if not knowledge_items:
    st.info("You haven't saved any knowledge items for this plan yet.")
    st.write("Go to the 'Learn Today' section to save concepts before you can practice!")
    st.page_link("pages/2_Plan_Details.py", label="Back to Plan Dashboard", icon="⬅️")
    st.stop()

# --- Function to generate exercises ---
def generate_exercises(items):
    context = "\n".join([f"- {item['term']}: {item['definition']}" for item in items])
    prompt = f"""
    Based on the following knowledge items, create a quiz with exactly 10 questions.
    The quiz must include a mix of the following three types: 'short_answer', 'multiple_choice', and 'fill_in_the_blank'.

    Your response MUST be a single valid JSON object with a key "questions", which is an array of question objects.
    Each question object must have a "type" and a "data" key.

    The "data" structure for each type is as follows:
    1. "type": "short_answer"
       "data": {{"question": "Your question here?", "answer": "The correct answer."}}
    2. "type": "multiple_choice"
       "data": {{"question": "Your question?", "options": ["A", "B", "C", "D"], "answer": "Correct option"}}
    3. "type": "fill_in_the_blank"
       "data": {{"sentence": "A sentence with a ____ to fill.", "blank_word": "word"}}

    Knowledge Items Context:
    ---
    {context}
    ---
    Generate the JSON quiz now.
    """
    response = model.generate_content(prompt)
    cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(cleaned_response)

# --- Initialize session state for exercises and chat ---
# This block ensures that if the user switches plans, a new set of questions is generated.
if st.session_state.get('exercise_last_pid') != pid:
    st.session_state.exercise_last_pid = pid
    st.session_state.exercise_questions = None
    st.session_state.exercise_feedback = {}
    st.session_state.exercise_messages = []

if "exercise_questions" not in st.session_state:
    st.session_state.exercise_questions = None
if "exercise_messages" not in st.session_state:
    st.session_state.exercise_messages = []
if "exercise_feedback" not in st.session_state:
    st.session_state.exercise_feedback = {}

# --- Layout ---
col1, col2 = st.columns([0.6, 0.4], gap="large")

# --- Left Column: Problems ---
with col1:
    st.header("Your Questions")
    if st.button("Generate New Questions"):
        st.session_state.exercise_questions = None # Clear old questions
        st.session_state.exercise_feedback = {} # Clear old feedback

    if not st.session_state.exercise_questions:
        with st.spinner("🤖 Generating your exercise..."):
            st.session_state.exercise_questions = generate_exercises(knowledge_items)

    questions = st.session_state.exercise_questions.get("questions", [])

    with st.container(height=800):
        if not questions:
            st.warning("Could not generate questions. Please try again.")
        else:
            for i, q in enumerate(questions):
                st.subheader(f"Question {i+1}")
                q_type = q.get("type")
                q_data = q.get("data", {})
                user_answer = None

                if q_type == "short_answer":
                    st.write(q_data.get("question"))
                    user_answer = st.text_input("Your Answer", key=f"sa_{i}", label_visibility="collapsed")

                elif q_type == "multiple_choice":
                    user_answer = st.radio(q_data.get("question"), options=q_data.get("options", []), key=f"mc_{i}", index=None)

                elif q_type == "fill_in_the_blank":
                    st.write(q_data.get("sentence", "").replace("____", " `____` "))
                    user_answer = st.text_input("Fill in the blank", key=f"fb_{i}")

                if st.button("Check Answer", key=f"check_{i}"):
                    if user_answer:
                        with st.spinner("🤖 Checking your answer..."):
                            # Prepare prompt for AI
                            check_prompt = f"""
                            You are a helpful and encouraging tutor. A student has submitted an answer for a question.
                            Your task is to evaluate it and provide feedback.

                            Question Details:
                            {json.dumps(q, indent=2)}

                            Student's Answer:
                            {json.dumps(user_answer, indent=2)}

                            Please evaluate the student's answer.
                            - If it is correct, congratulate them and briefly explain why it's correct.
                            - If it is incorrect, gently point out the mistake and provide a clear explanation of the correct answer.
                            - Keep your response concise and encouraging.
                            """
                            response = model.generate_content(check_prompt)
                            st.session_state.exercise_feedback[i] = response.text
                    else:
                        st.session_state.exercise_feedback[i] = "Please provide an answer before checking."

                # Display feedback if it exists
                if i in st.session_state.exercise_feedback:
                    feedback = st.session_state.exercise_feedback[i]
                    # A simple heuristic to determine if the answer was correct for styling
                    if "correct" in feedback.lower() or "well done" in feedback.lower() or "exactly" in feedback.lower():
                        st.success(feedback)
                    elif "incorrect" in feedback.lower() or "not quite" in feedback.lower():
                        st.error(feedback)
                    else:
                        st.info(feedback)

                st.divider()

# --- Right Column: Chat Interface ---
with col2:
    st.header("AI Assistant")
    st.info("Ask for hints, or ask the AI to adjust the questions!")

    # Display chat messages
    for message in st.session_state.exercise_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("How can I help?"):
        st.session_state.exercise_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                # Construct a detailed prompt for the AI
                current_questions_json = json.dumps(st.session_state.exercise_questions, indent=2)
                full_prompt = f"""
                You are an exercise assistant. The user is working on the following set of questions.
                Their request is: '{prompt}'

                If the user asks for a hint, provide one without giving away the answer.
                If the user asks to change the questions (e.g., 'make them easier', 'add more pairing questions'), please generate a new set of 10 questions based on their request and the original knowledge context.
                When generating new questions, you MUST respond with ONLY the new JSON object, following the exact same structure as the original. Do not add any other text.
                If you are just providing a hint or answering a question, respond with conversational text.

                Current Questions JSON:
                {current_questions_json}
                """

                response = model.generate_content(full_prompt)
                answer = response.text

                # Check if the AI returned a new JSON to replace the questions
                try:
                    cleaned_response = answer.strip().replace("```json", "").replace("```", "")
                    new_questions = json.loads(cleaned_response)
                    if "questions" in new_questions:
                        st.session_state.exercise_questions = new_questions
                        st.session_state.exercise_messages.append({"role": "assistant", "content": "I've updated the questions for you! They are now shown on the left."})
                        st.rerun()
                except (json.JSONDecodeError, TypeError):
                    # The response was not a valid JSON, so treat it as a conversational answer
                    st.session_state.exercise_messages.append({"role": "assistant", "content": answer})
                    st.markdown(answer)