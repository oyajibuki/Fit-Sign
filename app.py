import streamlit as st
import streamlit.components.v1 as components
import uuid
import qrcode
from io import BytesIO
import base64
from db import (
    init_db,
    get_or_create_user,
    get_user,
    get_templates,
    create_contract,
    get_contract,
    sign_contract,
    reject_contract,
    get_user_contracts,
    delete_draft_contract,
    save_user_profile,
    get_google_auth_url,
    get_line_auth_url,
    exchange_code_for_session,
    sign_out,
)
from pdf_gen import generate_pdf

st.set_page_config(
    page_title="Fit-Sign | 30秒で契約できる",
    page_icon="✍️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@500;700&display=swap');
html, body, [class*="css"] { font-family:'Inter', sans-serif; background:#F8FAFC !important; }
.stApp { background:#F8FAFC !important; }
.main > div { padding-top:0 !important; background:#F8FAFC; }
section[data-testid="stSidebar"] { display:none; }
#MainMenu, footer, header { visibility:hidden; }
.block-container { padding:0 1rem 5rem !important; max-width:540px !important; }

/* Nav */
.fs-nav { display:flex; align-items:center; justify-content:space-between; padding:16px 0 14px; margin-bottom:16px; border-bottom: 1px solid #F1F5F9; }
.fs-logo { font-family:'Space Grotesk',sans-serif; font-size:24px; font-weight:800; color:#0F172A; letter-spacing: -0.02em; }
.fs-logo span { color:#17C080; }
.fs-chip { background:#F1F5F9; border-radius:20px; padding:6px 14px; font-size:12px; color:#475569; font-weight:700; display:flex; align-items:center; gap:6px; }

/* Hero */
.fs-hero { text-align:center; padding:32px 0 24px; }
.fs-hero h1 { font-family:'Inter',sans-serif; font-size:36px; font-weight:900; color:#0F172A; letter-spacing:-0.04em; line-height:1.1; margin:0 0 12px; }
.fs-hero h1 span { color:#17C080; }
.fs-hero p { font-size:15px; color:#64748B; margin:0; font-weight: 500; }

/* Card */
.fs-card { background:white; border-radius:24px; padding:24px; margin-bottom:20px; box-shadow:0 4px 20px rgba(15, 23, 42, 0.04); border: 1px solid #F1F5F9; }

/* Steps */
.fs-steps { background:white; border-radius:24px; padding:24px; box-shadow:0 4px 20px rgba(15, 23, 42, 0.04); border: 1px solid #F1F5F9; }
.step-item { display:flex; align-items:center; gap:16px; padding:12px 0; border-bottom:1px solid #F8FAFC; }
.step-item:last-child { border-bottom:none; }
.step-num { width:34px; height:34px; background:#17C080; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:14px; font-weight:800; flex-shrink:0; }
.step-text { font-size:14px; color:#475569; font-weight: 500; }

/* Template card */
.tmpl-card { background:white; border-radius:20px; padding:20px; margin-bottom:14px; display:flex; align-items:center; gap:16px; box-shadow:0 2px 8px rgba(0,0,0,0.04); border:2.5px solid #F1F5F9; min-height:86px; transition:all .2s; }
.tmpl-card.selected { border-color:#17C080; background:#ECFDF5; }

/* Badges */
.badge-signed { background:#D1FAE5; color:#065F46; font-size:11px; font-weight:800; padding:4px 12px; border-radius:20px; text-transform: uppercase; letter-spacing: 0.05em; }
.badge-draft { background:#FEF3C7; color:#92400E; font-size:11px; font-weight:800; padding:4px 12px; border-radius:20px; text-transform: uppercase; letter-spacing: 0.05em; }
.badge-rejected { background:#FEE2E2; color:#991B1B; font-size:11px; font-weight:800; padding:4px 12px; border-radius:20px; text-transform: uppercase; letter-spacing: 0.05em; }

/* Contract body */
.contract-body { background:#F8FAFC; border-radius:16px; padding:24px; font-family: 'Hiragino Mincho ProN', Georgia, serif; font-size:15px; line-height:1.9; white-space:pre-wrap; color:#1E293B; border:1px solid #E2E8F0; margin:20px 0; }

/* QR */
.qr-box { background:white; border-radius:28px; padding:40px; text-align:center; box-shadow:0 10px 40px rgba(0,0,0,0.06); margin:20px 0; border: 1px solid #F1F5F9; }

/* State */
.state-success { background:#ECFDF5; border-radius:24px; padding:40px; text-align:center; margin:24px 0; border: 1px solid #D1FAE5; }
.state-success h2 { font-size:24px; color:#065F46; font-weight: 800; margin:0 0 8px; }
.state-success p { font-size:14px; color:#047857; margin:0; font-weight: 500; }
.state-rejected { background:#FEF2F2; border-radius:24px; padding:40px; text-align:center; margin:24px 0; border: 1px solid #FEE2E2; }
.state-rejected h2 { font-size:24px; color:#991B1B; font-weight: 800; margin:0 0 8px; }
.state-rejected p { font-size:14px; color:#B91C1C; margin:0; font-weight: 500; }

/* Limit bar */
.limit-bar-wrap { margin:16px 0; }
.limit-label { font-size:13px; color:#64748B; margin-bottom:8px; display:flex; justify-content:space-between; font-weight: 600; }
.limit-bar { height:8px; background:#F1F5F9; border-radius:4px; overflow:hidden; }
.limit-fill { height:100%; background:#17C080; border-radius:4px; }
.limit-fill.warn { background:#F59E0B; }
.limit-fill.full { background:#EF4444; }

/* Plan */
.plan-free { background:#F1F5F9; color:#475569; font-size:11px; font-weight:800; padding:3px 10px; border-radius:20px; }
.plan-paid { background:#17C080; color:white; font-size:11px; font-weight:800; padding:3px 10px; border-radius:20px; }

/* Sep */
.fs-sep { border:none; border-top:1.5px solid #F1F5F9; margin:24px 0; }

/* Upgrade */
.upgrade-cta { background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%); border-radius:24px; padding:32px; color:white; text-align:center; margin:20px 0; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.2); }

/* Contract list card */
.contract-list-card { background:white; border-radius:20px; padding:20px; margin-bottom:16px; box-shadow:0 4px 12px rgba(0,0,0,0.03); border: 1px solid #F1F5F9; }

/* Buttons */
div.stButton > button {
    width:100%; border-radius:20px !important; font-weight:800 !important;
    font-family:'Inter', sans-serif !important; font-size:14px !important;
    padding:14px 8px !important; border:none !important;
    transition:all .25s cubic-bezier(0.2, 1, 0.3, 1) !important; white-space:normal !important;
    word-break:keep-all !important; overflow-wrap:break-word !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -1px rgba(0, 0, 0, 0.04);
}
div.stButton > button:first-child { background:#1E293B !important; color:white !important; }
div.stButton > button:first-child:hover { background:#0F172A !important; transform:translateY(-2px) !important; box-shadow:0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important; }
div.stButton > button:active { transform: translateY(0px) !important; }

/* Large Primary Button */
div.stButton > button[kind="primary"] {
    background:#17C080 !important; color:white !important;
    font-size: 20px !important; padding: 22px 16px !important; border-radius: 24px !important;
    box-shadow: 0 10px 25px rgba(23, 192, 128, 0.25) !important;
}
div.stButton > button[kind="primary"]:hover {
    background:#129A66 !important; transform:translateY(-4px) !important;
    box-shadow: 0 15px 35px rgba(23, 192, 128, 0.35) !important;
}

/* Inputs */
div.stTextInput > div > div > input,
div.stTextArea > div > div > textarea {
    border-radius:16px !important; border:2px solid #F1F5F9 !important;
    font-family:'Inter', sans-serif !important; background:#F8FAFC !important;
    padding: 12px 16px !important;
}
div.stTextInput > div > div > input:focus,
div.stTextArea > div > div > textarea:focus {
    border-color:#17C080 !important; box-shadow:0 0 0 4px rgba(23, 192, 128, 0.1) !important; background:white !important;
}
div.stInfo, div.stSuccess, div.stWarning, div.stError { border-radius:16px !important; padding: 18px !important; font-weight: 500; }

/* Swipe transition overlays */
.page-transition-enter { animation: slideInRight .25s cubic-bezier(.22,.61,.36,1); }
.page-transition-exit  { animation: slideOutLeft .25s cubic-bezier(.22,.61,.36,1); }
@keyframes slideInRight { from { transform:translateX(100vw); opacity:0; } to { transform:translateX(0); opacity:1; } }
@keyframes slideOutLeft { from { transform:translateX(0); opacity:1; } to { transform:translateX(-100vw); opacity:0; } }

</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Init
# ──────────────────────────────────────────────
init_db()

LIMIT_FREE = 3
LIMIT_PAID = 100


def get_base_url():
    # secrets の BASE_URL を最優先（session_state にキャッシュしない）
    try:
        return st.secrets["BASE_URL"]
    except (KeyError, Exception):
        pass
    # fallback: Host ヘッダーから推測
    try:
        host = st.context.headers.get("Host", "localhost:8501")
        proto = "https" if "streamlit.app" in host else "http"
        return f"{proto}://{host}"
    except Exception:
        return "http://localhost:8501"


def get_user_id():
    return st.session_state.get("user_id")


def page_login():
    """Googleログインページ"""
    st.markdown("""
<div style="min-height:80vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px;">
  <div style="font-size:56px;margin-bottom:16px;">✍️</div>
  <div style="font-family:'Inter',sans-serif;font-size:32px;font-weight:900;color:#0F172A;letter-spacing:-0.04em;margin-bottom:8px;">
    Fit<span style="color:#17C080">Sign</span>
  </div>
  <div style="font-size:15px;color:#64748B;margin-bottom:40px;text-align:center;">
    30秒で契約できる、シンプルな電子署名サービス
  </div>
</div>
""", unsafe_allow_html=True)

    # エラーが session_state に残っていれば表示
    if "oauth_error" in st.session_state:
        err = st.session_state.pop("oauth_error")
        st.error(f"ログインエラー: {err}")

    # auth URL は session ごとに1度だけ生成する（rerun のたびに上書きすると PKCE ミスマッチになる）
    if "auth_urls_v3" not in st.session_state:
        rt = get_base_url()
        st.session_state["auth_urls_v3"] = {
            "google": get_google_auth_url(rt),
            "line": get_line_auth_url(rt)
        }
    urls = st.session_state["auth_urls_v3"]

    # 同一タブ遷移を確実にするため、JavaScript による window.top.location 遷移を行う
    st.markdown(f"""
<div style="display:flex;flex-direction:column;align-items:center;gap:16px;margin-top:-80px;">
  <!-- LINE Login -->
  <button onclick="window.top.location.href='{urls['line']}'" 
          style="display:flex;align-items:center;justify-content:center;gap:12px;background:#06C755;
                 border:none;border-radius:16px;padding:12px;font-size:15px;font-weight:700;color:white;
                 box-shadow:0 4px 12px rgba(6,199,85,0.25);cursor:pointer;width:240px;height:48px;">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
      <path d="M24 10.304c0-4.505-5.383-8.17-12-8.17s-12 3.665-12 8.17c0 4.035 4.27 7.42 10.04 8.045.39.085.92.258 1.05.592.12.308.08.79.04 1.103l-.17 1.034c-.05.313-.25 1.225 1.07.67 1.32-.555 7.14-4.2 9.74-7.19 1.48-1.78 2.23-3.04 2.23-4.299zM8.38 13.111h-3.48c-.28 0-.52-.24-.52-.52v-5.18c0-.28.24-.52.52-.52.28 0 .52.24.52.52v4.66h2.96c.28 0 .52.24.52.52 0 .28-.24.52-.52.52zm3.32-5.7c0-.28-.24-.52-.52-.52s-.52.24-.52.52v5.18c0 .28.24.52.52.52.28 0 .52-.24.52-.52v-5.18zm4.84 5.18c0 .22-.16.42-.4.49-.04.01-.08.01-.12.01-.18 0-.34-.1-.44-.24l-2.42-3.1v2.84c0 .28-.24.52-.52.52-.28 0-.52-.24-.52-.52v-5.18c0-.22.16-.42.4-.49.04-.01.08-.01.12-.01.18 0 .34.1.44.24l2.42 3.1v-2.84c0-.28.24-.52.52-.52s.52.24.52.52v5.18zm3.9-2.22h-2.12v1.7h2.12c.28 0 .52.24.52.52s-.24.52-.52.52h-2.64c-.28 0-.52-.24-.52-.52v-5.18c0-.28.24-.52.52-.52h2.64c.28 0 .52.24.52.52s-.24.52-.52.52h-2.12v1.44h2.12c.28 0 .52.24.52.52s-.24.52-.52.52z"/>
    </svg>
    LINEでログイン
  </button>

  <!-- Google Login -->
  <button onclick="window.top.location.href='{urls['google']}'" 
          style="display:flex;align-items:center;justify-content:center;gap:12px;background:white;border:2px solid #E2E8F0;
                 border-radius:16px;padding:12px;font-size:15px;font-weight:700;color:#1A1A2E;
                 box-shadow:0 4px 12px rgba(0,0,0,0.08);cursor:pointer;width:240px;height:48px;">
    <svg width="20" height="20" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
    Googleでログイン
  </button>
</div>
""", unsafe_allow_html=True)


def generate_qr(url: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=8, border=3)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1A1A2E", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def render_nav(user=None):
    plan_html = ""
    if user:
        if user["plan"] == "paid":
            plan_html = '<span class="plan-paid">有料</span>'
        else:
            count = user["contract_count"]
            limit = LIMIT_FREE if user["plan"] == "free" else LIMIT_PAID
            plan_html = f'<span class="plan-free">無料 {count}/{limit}</span>'
    name_html = ""
    if user and user.get("display_name"):
        name_html = f'<div class="fs-chip">👤 {user["display_name"]}</div>'
    st.markdown(
        f'<div class="fs-nav"><div class="fs-logo">Fit<span>Sign</span></div>'
        f'<div style="display:flex;align-items:center;gap:12px;">{name_html}{plan_html}</div></div>',
        unsafe_allow_html=True,
    )
    # ログアウトボタン
    col_spacer, col_btn = st.columns([8, 2])
    with col_btn:
        if st.button("ログアウト", key="logout_btn", use_container_width=True):
            sign_out()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def render_limit_bar(user):
    limit = LIMIT_FREE if user["plan"] == "free" else LIMIT_PAID
    count = user["contract_count"]
    pct = min(count / limit * 100, 100)
    cls = "full" if pct >= 100 else "warn" if pct >= 70 else ""
    st.markdown(
        f'<div class="limit-bar-wrap">'
        f'<div class="limit-label"><span>契約件数</span><span>{count} / {limit}</span></div>'
        f'<div class="limit-bar"><div class="limit-fill {cls}" style="width:{pct}%"></div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# Single Drum Picker – 0〜100万 円 (より分かりやすく)
# ──────────────────────────────────────────────
AMOUNT_OPTIONS = [
    "3,000円", "5,000円", "1万円", "3万円", "5万円", 
    "10万円", "30万円", "50万円", "100万円", "任意入力（手入力）"
]

CONTENT_OPTIONS_BY_TEMPLATE = {
    "業務委託": [
        "システム保守・運用サポート",
        "SNS運用代行・コンサルティング",
        "プログラミング講師・指導",
        "イベント企画・運営補助",
        "任意入力（手入力）",
    ],
    "単発": [
        "ウェブサイトのデザイン制作",
        "ロゴ・バナー作成",
        "動画編集・映像制作",
        "ライティング・文章執筆",
        "システム開発",
        "写真撮影・レタッチ",
        "任意入力（手入力）",
    ],
    "同意_ビジネス": [
        "秘密保持に関する同意（NDA）",
        "肖像権・著作権の使用許諾",
        "単発の軽微な作業合意",
        "トラブル時の免責同意",
        "任意入力（手入力）",
    ],
    "同意_プライベート": [
        "プライベートな関係に関する合意",
        "密室での面会・交際に関する合意",
        "宿泊を伴う旅行の合意",
        "トラブル時の免責同意",
        "任意入力（手入力）",
    ],
}



def amount_drum(default_index: int = 0) -> str:
    """Render single iOS-style drum for amount. Returns selected label."""
    key = "amount_drum_idx"
    if key not in st.session_state:
        st.session_state[key] = default_index

    opts = AMOUNT_OPTIONS
    init_idx = st.session_state[key]
    opts_js = "[" + ",".join(f'"{o}"' for o in opts) + "]"

def amount_drum(default_index: int = 0) -> str:
    """Render single iOS-style drum for amount. Returns selected label."""
    key = "amount_drum_idx"
    if key not in st.session_state:
        st.session_state[key] = default_index

    selected_label = st.selectbox("金額を選択", options=AMOUNT_OPTIONS, index=st.session_state[key], key="amount_sel_box")
    return selected_label

# Removed date_drum completely as requested.
# Swipe Navigation Helper
# ──────────────────────────────────────────────
def nav_to(page: str):
    """Navigate to a page with slide animation feel."""
    st.session_state.page = page
    st.session_state.nav_dir = "forward"
    st.rerun()


def nav_back(page: str):
    st.session_state.page = page
    st.session_state.nav_dir = "back"
    st.rerun()


def swipe_hint():
    """Renders an invisible swipe-capture area that maps left/right swipe to page back."""
    components.html("""
<script>
(function(){
  let startX = 0;
  document.addEventListener('touchstart', e => { startX = e.touches[0].clientX; });
  document.addEventListener('touchend', e => {
    const dx = e.changedTouches[0].clientX - startX;
    if (dx > 80) {
      // swipe right = go back
      const btns = window.parent.document.querySelectorAll('button');
      for (const b of btns) {
        if (b.textContent.includes('← ') || b.textContent.includes('戻る')) {
          b.click(); break;
        }
      }
    }
  });
})();
</script>
""", height=0)


# ──────────────────────────────────────────────
# Pages
# ──────────────────────────────────────────────

def page_profile(user):
    from db import save_user_profile
    render_nav(user)
    st.markdown("""
<div style="text-align:center;padding:12px 0 20px;">
  <div style="font-size:56px;margin-bottom:16px;">👤</div>
  <div style="font-family:'Inter', sans-serif;font-size:28px;font-weight:900;color:#0F172A;letter-spacing:-0.04em;">あなたの情報</div>
  <div style="font-size:14px;color:#64748B;margin-top:8px;font-weight:500;">契約書に記載されるあなたの情報を入力してください</div>
</div>
""", unsafe_allow_html=True)

    with st.container():
        default_name = user.get("display_name") or st.session_state.get("google_name", "")
        default_email = user.get("email") or st.session_state.get("google_email", "")
        name = st.text_input("氏名・会社名", value=default_name, placeholder="山田 太郎 / 株式会社サンプル")
        address = st.text_input("住所", value=user.get("address", ""), placeholder="東京都渋谷区1-1-1 ...")
        phone = st.text_input("電話番号", value=user.get("phone", ""), placeholder="090-0000-0000")
        email = st.text_input("メールアドレス", value=default_email, placeholder="yamada@example.com")

    st.markdown("<div style='margin-bottom:24px'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 保存してはじめる", key="btn_save_profile"):
            if name.strip():
                save_user_profile(user["id"], name.strip(), address.strip(), phone.strip(), email.strip())
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("氏名を入力してください")
    with col2:
        if st.button("→ スキップ", key="btn_skip_profile"):
            st.session_state.page = "home"
            st.rerun()


def page_sign(contract_id: str):
    contract = get_contract(contract_id)
    st.markdown('<div style="padding:16px 0 20px;font-family:Space Grotesk,sans-serif;font-size:20px;font-weight:700;color:#1A1A2E;">Fit<span style="color:#00C48C">Sign</span></div>', unsafe_allow_html=True)

    if not contract:
        st.error("契約が見つかりません。URLを確認してください。")
        return

    if contract["status"] == "signed":
        st.markdown(f'<div class="state-success"><div style="font-size:48px;margin-bottom:12px;">✅</div><h2>署名済みです</h2><p>{contract["signer_name"]} さんが署名済みです</p></div>', unsafe_allow_html=True)
        return

    if contract["status"] == "rejected":
        reason = contract.get("rejection_reason") or ""
        msg = f"理由: {reason}" if reason else "この契約は差戻しされました"
        st.markdown(f'<div class="state-rejected"><div style="font-size:48px;margin-bottom:12px;">❌</div><h2>差戻し済みです</h2><p>{msg}</p></div>', unsafe_allow_html=True)
        return

    st.markdown(f"""
<div class="fs-card" style="display:flex;align-items:center;gap:16px;margin-bottom:20px;">
  <span style="font-size:40px">{contract.get("template_emoji","📋")}</span>
  <div>
    <div style="font-weight:800;font-size:20px;color:#0F172A;letter-spacing:-0.02em;">{contract["template_name"]}</div>
    <div style="font-size:12px;color:#64748B;font-weight:600;font-family:monospace;">ID: {contract["id"]}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    creator = get_user(contract["creator_id"])
    if creator:
        st.markdown(f"""
<div class="fs-card" style="background:#F8FAFC; border:1px solid #E2E8F0;">
  <div style="font-size:11px;font-weight:800;color:#64748B;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:12px;">委託者（依頼者）情報</div>
  <div style="display:grid;grid-template-columns:50px 1fr;gap:8px;font-size:13px;line-height:1.5;">
    <div style="color:#64748B;font-weight:600;">氏名</div><div style="font-weight:800;color:#0F172A;">{creator.get("display_name") or "未登録"}</div>
    <div style="color:#64748B;font-weight:600;">住所</div><div style="color:#334155;">{creator.get("address") or "-"}</div>
    <div style="color:#64748B;font-weight:600;">電話</div><div style="color:#334155;">{creator.get("phone") or "-"}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    creator = get_user(contract["creator_id"])
    creator_name = creator.get("display_name") or "未登録" if creator else "未登録"
    signer_name = st.session_state.get("sign_done") or "（受託者）"

    raw_content = contract["content"]
    if "␞" in raw_content:
        disp_content, _extra_json = raw_content.split("␞", 1)
        import json as _pj
        try:
            _xtra = _pj.loads(_extra_json)
        except Exception:
            _xtra = {}
    else:
        disp_content = raw_content
        _xtra = {}
    if "同意書" in contract.get("template_name", ""):
        c_type = _xtra.get("consent_type", "")
        from db import CONSENT_PRIVATE_TEMPLATE, CONSENT_BUSINESS_TEMPLATE
        if "プライベート" in c_type:
            tmpl = CONSENT_PRIVATE_TEMPLATE
        else:
            tmpl = CONSENT_BUSINESS_TEMPLATE
    else:
        tmpl = contract["template_body"]

    body = tmpl.format(
        content=disp_content,
        amount=contract["amount"],
        contract_date=contract["contract_date"],
        creator_name=creator_name,
        signer_name=signer_name,
        start_date=_xtra.get("start_date", contract["contract_date"]),
        end_date=_xtra.get("end_date", ""),
        payment_unit=_xtra.get("payment_unit", ""),
        deadline=_xtra.get("deadline", contract["contract_date"]),
    )
    st.markdown(f'<div class="contract-body">{body}</div>', unsafe_allow_html=True)
    st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)

    st.markdown("### 署名または差戻し")
    signer_name = st.text_input("氏名を入力してください", placeholder="山田 太郎")
    agreed = st.checkbox("上記内容に同意します")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✍️ 署名・締結"):
            if not signer_name.strip():
                st.error("氏名を入力してください")
            elif not agreed:
                st.error("内容に同意してください")
            else:
                ip = "unknown"
                try:
                    from streamlit.web.server.websocket_headers import _get_websocket_headers
                    ip = _get_websocket_headers().get("X-Forwarded-For", "unknown")
                except Exception:
                    pass
                sign_contract(contract["id"], signer_name.strip(), ip)
                st.session_state.sign_done = signer_name.strip()
                st.rerun()
    with col2:
        if st.button("❌ 差戻す"):
            st.session_state.show_reject = True

    if st.session_state.get("show_reject"):
        with st.form("reject_form"):
            reason = st.text_area("差戻しの理由（任意）", placeholder="金額に誤りがあります、等")
            if st.form_submit_button("差戻しを確定する"):
                reject_contract(contract["id"], reason)
                st.session_state.show_reject = False
                st.session_state.reject_done = True
                st.rerun()

    if st.session_state.get("sign_done"):
        st.markdown(f'<div class="state-success" style="margin-top:16px;"><div style="font-size:40px;margin-bottom:10px;">🎉</div><h2>締結完了！</h2><p>{st.session_state.sign_done} さんの署名が完了しました</p></div>', unsafe_allow_html=True)

    if st.session_state.get("reject_done"):
        st.markdown('<div class="state-rejected" style="margin-top:16px;"><div style="font-size:40px;margin-bottom:10px;">👋</div><h2>差戻しました</h2><p>作成者に内容の再確認を依頼しました</p></div>', unsafe_allow_html=True)


def page_home(user):
    swipe_hint()
    render_nav(user)
    name = user.get("display_name") or ""
    greeting = f"{name}さん、" if name else ""
    st.markdown(f'<div class="fs-hero"><h1>{greeting}30秒で<br><span>契約</span>できる</h1><p>テンプレ選んで入力するだけ。QRコードで相手が署名。</p></div>', unsafe_allow_html=True)

    # Custom HTML for clickable cards
    # Standard Streamlit buttons for clean, functional operation
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div style="text-align:center;font-size:40px;margin-bottom:8px;">✍️</div>', unsafe_allow_html=True)
        if st.button("契約を書く", use_container_width=True, key="btn_create", type="primary"):
            nav_to("create")
    with col2:
        st.markdown('<div style="text-align:center;font-size:40px;margin-bottom:8px;">📋</div>', unsafe_allow_html=True)
        if st.button("契約一覧", use_container_width=True, key="btn_list"):
            nav_to("list")

    render_limit_bar(user)
    st.markdown("""
<div class="fs-steps" style="margin-top:8px;">
  <div style="font-size:13px;font-weight:700;color:#4A5568;margin-bottom:12px;">使い方</div>
  <div class="step-item"><div class="step-num">1</div><div class="step-text">テンプレートを選んで内容を入力</div></div>
  <div class="step-item"><div class="step-num">2</div><div class="step-text">QRコードを相手のスマホで読み取る</div></div>
  <div class="step-item"><div class="step-num">3</div><div class="step-text">相手が署名して締結完了！</div></div>
</div>
""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col_p, _ = st.columns([1, 2])
    with col_p:
        if st.button("👤 プロフィール設定"):
            nav_to("profile")

    st.markdown('<div style="margin-top:40px;padding-top:20px;border-top:1px solid #E2E8F0;text-align:center;">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        if st.button("利用規約", key="btn_tos", use_container_width=True):
            nav_to("tos")
    with f_col2:
        if st.button("プライバシー", key="btn_privacy", use_container_width=True):
            nav_to("privacy")
    with f_col3:
        if st.button("特商法表記", key="btn_law", use_container_width=True):
            nav_to("law")
    st.markdown('</div>', unsafe_allow_html=True)


def page_create(user):
    swipe_hint()
    render_nav(user)
    plan = user["plan"]
    count = user["contract_count"]
    limit = LIMIT_FREE if plan == "free" else LIMIT_PAID

    if count >= limit:
        st.markdown('<div class="upgrade-cta"><div style="font-size:36px;margin-bottom:8px;">🔒</div><h3>上限に達しました</h3><p>有料プランで最大100件まで作成できます</p></div>', unsafe_allow_html=True)
        if st.button("← ホームに戻る"):
            nav_back("home")
        return

    st.markdown("## 契約を作る")
    st.markdown("**① テンプレートを選択**")
    templates = get_templates(plan)
    selected_tmpl = st.session_state.get("selected_template", None)

    for tmpl in templates:
        is_selected = selected_tmpl and selected_tmpl["id"] == tmpl["id"]
        sel_class = " selected" if is_selected else ""
        
        lbl = f"{tmpl['emoji']} {tmpl['name']}"
        if is_selected:
            lbl = f"✅ {tmpl['name']} (選択中)"

        if st.button(lbl, key=f"tmpl_btn_{tmpl['id']}", type="primary" if is_selected else "secondary", use_container_width=True):
            st.session_state.selected_template = tmpl
            st.rerun()
        
        st.markdown(f'<div style="font-size:12px;color:#64748B;text-align:center;margin-top:-10px;margin-bottom:12px;">{tmpl["description"]}</div>', unsafe_allow_html=True)


    st.markdown("<br>", unsafe_allow_html=True)
    if not selected_tmpl:
        st.info("上の枠をタップしてテンプレートを選択してください")
        if st.button("← 戻る"):
            nav_back("home")
        return

    st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)

    tmpl_name_early = selected_tmpl["name"]

    if "業務委託" in tmpl_name_early and "単発" not in tmpl_name_early:
        _tmpl_key = "業務委託"
    elif "単発" in tmpl_name_early or "請負" in tmpl_name_early:
        _tmpl_key = "単発"
    else:
        _tmpl_key = "同意"

    consent_type = ""
    if _tmpl_key == "同意":
        st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)
        st.markdown("**② 同意書の用途を選択**")
        consent_type = st.radio("用途", [
            "ビジネス向け（秘密保持・ルール合意など）",
            "プライベート向け（親密な関係・プライベートな合意など）"
        ], label_visibility="collapsed")
        
        _content_key = "同意_プライベート" if "プライベート" in consent_type else "同意_ビジネス"
    else:
        _content_key = _tmpl_key

    content_opts = CONTENT_OPTIONS_BY_TEMPLATE[_content_key]

    st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)
    if _tmpl_key == "同意":
        st.markdown("**③ 対象事項・概要**")
        sample_content = st.selectbox("対象事項・概要", options=content_opts, index=0, key="content_select")
    else:
        st.markdown("**② 業務内容**")
        sample_content = st.selectbox("業務内容", options=content_opts, index=0, key="content_select")

    if sample_content == "任意入力（手入力）":
        content = st.text_input("内容を入力", placeholder="例: ウェブサイト制作" if _tmpl_key != "同意" else "例: ルール合意")

    else:
        content = sample_content
        st.info(f"選択中: {content}")

    # --- Template-specific fields ---
    start_date = ""
    end_date = ""
    payment_unit = ""
    final_amt_str = ""
    deadline = ""
    contract_date = ""

    # ---- Pattern A: 業務委託契約 ----
    if _tmpl_key == "業務委託":
        st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)
        st.markdown("**③ 契約期間**")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<small>開始日</small>", unsafe_allow_html=True)
            d_start = st.date_input("開始日", label_visibility="collapsed", key="d_start")
            start_date = d_start.strftime("%Y/%m/%d")
        with c2:
            st.markdown("<small>終了日</small>", unsafe_allow_html=True)
            d_end = st.date_input("終了日", label_visibility="collapsed", key="d_end")
            end_date = d_end.strftime("%Y/%m/%d")

        st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)
        st.markdown("**④ 報酬金額と支払単位**")
        payment_unit = st.radio("支払単位", ["月額", "時給", "総額"], horizontal=True)
        sample_amount = amount_drum()
        if sample_amount == "任意入力（手入力）":
            final_amt_str = st.text_input("金額を入力（円）", placeholder="例: 150,000")
        else:
            final_amt_str = sample_amount
            st.markdown(f'<div class="fs-card" style="text-align:center;padding:14px;background:#ECFDF5;border-color:#17C080;">💰 <strong style="font-size:18px;color:#065F46;">{payment_unit} {final_amt_str}</strong></div>', unsafe_allow_html=True)

        contract_date = start_date  # Used for signing date reference

    # ---- Pattern B: 単発業務（請負） ----
    elif _tmpl_key == "単発":
        st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)
        st.markdown("**③ 履行報酬金額**")
        sample_amount = amount_drum()
        if sample_amount == "任意入力（手入力）":
            final_amt_str = st.text_input("金額を入力（円）", placeholder="例: 50,000")
        else:
            final_amt_str = sample_amount
            st.markdown(f'<div class="fs-card" style="text-align:center;padding:14px;background:#ECFDF5;border-color:#17C080;">💰 <strong style="font-size:18px;color:#065F46;">{final_amt_str}</strong></div>', unsafe_allow_html=True)

        st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)
        st.markdown("**④ 納期（納品期限）**")
        d_deadline = st.date_input("納期", label_visibility="collapsed", key="d_deadline")
        deadline = d_deadline.strftime("%Y/%m/%d")
        contract_date = deadline

    # ---- Pattern C: 同意書 ----
    else:  # 同意書 - no amount
        st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)
        st.markdown("**④ 同意日**")
        d_contract = st.date_input("日付を選択", label_visibility="collapsed", key="d_contract")

        contract_date = d_contract.strftime("%Y/%m/%d")
        final_amt_str = ""  # 同意書は金額なし

    st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 戻る", key="btn_back_create"):
            nav_back("home")
    with col2:
        if st.button("作成する →", type="primary"):
            if not content.strip():
                st.error("内容を入力してください")
            else:
                # Pack extra fields into a structured content string for DB storage
                extra = {}
                if start_date:
                    extra["start_date"] = start_date
                if end_date:
                    extra["end_date"] = end_date
                if payment_unit:
                    extra["payment_unit"] = payment_unit
                if deadline:
                    extra["deadline"] = deadline
                # consent_type is only defined if we matched Pattern C, so check locals()
                _ctype = locals().get("consent_type", "")
                if _ctype:
                    extra["consent_type"] = _ctype


                import json as _json
                extra_json = _json.dumps(extra, ensure_ascii=False) if extra else ""
                # Store extra fields in the content field as JSON suffix (sep: ␞)
                stored_content = content.strip() + (f"␞{extra_json}" if extra_json else "")

                contract_id = create_contract(
                    creator_id=user["id"],
                    template_id=selected_tmpl["id"],
                    content=stored_content,
                    amount=final_amt_str.strip() if final_amt_str else "",
                    contract_date=str(contract_date),
                )
                st.session_state.created_contract_id = contract_id
                st.session_state.selected_template = None
                nav_to("qr")



def page_qr(user):
    swipe_hint()
    render_nav(user)

    contract_id = st.session_state.get("created_contract_id")
    if not contract_id:
        nav_back("home")
        return

    contract = get_contract(contract_id)
    if not contract:
        st.error("契約が見つかりません")
        return

    base_url = get_base_url()
    sign_url = f"{base_url}/?page=sign&id={contract_id}"

    st.markdown(f'<div style="background:#C6F6D5;border-radius:16px;padding:14px 16px;margin-bottom:20px;display:flex;align-items:center;gap:10px;"><span style="font-size:20px">✅</span><div><div style="font-weight:700;color:#276749;font-size:14px;">契約を作成しました！</div><div style="font-size:12px;color:#2F855A;">QRコードで署名してもらいましょう</div></div></div>', unsafe_allow_html=True)

    qr_b64 = generate_qr(sign_url)
    st.markdown(f'<div class="qr-box"><div style="font-size:13px;color:#718096;margin-bottom:16px;">相手のスマホで読み取る</div><img src="data:image/png;base64,{qr_b64}" width="220"><div style="font-size:11px;color:#A0AEC0;margin-top:12px;">契約ID: {contract_id}</div></div>', unsafe_allow_html=True)

    st.markdown("**署名URL（ワンクリックでコピー）**")
    copy_html = f"""
    <div style="display:flex; gap:8px;">
        <input type="text" id="url" value="{sign_url}" readonly style="flex-grow:1; padding:12px; border-radius:12px; border:2px solid #E2E8F0; font-family:monospace; background:#F8FAFC; color:#334155; font-size:14px; outline:none;">
        <button onclick="copyToClipboard()" style="padding:12px 20px; background:#10B981; color:white; border:none; border-radius:12px; font-weight:800; font-size:15px; cursor:pointer; white-space:nowrap; box-shadow:0 4px 6px -1px rgba(16,185,129,0.2);">📋 コピー</button>
    </div>
    <div id="msg" style="color:#059669; font-weight:bold; font-size:13px; margin-top:6px; height:16px; margin-left:4px;"></div>
    <script>
    function copyToClipboard() {{
        var copyText = document.getElementById("url");
        copyText.select();
        copyText.setSelectionRange(0, 99999);
        try {{
            document.execCommand("copy");
            document.getElementById("msg").innerText = "✔ コピーしました！";
            setTimeout(() => document.getElementById("msg").innerText = "", 2500);
        }} catch (err) {{
            document.getElementById("msg").innerText = "コピーに失敗しました";
        }}
    }}
    </script>
    """
    components.html(copy_html, height=80)

    with st.expander("契約内容を確認"):
        creator = get_user(contract["creator_id"])
        creator_name = creator.get("display_name") or "未登録" if creator else "未登録"
        signer_name = contract.get("signer_name") or "（受託者）"
        raw_content = contract["content"]
        if "␞" in raw_content:
            disp_content, _extra_json = raw_content.split("␞", 1)
            import json as _pj
            try:
                _xtra = _pj.loads(_extra_json)
            except Exception:
                _xtra = {}
        else:
            disp_content = raw_content
            _xtra = {}
        if "同意書" in contract.get("template_name", ""):
            c_type = _xtra.get("consent_type", "")
            from db import CONSENT_PRIVATE_TEMPLATE, CONSENT_BUSINESS_TEMPLATE
            if "プライベート" in c_type:
                tmpl = CONSENT_PRIVATE_TEMPLATE
            else:
                tmpl = CONSENT_BUSINESS_TEMPLATE
        else:
            tmpl = contract["template_body"]

        body = tmpl.format(
            content=disp_content,
            amount=contract["amount"],
            contract_date=contract["contract_date"],
            creator_name=creator_name,
            signer_name=signer_name,
            start_date=_xtra.get("start_date", contract["contract_date"]),
            end_date=_xtra.get("end_date", ""),
            payment_unit=_xtra.get("payment_unit", ""),
            deadline=_xtra.get("deadline", contract["contract_date"]),
        )

        st.markdown(f'<div class="contract-body">{body}</div>', unsafe_allow_html=True)


    if st.button("🔄 署名状況を確認"):
        st.rerun()

    latest = get_contract(contract_id)
    if latest and latest["status"] == "signed":
        st.markdown(f'<div class="state-success"><div style="font-size:40px;margin-bottom:10px;">🎉</div><h2>締結完了！</h2><p>{latest["signer_name"]} さんが署名しました</p></div>', unsafe_allow_html=True)
    elif latest and latest["status"] == "rejected":
        reason = latest.get("rejection_reason") or ""
        st.markdown(f'<div class="state-rejected"><div style="font-size:40px;margin-bottom:10px;">❌</div><h2>差戻されました</h2><p>{"理由: " + reason if reason else "内容を確認してください"}</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← ホーム"):
            nav_back("home")
    with col2:
        if st.button("📋 一覧を見る"):
            nav_to("list")


def page_list(user):
    swipe_hint()
    render_nav(user)
    st.markdown("## 契約一覧")
    render_limit_bar(user)

    contracts = get_user_contracts(user["id"])
    if not contracts:
        st.markdown('<div style="text-align:center;padding:48px 0;color:#A0AEC0;"><div style="font-size:48px;margin-bottom:12px;">📄</div><div style="font-size:15px;">まだ契約がありません</div></div>', unsafe_allow_html=True)
    else:
        for c in contracts:
            if c["status"] == "signed":
                badge = '<span class="badge-signed">締結済み ✅</span>'
            elif c["status"] == "rejected":
                badge = '<span class="badge-rejected">差戻し ❌</span>'
            else:
                badge = '<span class="badge-draft">未署名 ⏳</span>'
            info = f"署名者: {c['signer_name']}" if c.get("signer_name") else f"作成: {c['created_at'][:10]}"
            rej = f"<div style='font-size:11px;color:#9B2335;margin-top:4px;'>理由: {c['rejection_reason']}</div>" if c.get("rejection_reason") else ""
            disp_content = c["content"].split("␞")[0]
            st.markdown(f'<div class="contract-list-card"><div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px;"><div style="display:flex;align-items:center;gap:8px;"><span style="font-size:20px">{c.get("template_emoji","📋")}</span><div><div style="font-weight:700;font-size:14px;color:#1A1A2E;">{c["template_name"]}</div><div style="font-size:11px;color:#A0AEC0;">{c["id"]}</div></div></div>{badge}</div><div style="font-size:13px;color:#4A5568;margin-bottom:4px;">📝 {disp_content[:30]}{"..." if len(disp_content)>30 else ""}</div><div style="font-size:12px;color:#718096;">{info}</div>{rej}</div>', unsafe_allow_html=True)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("詳細・QR", key=f"detail_{c['id']}"):
                    st.session_state.viewing_contract = c["id"]
                    nav_to("detail")
            with col2:
                if c["status"] == "signed":
                    pdf_buf = generate_pdf(get_contract(c["id"]))
                    st.download_button("📥 PDF", data=pdf_buf, file_name=f"contract_{c['id']}.pdf", mime="application/pdf", key=f"pdf_{c['id']}")
            st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← ホーム"):
            nav_back("home")
    with col2:
        if st.button("✍️ 新規契約"):
            nav_to("create")



def page_detail(user):
    swipe_hint()
    render_nav(user)

    contract_id = st.session_state.get("viewing_contract")
    if not contract_id:
        nav_back("list")
        return

    contract = get_contract(contract_id)
    if not contract or contract["creator_id"] != user["id"]:
        st.error("契約が見つかりません")
        return

    status = contract["status"]
    if status == "signed":
        badge = '<span class="badge-signed">締結済み ✅</span>'
    elif status == "rejected":
        badge = '<span class="badge-rejected">差戻し ❌</span>'
    else:
        badge = '<span class="badge-draft">未署名 ⏳</span>'

    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;"><span style="font-size:28px">{contract.get("template_emoji","📋")}</span><div><div style="font-weight:700;font-size:18px;color:#1A1A2E;">{contract["template_name"]} {badge}</div><div style="font-size:12px;color:#A0AEC0;">契約ID: {contract["id"]}</div></div></div>', unsafe_allow_html=True)

    creator = get_user(contract["creator_id"])
    creator_name = creator.get("display_name") or "未登録" if creator else "未登録"
    signer_name = contract.get("signer_name") or "（受託者）"
    raw_content = contract["content"]
    if "␞" in raw_content:
        disp_content, _extra_json = raw_content.split("␞", 1)
        import json as _pj
        try:
            _xtra = _pj.loads(_extra_json)
        except Exception:
            _xtra = {}
    else:
        disp_content = raw_content
        _xtra = {}
    if "同意書" in contract.get("template_name", ""):
        c_type = _xtra.get("consent_type", "")
        from db import CONSENT_PRIVATE_TEMPLATE, CONSENT_BUSINESS_TEMPLATE
        if "プライベート" in c_type:
            tmpl = CONSENT_PRIVATE_TEMPLATE
        else:
            tmpl = CONSENT_BUSINESS_TEMPLATE
    else:
        tmpl = contract["template_body"]
    body = tmpl.format(
        content=disp_content,
        amount=contract["amount"],
        contract_date=contract["contract_date"],
        creator_name=creator_name,
        signer_name=signer_name,
        start_date=_xtra.get("start_date", contract["contract_date"]),
        end_date=_xtra.get("end_date", ""),
        payment_unit=_xtra.get("payment_unit", ""),
        deadline=_xtra.get("deadline", contract["contract_date"]),
    )
    st.markdown(f'<div class="contract-body">{body}</div>', unsafe_allow_html=True)

    if status == "signed":
        st.markdown(f'<div class="fs-card"><div style="font-size:12px;color:#718096;margin-bottom:4px;">署名者</div><div style="font-weight:700;font-size:16px;">{contract["signer_name"]}</div><div style="font-size:12px;color:#718096;margin-top:8px;">{contract.get("signed_at","")[:19]}</div></div>', unsafe_allow_html=True)
        pdf_buf = generate_pdf(contract)
        st.download_button("📥 PDFをダウンロード", data=pdf_buf, file_name=f"fitsign_{contract['id']}.pdf", mime="application/pdf")
    elif status == "rejected":
        reason = contract.get("rejection_reason") or "理由なし"
        st.markdown(f'<div class="state-rejected"><div style="font-size:32px;margin-bottom:8px;">❌</div><h2>差戻されました</h2><p>理由: {reason}</p></div>', unsafe_allow_html=True)
    else:
        base_url = get_base_url()
        sign_url = f"{base_url}/?page=sign&id={contract_id}"
        qr_b64 = generate_qr(sign_url)
        st.markdown(f'<div class="qr-box"><div style="font-size:13px;color:#718096;margin-bottom:16px;">相手のスマホで読み取る</div><img src="data:image/png;base64,{qr_b64}" width="200"></div>', unsafe_allow_html=True)
        st.text_input("署名URL", value=sign_url, disabled=True)

    with st.expander("🔐 改ざんチェック"):
        st.markdown(f"**SHA-256:** `{contract.get('hash','')}`")

    if st.button("← 一覧に戻る"):
        nav_back("list")

def page_tos(user):
    swipe_hint()
    render_nav(user)
    st.markdown("## 利用規約")
    st.markdown("""
<div class="fs-card" style="font-size:14px; line-height:1.8;">

<p><strong>第1条（適用）</strong></p>
<p>本規約は、ユーザーと本サービスの運営者（以下「運営者」といいます。）との間の、電子契約サービス「Fit-Sign」（以下「本サービス」といいます。）の利用に関わる一切の関係に適用されるものとします。</p>
<p>ユーザーは、本サービスを利用することにより、本規約に同意したものとみなされます。</p>

<p><strong>第2条（サービスの内容と変更）</strong></p>
<p>本サービスは、PDFファイル等への電子署名またはテキスト入力を補助するツールを提供します。</p>
<p>運営者は、現在本サービスを無料で提供していますが、将来的に機能の追加、変更、または一部および全部の機能を有料化する権利を留保します。有料化または大幅な仕様変更を行う場合は、事前に本ウェブサイト上にて告知します。</p>

<p><strong>第3条（禁止事項）</strong></p>
<p>ユーザーは、本サービスの利用にあたり、以下の行為をしてはなりません。</p>
<ul>
  <li>法令または公序良俗に違反する行為</li>
  <li>犯罪行為に関連する行為</li>
  <li>運営者、本サービスの他のユーザー、または第三者のサーバーまたはネットワークの機能を破壊したり、妨害したりする行為</li>
  <li>本サービスによって得られた情報を商業的に転用する行為（ただし、ユーザー自身の業務上の契約締結目的での利用はこれに該当しません）</li>
  <li>虚偽の署名、または権限のない第三者の署名を無断で行う行為</li>
</ul>

<p><strong>第4条（免責事項）</strong></p>
<p>運営者は、本サービスに事実上または法律上の瑕疵がないことを明示的にも黙示的にも保証しておりません。</p>
<p>本サービスを利用して作成された契約書等の法的有効性、証拠力等について、運営者は一切の保証を行わず、これに起因するユーザー間の紛争について一切の責任を負いません。</p>
<p>本サービスは一時的なデータ処理を行うものであり、アップロードされたファイルや署名データの永続的な保存を保証するものではありません。ユーザーは自身の責任においてデータのバックアップを行うものとします。</p>

<p><strong>第5条（利用規約の変更）</strong></p>
<p>運営者は、必要と判断した場合には、ユーザーに通知することなくいつでも本規約を変更することができるものとします。</p>

</div>
    """, unsafe_allow_html=True)
    if st.button("← ホームに戻る", key="back_tos"):
        nav_back("home")

def page_privacy(user):
    swipe_hint()
    render_nav(user)
    st.markdown("## プライバシーポリシー")
    st.markdown("""
<div class="fs-card" style="font-size:14px; line-height:1.8;">

<p><strong>1. 収集する情報</strong></p>
<p>本サービスでは、機能提供のために以下の情報を取得・処理する場合があります。</p>
<ul>
  <li>ユーザーがアップロードしたPDFファイルデータ</li>
  <li>入力されたテキスト情報、電子署名データ</li>
  <li>アクセスログ（IPアドレス、ブラウザ情報など）</li>
</ul>

<p><strong>2. 利用目的</strong></p>
<p>収集した情報は、以下の目的で利用します。</p>
<ul>
  <li>本サービスの機能の提供・運営のため</li>
  <li>ユーザーからのお問い合わせに回答するため</li>
  <li>本サービスの利用状況の分析および機能改善のため</li>
</ul>

<p><strong>3. データの保存と破棄</strong></p>
<p>本サービスに入力・アップロードされたファイルデータおよび署名データは、当該セッションの処理が完了した時点、または一定時間経過後に、サーバー上から自動的かつ不可逆的に破棄されます。運営者はこれらの契約内容を閲覧・保存・二次利用することはありません。</p>

<p><strong>4. 第三者提供</strong></p>
<p>運営者は、法令に基づく場合を除き、あらかじめユーザーの同意を得ることなく、第三者に個人情報またはアップロードされたデータを提供することはありません。</p>

</div>
    """, unsafe_allow_html=True)
    if st.button("← ホームに戻る", key="back_privacy"):
        nav_back("home")

def page_law(user):
    swipe_hint()
    render_nav(user)
    st.markdown("## 特定商取引法に基づく表記")
    st.markdown("""
<div class="fs-card" style="font-size:14px; line-height:1.8;">
<p style="color:#64748B; font-size:12px; margin-bottom:16px; border:1px solid #E2E8F0; border-radius:8px; padding:10px; background:#F8FAFC;">
  ℹ️ 本サービスは現在完全無料で提供中のため、特定商取引法（通信販売）の表記義務は発生していません。将来の有料化に備えて、以下に事業者情報を掲載しています。
</p>
<table style="width:100%; border-collapse: collapse; font-size:13px;">
  <tr><td style="padding:10px 0; border-bottom:1px solid #F1F5F9; font-weight:bold; width:38%; vertical-align:top;">販売業者</td><td style="padding:10px 0; border-bottom:1px solid #F1F5F9;">Fit-Sign</td></tr>
  <tr><td style="padding:10px 0; border-bottom:1px solid #F1F5F9; font-weight:bold; vertical-align:top;">代表責任者</td><td style="padding:10px 0; border-bottom:1px solid #F1F5F9;">関 順子</td></tr>
  <tr><td style="padding:10px 0; border-bottom:1px solid #F1F5F9; font-weight:bold; vertical-align:top;">所在地</td><td style="padding:10px 0; border-bottom:1px solid #F1F5F9;">静岡県富士宮市</td></tr>
  <tr><td style="padding:10px 0; border-bottom:1px solid #F1F5F9; font-weight:bold; vertical-align:top;">連絡先</td><td style="padding:10px 0; border-bottom:1px solid #F1F5F9;">メール: oyajibuki@gmail.com<br><span style="font-size:12px; color:#64748B;">※お問い合わせは原則メールにて承っております</span></td></tr>
  <tr><td style="padding:10px 0; border-bottom:1px solid #F1F5F9; font-weight:bold; vertical-align:top;">販売価格</td><td style="padding:10px 0; border-bottom:1px solid #F1F5F9;">現在はすべての機能を無料で提供しているため、該当事項はありません。</td></tr>
  <tr><td style="padding:10px 0; font-weight:bold; vertical-align:top;">必要料金</td><td style="padding:10px 0;">インターネット接続にかかる通信回線等の諸費用は、お客様のご負担となります。</td></tr>
</table>
</div>
    """, unsafe_allow_html=True)
    if st.button("← ホームに戻る", key="back_law"):
        nav_back("home")



# ──────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────

def main():
    params = st.query_params

    # ── 署名ページは認証不要 ──────────────────────────────
    if params.get("page") == "sign":
        page_sign(params.get("id", ""))
        return

    # ── OAuth コールバック処理 ────────────────────────────
    if "code" in params:
        code = params.get("code", "")
        # flow_id (fid) を取得
        flow_id = params.get("fid", "")
        try:
            result = exchange_code_for_session(code, flow_id)
            if result is None or result.user is None:
                raise ValueError("ユーザー情報の取得に失敗しました。")
            st.session_state.user_id = result.user.id
            # アカウント情報を session_state に保存（プロフィール初期値用）
            meta = result.user.user_metadata or {}
            st.session_state["google_email"] = result.user.email or ""
            st.session_state["google_name"] = meta.get("full_name") or meta.get("name") or meta.get("display_name") or ""
            st.session_state.pop("oauth_error", None)
            st.session_state.pop("auth_urls_v3", None)
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            # エラーを session_state に保存してから params をクリア → rerun後に表示
            st.session_state["oauth_error"] = str(e)
            st.query_params.clear()
            st.rerun()
        return

    # ── 未ログインはログインページへ ─────────────────────
    user_id = get_user_id()
    if not user_id:
        page_login()
        return

    user = get_or_create_user(user_id)

    page = st.session_state.get("page", "")
    if "page" in st.query_params:
        page = st.query_params["page"]

    if page == "home":
        page_home(user)
    elif page == "profile":
        page_profile(user)
    elif page == "create":
        page_create(user)
    elif page == "qr":
        page_qr(user)
    elif page == "list":
        page_list(user)
    elif page == "detail":
        page_detail(user)
    elif page == "tos":
        page_tos(user)
    elif page == "privacy":
        page_privacy(user)
    elif page == "law":
        page_law(user)
    else:
        # Default page if not found or session state is empty
        st.session_state.page = "profile" if not user.get("display_name") else "home"
        st.rerun()


main()
