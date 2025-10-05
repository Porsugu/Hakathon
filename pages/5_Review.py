import streamlit as st
from db_functions import get_knowledge_items_by_plan, get_plans_by_user, delete_knowledge_item
from utils import ensure_plan_selected

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

st.title(f"🧠 Review: {plan_name}")

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

st.divider()
st.page_link("pages/2_Plan_Details.py", label="Back to Plan Dashboard", icon="⬅️")