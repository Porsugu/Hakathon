import os, json, base64, hashlib, secrets, requests
import streamlit as st
import platform, subprocess, webbrowser
from urllib.parse import urlencode
from db_functions import upsert_user

# ================== 基本設定 ==================
st.set_page_config(page_title="Welcome", page_icon="👋", layout="centered")

# 打開除錯模式時，會「停用」自動跳轉與 st.stop()，讓你看得到 DEBUG
DEBUG_OAUTH = False   # ◎ 除錯時 True；完成後改成 False

GOOGLE_CLIENT_ID = st.secrets["google_oauth"]["CLIENT_ID"]
GOOGLE_CLIENT_SECRET = st.secrets["google_oauth"]["CLIENT_SECRET"]
REDIRECT_URI = st.secrets["google_oauth"]["REDIRECT_URI"]  # 必須與 Google Console 完全一致
AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"
SCOPES = ["openid", "email", "profile"]

def current_base_url():
    return REDIRECT_URI

def create_pkce_pair():
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8").rstrip("=")
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge

# 伺服端暫存：用 state 把 code_verifier 存起來，避免回調後 session 遺失
@st.cache_resource
def state_store():
    return {}  # {state: {"cv": code_verifier, "ts": epoch_seconds}}

# ================== 樣式 ==================
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

# ================== Session 初始化 ==================
ss = st.session_state
if "user" not in ss:
    ss.user = None
   
# 之後就可以安全地使用
if not ss.user:
    st.write("User")
else:
    st.write(f"歡迎回來，{ss.user}")

# --- Fallback Router ---
if ss.get("user") and not DEBUG_OAUTH:
    if st.query_params.get("view") == "main":
        try:
            st.switch_page("main.py")
        except Exception:
            st.write("Routing to Main page")
            st.stop()

def clear_query_params():
    st.query_params.clear()

# ================== Sidebar Debug（永遠可見） ==================
with st.sidebar:
    st.subheader("🔎 Auth Debug")
    st.write("Login status:", "✅ Logged in" if ss.get("user") else "❌ Not logged in")
    st.caption("redirect_uri used:")
    st.code(current_base_url())
    st.caption("Query params")
    st.json(dict(st.query_params))
    st.caption("Session snapshot")
    st.json({
        "oauth_state": ss.get("oauth_state"),
        "has_code_verifier": bool(ss.get("code_verifier")),
        "has_user": bool(ss.get("user")),
    })

# ================== Google 回調處理 ==================
query = st.query_params
code = query.get("code")
state = query.get("state")

if code and state:
    st.info("DEBUG: Received code/state from Google.")

    # 從 state_store 取回 code_verifier（優先），若沒有再用 session 的備援
    store = state_store()
    entry = store.pop(state, None)
    cv = (entry or {}).get("cv") or ss.get("code_verifier")

    # 也檢查 state 是否對得上（用 session 版本作輔助）
    state_ok = (ss.get("oauth_state") == state) or (entry is not None)

    st.write("DEBUG oauth_state(check):", ss.get("oauth_state"))
    st.write("DEBUG state_ok:", state_ok)
    st.write("DEBUG has_code_verifier:", bool(cv))

    if not state_ok or not cv:
        st.error("State 或 code_verifier 不存在（可能是回調後 session 遺失）。請重新登入。")
    else:
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "code_verifier": cv,
            "grant_type": "authorization_code",
            "redirect_uri": current_base_url(),
        }
        token_resp = requests.post(TOKEN_ENDPOINT, data=data, timeout=10)

        st.write("DEBUG token_status:", token_resp.status_code)
        st.code(token_resp.text[:800])

        if token_resp.ok:
            tokens = token_resp.json()
            access_token = tokens.get("access_token")
            id_token = tokens.get("id_token")
            st.write("DEBUG tokens keys:", list(tokens.keys()))

            u = requests.get(USERINFO_ENDPOINT, headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
            st.write("DEBUG userinfo_status:", u.status_code)
            st.code(u.text[:500])

            info = None
            if u.ok:
                info = u.json()
                
            else:
                # 備援：從 id_token 取基本資料（不驗簽，僅除錯用）
                try:
                    def decode_jwt_noverify(jwt_str):
                        p = jwt_str.split(".")
                        import base64, json
                        return json.loads(base64.urlsafe_b64decode(p[1] + "=="))
                    claims = decode_jwt_noverify(id_token) if id_token else None
                    if claims:
                        info = {
                            "sub": claims.get("sub"),
                            "email": claims.get("email"),
                            "name": claims.get("name") or claims.get("given_name"),
                            "picture": claims.get("picture"),
                        }
                except Exception:
                    pass

            if info and info.get("sub"):
                # 1. first upsert the google yser to DB, getting uid (=Google sub)
                try:
                    uid = upsert_user(info)
                except Exception as e:
                    st.error(f"Database error in writting user: {e}")
                    st.stop()
                
                # 2. setting session : let all the pages could use uid to check the info
                ss["uid"] = uid
                ss["user_info"] = info
                ss.user = {
                    "id": f"google:{info.get('sub')}",
                    "sub": info.get("sub"),
                    "email": info.get("email"),
                    "name": info.get("name"),
                    "picture": info.get("picture"),
                }
                # 清掉一次性資料 & 查詢參數
                ss.oauth_state = None
                ss.code_verifier = None
                if not DEBUG_OAUTH:
                    clear_query_params()
                st.success("✅ Login success, user stored in session_state.")

                # 登入後導頁（DEBUG 時不跳轉）
                if not DEBUG_OAUTH:
                    try:
                        st.switch_page("main.py")
                    except Exception:
                        st.query_params["view"] = "main"
                        # st.markdown("<script>window.location.reload()</script>", unsafe_allow_html=True)
                        st.rerun()
            else:
                st.error("取得使用者資訊失敗（access_token 或 id_token 無效）。")
        else:
            st.error("Token 交換失敗（請檢查 redirect_uri 是否與 Console 完全一致、或 code 是否已被使用）。")

# ================== 開啟 Google 登入 ==================
def os_open(url: str) -> bool:
    try:
        os_name = platform.system()
        if os_name == "Windows":
            os.startfile(url)  # type: ignore[attr-defined]
            return True
        elif os_name == "Darwin":
            subprocess.run(["open", url], check=False)
            return True
        else:
            subprocess.run(["xdg-open", url], check=False)
            return True
    except Exception:
        pass
    try:
        return webbrowser.open(url, new=1, autoraise=True)
    except Exception:
        return False

if not ss.user:
    if st.button("🔐 Sign in with Google", use_container_width=True):
        code_verifier, code_challenge = create_pkce_pair()
        ss.code_verifier = code_verifier
        state = secrets.token_urlsafe(16)
        ss.oauth_state = state

        # 同時寫入伺服端暫存，預防 session 在回調時遺失
        store = state_store()
        store[state] = {"cv": code_verifier}

        auth_params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": current_base_url(),
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "online",
            "prompt": "consent",
        }
        auth_url = f"{AUTH_ENDPOINT}?{urlencode(auth_params)}"

        st.write("DEBUG auth_url:", auth_url)
        if not DEBUG_OAUTH:
            ok = os_open(auth_url)
            if not ok:
                st.link_button("Continue to Google →", auth_url, use_container_width=True)
            st.stop()
        else:
            st.info("DEBUG_OAUTH=True，不自動跳轉。請手動點下面按鈕前往 Google：")
            st.link_button("Continue to Google →", auth_url, use_container_width=True)

# ================== 已登入畫面 ==================
else:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1,3])
        with col1:
            if ss.user.get("picture"):
                st.image(ss.user["picture"], caption="", use_column_width=True)
        with col2:
            st.markdown(f"### 👤 {ss.user.get('name','User')}")
            st.markdown(f"- **Email**: {ss.user.get('email')}")
            st.markdown(f"- **User ID**: `{ss.user.get('id')}`")
            st.success("Log in Success!")

        if st.button("Log out", use_container_width=True):
            ss.user = None
            ss.oauth_state = None
            ss.code_verifier = None
            if not DEBUG_OAUTH:
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
