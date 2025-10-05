import streamlit as st

st.set_page_config(page_title="Dashboard", layout="wide")
ss = st.session_state

# 沒登入就丟回去登入頁
if not ss.get("user"):
    st.warning("You are not logged in. Redirecting to login…")
    st.query_params.pop("view", None)
    st.rerun()

st.title("📊 Dashboard")
st.write(f"Welcome, **{ss['user'].get('name','User')}** ({ss['user'].get('email')})")

if st.button("Log out"):
    ss.user = None
    ss.oauth_state = None
    ss.code_verifier = None
    st.rerun()
