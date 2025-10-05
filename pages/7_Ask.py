import streamlit as st
from db_functions import get_knowledge_items_by_plan, get_plans_by_user, add_knowledge_item
from utils import ensure_plan_selected
import google.generativeai as genai
import json

st.set_page_config(page_title="Ask Something", layout="wide")

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

# --- Fetch Data for Context ---
knowledge_items = get_knowledge_items_by_plan(uid, pid)
all_plans = get_plans_by_user(uid)
current_plan = next((plan for plan in all_plans if plan['pid'] == pid), None)
plan_name = current_plan['plan_name'] if current_plan else "your plan"

st.title(f"❓ Ask about: {plan_name}")
st.info("Ask any question related to your learning plan. If it's an important concept, you'll be able to save it to your knowledge base.")

# --- Initialize Session State ---
if st.session_state.get('ask_last_pid') != pid:
    st.session_state.ask_last_pid = pid
    st.session_state.ask_messages = []
    st.session_state.blackboard_item = None

if "ask_messages" not in st.session_state:
    st.session_state.ask_messages = []
if "blackboard_item" not in st.session_state:
    st.session_state.blackboard_item = None

# --- Layout ---
col1, col2 = st.columns([0.5, 0.5], gap="large")

# --- Left Column: Blackboard ---
with col1:
    st.header("Blackboard")
    with st.container(height=700, border=True):
        if st.session_state.blackboard_item:
            item = st.session_state.blackboard_item
            st.subheader(item['term'])
            st.write(item['definition'])
            if item.get('example'):
                st.code(item['example'], language='python')
            
            if st.button("Add to Knowledge Base", use_container_width=True):
                full_definition = item['definition']
                if item.get('example'):
                    full_definition += f"\n\n**Example:**\n```\n{item['example']}\n```"
                add_knowledge_item(uid, pid, 'concept', item['term'], full_definition)
                st.toast(f"✅ Saved '{item['term']}'!")
                st.session_state.blackboard_item = None # Clear after saving
        else:
            st.write("Important concepts you ask about will appear here...")

# --- Right Column: Chat Interface ---
with col2:
    st.header("Chat")

    # Display chat messages
    for message in st.session_state.ask_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input(f"Ask a question about {plan_name}..."):
        st.session_state.ask_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                # Build context from saved knowledge
                context = "\n".join([f"- {item['term']}: {item['definition']}" for item in knowledge_items])

                # Construct a detailed prompt for the AI
                full_prompt = f"""
                You are a helpful tutor for a student learning about '{plan_name}'.
                The user's question is: "{prompt}"

                First, decide if the question is related to '{plan_name}'.
                - If it is NOT related, respond with a conversational message explaining you can only answer questions about the topic.

                - If it IS related, decide if the answer is a distinct, important "knowledge point" (like a vocabulary word, a function, a grammar rule, a specific formula).
                    - If it IS a knowledge point, you MUST respond with ONLY a single JSON object with this structure:
                      `{{"is_knowledge_point": true, "data": {{"term": "...", "definition": "...", "example": "..."}}}}`
                
                - If the question is related but requires a general explanation or a conversational answer (not a dictionary-style entry), you MUST respond with ONLY a single JSON object with this structure:
                  `{{"is_knowledge_point": false, "data": {{"answer": "Your conversational answer here."}}}}`

                Here is some context of what the user has already saved:
                ---
                {context}
                ---
                """

                response = model.generate_content(full_prompt)
                answer_text = response.text

                try:
                    # Attempt to parse the AI's response as JSON
                    cleaned_response = answer_text.strip().replace("```json", "").replace("```", "")
                    ai_response_data = json.loads(cleaned_response)

                    is_knowledge = ai_response_data.get("is_knowledge_point", False)
                    data = ai_response_data.get("data", {})

                    if is_knowledge:
                        # It's a knowledge point, display on blackboard
                        st.session_state.blackboard_item = data
                        # Add a message to the chat to direct the user
                        chat_message = f"I've put the details for **{data.get('term')}** on the blackboard for you. You can save it to your knowledge base from there!"
                        st.markdown(chat_message)
                        st.session_state.ask_messages.append({"role": "assistant", "content": chat_message})
                        st.rerun()
                        
                    else:
                        # It's a conversational answer
                        chat_message = data.get("answer", "I'm not sure how to respond to that, please try asking differently.")
                        st.markdown(chat_message)
                        st.session_state.ask_messages.append({"role": "assistant", "content": chat_message})
                        if st.session_state.blackboard_item:
                            st.session_state.blackboard_item = None # Clear blackboard
                            st.rerun()

                except (json.JSONDecodeError, TypeError):
                    # If JSON parsing fails, treat it as a simple conversational response
                    st.markdown(answer_text)
                    st.session_state.ask_messages.append({"role": "assistant", "content": answer_text})
                    st.session_state.blackboard_item = None # Clear blackboard

st.divider()
st.page_link("pages/2_Plan_Details.py", label="Back to Plan Dashboard", icon="⬅️")