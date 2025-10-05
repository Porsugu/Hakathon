import streamlit as st
from db_functions import get_plans_by_user, update_plan_content
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
if 'current_plan_id' not in st.session_state:
    st.error("No plan selected. Please go back to the homepage and select a plan.")
    st.page_link("main.py", label="Go to Homepage", icon="🏠")
    st.stop()

pid = st.session_state['current_plan_id']
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
        content = json.loads(plan['daily_content'])
        # Find the first task that is not completed
        task = next((day for day in content if day.get('status') != 'completed'), None)
        return plan, task
    except (json.JSONDecodeError, TypeError):
        return plan, None

plan_data, today_task = get_current_plan_and_task()

if not plan_data:
    st.error("Could not find the selected plan.")
    st.stop()

if not today_task:
    st.success("🎉 Congratulations! You have completed all tasks in this plan.")
    st.balloons()
    st.page_link("main.py", label="Back to My Plans", icon="🏠")
    st.stop()

st.title(f"📖 Learn Today: {today_task['topic']}")
st.caption(f"Part of your plan: **{plan_data['plan_name']}**")
st.divider()

# --- Layout: Learning material on the left, Chat on the right ---
col1, col2 = st.columns([0.5, 0.5], gap="large")

# --- Left Column: Generate and display learning material ---
with col1:
    st.header("Your Learning Material")
    with st.container(height=700): # This makes the container scrollable
        # Use session state to cache the generated material to avoid re-generating on every interaction
        if "learning_material" not in st.session_state or st.session_state.get("current_task_day") != today_task['day']:
            with st.spinner("🤖 Generating today's lesson..."):
                prompt = f"""
                Please act as a helpful tutor. Generate a brief, easy-to-understand learning material for a student.
                The topic is: "{today_task['topic']}"
                The specific learning goals are: "{today_task['details']}"
                
                Structure the material clearly using markdown. Use headings, bullet points, and bold text to make it easy to read.
                Start with a simple introduction and then explain the key concepts.
                """
                response = model.generate_content(prompt)
                st.session_state.learning_material = response.text
                st.session_state.current_task_day = today_task['day']
        
        st.markdown(st.session_state.learning_material)

# --- Right Column: Chat Interface ---
with col2:
    st.header("Ask a Question")

    # Initialize chat history
    if "learn_messages" not in st.session_state or st.session_state.get("current_task_day") != today_task['day']:
        st.session_state.learn_messages = []
        st.session_state.current_task_day = today_task['day']

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
                context = st.session_state.learning_material
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