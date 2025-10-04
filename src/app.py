# filepath: streamlit-welcome-app/src/app.py

import streamlit as st
from components.buttons import create_button

st.set_page_config(page_title="Welcome App", page_icon="👋", layout="centered")

#topic and introduction
st.title("Welcome to the AI tutorial!")
st.subheader("This teacher will better than your colledge one.")

st.write("""
This is a simple Streamlit app that demonstrates how to create a welcome page with a button.    
Click the button below to get started!!!
""")

if create_button("Get Started"):
    st.write("Let's get started with the tutorial!")

st.divider()
st.write("Here is something")