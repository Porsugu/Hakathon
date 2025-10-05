import os
import json
import base64
import hashlib
import secrets
import streamlit as st
import streamlit.components.v1 as components
import platform, subprocess, webbrowser
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
import requests

# ====== 設定 ======
st.set_page_config(page_title="Welcome", page_icon="👋", layout="centered")

GOOGLE_CLIENT_ID = st.secrets["google_oauth"]["CLIENT_ID"]
GOOGLE_CLIENT_SECRET = st.secrets["google_oauth"]["CLIENT_SECRET"]
REDIRECT_URI = st.secrets["google_oauth"]["REDIRECT_URI"]  # e.g. http://localhost:8501
AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"
SCOPES = ["openid", "email", "profile"]

# ====== 小工具：取得目前頁面（去除查詢參數）======
def current_base_url():
    # 使用你設定的 REDIRECT_URI；如需自動偵測也可用下面方式：
    # 但在某些部署環境取值不穩定，故建議 secrets 固定設定
    return REDIRECT_URI

# ====== 產生與檢查 PKCE ======
def create_pkce_pair():
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8").rstrip("=")
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge

# ====== 畫面樣式 ======
st.markdown("""
<style>
.title { text-align:center; font-size:90px; font-weight:800; line-height:1.1; }
.subtitle_1 { text-align:center; font-size:22px; margin-bottom:28px; }
.subtitle_2 { text-align:center; font-size:22px; color:#555; margin-bottom:28px; }
.card { max-width:640px; margin:0 auto; padding:24px 28px; border:1px solid #eee; border-radius:18px; box-shadow: 0 6px 24px rgba(0,0,0,.06); background:#fff; }
.btn { display:block; width:100%; padding:14px 18px; border-radius:12px; border:none; font-size:18px; font-weight:600; cursor:pointer; }
.google { background:#fff; border:1px solid #ddd; }
.logout { background:#ef4444; color:#fff; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">AI Tutor</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle_1">A tutor who is better than your college one.</div>', unsafe_allow_html=True)
st.divider()
st.markdown('<div class="subtitle_2">Sign up or log in</div>', unsafe_allow_html=True)

# ====== Session 初始化 ======
if "user" not in st.session_state:
    st.session_state.user = None

if "oauth_state" not in st.session_state:
    st.session_state.oauth_state = None

if "code_verifier" not in st.session_state:
    st.session_state.code_verifier = None

# ====== 如果 Google 回來時帶 code/state，先處理回調 ======
query_params = st.query_params  # Streamlit >= 1.30 推薦用法
code = query_params.get("code", None)
state = query_params.get("state", None)

def clear_query_params():
    st.query_params.clear()  # 清掉網址上的 code/state，避免重整重觸發

if code and state and st.session_state.oauth_state == state and st.session_state.code_verifier:
    # 交換 token
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "code_verifier": st.session_state.code_verifier,
        "grant_type": "authorization_code",
        "redirect_uri": current_base_url(),
    }
    token_resp = requests.post(TOKEN_ENDPOINT, data=data, timeout=10)
    if token_resp.ok:
        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        id_token = tokens.get("id_token")

        # 取使用者資料
        headers = {"Authorization": f"Bearer {access_token}"}
        u = requests.get(USERINFO_ENDPOINT, headers=headers, timeout=10)
        if u.ok:
            info = u.json()  # 包含 sub, email, name, picture 等
            st.session_state.user = {
                "email": info.get("email"),
                "name": info.get("name"),
                "picture": info.get("picture"),
                "sub": info.get("sub"),
            }
            clear_query_params()
            # 成功登入後切換視圖（單頁應用示例）
            st.session_state.post_login_view = "dashboard"
            st.rerun()

            # ====== 登入成功後自動切換視圖（單頁用 query param 控制） ======
            if st.session_state.get("post_login_view"):
                view = st.session_state.pop("post_login_view")
                st.query_params["view"] = view
                st.markdown("<script>window.location.reload();</script>", unsafe_allow_html=True)
                st.stop()

            # 視圖切換（例）
            view = st.query_params.get("view", "welcome")


        else:
            st.error("Fail to read the user info, please try again。")
    else:
        st.error("Fail to exchange the tokin, please try again。")
if st.session_state.get("pending_auth_url"):
    auth_url = st.session_state.pop("pending_auth_url")  # 取完就清除

    st.markdown(f"""
        <script>
        (function () {{
            var u = "{auth_url}";
            try {{
                if (window !== window.top) {{
                    // 若被嵌在 iframe，改導到最外層視窗
                    window.top.location.assign(u);
                }} else {{
                    window.location.assign(u);
                }}
            }} catch (e) {{
                window.location.href = u;
            }}
        }})();
        </script>
        <noscript><meta http-equiv="refresh" content="0; url={auth_url}"></noscript>
    """, unsafe_allow_html=True)
    st.stop()


def os_open(url: str) -> bool:
    try:
        os_name = platform.system()
        if os_name == "Windows":
            # Safest: let Windows shell handle the URL directly
            os.startfile(url)  # type: ignore[attr-defined]
            return True
        elif os_name == "Darwin":
            subprocess.run(["open", url], check=False)
            return True
        else:  # Linux
            subprocess.run(["xdg-open", url], check=False)
            return True
    except Exception:
        pass
    try:
        return webbrowser.open(url, new=1, autoraise=True)
    except Exception:
        return False


# ====== 未登入：顯示 Google 登入按鈕 ======
if not st.session_state.user:
    if st.button("🔐 Sign in with Google", use_container_width=True):
        code_verifier, code_challenge = create_pkce_pair()
        st.session_state.code_verifier = code_verifier
        st.session_state.oauth_state = secrets.token_urlsafe(16)

        auth_params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": current_base_url(),
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "state": st.session_state.oauth_state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "online",
            "prompt": "consent",
        }
        auth_url = f"{AUTH_ENDPOINT}?{urlencode(auth_params)}"

        # ✅ 本機自動開啟預設瀏覽器（不依賴前端腳本/iframe）
        ok = os_open(auth_url)
        if not ok:
            # 最後備援：提供可點擊的連結
            st.link_button("Continue to Google →", auth_url, use_container_width=True)

        st.stop()

    st.markdown('</div>', unsafe_allow_html=True)
    # 可保留一條備援連結（若 JS 被阻擋時使用）

# ====== 已登入：顯示使用者資訊與登出 ======
else:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1,3])
        with col1:
            if st.session_state.user.get("picture"):
                st.image(st.session_state.user["picture"], caption="", use_column_width=True)
        with col2:
            st.markdown(f"### 👤 {st.session_state.user.get('name','User')}")
            st.markdown(f"- **Email**: {st.session_state.user.get('email')}")
            st.success("Log in Success! MAMAMIA!")

        if st.button("Log in", use_container_width=True):
            st.session_state.user = None
            st.session_state.oauth_state = None
            st.session_state.code_verifier = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
