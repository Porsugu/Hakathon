# test_redirect.py
import streamlit as st
import webbrowser
import sys
import platform
import subprocess

st.set_page_config(page_title="Redirect MRE", layout="centered")
st.title("Redirect test (OS-level)")

def os_open(url: str) -> bool:
    """
    嘗試用最穩的 OS 指令開啟網址；若失敗再退回 webbrowser.open
    回傳 True 表示我們已要求系統開啟（通常會成功在預設瀏覽器開新分頁）
    """
    try:
        os_name = platform.system()
        if os_name == "Windows":
            # 使用 'start' 必須透過 shell
            subprocess.run(["cmd", "/c", "start", "", url], check=False)
            return True
        elif os_name == "Darwin":  # macOS
            subprocess.run(["open", url], check=False)
            return True
        else:  # Linux
            # 若有 xdg-open
            subprocess.run(["xdg-open", url], check=False)
            return True
    except Exception:
        pass

    try:
        return webbrowser.open(url, new=1, autoraise=True)
    except Exception:
        return False

col1, col2 = st.columns(2)
with col1:
    if st.button("→ Open example.com (auto)"):
        ok = os_open("https://example.com")
        if not ok:
            st.link_button("Fallback: click to open example.com", "https://example.com")
        st.stop()

with col2:
    if st.button("→ Open Google OAuth page (auto)"):
        ok = os_open("https://accounts.google.com/o/oauth2/v2/auth")
        if not ok:
            st.link_button("Fallback: click to open Google OAuth", "https://accounts.google.com/o/oauth2/v2/auth")
        st.stop()

st.info("這個測試使用 OS 層級開啟網址，不依賴 <script>/iframe/meta refresh。請確保是在本機執行。")
