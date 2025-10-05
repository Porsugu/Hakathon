import streamlit as st
from db_functions import get_plans_by_user, add_knowledge_item, update_plan_content
from utils import ensure_plan_selected
import google.generativeai as genai
import json
from config import config
from config import get_ai_manager

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

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #1a1d23;
            color: #f5f5f5;
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

        /* Info boxes */
        .stAlert {
            background-color: #1f2937 !important;
            color: #e5e7eb !important;
            border: none;
        }

        /* Containers */
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
            background-color: #1a1d23;
            border: 1px solid #2e3440;
            border-radius: 12px;
            padding: 1em;
            margin-bottom: 1em;
        }
            
        header[data-testid="stHeader"] {
            background-color: #0e1117 !important; 
            color: #f5f5f5 !important;           
            box-shadow: none !important;
        }

        /* Make the container for the back button invisible */
        .back-button-container > div {
            background-color: transparent !important;
            border: none !important;
        }

        /* Make the container for the title bar invisible */
        .title-bar-container > div > div > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
        }

        /* Hide the sidebar hamburger button */
        button[title="Open navigation"] {
            display: none !important;
        }

        /* Style for copyable code/latex blocks */
        div[data-testid="stCodeBlock"] > div, div[data-testid="stLatex"] > div, pre {
            background-color: #262730 !important; /* A medium-dark grey */
            border-radius: 8px;
            padding: 1em;
            color: #f5f5f5 !important;
        }

        /* Style for toast notifications */
        div[data-testid="stToast"] {
            background-color: #262730;
            border: 1px solid #4b5563;
            color: #f5f5f5;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Learn Today", layout="wide")

# --- Check for selected plan ---
pid = ensure_plan_selected()
uid = st.session_state.get('user_id', 1)

# --- AI Configuration ---
ai_manager = get_ai_manager()
if not ai_manager.initialize():
    st.error("AI could not be initialized. Check your secrets or environment variables.")
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

title_col, back_button_col = st.columns([0.8, 0.2])
with title_col:
    st.title(f"📖 Learn: {plan_data['plan_name']}")
    st.caption(f"Part of your plan: **{plan_data['plan_name']}**")
with back_button_col:
    st.markdown('<div class="back-button-container">', unsafe_allow_html=True)
    if st.button("◀ Back", use_container_width=True):
        st.switch_page("pages/2_Plan_Details.py")
    st.markdown('</div>', unsafe_allow_html=True)

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
                special_instructions = plan_data['special_instructions'] if 'special_instructions' in plan_data.keys() else None
                instruction_prompt_part = ""
                if special_instructions:
                    instruction_prompt_part = f"""
                Additionally, please adhere to the following special instructions from the user for their teaching materials:
                ---
                {special_instructions}
                ---
                """

                prompt = f"""
                Please act as a helpful and patient tutor. Your task is to generate comprehensive learning material for a complete beginner.
                Break the topic down into its most fundamental, atomic concepts. Each concept should be explained clearly and concisely, as if you are creating study notes.

                The topic is: "{current_day_task['topic']}"
                The specific learning goals are: "{current_day_task['details']}"
                {instruction_prompt_part}
                
                Your response MUST be a single valid JSON object.
                This object must have one key: "learning_material".
                IMPORTANT: All backslashes `\` inside the JSON string values must be properly escaped (as `\\`).
                The value of "learning_material" must be an array of content blocks. Each block is an object with a "type" and "content".
                
                Here are the available types and their "content" structure:
                - "type": "paragraph": "content" is a string of explanatory text. Use markdown for formatting. IMPORTANT: Any inline LaTeX math notation must be wrapped in single dollar signs, like `$\\pi$`.
                - "type": "key_concept": "content" is {{"term": "The specific term or concept", "definition": "A precise, clear definition.", "example": "A short, practical example."}}.
                - "type": "theorem": "content" is {{"name": "Name of the Theorem/Rule", "statement": "The full statement.", "example": "A clear, practical example."}}.
                - "type": "latex_equation": "content" is {{"title": "Name of the equation", "equation": "a^2 + b^2 = c^2", "explanation": "A brief explanation of what the equation represents."}}.
                - "type": "table": "content" is {{"title": "Title for the table", "headers": ["Header1", "Header2"], "rows": [["r1c1", "r1c2"], ["r2c1", "r2c2"]]}}. The 'headers' array MUST contain unique strings.
                - "type": "code_example": "content" is {{"title": "Purpose of the code snippet", "language": "e.g., python", "code": "Your code here.", "explanation": "A brief explanation of what the code does."}}.
                
                **If the topic is about learning a language, use these special types for vocabulary and grammar:**
                - "type": "vocabulary_card": "content" is {{"word": "The vocabulary word", "part_of_speech": "e.g., Noun, Verb", "meaning": "The definition of the word.", "example": "An example sentence using the word."}}.
                - "type": "grammar_card": "content" is {{"grammar_point": "The name of the grammar rule", "rule_of_use": "When and how to use the rule.", "meaning": "What the grammar conveys.", "example": "An example sentence demonstrating the rule."}}.
                
                For general topics, use "key_concept". For language topics, use "vocabulary_card" and "grammar_card" instead of "key_concept" for words and grammar rules.
                
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
                response = ai_manager.generate_content(prompt)
                if not response:
                    st.error("AI returned no content for learning material.")
                    learning_material = {"learning_material": []}
                else:
                    cleaned_response = response.replace("```json", "").replace("```", "").strip()
                    # A more robust way to handle backslashes for JSON parsing.
                    # This escapes backslashes that are not already part of a valid escape sequence.
                    import re
                    learning_material = json.loads(re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', cleaned_response))
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
                    st.markdown(content.get("definition", ""))
                    if content.get("example"):
                        st.markdown(f"**Example:** {content.get('example')}")
                    if st.button("Save to Knowledge Base", key=f"save_concept_{i}"):
                        full_definition = f"{content.get('definition')}\n\n**Example:** {content.get('example')}"
                        add_knowledge_item(uid, pid, 'concept', content.get("term"), content.get("definition", ""))
                        st.toast(f"✅ Saved '{content.get('term')}'!")

            elif block_type == "theorem" and isinstance(content, dict):
                with st.container(border=True):
                    st.subheader(content.get("name", "Theorem/Rule"))
                    st.markdown(content.get("statement", ""))
                    if content.get("example"):
                        st.markdown(f"**Example:** {content.get('example')}")
                    if st.button("Save to Knowledge Base", key=f"save_theorem_{i}"):
                        full_definition = f"{content.get('statement')}\n\n**Example:** {content.get('example')}"
                        add_knowledge_item(uid, pid, 'theorem', content.get("name"), full_definition)
                        st.toast(f"✅ Saved '{content.get('name')}'!")

            elif block_type == "vocabulary_card" and isinstance(content, dict):
                with st.container(border=True):
                    st.subheader(content.get("word", "Vocabulary"))
                    st.markdown(f"**Part of speech:** {content.get('part_of_speech', 'N/A')}")
                    st.markdown(f"**Meaning:** {content.get('meaning', 'N/A')}")
                    if content.get("example"):
                        st.markdown(f"**Example:** {content.get('example')}")
                    if st.button("Save to Knowledge Base", key=f"save_vocab_{i}"):
                        full_definition = f"**Part of speech:** {content.get('part_of_speech', 'N/A')}\n\n**Meaning:** {content.get('meaning', 'N/A')}\n\n**Example:** {content.get('example', 'N/A')}"
                        add_knowledge_item(uid, pid, 'vocabulary', content.get("word"), full_definition)
                        st.toast(f"✅ Saved '{content.get('word')}'!")

            elif block_type == "grammar_card" and isinstance(content, dict):
                with st.container(border=True):
                    st.subheader(content.get("grammar_point", "Grammar Rule"))
                    st.markdown(f"**Rule of use:** {content.get('rule_of_use', 'N/A')}")
                    st.markdown(f"**Meaning:** {content.get('meaning', 'N/A')}")
                    if content.get("example"):
                        st.markdown(f"**Example:** {content.get('example')}")
                    if st.button("Save to Knowledge Base", key=f"save_grammar_{i}"):
                        full_definition = f"**Rule of use:** {content.get('rule_of_use', 'N/A')}\n\n**Meaning:** {content.get('meaning', 'N/A')}\n\n**Example:** {content.get('example', 'N/A')}"
                        add_knowledge_item(uid, pid, 'grammar', content.get("grammar_point"), full_definition)
                        st.toast(f"✅ Saved '{content.get('grammar_point')}'!")

            elif block_type == "latex_equation" and isinstance(content, dict):
                with st.container(border=True):
                    equation_title = content.get("title", "Equation")
                    st.subheader(equation_title)
                    st.latex(content.get("equation", ""))
                    if content.get("explanation"):
                        # Use latex for explanation if it might contain math symbols
                        st.markdown(content.get("explanation", ""))
                    if st.button("Save to Knowledge Base", key=f"save_equation_{i}"):
                        # Format the equation and explanation for saving
                        full_definition = f"```latex\n{content.get('equation', '')}\n```\n\n**Explanation:**\n{content.get('explanation', '')}"
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
                        st.markdown(content.get("explanation", ""))
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

                special_instructions = plan_data['special_instructions'] if 'special_instructions' in plan_data.keys() else None
                instruction_prompt_part = ""
                if special_instructions:
                    instruction_prompt_part = f"""
                When answering, please also adhere to the following special instructions from the user regarding teaching style:
                ---
                {special_instructions}
                ---
                """

                original_material_json = json.dumps(learning_material, indent=2)
                full_prompt = f"""
                You are a helpful tutor. A student is studying the learning material below and has a request.

                **User's Request:** "{prompt}"

                **Current Learning Material (JSON):**
                ```json
                {original_material_json}
                ```

                **Your Task:**
                1.  Analyze the user's request.
                2.  If the request is a simple question that can be answered conversationally, respond with a JSON object like this:
                    `{{"action": "answer", "content": "Your conversational answer here."}}`
                3.  If the request implies a change to the learning material (e.g., "make it simpler", "add an example", "show this as a table"), you MUST regenerate the **entire** `learning_material` array and respond with a JSON object like this:
                    `{{"action": "regenerate", "content": {{"learning_material": [...]}}}}`
                    The regenerated content must follow the exact same structure as the original.
                4.  Your response must be ONLY the JSON object.
                5.  IMPORTANT: All backslashes `\` inside the JSON string values must be properly escaped (as `\\`).

                {instruction_prompt_part}
                """
                
                response_text = ai_manager.generate_content(full_prompt)
                if not response_text:
                    st.error("AI returned no response.")
                    st.session_state.learn_messages.append({"role": "assistant", "content": "AI returned no response."})
                else:
                    try:
                        cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
                        # A more robust way to handle backslashes for JSON parsing.
                        # This escapes backslashes that are not already part of a valid escape sequence.
                        import re
                        ai_response = json.loads(re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', cleaned_response))
                        action = ai_response.get("action")
                        content = ai_response.get("content")

                        if action == "regenerate" and "learning_material" in content:
                            st.session_state.learning_materials_cache[pid][current_day_task['day']] = content
                            st.session_state.learn_messages.append({"role": "assistant", "content": "I've updated the learning material on the left based on your request!"})
                            st.rerun()
                        else: # Default to "answer"
                            answer = content if isinstance(content, str) else content.get("answer", "I'm not sure how to respond to that.")
                            st.markdown(answer)
                            st.session_state.learn_messages.append({"role": "assistant", "content": answer})
                    except (json.JSONDecodeError, TypeError):
                        st.markdown(response_text) # Fallback for non-JSON response
                        st.session_state.learn_messages.append({"role": "assistant", "content": response_text})