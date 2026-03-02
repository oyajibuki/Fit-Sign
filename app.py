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

# ────────────────────────────────────────────
# Page config
# ────────────────────────────────────────────
st.set_page_config(
    page_title="FitSign – スマホ2台で30秒契約",
    page_icon="✍️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ────────────────────────────────────────────
# CSS – クリーン・ライトブルー系・モバイルファースト
# ────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&family=Space+Grotesk:wght@500;700&display=swap');

/* ─── Base ─── */
html, body, [class*="css"] {
    font-family: 'Noto Sans JP', sans-serif;
    background: #F0F4FF !important;
}
.main > div { padding-top: 0 !important; background: #F0F4FF; }
.stApp { background: #F0F4FF !important; }
section[data-testid="stSidebar"] { display: none; }
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 0 1rem 5rem !important;
    max-width: 480px !important;
    background: transparent;
}

/* ─── Nav ─── */
.fs-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 0 14px;
    margin-bottom: 20px;
}
.fs-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 22px; font-weight: 700; letter-spacing: -0.5px;
    color: #1A1A2E;
}
.fs-logo span { color: #00C48C; }
.fs-user-chip {
    background: white;
    border: 1.5px solid #E2E8F0;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    color: #4A5568;
    font-weight: 500;
}

/* ─── Hero ─── */
.fs-hero {
    text-align: center;
    padding: 36px 0 24px;
}
.fs-hero h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 36px; font-weight: 700;
    color: #1A1A2E;
    letter-spacing: -1px;
    line-height: 1.2;
    margin: 0 0 10px;
}
.fs-hero h1 span { color: #00C48C; }
.fs-hero p {
    font-size: 14px;
    color: #718096;
    margin: 0;
}

/* ─── White Card ─── */
.fs-card {
    background: white;
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* ─── Action Buttons ─── */
.action-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 16px;
}
.action-btn {
    background: white;
    border-radius: 20px;
    padding: 20px 12px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    cursor: pointer;
    text-decoration: none;
}
.action-btn .ab-icon { font-size: 32px; margin-bottom: 8px; }
.action-btn .ab-label { font-size: 13px; font-weight: 700; color: #1A1A2E; }
.action-btn .ab-sub { font-size: 11px; color: #A0AEC0; margin-top: 2px; }

/* ─── Step ─── */
.fs-steps {
    background: white;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.step-item {
    display: flex; align-items: center; gap: 14px;
    padding: 10px 0;
    border-bottom: 1px solid #EDF2F7;
}
.step-item:last-child { border-bottom: none; }
.step-num {
    width: 32px; height: 32px;
    background: #1A1A2E;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 13px; font-weight: 700;
    flex-shrink: 0;
}
.step-text { font-size: 13px; color: #4A5568; }

/* ─── Template Card ─── */
.tmpl-card {
    background: white;
    border-radius: 16px;
    padding: 16px 18px;
    margin-bottom: 12px;
    display: flex; align-items: center; gap: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border: 2px solid transparent;
    transition: border-color 0.15s;
    min-height: 76px;
}
.tmpl-card.selected { border-color: #00C48C; }
.tmpl-emoji { font-size: 28px; }
.tmpl-name { font-weight: 700; font-size: 15px; color: #1A1A2E; }
.tmpl-desc { font-size: 12px; color: #718096; margin-top: 2px; }

/* ─── Status Badges ─── */
.badge-signed {
    background: #C6F6D5; color: #276749;
    font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px;
}
.badge-draft {
    background: #FEFCBF; color: #744210;
    font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px;
}
.badge-rejected {
    background: #FED7D7; color: #9B2335;
    font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px;
}

/* ─── Contract body ─── */
.contract-body {
    background: #F7FAFC;
    border-radius: 12px;
    padding: 20px;
    font-size: 14px;
    line-height: 1.8;
    white-space: pre-wrap;
    color: #2D3748;
    border: 1px solid #E2E8F0;
    margin: 16px 0;
}

/* ─── QR Box ─── */
.qr-box {
    background: white;
    border-radius: 20px;
    padding: 28px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin: 16px 0;
}
.qr-box img { border-radius: 12px; }

/* ─── Success/Error states ─── */
.state-success {
    background: #C6F6D5;
    border-radius: 20px;
    padding: 28px;
    text-align: center;
    margin: 20px 0;
}
.state-success h2 { font-size: 22px; color: #276749; margin: 0 0 6px; }
.state-success p { font-size: 13px; color: #2F855A; margin: 0; }

.state-rejected {
    background: #FED7D7;
    border-radius: 20px;
    padding: 28px;
    text-align: center;
    margin: 20px 0;
}
.state-rejected h2 { font-size: 22px; color: #9B2335; margin: 0 0 6px; }
.state-rejected p { font-size: 13px; color: #C53030; margin: 0; }

/* ─── Limit bar ─── */
.limit-bar-wrap { margin: 16px 0; }
.limit-label { font-size: 12px; color: #718096; margin-bottom: 6px; display: flex; justify-content: space-between; }
.limit-bar { height: 6px; background: #EDF2F7; border-radius: 3px; overflow: hidden; }
.limit-fill { height: 100%; background: #1A1A2E; border-radius: 3px; transition: width 0.3s; }
.limit-fill.warn { background: #ECC94B; }
.limit-fill.full { background: #FC8181; }

/* ─── Plan ─── */
.plan-free { background: #EDF2F7; color: #4A5568; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.plan-paid { background: #1A1A2E; color: white; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 20px; }

/* ─── Separator ─── */
.fs-sep { border: none; border-top: 1.5px solid #EDF2F7; margin: 16px 0; }

/* ─── Upgrade CTA ─── */
.upgrade-cta {
    background: linear-gradient(135deg, #1A1A2E 0%, #2D3748 100%);
    border-radius: 20px;
    padding: 24px;
    color: white;
    text-align: center;
    margin: 16px 0;
}
.upgrade-cta h3 { font-size: 18px; margin: 0 0 8px; }
.upgrade-cta p { font-size: 13px; opacity: 0.75; margin: 0 0 16px; }

/* ─── Contract card in list ─── */
.contract-list-card {
    background: white;
    border-radius: 16px;
    padding: 16px 18px;
    margin-bottom: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* ─── Streamlit widget overrides ─── */
div.stButton > button {
    width: 100%;
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-family: 'Noto Sans JP', sans-serif !important;
    font-size: 14px !important;
    padding: 12px 4px !important;
    border: none !important;
    transition: all 0.2s !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
div.stButton > button:first-child {
    background: #1A1A2E !important;
    color: white !important;
}
div.stButton > button:first-child:hover {
    background: #2D3748 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
}

div.stTextInput > div > div > input,
div.stSelectbox > div > div,
div.stDateInput > div > div > input,
div.stTextArea > div > div > textarea {
    border-radius: 12px !important;
    border: 1.5px solid #E2E8F0 !important;
    font-family: 'Noto Sans JP', sans-serif !important;
    background: #F7FAFC !important;
}
div.stTextInput > div > div > input:focus,
div.stTextArea > div > div > textarea:focus {
    border-color: #00C48C !important;
    box-shadow: 0 0 0 3px rgba(0,196,140,0.15) !important;
    background: white !important;
}
div.stInfo { border-radius: 12px !important; }
div.stSuccess { border-radius: 12px !important; }
div.stWarning { border-radius: 12px !important; }
div.stError { border-radius: 12px !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────
# Init
# ────────────────────────────────────────────
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
        return st.secrets.get("BASE_URL", "http://localhost:8501")


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
    name_display = ""
    if user and user.get("display_name"):
        name_display = f'<div class="fs-user-chip">👤 {user["display_name"]}</div>'
    st.markdown(
        f"""
    <div class="fs-nav">
        <div class="fs-logo">Fit<span>Sign</span></div>
        <div style="display:flex;align-items:center;gap:8px;">{name_display}{plan_html}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_limit_bar(user):
    limit = LIMIT_FREE if user["plan"] == "free" else LIMIT_PAID
    count = user["contract_count"]
    pct = min(count / limit * 100, 100)
    cls = "full" if pct >= 100 else "warn" if pct >= 70 else ""
    st.markdown(
        f"""
    <div class="limit-bar-wrap">
        <div class="limit-label">
            <span>契約件数</span>
            <span>{count} / {limit}</span>
        </div>
        <div class="limit-bar"><div class="limit-fill {cls}" style="width:{pct}%"></div></div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ────────────────────────────────────────────
# Drum Picker Component (iOS-style scroll wheel)
# ────────────────────────────────────────────

def drum_picker(key: str, options: list, label: str = "", default_index: int = 0) -> str:
    """Render an iOS-style drum picker. Returns selected value."""
    if key not in st.session_state:
        st.session_state[key] = options[default_index]

    opts_json = "[" + ",".join(f'"{o}"' for o in options) + "]"
    init_val = st.session_state[key]
    init_idx = options.index(init_val) if init_val in options else default_index

    html = f"""
<style>
.drum-wrap {{
    position: relative; height: 180px; overflow: hidden;
    border-radius: 14px; background: #F7FAFC;
    border: 1.5px solid #E2E8F0;
    user-select: none;
}}
.drum-mask-top, .drum-mask-bot {{
    position: absolute; left:0; right:0; height:60px; z-index:2; pointer-events:none;
}}
.drum-mask-top {{ top:0; background: linear-gradient(to bottom, #F7FAFC 30%, transparent); }}
.drum-mask-bot {{ bottom:0; background: linear-gradient(to top, #F7FAFC 30%, transparent); }}
.drum-selector {{
    position: absolute; top:50%; left:8px; right:8px;
    transform: translateY(-50%);
    height: 52px; border-radius: 10px;
    background: rgba(0,196,140,0.12);
    border: 1.5px solid rgba(0,196,140,0.4);
    z-index:1; pointer-events:none;
}}
.drum-list {{
    position: absolute; width: 100%;
    transition: transform 0.15s cubic-bezier(.22,.61,.36,1);
    cursor: grab;
}}
.drum-item {{
    height: 52px; display: flex; align-items: center; justify-content: center;
    font-size: 17px; font-weight: 600; color: #2D3748;
    font-family: 'Noto Sans JP', sans-serif;
}}
#drum-label-{key} {{
    font-size: 12px; color: #718096; font-weight: 600;
    text-align:center; margin-bottom: 6px; letter-spacing: 0.5px;
}}
</style>
<div id="drum-label-{key}">{label}</div>
<div class="drum-wrap" id="drum-{key}">
    <div class="drum-mask-top"></div>
    <div class="drum-selector"></div>
    <div class="drum-list" id="list-{key}"></div>
    <div class="drum-mask-bot"></div>
</div>
<input type="hidden" id="val-{key}" value="{options[init_idx]}">
<script>
(function(){{
    const opts = {opts_json};
    const ITEM_H = 52;
    const PAD = 2; // number of padding items top/bottom
    const list = document.getElementById("list-{key}");
    const hiddenInput = document.getElementById("val-{key}");
    let currentIdx = {init_idx};
    let startY = 0, lastY = 0, offset = 0, animId = null;

    // Build padded list
    const allItems = [...Array(PAD).fill(null), ...opts, ...Array(PAD).fill(null)];
    allItems.forEach((o, i) => {{
        const div = document.createElement("div");
        div.className = "drum-item";
        div.textContent = o || "";
        list.appendChild(div);
    }});

    function setOffset(idx, animate) {{
        currentIdx = Math.max(0, Math.min(opts.length - 1, idx));
        offset = -( (currentIdx + PAD) * ITEM_H - 64 );
        list.style.transition = animate ? "transform 0.2s cubic-bezier(.22,.61,.36,1)" : "none";
        list.style.transform = "translateY(" + offset + "px)";
        hiddenInput.value = opts[currentIdx];
        hiddenInput.dispatchEvent(new Event("change"));
    }}
    setOffset({init_idx}, false);

    const drum = document.getElementById("drum-{key}");
    let isDragging = false;
    let dragStartOffset = 0;

    drum.addEventListener("touchstart", e => {{
        isDragging = true;
        startY = e.touches[0].clientY;
        dragStartOffset = offset;
        list.style.transition = "none";
    }}, {{passive: true}});

    drum.addEventListener("touchmove", e => {{
        if (!isDragging) return;
        const dy = e.touches[0].clientY - startY;
        offset = dragStartOffset + dy;
        list.style.transform = "translateY(" + offset + "px)";
        e.preventDefault();
    }}, {{passive: false}});

    drum.addEventListener("touchend", e => {{
        isDragging = false;
        const dy = e.changedTouches[0].clientY - startY;
        const idxDelta = -Math.round(dy / ITEM_H);
        setOffset(currentIdx + idxDelta, true);
    }});

    // Mouse events for desktop testing
    drum.addEventListener("mousedown", e => {{
        isDragging = true;
        startY = e.clientY;
        dragStartOffset = offset;
        list.style.transition = "none";
    }});
    document.addEventListener("mousemove", e => {{
        if (!isDragging) return;
        const dy = e.clientY - startY;
        offset = dragStartOffset + dy;
        list.style.transform = "translateY(" + offset + "px)";
    }});
    document.addEventListener("mouseup", e => {{
        if (!isDragging) return;
        isDragging = false;
        const dy = e.clientY - startY;
        const idxDelta = -Math.round(dy / ITEM_H);
        setOffset(currentIdx + idxDelta, true);
    }});

    // Post selected value to Streamlit via query params trick
    hiddenInput.addEventListener("change", () => {{
        // We'll use a polling approach via Streamlit's URL trick
    }});
}})();
</script>
"""
    # Render and provide a regular selectbox to capture actual value
    components.html(html, height=220)
    selected = st.selectbox(
        label,
        options=options,
        index=init_idx,
        key=f"sel_{key}",
        label_visibility="collapsed",
    )
    return selected


# ────────────────────────────────────────────
# Pages
# ────────────────────────────────────────────

def page_profile(user):
    """プロフィール登録画面 – 初回またはナビから"""
    render_nav(user)

    st.markdown(
        """
    <div style="text-align:center;padding:36px 0 20px;">
        <div style="font-size:56px;margin-bottom:16px;">👤</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:700;color:#1A1A2E;">
            はじめに
        </div>
        <div style="font-size:14px;color:#718096;margin-top:8px;">
            あなたの名前を登録しておくと、<br>契約作成がスムーズになります
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    current_name = user.get("display_name", "") or ""
    new_name = st.text_input(
        "名前（表示名）",
        value=current_name,
        placeholder="山田 太郎",
        key="profile_name_input",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 保存してはじめる", key="btn_save_profile"):
            if new_name.strip():
                save_display_name(user["id"], new_name.strip())
                st.success(f"「{new_name.strip()}」として登録しました！")
            st.session_state.page = "home"
            st.rerun()
    with col2:
        if st.button("→ スキップ", key="btn_skip_profile"):
            st.session_state.page = "home"
            st.rerun()


def page_sign(contract_id: str):
    """署名ページ（QRからアクセス）"""
    contract = get_contract(contract_id)

    st.markdown(
        '<div style="padding:16px 0 20px;font-family:Space Grotesk,sans-serif;font-size:20px;font-weight:700;color:#1A1A2E;">Fit<span style="color:#00C48C">Sign</span></div>',
        unsafe_allow_html=True,
    )

    if not contract:
        st.error("契約が見つかりません。URLを確認してください。")
        return

    if contract["status"] == "signed":
        st.markdown(
            f"""
        <div class="state-success">
            <div style="font-size:48px;margin-bottom:12px;">✅</div>
            <h2>署名済みです</h2>
            <p>{contract['signer_name']} さんが署名済みです</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    if contract["status"] == "rejected":
        reason = contract.get("rejection_reason", "") or ""
        st.markdown(
            f"""
        <div class="state-rejected">
            <div style="font-size:48px;margin-bottom:12px;">❌</div>
            <h2>差戻し済みです</h2>
            <p>{"理由: " + reason if reason else "この契約は差戻しされました"}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    # Contract header
    st.markdown(
        f"""
    <div class="fs-card" style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
        <span style="font-size:32px">{contract.get('template_emoji','📋')}</span>
        <div>
            <div style="font-weight:700;font-size:18px;color:#1A1A2E;">{contract['template_name']}</div>
            <div style="font-size:11px;color:#A0AEC0;">契約ID: {contract['id']}</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    body = contract["template_body"].format(
        content=contract["content"],
        amount=contract["amount"],
        contract_date=contract["contract_date"],
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
                    headers = _get_websocket_headers()
                    ip = headers.get("X-Forwarded-For", headers.get("X-Real-IP", "unknown"))
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
        name = st.session_state.sign_done
        st.markdown(
            f"""
        <div class="state-success" style="margin-top:16px;">
            <div style="font-size:40px;margin-bottom:10px;">🎉</div>
            <h2>締結完了！</h2>
            <p>{name} さんの署名が完了しました</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    if st.session_state.get("reject_done"):
        st.markdown(
            """
        <div class="state-rejected" style="margin-top:16px;">
            <div style="font-size:40px;margin-bottom:10px;">👋</div>
            <h2>差戻しました</h2>
            <p>作成者に内容の再確認を依頼しました</p>
        </div>
        """,
            unsafe_allow_html=True,
        )


def page_home(user):
    render_nav(user)

    # Hero
    name = user.get("display_name", "") or ""
    greeting = f"{name}さん、" if name else ""
    st.markdown(
        f"""
    <div class="fs-hero">
        <h1>{greeting}30秒で<br><span>契約</span>できる</h1>
        <p>テンプレ選んで入力するだけ。QRコードで相手が署名。</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Action grid – replaced with 2 Streamlit buttons
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
        <div class="fs-card" style="text-align:center;min-height:110px;display:flex;flex-direction:column;align-items:center;justify-content:center;">
            <div style="font-size:36px;margin-bottom:8px;">✍️</div>
            <div style="font-weight:700;font-size:14px;color:#1A1A2E;">契約を作る</div>
            <div style="font-size:11px;color:#A0AEC0;margin-top:2px;">新規作成</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("契約を作る", key="btn_create"):
            st.session_state.page = "create"
            st.rerun()
    with col2:
        st.markdown(
            """
        <div class="fs-card" style="text-align:center;min-height:110px;display:flex;flex-direction:column;align-items:center;justify-content:center;">
            <div style="font-size:36px;margin-bottom:8px;">📋</div>
            <div style="font-weight:700;font-size:14px;color:#1A1A2E;">契約一覧</div>
            <div style="font-size:11px;color:#A0AEC0;margin-top:2px;">作成した契約</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("契約一覧", key="btn_list"):
            st.session_state.page = "list"
            st.rerun()

    render_limit_bar(user)

    # How it works
    st.markdown(
        """
    <div class="fs-steps">
        <div style="font-size:13px;font-weight:700;color:#4A5568;margin-bottom:12px;">使い方</div>
        <div class="step-item">
            <div class="step-num">1</div>
            <div class="step-text">テンプレートを選んで内容を入力</div>
        </div>
        <div class="step-item">
            <div class="step-num">2</div>
            <div class="step-text">QRコードを相手のスマホで読み取る</div>
        </div>
        <div class="step-item">
            <div class="step-num">3</div>
            <div class="step-text">相手が署名して締結完了！</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    col_p, _ = st.columns([1, 2])
    with col_p:
        if st.button("👤 プロフィール設定"):
            st.session_state.page = "profile"
            st.rerun()


def page_create(user):
    render_nav(user)

    plan = user["plan"]
    count = user["contract_count"]
    limit = LIMIT_FREE if plan == "free" else LIMIT_PAID

    if count >= limit:
        st.markdown(
            """
        <div class="upgrade-cta">
            <div style="font-size:36px;margin-bottom:8px;">🔒</div>
            <h3>上限に達しました</h3>
            <p>有料プランで最大100件まで契約を作成できます</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("← ホームに戻る"):
            st.session_state.page = "home"
            st.rerun()
        return

    st.markdown("## 契約を作る")

    # ── Step 1: Template selection ──
    st.markdown("**① テンプレートを選択**")
    templates = get_templates(plan)
    selected_tmpl = st.session_state.get("selected_template", None)

    for tmpl in templates:
        is_selected = selected_tmpl and selected_tmpl["id"] == tmpl["id"]
        sel_class = " selected" if is_selected else ""
        st.markdown(
            f"""
        <div class="tmpl-card{sel_class}">
            <span class="tmpl-emoji">{tmpl['emoji']}</span>
            <div>
                <div class="tmpl-name">{tmpl['name']}</div>
                <div class="tmpl-desc">{tmpl['description']}</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        _lbl = ('\u2705 \u9078\u629e\u4e2d' if is_selected else ('\u9078\u629e\uff1a' + tmpl['name']))
        if st.button(
            _lbl,
            key=f"tmpl_{tmpl['id']}",
        ):
            st.session_state.selected_template = tmpl
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if not selected_tmpl:
        st.info("テンプレートを選択してください")
        if st.button("← 戻る"):
            st.session_state.page = "home"
            st.rerun()
        return

    st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)
    st.markdown("**② 内容を入力**")

    content = st.text_input("業務内容", placeholder="ウェブサイトのデザイン制作")
    contract_date = st.date_input("日付")

    st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)

    # ── Drum Picker for Amount ──
    st.markdown("**③ 金額をドラムで選択（円）**")
    man_options = [f"{i}万" for i in range(0, 101)]
    sen_options = [f"{i}千" for i in range(0, 10)]
    hyaku_options = [f"{i}百" for i in range(0, 10)]

    col_m, col_s, col_h = st.columns(3)
    with col_m:
        man = drum_picker("man", man_options, "万の位", 0)
    with col_s:
        sen = drum_picker("sen", sen_options, "千の位", 0)
    with col_h:
        hyaku = drum_picker("hyaku", hyaku_options, "百の位", 0)

    man_n = int(man.replace("万", "")) * 10000
    sen_n = int(sen.replace("千", "")) * 1000
    hyaku_n = int(hyaku.replace("百", "")) * 100
    total_amount = man_n + sen_n + hyaku_n
    st.markdown(
        f'<div class="fs-card" style="text-align:center;padding:14px;">💰 <strong>{total_amount:,}円</strong></div>',
        unsafe_allow_html=True,
    )

    # Manual override
    manual_amount = st.text_input("または金額を直接入力（任意）", placeholder="123,456", key="manual_amount_input")

    st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 戻る"):
            st.session_state.page = "home"
            st.rerun()
    with col2:
        if st.button("契約を作成する →"):
            if not content.strip():
                st.error("内容を入力してください")
            else:
                amount_str = manual_amount.strip() if manual_amount.strip() else f"{total_amount:,}"
                contract_id = create_contract(
                    creator_id=user["id"],
                    template_id=selected_tmpl["id"],
                    content=content.strip(),
                    amount=amount_str,
                    contract_date=str(contract_date),
                )
                st.session_state.created_contract_id = contract_id
                st.session_state.selected_template = None
                st.session_state.page = "qr"
                st.rerun()


def page_qr(user):
    render_nav(user)

    contract_id = st.session_state.get("created_contract_id")
    if not contract_id:
        st.session_state.page = "home"
        st.rerun()
        return

    contract = get_contract(contract_id)
    if not contract:
        st.error("契約が見つかりません")
        return

    base_url = get_base_url()
    sign_url = f"{base_url}/?page=sign&id={contract_id}"

    st.markdown(
        f"""
    <div style="background:#C6F6D5;border-radius:16px;padding:14px 16px;margin-bottom:20px;display:flex;align-items:center;gap:10px;">
        <span style="font-size:20px">✅</span>
        <div>
            <div style="font-weight:700;color:#276749;font-size:14px;">契約を作成しました！</div>
            <div style="font-size:12px;color:#2F855A;">相手にQRコードを読み取ってもらいましょう</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    qr_b64 = generate_qr(sign_url)
    st.markdown(
        f"""
    <div class="qr-box">
        <div style="font-size:13px;color:#718096;margin-bottom:16px;">相手のスマホで読み取る</div>
        <img src="data:image/png;base64,{qr_b64}" width="220">
        <div style="font-size:11px;color:#A0AEC0;margin-top:12px;">契約ID: {contract_id}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.text_input("署名URL（コピーして送れます）", value=sign_url, disabled=True)

    with st.expander("契約内容を確認"):
        body = contract["template_body"].format(
            content=contract["content"],
            amount=contract["amount"],
            contract_date=contract["contract_date"],
        )
        st.markdown(f'<div class="contract-body">{body}</div>', unsafe_allow_html=True)

    if st.button("🔄 署名状況を確認"):
        st.rerun()

    latest = get_contract(contract_id)
    if latest and latest["status"] == "signed":
        st.markdown(
            f"""
        <div class="state-success">
            <div style="font-size:40px;margin-bottom:10px;">🎉</div>
            <h2>締結完了！</h2>
            <p>{latest['signer_name']} さんが署名しました</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    elif latest and latest["status"] == "rejected":
        reason = latest.get("rejection_reason", "") or ""
        st.markdown(
            f"""
        <div class="state-rejected">
            <div style="font-size:40px;margin-bottom:10px;">❌</div>
            <h2>差戻されました</h2>
            <p>{"理由: " + reason if reason else "内容を確認してください"}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← ホーム"):
            st.session_state.page = "home"
            st.rerun()
    with col2:
        if st.button("📋 一覧を見る"):
            st.session_state.page = "list"
            st.rerun()


def page_list(user):
    render_nav(user)

    st.markdown("## 契約一覧")
    render_limit_bar(user)

    contracts = get_user_contracts(user["id"])

    if not contracts:
        st.markdown(
            """
        <div style="text-align:center;padding:48px 0;color:#A0AEC0;">
            <div style="font-size:48px;margin-bottom:12px;">📄</div>
            <div style="font-size:15px;">まだ契約がありません</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        for c in contracts:
            if c["status"] == "signed":
                status_badge = '<span class="badge-signed">締結済み ✅</span>'
            elif c["status"] == "rejected":
                status_badge = '<span class="badge-rejected">差戻し ❌</span>'
            else:
                status_badge = '<span class="badge-draft">未署名 ⏳</span>'

            signed_info = f"署名者: {c['signer_name']}" if c.get("signer_name") else f"作成: {c['created_at'][:10]}"
            rejection_text = f"<div style='font-size:11px;color:#9B2335;margin-top:4px;'>理由: {c['rejection_reason']}</div>" if c.get("rejection_reason") else ""

            st.markdown(
                f"""
            <div class="contract-list-card">
                <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span style="font-size:20px">{c.get('template_emoji','📋')}</span>
                        <div>
                            <div style="font-weight:700;font-size:14px;color:#1A1A2E;">{c['template_name']}</div>
                            <div style="font-size:11px;color:#A0AEC0;">{c['id']}</div>
                        </div>
                    </div>
                    {status_badge}
                </div>
                <div style="font-size:13px;color:#4A5568;margin-bottom:4px;">📝 {c['content'][:30]}{'...' if len(c['content'])>30 else ''}</div>
                <div style="font-size:12px;color:#718096;">{signed_info}</div>
                {rejection_text}
            </div>
            """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("詳細・QR", key=f"detail_{c['id']}"):
                    st.session_state.viewing_contract = c["id"]
                    st.session_state.page = "detail"
                    st.rerun()
            with col2:
                if c["status"] == "signed":
                    pdf_buf = generate_pdf(get_contract(c["id"]))
                    st.download_button(
                        "📥 PDF",
                        data=pdf_buf,
                        file_name=f"contract_{c['id']}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{c['id']}",
                    )

            st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← ホーム"):
            st.session_state.page = "home"
            st.rerun()
    with col2:
        if st.button("✍️ 新規契約"):
            st.session_state.page = "create"
            st.rerun()

    with st.expander("⚙️ 開発者設定"):
        st.markdown(f"**あなたのID:** `{user['id']}`")
        st.markdown(f"**プラン:** {user['plan']}")
        st.markdown("---")
        st.markdown("**ベースURL設定**（QRコード用）")
        new_base = st.text_input("BASE_URL", value=get_base_url())
        if st.button("URLを保存"):
            st.session_state.base_url = new_base
            st.success("保存しました")

        st.markdown("---")
        if user["plan"] == "free":
            if st.button("🔓 有料プランに変更（テスト用）"):
                upgrade_to_paid(user["id"])
                st.success("有料プランに変更しました")
                st.rerun()
        else:
            st.success("有料プランです")


def page_detail(user):
    render_nav(user)

    contract_id = st.session_state.get("viewing_contract")
    if not contract_id:
        st.session_state.page = "list"
        st.rerun()
        return

    contract = get_contract(contract_id)
    if not contract or contract["creator_id"] != user["id"]:
        st.error("契約が見つかりません")
        return

    status = contract["status"]
    if status == "signed":
        status_badge = '<span class="badge-signed">締結済み ✅</span>'
    elif status == "rejected":
        status_badge = '<span class="badge-rejected">差戻し ❌</span>'
    else:
        status_badge = '<span class="badge-draft">未署名 ⏳</span>'

    st.markdown(
        f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <span style="font-size:28px">{contract.get('template_emoji','📋')}</span>
        <div>
            <div style="font-weight:700;font-size:18px;color:#1A1A2E;">{contract['template_name']} {status_badge}</div>
            <div style="font-size:12px;color:#A0AEC0;">契約ID: {contract['id']}</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    body = contract["template_body"].format(
        content=contract["content"],
        amount=contract["amount"],
        contract_date=contract["contract_date"],
    )
    st.markdown(f'<div class="contract-body">{body}</div>', unsafe_allow_html=True)

    if status == "signed":
        st.markdown(
            f"""
        <div class="fs-card" style="margin-top:0;">
            <div style="font-size:12px;color:#718096;margin-bottom:4px;">署名者</div>
            <div style="font-weight:700;font-size:16px;">{contract['signer_name']}</div>
            <div style="font-size:12px;color:#718096;margin-top:8px;">{contract.get('signed_at','')[:19]}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        pdf_buf = generate_pdf(contract)
        st.download_button(
            "📥 PDFをダウンロード",
            data=pdf_buf,
            file_name=f"fitsign_{contract['id']}.pdf",
            mime="application/pdf",
        )
    elif status == "rejected":
        reason = contract.get("rejection_reason", "") or ""
        st.markdown(
            f"""
        <div class="state-rejected">
            <div style="font-size:32px;margin-bottom:8px;">❌</div>
            <h2>差戻されました</h2>
            <p>{"理由: " + reason if reason else "理由なし"}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        base_url = get_base_url()
        sign_url = f"{base_url}/?page=sign&id={contract_id}"
        qr_b64 = generate_qr(sign_url)
        st.markdown(
            f"""
        <div class="qr-box">
            <div style="font-size:13px;color:#718096;margin-bottom:16px;">相手のスマホで読み取る</div>
            <img src="data:image/png;base64,{qr_b64}" width="200">
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.text_input("署名URL", value=sign_url, disabled=True)

    with st.expander("🔐 改ざんチェック"):
        st.markdown(f"**SHA-256:** `{contract.get('hash','')}`")
        st.caption("この値を保存しておくことで、契約内容の改ざんを検証できます")

    if st.button("← 一覧に戻る"):
        st.session_state.page = "list"
        st.rerun()


# ────────────────────────────────────────────
# Router
# ────────────────────────────────────────────

def main():
    params = st.query_params
    page_param = params.get("page", "")
    contract_id_param = params.get("id", "")

    if page_param == "sign" and contract_id_param:
        page_sign(contract_id_param)
        return

    user_id = get_user_id()
    user = get_or_create_user(user_id)

    # First-time: redirect to profile setup
    if "page" not in st.session_state:
        if not user.get("display_name"):
            st.session_state.page = "profile"
        else:
            st.session_state.page = "home"

    current_page = st.session_state.page

    if current_page == "home":
        page_home(user)
    elif current_page == "profile":
        page_profile(user)
    elif current_page == "create":
        page_create(user)
    elif current_page == "qr":
        page_qr(user)
    elif current_page == "list":
        page_list(user)
    elif current_page == "detail":
        page_detail(user)
    else:
        st.session_state.page = "home"
        st.rerun()


main()
