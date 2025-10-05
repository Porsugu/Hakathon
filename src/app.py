import streamlit as st

st.set_page_config(page_title="AI tutor", page_icon="🎓",layout="centered")


# --- CSS 樣式調整 ---
st.markdown(
    """
    <style>
    /* 讓標題置中 */
    .title {
        text-align: center;
        font-size: 8vw;
        font-weight: 600;
        font-family: "Kode Mono", monospace;
    }
    .subtitle {
        text-align: center;
        font-size: 22px;
        color: #555555;
        margin-bottom: 30px;
        font-family: "Kode Mono", monospace;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 12px;
        height: 50px;
        font-size: 20px;
        margin: auto;
        display: block;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Welcoming Section ---
st.markdown('<h1 class="title">👋 Welcome to AI Tutor</h1>', unsafe_allow_html=True)
st.markdown('<h6 class="subtitle">A teacher better than your colledge one.</h6>', unsafe_allow_html=True)

# --- 按鈕 ---
if st.button("Get Started 🚀"):
    st.success("Welcome! Let’s start exploring the app 🎉")

# --- 分隔線 & 說明 ---
# st.markdown("---")
# st.info("💡 你可以在這裡放入一些簡單的介紹、使用說明或連結。")