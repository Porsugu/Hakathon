import streamlit as st

# setting icon
st.set_page_config(page_title="Welcome", page_icon="👋", layout="centered")

st.title("👋 AI tutorial")
st.subheader("Better than your college one.")

st.write(
    """
    welcome to my website. This is a simple welcome page created with Streamlit.
    """
)

# add button
if st.button("start exploring"):
    st.success("button is clicked")

st.divider()

st.info("info")
