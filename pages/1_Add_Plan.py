import streamlit as st
import sqlite3
from db_functions import add_plan

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
        
    </style>
""", unsafe_allow_html=True)

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