import streamlit as st
from db_functions import get_knowledge_items_by_plan, get_plans_by_user, delete_knowledge_item
from utils import ensure_plan_selected

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
        [data-testid="stCodeBlock"], [data-testid="stLatex"] {
            background-color: #262730; /* A medium-dark grey */
            border-radius: 8px;
            padding: 1em;
        }
        
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Review Flashcards", layout="centered")

# --- Check for selected plan ---
pid = ensure_plan_selected()
uid = st.session_state.get('user_id', 1)

# --- Fetch Data ---
review_items = get_knowledge_items_by_plan(uid, pid)

# Fetch the plan name for the title
all_plans = get_plans_by_user(uid)
current_plan = next((plan for plan in all_plans if plan['pid'] == pid), None)
plan_name = current_plan['plan_name'] if current_plan else "your plan"

title_col, back_button_col = st.columns([0.8, 0.2])
with title_col:
    st.title(f"🧠 Review: {plan_name}")
with back_button_col:
    st.markdown('<div class="back-button-container">', unsafe_allow_html=True)
    if st.button("◀ Back", use_container_width=True):
        st.switch_page("pages/2_Plan_Details.py")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Handle No Items ---
if not review_items:
    st.info("You haven't saved any knowledge items for this plan yet.")
    st.write("Go to the 'Learn Today' section to start saving concepts!")
    st.page_link("pages/2_Plan_Details.py", label="Back to Plan Dashboard", icon="⬅️")
    st.stop()

# --- Initialize Session State for Flashcards ---
if 'review_index' not in st.session_state:
    st.session_state.review_index = 0
if 'card_flipped' not in st.session_state:
    st.session_state.card_flipped = False

# Reset if user navigates away and comes back to a different plan's review
if st.session_state.review_index >= len(review_items):
    st.session_state.review_index = 0

# --- Flashcard Display ---
total_cards = len(review_items)
current_index = st.session_state.review_index
current_item = review_items[current_index]

st.progress((current_index + 1) / total_cards, text=f"Card {current_index + 1} of {total_cards}")

with st.container(height=350, border=True):
    # Display the front of the card (the term)
    st.subheader(current_item['term'])
    st.divider()
    # Display the back of the card (the definition) if flipped
    if st.session_state.card_flipped:
        st.markdown(current_item['definition'])

# --- Control Buttons ---
col1, col2, col3, col4 = st.columns([1, 2, 1, 1])

with col1:
    if st.button("⬅️ Previous", use_container_width=True, disabled=current_index <= 0):
        st.session_state.review_index -= 1
        st.session_state.card_flipped = False # Reset flip state
        st.rerun()

with col2:
    if st.button("🔄 Flip Card", use_container_width=True, type="primary"):
        st.session_state.card_flipped = not st.session_state.card_flipped
        st.rerun()

with col3:
    if st.button("Next ➡️", use_container_width=True, disabled=current_index >= total_cards - 1):
        st.session_state.review_index += 1
        st.session_state.card_flipped = False # Reset flip state
        st.rerun()

with col4:
    if st.button("🗑️ Delete", use_container_width=True):
        delete_knowledge_item(current_item['item_id'])
        st.toast(f"Deleted '{current_item['term']}'")
        # After deleting, we don't increment the index, as the list will shorten
        # and the next item will shift into the current index.
        st.rerun()