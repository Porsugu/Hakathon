import streamlit as st
from db_functions import get_knowledge_items_by_plan, get_plans_by_user, add_knowledge_item
from utils import ensure_plan_selected
import re
import google.generativeai as genai
import json

st.markdown("""
    <style>
        /* General background and text */
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

        /* Progress bar */
        [data-testid="stProgress"] > div > div {
            background-color: #0078ff !important;
        }
            
        /* Remove background from progress bar label */
        [data-testid="stProgress"] [data-testid="stMarkdownContainer"] {
            background: transparent !important;
        }

        /* Containers */
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
            background-color: #1a1d23;
            border: 1px solid #2e3440;
            border-radius: 12px;
            padding: 1em;
            margin-bottom: 1em;
        }
            
        section[data-testid="stSidebar"] .stAlert {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }

        section[data-testid="stSidebar"] .stAlert p {
            color: #f5f5f5 !important;
        }
        
        div.stAlert {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }

        div.stAlert p {
            color: #f5f5f5 !important;
        }
            
        header[data-testid="stHeader"] {
            background-color: #0e1117 !important; 
            color: #f5f5f5 !important;           
        }

        header[data-testid="stHeader"] .css-1v0mbdj {
            color: #f5f5f5 !important;
        }

        header[data-testid="stHeader"] {
            box-shadow: none !important;
        }

        /* Make the container for the back button invisible */
        .back-button-container > div {
            background-color: transparent !important;
            border: none !important;
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

title_col, back_button_col = st.columns([0.8, 0.2])
with title_col:
    st.title(f"❓ Ask about: {plan_name}")
with back_button_col:
    st.markdown('<div class="back-button-container">', unsafe_allow_html=True)
    if st.button("◀ Back", use_container_width=True):
        st.switch_page("pages/2_Plan_Details.py")
    st.markdown('</div>', unsafe_allow_html=True)

st.info("Ask any question related to your learning plan. If it's an important concept, you'll be able to save it to your knowledge base.", icon="💡")

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
            
            # Use the same rendering logic as the Review page
            item_type = item.get('item_type', 'concept') # Default to concept
            definition_text = item['definition']

            if item_type == 'equation':
                match = re.search(r"```latex\n(.*?)\n```\n\n\*\*Explanation:\*\*\n(.*)", definition_text, re.DOTALL)
                if match:
                    st.latex(match.group(1))
                    st.markdown(match.group(2))
                else:
                    st.markdown(definition_text) # Fallback
            elif item_type == 'code':
                match = re.search(r"```.*?\n(.*?)```\n\n\*\*Explanation:\*\*\n(.*)", definition_text, re.DOTALL)
                if match:
                    st.code(match.group(1))
                    st.markdown(match.group(2))
                else:
                    st.markdown(definition_text) # Fallback
            elif item_type == 'vocabulary':
                # The definition is already a formatted markdown string
                st.markdown(definition_text)
            elif item_type == 'grammar':
                # The definition is already a formatted markdown string
                st.markdown(definition_text)
            elif item_type == 'table':
                # The definition is a markdown table string
                st.markdown(definition_text)
            elif item_type in ['concept', 'theorem']:
                # These are also markdown strings
                st.markdown(definition_text)
            
            if st.button("Add to Knowledge Base", use_container_width=True):
                # The definition is already formatted correctly when placed on the blackboard
                # The 'item_type' is also preserved
                add_knowledge_item(uid, pid, item_type, item['term'], definition_text)
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
                def format_knowledge_for_ai(items):
                    """Formats knowledge items into a readable string for the AI context."""
                    formatted_items = []
                    for item in items:
                        term = item['term']
                        definition = item['definition']
                        item_type = item['item_type']
                        if item_type == 'equation':
                            match = re.search(r"```latex\n(.*?)\n```\n\n\*\*Explanation:\*\*\n(.*)", definition, re.DOTALL)
                            if match:
                                definition = f"Equation: {match.group(1).strip()}. Explanation: {match.group(2).strip()}"
                        elif item_type == 'code':
                            definition = re.sub(r"```.*?\n", "", definition).replace("```", "")
                        formatted_items.append(f"- {term}: {definition}")
                    return "\n".join(formatted_items)
                # Build context from saved knowledge
                knowledge_context = format_knowledge_for_ai(knowledge_items)
                
                special_instructions = current_plan['special_instructions'] if current_plan and 'special_instructions' in current_plan.keys() else None
                instruction_prompt_part = ""
                if special_instructions:
                    instruction_prompt_part = f"""Please also consider the user's general instructions for this plan:
                    ---
                    {special_instructions}
                    ---
                    """

                # Construct a detailed prompt for the AI
                full_prompt = f"""
                You are a helpful tutor for a student learning about '{plan_name}'.
                The user's question is: "{prompt}"

                First, decide if the question is related to '{plan_name}'.
                - If it is NOT related, respond with a conversational message explaining you can only answer questions about the topic.

                - If it IS related, decide if the answer is a distinct, important "knowledge point".
                    - If it IS a knowledge point, you MUST respond with ONLY a single JSON object with `{{"is_knowledge_point": true, "data": ...}}`.
                    - The "data" object MUST contain a "term", "definition", and "item_type".
                    
                    - Use "item_type": "vocabulary" for a single word. The "term" is the word, and the "definition" MUST be a markdown string formatted like this:
                      `**Part of speech:** ...\\n\\n**Meaning:** ...\\n\\n**Example:** ...`
                      
                    - Use "item_type": "grammar" for a grammar rule. The "term" is the rule name, and the "definition" MUST be a markdown string formatted like this:
                      `**Rule of use:** ...\\n\\n**Meaning:** ...\\n\\n**Example:** ...`

                    - Use "item_type": "equation" for formulas. The "term" is the equation name, and the "definition" MUST be a markdown string formatted like this:
                      `"```latex\\n[LATEX_HERE]\\n```\\n\\n**Explanation:**\\n[EXPLANATION_HERE]"`

                    - Use "item_type": "code" for code snippets. The "term" is the snippet title, and the "definition" MUST be a markdown string formatted like this:
                      `"```[LANG]\\n[CODE_HERE]\\n```\\n\\n**Explanation:**\\n[EXPLANATION_HERE]"`

                    - For any other general concept, use "item_type": "concept". The "definition" is a simple markdown string.

                - If the question requires a general explanation (not a dictionary-style entry), you MUST respond with ONLY a single JSON object with this structure:
                  `{{"is_knowledge_point": false, "data": {{"answer": "Your conversational answer here."}}}}`

                {instruction_prompt_part}

                Here is some context of what the user has already saved:
                ---
                {knowledge_context}
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

                    if is_knowledge and "term" in data and "definition" in data and "item_type" in data:
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