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
\
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
# Determine if we need to generate content *before* rendering the buttons.
# This ensures they are disabled on the initial load.
is_generating = current_day_task['day'] not in st.session_state.learning_materials_cache[pid]

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
            with st.spinner("🤖 Generating today's lesson..."):
                prompt = f"""
                Please act as a helpful and patient tutor. Your task is to generate comprehensive learning material for a complete beginner.
                Break the topic down into its most fundamental, atomic concepts. Each concept should be explained clearly and concisely, as if you are creating study notes.

                The topic is: "{current_day_task['topic']}"
                The specific learning goals are: "{current_day_task['details']}"
                
                Your response MUST be a single valid JSON object.
                This object must have one key: "learning_material".
                The value of "learning_material" must be an array of content blocks. Each block is an object with a "type" and "content".
                
                Here are the available types and their "content" structure:
                1. "type": "paragraph"
                   "content": "A string of explanatory text. Use markdown for formatting."
                2. "type": "key_concept"
                   "content": {{"term": "The specific term or concept", "definition": "A precise, clear definition.", "example": "A short, practical example."}}
                3. "type": "theorem"
                   "content": {{"name": "Name of the Theorem/Rule", "statement": "The full statement.", "example": "A clear, practical example."}}
                4. "type": "latex_equation"
                   "content": {{"title": "Name of the equation", "equation": "a^2 + b^2 = c^2", "explanation": "A brief explanation of what the equation represents."}}
                5. "type": "table"
                   "content": {{"title": "Title for the table", "headers": ["Header1", "Header2"], "rows": [["r1c1", "r1c2"], ["r2c1", "r2c2"]]}}. The 'headers' array MUST contain unique strings.
                6. "type": "code_example"
                   "content": {{"title": "Purpose of the code snippet", "language": "e.g., python", "code": "Your code here.", "explanation": "A brief explanation of what the code does."}}
                
                Generate a sequence of these blocks to create a complete and easy-to-understand lesson. Use the "key_concept" type for all fundamental definitions.
                Do not avoid defining a term as a "key_concept" just because it is also part of a table or another block type. If a term is important for a beginner to know, it must have its own "key_concept" definition.
                Ensure all concepts and theorems have good examples.
                
                Example JSON structure:
                {{
                  "learning_material": [
                    {{"type": "paragraph", "content": "Let's start with the basics of the Pythagorean theorem."}},
                    {{"type": "theorem", "content": {{"name": "Pythagorean Theorem", "statement": "In a right-angled triangle, the square of the hypotenuse is equal to the sum of the squares of the other two sides.", "example": "If side a=3 and side b=4, then c^2 = 3^2 + 4^2 = 9 + 16 = 25, so c=5."}}}},
                    {{"type": "latex_equation", "content": "a^2 + b^2 = c^2"}}
                  ]
                }}
                """
                response = model.generate_content(prompt)
                cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
                learning_material = json.loads(cleaned_response)
                # Save to cache
                st.session_state.learning_materials_cache[pid][current_day_task['day']] = learning_material
                # Force a rerun to re-evaluate the 'is_generating' flag and enable the buttons.
                st.rerun()

        for i, block in enumerate(learning_material.get("learning_material", [])):
            block_type = block.get("type")
            content = block.get("content")

            if block_type == "paragraph":
                st.markdown(content)
            
            elif block_type == "key_concept" and isinstance(content, dict):
                with st.container(border=True):
                    st.subheader(content.get("term", "Key Concept"))
                    st.write(content.get("definition"))
                    if content.get("example"):
                        st.markdown(f"**Example:** {content.get('example')}")
                    if st.button("Save to Knowledge Base", key=f"save_concept_{i}"):
                        full_definition = f"{content.get('definition')}\n\n**Example:** {content.get('example')}"
                        add_knowledge_item(uid, pid, 'concept', content.get("term"), full_definition)
                        st.toast(f"✅ Saved '{content.get('term')}'!")

            elif block_type == "theorem" and isinstance(content, dict):
                with st.container(border=True):
                    st.subheader(content.get("name", "Theorem/Rule"))
                    st.write(content.get("statement"))
                    if content.get("example"):
                        st.markdown(f"**Example:** {content.get('example')}")
                    if st.button("Save to Knowledge Base", key=f"save_theorem_{i}"):
                        full_definition = f"{content.get('statement')}\n\n**Example:** {content.get('example')}"
                        add_knowledge_item(uid, pid, 'theorem', content.get("name"), full_definition)
                        st.toast(f"✅ Saved '{content.get('name')}'!")

            elif block_type == "latex_equation":
                with st.container(border=True):
                    equation_title = content.get("title", "Equation")
                    st.subheader(equation_title)
                    st.latex(content.get("equation", ""))
                    if content.get("explanation"):
                        st.write(content.get("explanation"))
                    if st.button("Save to Knowledge Base", key=f"save_equation_{i}"):
                        # Format the equation and explanation for saving
                        full_definition = f"```latex\n{content.get('equation', '')}\n```\n\n**Explanation:**\n{content.get('explanation', 'No explanation provided.')}"
                        add_knowledge_item(uid, pid, 'equation', equation_title, full_definition)
                        st.toast(f"✅ Saved '{equation_title}'!")

            elif block_type == "table" and isinstance(content, dict):
                import pandas as pd
                with st.container(border=True):
                    table_title = content.get("title", "Data Table")
                    st.subheader(table_title)
                    headers = content.get("headers", [])
                    # Defensively handle duplicate headers from the AI
                    unique_headers = []
                    for h in headers:
                        if h not in unique_headers:
                            unique_headers.append(h)
                    
                    # Ensure all rows have the same number of columns as the headers
                    num_columns = len(unique_headers)
                    sanitized_rows = [row[:num_columns] for row in content.get("rows", [])]
                    df = pd.DataFrame(sanitized_rows, columns=unique_headers)
                    st.table(df)
                    if st.button("Save to Knowledge Base", key=f"save_table_{i}"):
                        # Manually create a markdown table to avoid the 'tabulate' dependency.
                        headers_str = "| " + " | ".join(df.columns) + " |"
                        separator_str = "| " + " | ".join(["---"] * len(df.columns)) + " |"
                        rows_str = "\n".join(["| " + " | ".join(map(str, row)) + " |" for row in df.itertuples(index=False)])
                        markdown_table = f"{headers_str}\n{separator_str}\n{rows_str}"
                        add_knowledge_item(uid, pid, 'table', table_title, markdown_table)
                        st.toast(f"✅ Saved '{table_title}'!")

            elif block_type == "code_example" and isinstance(content, dict):
                with st.container(border=True):
                    code_title = content.get("title", "Code Example")
                    st.subheader(code_title)
                    st.code(content.get("code", ""), language=content.get("language", "plaintext"))
                    if content.get("explanation"):
                        st.write(content.get("explanation"))
                    if st.button("Save to Knowledge Base", key=f"save_code_{i}"):
                        # Format the code and explanation for saving
                        full_definition = f"```\n{content.get('code', '')}\n```\n\n**Explanation:**\n{content.get('explanation', 'No explanation provided.')}"
                        add_knowledge_item(uid, pid, 'code', code_title, full_definition)
                        st.toast(f"✅ Saved '{code_title}'!")

            st.write("") # Adds a little vertical space

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
                # Create a simple text representation of the complex learning material for context
                context_list = []
                for block in learning_material.get("learning_material", []):
                    if block.get("type") == "paragraph":
                        context_list.append(block.get("content"))
                    elif block.get("type") == "key_concept":
                        c = block.get("content", {})
                        context_list.append(f"Concept '{c.get('term')}': {c.get('definition')}")
                    elif block.get("type") == "theorem":
                        c = block.get("content", {})
                        context_list.append(f"Rule '{c.get('name')}': {c.get('statement')}")
                    elif block.get("type") == "latex_equation":
                        c = block.get("content", {})
                        context_list.append(f"Equation '{c.get('title')}': {c.get('explanation')}")
                    elif block.get("type") == "code_example":
                        c = block.get("content", {})
                        context_list.append(f"Code '{c.get('title')}': {c.get('explanation')}")

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