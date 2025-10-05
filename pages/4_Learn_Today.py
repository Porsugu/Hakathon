import streamlit as st
from db_functions import get_plans_by_user, add_knowledge_item, update_plan_content
from utils import ensure_plan_selected
import google.generativeai as genai
import json

st.markdown("""
    <style> 
        /* General dark background and text */
        .stApp {
            background-color: #0e1117;
            color: #f5f5f5;
        }
        h1, h2, h3, h4, h5, h6, p, span, div {
            color: #f5f5f5 !important;
        }

        /* Top bar */
        header[data-testid="stHeader"] {
            background-color: #0e1117 !important;
            color: #f5f5f5 !important;
            box-shadow: none !important;
        }
        header[data-testid="stHeader"] .css-1v0mbdj {
            color: #f5f5f5 !important;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1a1d23 !important;
            color: #f5f5f5 !important;
        }
        section[data-testid="stSidebar"] .stAlert {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }
        section[data-testid="stSidebar"] .stAlert p {
            color: #f5f5f5 !important;
        }

        /* Buttons */
        div.stButton > button {
            background-color: #0078ff;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.6em 1em;
            font-weight: 600;
            transition: 0.2s ease-in-out;
        }
        div.stButton > button:hover {
            background-color: #0056b3;
            transform: scale(1.05);
        }

        /* Info / Error / Success Boxes */
        .stAlert {
            border: none !important;
            background-color: transparent !important;
            color: #f5f5f5 !important;
            box-shadow: none !important;
        }

        /* Expanders (Days) */
        details {
            background-color: #1a1d23 !important;
            border: 1px solid #2e3440 !important;
            border-radius: 8px !important;
            margin-bottom: 8px !important;
        }

        /* Progress bars */
        [data-testid="stProgress"] > div > div {
            background-color: #0078ff !important;
        }

        /* Chat input box */
        div[data-testid="stChatInput"] textarea {
            color: #f5f5f5 !important;
        }

        /* Chat messages */
        div[data-testid="stChatMessage"] {
            background-color: #1a1d23 !important;
            border-radius: 12px !important;
            padding: 1em !important;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Learn Today", layout="wide")

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

# --- Fetch plan and find today's task ---
def get_current_plan_and_task():
    all_plans = get_plans_by_user(uid)
    plan = next((p for p in all_plans if p['pid'] == pid), None)
    if not plan:
        return None, None
    
    try:
        daily_content = json.loads(plan['daily_content'])
        return plan, daily_content
    except (json.JSONDecodeError, TypeError):
        return plan, None

plan_data, daily_content = get_current_plan_and_task()

if not plan_data:
    st.error("Could not find the selected plan.")
    st.stop()

if not daily_content:
    st.success("🎉 Congratulations! You have completed all tasks in this plan.")
    st.balloons()
    st.page_link("main.py", label="Back to My Plans", icon="🏠")
    st.stop()

# --- Initialize Session State for Navigation and Caching ---
# This block ensures that if the user switches plans, the view resets correctly.
if st.session_state.get('last_viewed_pid') != pid:
    st.session_state.last_viewed_pid = pid
    if 'viewed_day_index' in st.session_state:
        del st.session_state['viewed_day_index'] # Force re-evaluation for new plan

if 'learning_materials_cache' not in st.session_state:
    st.session_state.learning_materials_cache = {}

# Initialize cache for the current plan if it doesn't exist
if pid not in st.session_state.learning_materials_cache:
    st.session_state.learning_materials_cache[pid] = {}

first_pending_index = next((i for i, day in enumerate(daily_content) if day.get('status') != 'completed'), 0)
st.session_state.viewed_day_index = st.session_state.get('viewed_day_index', first_pending_index)

# Ensure index is within bounds
if st.session_state.viewed_day_index >= len(daily_content):
    st.session_state.viewed_day_index = len(daily_content) - 1

current_day_index = st.session_state.viewed_day_index
current_day_task = daily_content[current_day_index]

st.title(f"📖 Learn: {plan_data['plan_name']}")
st.caption(f"Part of your plan: **{plan_data['plan_name']}**")
st.divider()

# --- Day Navigation ---
is_generating = st.session_state.get('is_generating', False)
nav_cols = st.columns([1, 1, 1])
with nav_cols[0]:
    if st.button("⬅️ Previous Day", use_container_width=True, disabled=(current_day_index <= 0 or is_generating)):
        st.session_state.viewed_day_index -= 1
        st.rerun()
with nav_cols[1]:
    if st.button("✅ Mark as Complete", use_container_width=True, type="primary", disabled=(current_day_task.get('status') == 'completed' or is_generating)):
        # Update the status in the local copy
        daily_content[current_day_index]['status'] = 'completed'
        # Save the updated plan back to the database
        update_plan_content(pid, json.dumps(daily_content))
        st.toast(f"Day {current_day_task['day']} marked as complete!")
        # Move to the next pending day
        next_pending_index = next((i for i, day in enumerate(daily_content) if day.get('status') != 'completed'), current_day_index)
        st.session_state.viewed_day_index = next_pending_index
        st.rerun()

with nav_cols[2]:
    if st.button("Next Day ➡️", use_container_width=True, disabled=(current_day_index >= len(daily_content) - 1 or is_generating)):
        st.session_state.viewed_day_index += 1
        st.rerun()

# --- Layout: Learning material on the left, Chat on the right ---
col1, col2 = st.columns([0.5, 0.5], gap="large")

# --- Left Column: Generate and display learning material ---
with col1:
    st.header(f"Day {current_day_task['day']}: {current_day_task['topic']}")
    with st.container(height=700): # This makes the container scrollable
        # Use the cache if content is already generated for this day
        if current_day_task['day'] in st.session_state.learning_materials_cache[pid]:
            learning_material = st.session_state.learning_materials_cache[pid][current_day_task['day']]
        else:
            st.session_state.is_generating = True
            with st.spinner("🤖 Breaking down today's topic into key concepts..."):
                prompt = f"""
                Please act as a helpful tutor. Your task is to break down a learning topic into key, saveable knowledge points.
                The topic is: "{current_day_task['topic']}"
                The specific learning goals are: "{current_day_task['details']}"
                
                Your response MUST be a single valid JSON object.
                This object must have one key: "knowledge_points".
                The value of "knowledge_points" must be an array of objects.
                Each object in the array represents a single, distinct piece of knowledge and must have three keys:
                1. "term": A concise string for the concept, term, or rule.
                2. "definition": A clear, easy-to-understand explanation of the term.
                3. "example": A short, practical code or usage example for the term.
                
                Example response format:
                {{
                  "knowledge_points": [
                    {{
                      "term": "Python Variable",
                      "definition": "A symbolic name that is a reference or pointer to an object. Once an object is assigned to a variable, you can refer to the object by that name."
                    }},
                    {{
                      "term": "Python String",
                      "definition": "A sequence of characters enclosed in single, double, or triple quotes. Strings are immutable.",
                      "example": "name = 'Alice'\\nprint(f'Hello, {{name}}')"
                    }}
                  ]
                }}
                """
                response = model.generate_content(prompt)
                cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
                learning_material = json.loads(cleaned_response)
                # Save to cache
                st.session_state.learning_materials_cache[pid][current_day_task['day']] = learning_material
            # The script will now continue and render the newly generated content
            # in the same run, avoiding a rerun.
            st.session_state.is_generating = False

        for i, item in enumerate(learning_material.get("knowledge_points", [])):
            with st.container(border=True):
                st.subheader(item['term'])
                st.write(item['definition'])
                if item.get('example'):
                    st.code(item['example'], language='python')
                if st.button("Save to Knowledge Base", key=f"save_{i}"):
                    # Combine definition and example for saving
                    full_definition = item['definition']
                    if item.get('example'):
                        full_definition += f"\n\n**Example:**\n```\n{item['example']}\n```"
                    add_knowledge_item(uid, pid, 'concept', item['term'], full_definition)
                    st.toast(f"✅ Saved '{item['term']}'!")

# --- Right Column: Chat Interface ---
with col2:
    st.header("Ask a Question")

    # Initialize chat history
    if 'learn_messages' not in st.session_state or st.session_state.get("current_task_day") != current_day_task['day']:
        st.session_state.learn_messages = [] # Reset chat for new day
        st.session_state.current_task_day = current_day_task['day']

    # Display chat messages
    for message in st.session_state.learn_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("Ask about today's topic..."):
        st.session_state.learn_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                # Construct a context-aware prompt
                # We'll format the knowledge points as context for the chat bot
                context_list = [f"- {item['term']}: {item['definition']}\n  Example: {item.get('example', 'N/A')}" for item in learning_material.get("knowledge_points", [])]
                context = "\n".join(context_list)

                full_prompt = f"""
                You are a helpful tutor. A student is currently studying the following material:
                ---
                {context}
                ---
                The student's question is: "{prompt}"
                
                Please answer the student's question based on the learning material. If the question is outside the scope of the material, politely say so.
                """
                
                response = model.generate_content(full_prompt)
                answer = response.text
                st.markdown(answer)
                st.session_state.learn_messages.append({"role": "assistant", "content": answer})