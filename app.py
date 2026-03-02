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
    upgrade_to_paid,
    delete_draft_contract,
    save_display_name,
)
from pdf_gen import generate_pdf

st.set_page_config(
    page_title="FitSign",
    page_icon="✍️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&family=Space+Grotesk:wght@500;700&display=swap');
html, body, [class*="css"] { font-family:'Noto Sans JP',sans-serif; background:#F0F4FF !important; }
.stApp { background:#F0F4FF !important; }
.main > div { padding-top:0 !important; background:#F0F4FF; }
section[data-testid="stSidebar"] { display:none; }
#MainMenu, footer, header { visibility:hidden; }
.block-container { padding:0 1rem 5rem !important; max-width:480px !important; }

/* Nav */
.fs-nav { display:flex; align-items:center; justify-content:space-between; padding:16px 0 14px; margin-bottom:16px; }
.fs-logo { font-family:'Space Grotesk',sans-serif; font-size:22px; font-weight:700; color:#1A1A2E; }
.fs-logo span { color:#00C48C; }
.fs-chip { background:white; border:1.5px solid #E2E8F0; border-radius:20px; padding:4px 12px; font-size:12px; color:#4A5568; font-weight:500; }

/* Hero */
.fs-hero { text-align:center; padding:28px 0 20px; }
.fs-hero h1 { font-family:'Space Grotesk',sans-serif; font-size:36px; font-weight:700; color:#1A1A2E; letter-spacing:-1px; line-height:1.2; margin:0 0 10px; }
.fs-hero h1 span { color:#00C48C; }
.fs-hero p { font-size:14px; color:#718096; margin:0; }

/* Card */
.fs-card { background:white; border-radius:20px; padding:20px; margin-bottom:16px; box-shadow:0 2px 12px rgba(0,0,0,0.06); }

/* Steps */
.fs-steps { background:white; border-radius:20px; padding:20px; box-shadow:0 2px 12px rgba(0,0,0,0.06); }
.step-item { display:flex; align-items:center; gap:14px; padding:10px 0; border-bottom:1px solid #EDF2F7; }
.step-item:last-child { border-bottom:none; }
.step-num { width:32px; height:32px; background:#1A1A2E; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:13px; font-weight:700; flex-shrink:0; }
.step-text { font-size:13px; color:#4A5568; }

/* Template card */
.tmpl-card { background:white; border-radius:16px; padding:16px 18px; margin-bottom:12px; display:flex; align-items:center; gap:14px; box-shadow:0 2px 8px rgba(0,0,0,0.06); border:2px solid transparent; min-height:76px; transition:border-color .15s; }
.tmpl-card.selected { border-color:#00C48C; background:#F0FDF9; }

/* Badges */
.badge-signed { background:#C6F6D5; color:#276749; font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; }
.badge-draft { background:#FEFCBF; color:#744210; font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; }
.badge-rejected { background:#FED7D7; color:#9B2335; font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; }

/* Contract body */
.contract-body { background:#F7FAFC; border-radius:12px; padding:20px; font-size:14px; line-height:1.8; white-space:pre-wrap; color:#2D3748; border:1px solid #E2E8F0; margin:16px 0; }

/* QR */
.qr-box { background:white; border-radius:20px; padding:28px; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.06); margin:16px 0; }

/* State */
.state-success { background:#C6F6D5; border-radius:20px; padding:28px; text-align:center; margin:20px 0; }
.state-success h2 { font-size:22px; color:#276749; margin:0 0 6px; }
.state-success p { font-size:13px; color:#2F855A; margin:0; }
.state-rejected { background:#FED7D7; border-radius:20px; padding:28px; text-align:center; margin:20px 0; }
.state-rejected h2 { font-size:22px; color:#9B2335; margin:0 0 6px; }
.state-rejected p { font-size:13px; color:#C53030; margin:0; }

/* Limit bar */
.limit-bar-wrap { margin:12px 0; }
.limit-label { font-size:12px; color:#718096; margin-bottom:6px; display:flex; justify-content:space-between; }
.limit-bar { height:6px; background:#EDF2F7; border-radius:3px; overflow:hidden; }
.limit-fill { height:100%; background:#1A1A2E; border-radius:3px; }
.limit-fill.warn { background:#ECC94B; }
.limit-fill.full { background:#FC8181; }

/* Plan */
.plan-free { background:#EDF2F7; color:#4A5568; font-size:11px; font-weight:700; padding:2px 8px; border-radius:20px; }
.plan-paid { background:#1A1A2E; color:white; font-size:11px; font-weight:700; padding:2px 8px; border-radius:20px; }

/* Sep */
.fs-sep { border:none; border-top:1.5px solid #EDF2F7; margin:16px 0; }

/* Upgrade */
.upgrade-cta { background:linear-gradient(135deg,#1A1A2E 0%,#2D3748 100%); border-radius:20px; padding:24px; color:white; text-align:center; margin:16px 0; }

/* Contract list card */
.contract-list-card { background:white; border-radius:16px; padding:16px 18px; margin-bottom:14px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }

/* Buttons */
div.stButton > button {
    width:100%; border-radius:14px !important; font-weight:700 !important;
    font-family:'Noto Sans JP',sans-serif !important; font-size:14px !important;
    padding:12px 8px !important; border:none !important;
    transition:all .2s !important; white-space:nowrap;
}
div.stButton > button:first-child { background:#1A1A2E !important; color:white !important; }
div.stButton > button:first-child:hover { background:#2D3748 !important; transform:translateY(-1px) !important; box-shadow:0 4px 12px rgba(0,0,0,.2) !important; }

/* Inputs */
div.stTextInput > div > div > input,
div.stTextArea > div > div > textarea {
    border-radius:12px !important; border:1.5px solid #E2E8F0 !important;
    font-family:'Noto Sans JP',sans-serif !important; background:#F7FAFC !important;
}
div.stTextInput > div > div > input:focus,
div.stTextArea > div > div > textarea:focus {
    border-color:#00C48C !important; box-shadow:0 0 0 3px rgba(0,196,140,.15) !important; background:white !important;
}
div.stInfo, div.stSuccess, div.stWarning, div.stError { border-radius:12px !important; }

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


def _get_base_url():
    try:
        import streamlit.web.server.websocket_headers as wh
        headers = wh._get_websocket_headers()
        host = headers.get("Host", "localhost:8501")
        proto = "https" if "streamlit.app" in host else "http"
        return f"{proto}://{host}"
    except Exception:
        try:
            return st.secrets.get("BASE_URL", "http://localhost:8501")
        except Exception:
            return "http://localhost:8501"


def get_base_url():
    if "base_url" not in st.session_state:
        st.session_state.base_url = _get_base_url()
    return st.session_state.base_url


def get_user_id():
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id


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
        f'<div style="display:flex;align-items:center;gap:8px;">{name_html}{plan_html}</div></div>',
        unsafe_allow_html=True,
    )


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
# Single Drum Picker – 0〜100万 円 (1万刻み) + 1000円刻み微調整
# ──────────────────────────────────────────────
AMOUNT_OPTIONS = (
    ["0円"] +
    [f"{i}千円" for i in range(1, 10)] +
    [f"{i}万円" for i in range(1, 101)]
)

AMOUNT_VALUES = (
    [0] +
    [i * 1000 for i in range(1, 10)] +
    [i * 10000 for i in range(1, 101)]
)


def amount_drum(default_index: int = 0) -> int:
    """Render single iOS-style drum for amount. Returns selected amount in yen."""
    key = "amount_drum"
    if key not in st.session_state:
        st.session_state[key] = default_index

    opts = AMOUNT_OPTIONS
    init_idx = st.session_state[key]
    opts_js = "[" + ",".join(f'"{o}"' for o in opts) + "]"

    html = f"""
<style>
.drum-wrap {{
  position:relative; height:200px; overflow:hidden;
  border-radius:16px; background:#F7FAFC; border:1.5px solid #E2E8F0;
  user-select:none; touch-action:none;
}}
.drum-mask-top,.drum-mask-bot {{
  position:absolute; left:0; right:0; height:68px; z-index:2; pointer-events:none;
}}
.drum-mask-top {{ top:0; background:linear-gradient(to bottom,#F7FAFC 40%,transparent); }}
.drum-mask-bot {{ bottom:0; background:linear-gradient(to top,#F7FAFC 40%,transparent); }}
.drum-sel {{
  position:absolute; top:50%; left:12px; right:12px;
  transform:translateY(-50%); height:52px;
  border-radius:12px; background:rgba(0,196,140,.12);
  border:1.5px solid rgba(0,196,140,.5); z-index:1; pointer-events:none;
}}
.drum-list {{ position:absolute; width:100%; will-change:transform; cursor:grab; }}
.drum-list:active {{ cursor:grabbing; }}
.drum-item {{
  height:52px; display:flex; align-items:center; justify-content:center;
  font-size:18px; font-weight:700; color:#1A1A2E; font-family:'Noto Sans JP',sans-serif;
}}
</style>
<div class="drum-wrap" id="drum-wrap">
  <div class="drum-mask-top"></div>
  <div class="drum-sel"></div>
  <div class="drum-list" id="drum-list"></div>
  <div class="drum-mask-bot"></div>
</div>
<input type="hidden" id="drum-out" value="{init_idx}">
<script>
(function(){{
  const OPTS = {opts_js};
  const ITEM_H = 52;
  const PAD = 2;
  const list = document.getElementById('drum-list');
  const out  = document.getElementById('drum-out');
  let idx = {init_idx};
  let startY = 0, baseOffset = 0, isDragging = false;

  const allItems = [...Array(PAD).fill(''), ...OPTS, ...Array(PAD).fill('')];
  allItems.forEach(o => {{
    const d = document.createElement('div');
    d.className = 'drum-item';
    d.textContent = o;
    list.appendChild(d);
  }});

  function getOffset(i) {{
    return -((i + PAD) * ITEM_H - 74);
  }}

  function snap(i, animate) {{
    idx = Math.max(0, Math.min(OPTS.length - 1, i));
    list.style.transition = animate ? 'transform .2s cubic-bezier(.22,.61,.36,1)' : 'none';
    list.style.transform = 'translateY(' + getOffset(idx) + 'px)';
    out.value = idx;
  }}

  snap({init_idx}, false);

  const wrap = document.getElementById('drum-wrap');

  // Touch
  wrap.addEventListener('touchstart', e => {{
    isDragging = true;
    startY = e.touches[0].clientY;
    baseOffset = getOffset(idx);
    list.style.transition = 'none';
    e.preventDefault();
  }}, {{passive:false}});
  wrap.addEventListener('touchmove', e => {{
    if (!isDragging) return;
    const dy = e.touches[0].clientY - startY;
    list.style.transform = 'translateY(' + (baseOffset + dy) + 'px)';
    e.preventDefault();
  }}, {{passive:false}});
  wrap.addEventListener('touchend', e => {{
    if (!isDragging) return;
    isDragging = false;
    const dy = e.changedTouches[0].clientY - startY;
    snap(idx - Math.round(dy / ITEM_H), true);
  }});

  // Mouse
  wrap.addEventListener('mousedown', e => {{
    isDragging = true;
    startY = e.clientY;
    baseOffset = getOffset(idx);
    list.style.transition = 'none';
  }});
  document.addEventListener('mousemove', e => {{
    if (!isDragging) return;
    const dy = e.clientY - startY;
    list.style.transform = 'translateY(' + (baseOffset + dy) + 'px)';
  }});
  document.addEventListener('mouseup', e => {{
    if (!isDragging) return;
    isDragging = false;
    const dy = e.clientY - startY;
    snap(idx - Math.round(dy / ITEM_H), true);
  }});
}})();
</script>
"""
    st.markdown('<div style="font-size:12px;font-weight:700;color:#718096;margin-bottom:6px;letter-spacing:.5px;">金額を選択</div>', unsafe_allow_html=True)
    components.html(html, height=220)

    # Use selectbox underneath as the actual state holder
    selected_label = st.selectbox(
        "金額",
        options=AMOUNT_OPTIONS,
        index=init_idx,
        key="amount_sel",
        label_visibility="collapsed",
    )
    sel_idx = AMOUNT_OPTIONS.index(selected_label)
    return AMOUNT_VALUES[sel_idx]


# ──────────────────────────────────────────────
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
    render_nav(user)
    st.markdown("""
<div style="text-align:center;padding:32px 0 20px;">
  <div style="font-size:56px;margin-bottom:16px;">👤</div>
  <div style="font-family:'Space Grotesk',sans-serif;font-size:26px;font-weight:700;color:#1A1A2E;">はじめに</div>
  <div style="font-size:14px;color:#718096;margin-top:8px;">お名前を登録するとスムーズに使えます</div>
</div>
""", unsafe_allow_html=True)

    current_name = user.get("display_name") or ""
    new_name = st.text_input("名前（表示名）", value=current_name, placeholder="山田 太郎", key="p_name")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 保存してはじめる", key="btn_save_profile"):
            if new_name.strip():
                save_display_name(user["id"], new_name.strip())
            st.session_state.page = "home"
            st.rerun()
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
<div class="fs-card" style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
  <span style="font-size:32px">{contract.get("template_emoji","📋")}</span>
  <div>
    <div style="font-weight:700;font-size:18px;color:#1A1A2E;">{contract["template_name"]}</div>
    <div style="font-size:11px;color:#A0AEC0;">契約ID: {contract["id"]}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    body = contract["template_body"].format(
        content=contract["content"], amount=contract["amount"], contract_date=contract["contract_date"]
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

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="fs-card" style="text-align:center;min-height:110px;display:flex;flex-direction:column;align-items:center;justify-content:center;"><div style="font-size:36px;margin-bottom:8px;">✍️</div><div style="font-weight:700;font-size:14px;color:#1A1A2E;">契約を作る</div><div style="font-size:11px;color:#A0AEC0;margin-top:2px;">新規作成</div></div>', unsafe_allow_html=True)
        if st.button("契約を作る", key="btn_create"):
            nav_to("create")
    with col2:
        st.markdown('<div class="fs-card" style="text-align:center;min-height:110px;display:flex;flex-direction:column;align-items:center;justify-content:center;"><div style="font-size:36px;margin-bottom:8px;">📋</div><div style="font-weight:700;font-size:14px;color:#1A1A2E;">契約一覧</div><div style="font-size:11px;color:#A0AEC0;margin-top:2px;">作成した契約</div></div>', unsafe_allow_html=True)
        if st.button("契約一覧", key="btn_list"):
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
        st.markdown(f'<div class="tmpl-card{sel_class}"><span style="font-size:28px">{tmpl["emoji"]}</span><div><div style="font-weight:700;font-size:15px;color:#1A1A2E;">{tmpl["name"]}</div><div style="font-size:12px;color:#718096;margin-top:2px;">{tmpl["description"]}</div></div></div>', unsafe_allow_html=True)
        _lbl = "✅ 選択中" if is_selected else ("選択：" + tmpl["name"])
        if st.button(_lbl, key=f"tmpl_{tmpl['id']}"):
            st.session_state.selected_template = tmpl
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if not selected_tmpl:
        st.info("テンプレートを選択してください")
        if st.button("← 戻る"):
            nav_back("home")
        return

    st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)
    st.markdown("**② 業務内容を入力**")
    content = st.text_input("業務内容", placeholder="ウェブサイトのデザイン制作")
    contract_date = st.date_input("日付")

    st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)
    st.markdown("**③ 金額を選択**")
    amount_yen = amount_drum()
    st.markdown(f'<div class="fs-card" style="text-align:center;padding:14px;">💰 <strong style="font-size:18px;">{amount_yen:,}円</strong></div>', unsafe_allow_html=True)
    manual_override = st.text_input("または金額を直接入力（任意）", placeholder="例: 123,456", key="manual_amt")

    st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 戻る", key="btn_back_create"):
            nav_back("home")
    with col2:
        if st.button("作成する →"):
            if not content.strip():
                st.error("内容を入力してください")
            else:
                final_amount = manual_override.strip() if manual_override.strip() else f"{amount_yen:,}"
                contract_id = create_contract(
                    creator_id=user["id"],
                    template_id=selected_tmpl["id"],
                    content=content.strip(),
                    amount=final_amount,
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

    st.text_input("署名URL（コピーして送れます）", value=sign_url, disabled=True)

    with st.expander("契約内容を確認"):
        body = contract["template_body"].format(content=contract["content"], amount=contract["amount"], contract_date=contract["contract_date"])
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
            st.markdown(f'<div class="contract-list-card"><div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px;"><div style="display:flex;align-items:center;gap:8px;"><span style="font-size:20px">{c.get("template_emoji","📋")}</span><div><div style="font-weight:700;font-size:14px;color:#1A1A2E;">{c["template_name"]}</div><div style="font-size:11px;color:#A0AEC0;">{c["id"]}</div></div></div>{badge}</div><div style="font-size:13px;color:#4A5568;margin-bottom:4px;">📝 {c["content"][:30]}{"..." if len(c["content"])>30 else ""}</div><div style="font-size:12px;color:#718096;">{info}</div>{rej}</div>', unsafe_allow_html=True)

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

    with st.expander("⚙️ 開発者設定"):
        st.markdown(f"**あなたのID:** `{user['id']}`")
        new_base = st.text_input("BASE_URL", value=get_base_url())
        if st.button("URLを保存"):
            st.session_state.base_url = new_base
            st.success("保存しました")
        st.markdown("---")
        if user["plan"] == "free":
            if st.button("🔓 有料プランに変更（テスト用）"):
                upgrade_to_paid(user["id"])
                st.success("変更しました")
                st.rerun()


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

    body = contract["template_body"].format(content=contract["content"], amount=contract["amount"], contract_date=contract["contract_date"])
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


# ──────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────

def main():
    params = st.query_params
    page_param = params.get("page", "")
    contract_id_param = params.get("id", "")

    if page_param == "sign" and contract_id_param:
        page_sign(contract_id_param)
        return

    user_id = get_user_id()
    user = get_or_create_user(user_id)

    if "page" not in st.session_state:
        st.session_state.page = "profile" if not user.get("display_name") else "home"

    page = st.session_state.page
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
    else:
        st.session_state.page = "home"
        st.rerun()


main()
