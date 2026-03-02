import streamlit as st
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
    get_user_contracts,
    upgrade_to_paid,
    delete_draft_contract,
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
# CSS – モダン・クリーン・モバイルファースト
# ────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&family=Space+Grotesk:wght@500;700&display=swap');

/* Reset & base */
html, body, [class*="css"] {
    font-family: 'Noto Sans JP', sans-serif;
}
.main > div { padding-top: 0 !important; }
section[data-testid="stSidebar"] { display: none; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 1rem 4rem !important; max-width: 480px !important; }

/* App shell */
.fs-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 0 12px;
    border-bottom: 2px solid #111;
    margin-bottom: 28px;
}
.fs-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 22px; font-weight: 700; letter-spacing: -0.5px;
    color: #111;
}
.fs-logo span { color: #00C48C; }

/* Hero */
.fs-hero {
    background: #111;
    border-radius: 20px;
    padding: 32px 24px;
    margin-bottom: 24px;
    color: white;
    text-align: center;
}
.fs-hero h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 28px; font-weight: 700; margin: 0 0 8px;
    letter-spacing: -1px; line-height: 1.2;
}
.fs-hero p { font-size: 14px; opacity: 0.7; margin: 0; }
.fs-badge {
    display: inline-block;
    background: #00C48C; color: #111;
    font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px;
    margin-bottom: 14px; letter-spacing: 0.5px;
}

.fs-card {
    background: white;
    border: 1.5px solid #E5E7EB;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 20px; /* 余白を広げた */
    transition: border-color 0.15s;
    min-height: 120px; /* 箱の高さを揃える */
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.fs-card:hover { border-color: #111; }
.fs-card-selected {
    border: 2px solid #111 !important;
    background: #F9FAFB;
}

/* Template cards */
.tmpl-card {
    background: white;
    border: 1.5px solid #E5E7EB;
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 12px;
    cursor: pointer;
    display: flex; align-items: center; gap: 14px;
    min-height: 80px; /* テンプレートも高さを揃える */
}
.tmpl-emoji { font-size: 28px; }
.tmpl-name { font-weight: 700; font-size: 15px; color: #111; }
.tmpl-desc { font-size: 12px; color: #6B7280; margin-top: 2px; }

/* Status badges */
.badge-signed {
    background: #D1FAE5; color: #065F46;
    font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px;
}
.badge-draft {
    background: #FEF3C7; color: #92400E;
    font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px;
}
.badge-rejected {
    background: #FEE2E2; color: #991B1B;
    font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px;
}

/* Contract detail */
.contract-body {
    background: #F9FAFB;
    border-radius: 12px;
    padding: 20px;
    font-size: 14px;
    line-height: 1.8;
    white-space: pre-wrap;
    color: #1F2937;
    border: 1px solid #E5E7EB;
    margin: 16px 0;
    font-family: 'Noto Sans JP', sans-serif;
}

/* Limit bar */
.limit-bar-wrap { margin: 16px 0; }
.limit-label { font-size: 12px; color: #6B7280; margin-bottom: 6px; display: flex; justify-content: space-between; }
.limit-bar { height: 6px; background: #E5E7EB; border-radius: 3px; overflow: hidden; }
.limit-fill { height: 100%; background: #111; border-radius: 3px; transition: width 0.3s; }
.limit-fill.warn { background: #F59E0B; }
.limit-fill.full { background: #EF4444; }

/* Plan badge */
.plan-free { background: #F3F4F6; color: #374151; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.plan-paid { background: #111; color: white; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 20px; }

/* QR box */
.qr-box {
    background: #F9FAFB;
    border: 1.5px solid #E5E7EB;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    margin: 16px 0;
}
.qr-box img { border-radius: 8px; }

/* Separator */
.fs-sep { border: none; border-top: 1.5px solid #E5E7EB; margin: 20px 0; }

/* Sign success */
.sign-success {
    background: #D1FAE5;
    border-radius: 16px;
    padding: 28px;
    text-align: center;
    margin: 20px 0;
}
.sign-success h2 { font-size: 24px; color: #065F46; margin: 0 0 8px; }
.sign-success p { font-size: 14px; color: #047857; margin: 0; }

/* Upgrade CTA */
.upgrade-cta {
    background: linear-gradient(135deg, #111 0%, #374151 100%);
    border-radius: 16px;
    padding: 24px;
    color: white;
    text-align: center;
    margin: 16px 0;
}
.upgrade-cta h3 { font-size: 18px; margin: 0 0 8px; }
.upgrade-cta p { font-size: 13px; opacity: 0.8; margin: 0 0 16px; }

/* Step indicator */
.step-row { display: flex; align-items: center; gap: 8px; margin-bottom: 20px; }
.step-dot { width: 28px; height: 28px; border-radius: 50%; background: #111; color: white; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; flex-shrink: 0; }
.step-dot.inactive { background: #E5E7EB; color: #9CA3AF; }
.step-line { flex: 1; height: 2px; background: #E5E7EB; }

/* Override Streamlit buttons */
div.stButton > button {
    width: 100%;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-family: 'Noto Sans JP', sans-serif !important;
    font-size: 14px !important; /* 少し小さくして文字切れ防止 */
    padding: 10px 4px !important; /* 横のパディングを狭めた */
    border: none !important;
    transition: all 0.15s !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
div.stButton > button:first-child {
    background: #111 !important;
    color: white !important;
}
div.stButton > button:first-child:hover {
    background: #374151 !important;
    transform: translateY(-1px) !important;
}

/* Text inputs */
div.stTextInput > div > div > input,
div.stSelectbox > div > div,
div.stDateInput > div > div > input {
    border-radius: 10px !important;
    border: 1.5px solid #E5E7EB !important;
    font-family: 'Noto Sans JP', sans-serif !important;
}
div.stTextInput > div > div > input:focus {
    border-color: #111 !important;
    box-shadow: 0 0 0 2px rgba(17,17,17,0.08) !important;
}

/* Checkbox */
div.stCheckbox label { font-size: 14px !important; }

/* Info box */
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
    img = qr.make_image(fill_color="black", back_color="white")
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

    st.markdown(
        f"""
    <div class="fs-nav">
        <div class="fs-logo">Fit<span>Sign</span></div>
        <div>{plan_html}</div>
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
# Pages
# ────────────────────────────────────────────


def page_sign(contract_id: str):
    """署名ページ（QRからアクセス）"""
    contract = get_contract(contract_id)

    st.markdown('<div class="fs-logo" style="padding:16px 0 20px;font-family:Space Grotesk,sans-serif;font-size:20px;font-weight:700;">Fit<span style="color:#00C48C">Sign</span></div>', unsafe_allow_html=True)

    if not contract:
        st.error("契約が見つかりません。URLを確認してください。")
        return

    if contract["status"] == "signed":
        st.markdown(
            f"""
        <div class="sign-success">
            <div style="font-size:48px;margin-bottom:12px;">✅</div>
            <h2>署名済みです</h2>
            <p>{contract['signer_name']} さんが署名済みです</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    # テンプレート名
    st.markdown(
        f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <span style="font-size:28px">{contract.get('template_emoji','📋')}</span>
        <div>
            <div style="font-weight:700;font-size:18px;color:#111;">{contract['template_name']}</div>
            <div style="font-size:12px;color:#6B7280;">契約ID: {contract['id']}</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 契約本文
    body = contract["template_body"].format(
        content=contract["content"],
        amount=contract["amount"],
        contract_date=contract["contract_date"],
    )
    st.markdown(f'<div class="contract-body">{body}</div>', unsafe_allow_html=True)

    st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)

    # 署名フォーム
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
                from db import reject_contract
                reject_contract(contract["id"], reason)
                st.session_state.show_reject = False
                st.session_state.reject_done = True
                st.rerun()

    if st.session_state.get("sign_done"):
        name = st.session_state.sign_done
        st.markdown(
            f"""
        <div class="sign-success" style="margin-top:16px;">
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
        <div style="background:#FEE2E2;border-radius:16px;padding:28px;text-align:center;margin-top:16px;color:#991B1B;">
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
    st.markdown(
        """
    <div class="fs-hero">
        <div class="fs-badge">スマホ2台で完結</div>
        <h1>30秒で<br>契約できる</h1>
        <p>テンプレ選んで入力するだけ。<br>QRコードで相手が署名。</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✍️ 契約を作る"):
            st.session_state.page = "create"
            st.rerun()
    with col2:
        if st.button("📋 契約一覧"):
            st.session_state.page = "list"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    render_limit_bar(user)

    # 使い方
    st.markdown(
        """
    <div style="margin-top:8px;">
        <div style="font-size:13px;font-weight:700;color:#374151;margin-bottom:12px;">使い方</div>
        <div style="display:flex;flex-direction:column;gap:8px;">
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="width:28px;height:28px;background:#111;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:700;flex-shrink:0;">1</div>
                <div style="font-size:13px;color:#374151;">テンプレートを選んで内容を入力</div>
            </div>
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="width:28px;height:28px;background:#111;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:700;flex-shrink:0;">2</div>
                <div style="font-size:13px;color:#374151;">QRコードを相手のスマホで読み取る</div>
            </div>
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="width:28px;height:28px;background:#111;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:700;flex-shrink:0;">3</div>
                <div style="font-size:13px;color:#374151;">相手が署名して締結完了</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


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

    # テンプレ選択
    st.markdown("**① テンプレートを選択**")
    templates = get_templates(plan)

    selected_tmpl = st.session_state.get("selected_template", None)

    for tmpl in templates:
        is_selected = selected_tmpl and selected_tmpl["id"] == tmpl["id"]
        border = "border: 2px solid #111;" if is_selected else "border: 1.5px solid #E5E7EB;"
        bg = "background:#F9FAFB;" if is_selected else ""
        if st.button(
            f"{tmpl['emoji']}  {tmpl['name']}  —  {tmpl['description']}",
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

    st.markdown(f"**選択中:** {selected_tmpl['emoji']} {selected_tmpl['name']}")
    st.markdown('<hr class="fs-sep">', unsafe_allow_html=True)

    st.markdown("**② 内容を入力**")
    content = st.text_input("業務内容・内容", placeholder="ウェブサイトのデザイン制作")
    amount = st.text_input("金額・条件", placeholder="50,000")
    contract_date = st.date_input("日付")

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
            elif not amount.strip():
                st.error("金額・条件を入力してください")
            else:
                contract_id = create_contract(
                    creator_id=user["id"],
                    template_id=selected_tmpl["id"],
                    content=content.strip(),
                    amount=amount.strip(),
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

    st.markdown("## QRコードを表示")
    st.markdown(
        f"""
    <div style="background:#D1FAE5;border-radius:12px;padding:14px 16px;margin-bottom:16px;display:flex;align-items:center;gap:10px;">
        <span style="font-size:20px">✅</span>
        <div>
            <div style="font-weight:700;color:#065F46;font-size:14px;">契約を作成しました！</div>
            <div style="font-size:12px;color:#047857;">相手にQRコードを読み取ってもらいましょう</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # QR
    qr_b64 = generate_qr(sign_url)
    st.markdown(
        f"""
    <div class="qr-box">
        <div style="font-size:13px;color:#6B7280;margin-bottom:16px;">相手のスマホで読み取る</div>
        <img src="data:image/png;base64,{qr_b64}" width="220">
        <div style="font-size:11px;color:#9CA3AF;margin-top:12px;">契約ID: {contract_id}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # URL表示
    st.text_input("署名URL（コピーして送ることもできます）", value=sign_url, disabled=True)

    # 契約内容プレビュー
    with st.expander("契約内容を確認"):
        body = contract["template_body"].format(
            content=contract["content"],
            amount=contract["amount"],
            contract_date=contract["contract_date"],
        )
        st.markdown(f'<div class="contract-body">{body}</div>', unsafe_allow_html=True)

    # ステータス確認
    if st.button("🔄 署名状況を確認"):
        st.rerun()

    latest = get_contract(contract_id)
    if latest and latest["status"] == "signed":
        st.markdown(
            f"""
        <div class="sign-success">
            <div style="font-size:40px;margin-bottom:10px;">🎉</div>
            <h2>締結完了！</h2>
            <p>{latest['signer_name']} さんが署名しました</p>
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
        <div style="text-align:center;padding:48px 0;color:#9CA3AF;">
            <div style="font-size:48px;margin-bottom:12px;">📄</div>
            <div style="font-size:15px;">まだ契約がありません</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        for c in contracts:
            status_badge = ""
            if c["status"] == "signed":
                status_badge = '<span class="badge-signed">締結済み ✅</span>'
            elif c["status"] == "rejected":
                status_badge = '<span class="badge-rejected">差戻し ❌</span>'
            else:
                status_badge = '<span class="badge-draft">未署名 ⏳</span>'
            
            signed_info = f"署名者: {c['signer_name']}" if c.get("signer_name") else f"作成: {c['created_at'][:10]}"
            rejection_text = f"<div style='font-size:11px;color:#991B1B;margin-top:4px;'>理由: {c['rejection_reason']}</div>" if c.get("rejection_reason") else ""

            st.markdown(
                f"""
            <div class="fs-card">
                <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span style="font-size:20px">{c.get('template_emoji','📋')}</span>
                        <div>
                            <div style="font-weight:700;font-size:14px;color:#111;">{c['template_name']}</div>
                            <div style="font-size:11px;color:#9CA3AF;">{c['id']}</div>
                        </div>
                    </div>
                    {status_badge}
                </div>
                <div style="font-size:13px;color:#374151;margin-bottom:4px;">📝 {c['content'][:30]}{'...' if len(c['content'])>30 else ''}</div>
                <div style="font-size:12px;color:#6B7280;">{signed_info}</div>
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

    # Admin section
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
    status_badge = ""
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
            <div style="font-weight:700;font-size:18px;color:#111;">{contract['template_name']} {status_badge}</div>
            <div style="font-size:12px;color:#6B7280;">契約ID: {contract['id']}</div>
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
        <div style="background:#F9FAFB;border-radius:12px;padding:16px;border:1px solid #E5E7EB;">
            <div style="font-size:12px;color:#6B7280;margin-bottom:4px;">署名者</div>
            <div style="font-weight:700;font-size:16px;">{contract['signer_name']}</div>
            <div style="font-size:12px;color:#6B7280;margin-top:8px;">{contract.get('signed_at','')[:19]}</div>
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
    else:
        # QR再表示
        base_url = get_base_url()
        sign_url = f"{base_url}/?page=sign&id={contract_id}"
        qr_b64 = generate_qr(sign_url)
        st.markdown(
            f"""
        <div class="qr-box">
            <div style="font-size:13px;color:#6B7280;margin-bottom:16px;">相手のスマホで読み取る</div>
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
    # Query params routing（署名ページ）
    params = st.query_params
    page_param = params.get("page", "")
    contract_id_param = params.get("id", "")

    if page_param == "sign" and contract_id_param:
        page_sign(contract_id_param)
        return

    # 通常アプリ
    user_id = get_user_id()
    user = get_or_create_user(user_id)

    if "page" not in st.session_state:
        st.session_state.page = "home"

    current_page = st.session_state.page

    if current_page == "home":
        page_home(user)
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
