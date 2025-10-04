import streamlit as st
import sqlite3
from db_functions import add_plan

# Set up the page
st.set_page_config(page_title="Add Learning Plan", layout="wide")

# Connect to the database
def get_db_connection():
    conn = sqlite3.connect('learning_os.db')
    conn.row_factory = sqlite3.Row
    return conn

# Main content
st.title("Add a New Learning Plan")

# Input fields
learning_target = st.text_input("Learning Target", placeholder="Enter your learning goal")
learning_time = st.number_input("Learning Time (in days)", min_value=1, step=1)

# Add Plan button
if st.button("Submit"):
    if learning_target and learning_time:
        # Fetch user ID (for demonstration purposes, using a static user ID)
        uid = 1  # Replace with dynamic user authentication in production

        # Prepare daily content as a placeholder (can be updated later)
        daily_content = f"Target: {learning_target}, Time: {learning_time} days"

        # Add the plan to the database
        add_plan(uid, learning_target, daily_content)

        st.success("Learning plan added successfully!")
    else:
        st.error("Please fill in all fields.")