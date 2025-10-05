import os
import json
import base64
import hashlib
import secrets
import streamlit as st
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
.title { text-align:center; font-size:72px; font-weight:800; line-height:1.1; }
.subtitle { text-align:center; font-size:22px; color:#555; margin-bottom:28px; }
.card { max-width:640px; margin:0 auto; padding:24px 28px; border:1px solid #eee; border-radius:18px; box-shadow: 0 6px 24px rgba(0,0,0,.06); background:#fff; }
.btn { display:block; width:100%; padding:14px 18px; border-radius:12px; border:none; font-size:18px; font-weight:600; cursor:pointer; }
.google { background:#fff; border:1px solid #ddd; }
.logout { background:#ef4444; color:#fff; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">👋 Welcome</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Sign in to continue</div>', unsafe_allow_html=True)

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
        else:
            st.error("讀取使用者資料失敗")
    else:
        st.error("Token 交換失敗，請重試。")

# ====== 未登入：顯示 Google 登入按鈕 ======
if not st.session_state.user:
    st.markdown('<div class="card">', unsafe_allow_html=True)

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
            "prompt": "consent",  # 開發中可強制顯示授權畫面
        }
        auth_url = f"{AUTH_ENDPOINT}?{urlencode(auth_params)}"
        st.markdown(f"[前往 Google 登入]({auth_url})")
        st.info("若沒有自動跳轉，請點上方連結完成登入。")

    st.markdown('</div>', unsafe_allow_html=True)

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
            st.success("已登入！你可以在這裡顯示主功能。")

        if st.button("登出", use_container_width=True):
            st.session_state.user = None
            st.session_state.oauth_state = None
            st.session_state.code_verifier = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
