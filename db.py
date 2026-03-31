import uuid
import hashlib
import json
import os
import base64
import time
import urllib.parse
from datetime import datetime, timezone

import streamlit as st
import requests
from supabase import create_client

# ============================================================
#  Supabase クライアント（secrets.toml / Streamlit Cloud Secrets）
# ============================================================
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


# ============================================================
#  テンプレート文字列（template_bodyが取れない同意書用）
# ============================================================
CONSENT_BUSINESS_TEMPLATE = """業務に関する同意書

私（以下「同意者」という）は、貴社との間で実施する以下の業務（以下「本件」という）に関し、以下の事項を遵守することに同意いたします。
対象事項： {content}

第1条（秘密保持）
同意者は、本件に関して貴社から提供された一切の技術上、営業上その他の情報（以下「秘密情報」という）を厳重に管理し、貴社の事前の書面による承諾なく、第三者に開示または漏洩しないものとする。

第2条（権利の帰属・許諾）
本件に関連して同意者が提供したデータ、画像、成果物等の著作権や使用権については、貴社が本件の目的の範囲内で自由に利用することを許諾する。

第3条（禁止事項および損害賠償）
同意者は、本件を通じて得た情報を利用して貴社の不利益となる行為を行ってはならない。本同意書の定めに違反し貴社に損害を与えた場合、その損害を賠償する責任を負うものとする。"""


CONSENT_PRIVATE_TEMPLATE = """プライベートに関する同意書

甲（以下「甲」という）と、乙（以下「乙」という）は、両者間で実施する以下の事項（以下「本件」という）に関し、お互いを尊重し、以下の通り合意する。
対象事項： {content}

第1条（自由意志の確認）
甲および乙は、本件を実施するにあたり、いかなる強要、脅迫、または正常な判断ができない状態（過度な飲酒や薬物の影響等）にもなく、完全なる自由意志に基づいて、性的接触を含む本件の実施に同意したことを相互に確認する。

第2条（同意の撤回・中止の権利）
1. 甲および乙は、本同意書への署名後、または本件の実施途中であっても、自身の意思によりいつでも本同意を撤回し、直ちに本件を中止する権利を有する。
2. 前項の撤回や中止が行われた場合、双方はそれを速やかに受け入れ、相手方に対して金銭的・精神的なペナルティや責任を追及しないものとする。

第3条（プライバシーの保護と撮影・録音の禁止）
甲および乙は、相手方の明確な事前の同意がない限り、本件に関する写真、動画、音声等の記録を一切行ってはならない。また、本件に関する私的な情報を、SNS等のインターネット上や第三者に漏洩・公開してはならない。

第4条（健康と安全の配慮）
甲および乙は、本件の実施にあたり、お互いの心身の健康と安全を最優先とし、必要な配慮を誠実に行うものとする。"""


LIMIT_FREE = 3


def init_db():
    """Supabase移行後は不要だがapp.pyとの互換性のために残す"""
    pass


# ============================================================
#  認証（Supabase Auth × Google OAuth / PKCE）
# ============================================================

@st.cache_resource
def _pkce_storage():
    """フローID毎に PKCE code_verifier を保持するストア。
    サーバーサイドで一元管理し、リダイレクト後の照合に使用。
    """
    return {}


def _generate_pkce_pair():
    """code_verifier と code_challenge を生成する"""
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode().rstrip("=")
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return code_verifier, code_challenge


def get_auth_url(provider: str, redirect_to: str) -> str:
    """OAuth の認証URLを返す。
    PKCE ミスマッチを防ぐため、フローIDを発行して管理。
    """
    code_verifier, code_challenge = _generate_pkce_pair()
    flow_id = str(uuid.uuid4())

    # サーバーサイドに保存
    storage = _pkce_storage()
    storage[flow_id] = {
        "cv": code_verifier,
        "ts": time.time()
    }

    # redirect_to に flow_id (fid) を付与
    sep = "&" if "?" in redirect_to else "?"
    final_redirect = f"{redirect_to}{sep}fid={flow_id}"

    supabase_url = st.secrets["SUPABASE_URL"].rstrip("/")
    qs = urllib.parse.urlencode({
        "provider": provider,
        "redirect_to": final_redirect,
        "code_challenge": code_challenge,
        "code_challenge_method": "s256",
        # LINE 等で profile 情報を取得するために必要
        "scope": "openid profile email" if provider == "google" else "openid profile",
    })
    return f"{supabase_url}/auth/v1/authorize?{qs}"


def get_google_auth_url(redirect_to: str) -> str:
    return get_auth_url("google", redirect_to)


import requests
import uuid

def get_line_auth_url(redirect_to: str) -> str:
    """LINEの認可URLを直接生成する（Supabaseを介さない）"""
    flow_id = str(uuid.uuid4())
    code_verifier, code_challenge = _generate_pkce_pair()
    
    storage = _pkce_storage()
    storage[flow_id] = {
        "cv": code_verifier,
        "ts": time.time(),
        "type": "line_direct"
    }
    
    line_client_id = st.secrets.get("LINE_CHANNEL_ID", "2009662287")
    # Streamlit Cloud のベースURLを特定
    base_url = st.secrets.get("BASE_URL", "https://fit-sign.streamlit.app")
    redirect_uri = base_url.rstrip("/") + "/"
    
    qs = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": line_client_id,
        "redirect_uri": redirect_uri,
        "state": flow_id,  # fid として state に入れる
        "scope": "profile openid",
        "nonce": str(uuid.uuid4()),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })
    return f"https://access.line.me/oauth2/v2.1/authorize?{qs}"


def exchange_line_code(code: str, flow_id: str):
    """LINEの認証コードをトークンとプロフィールに交換する"""
    storage = _pkce_storage()
    data = storage.get(flow_id)
    if not data or data.get("type") != "line_direct":
        raise ValueError("認証セッションが無効です。")
    
    cv = data.get("cv", "")
    line_client_id = st.secrets.get("LINE_CHANNEL_ID")
    line_client_secret = st.secrets.get("LINE_CHANNEL_SECRET")
    base_url = st.secrets.get("BASE_URL", "https://fit-sign.streamlit.app")
    redirect_uri = base_url.rstrip("/") + "/"
    
    # 1. Token Exchange
    res = requests.post("https://api.line.me/oauth2/v2.1/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": line_client_id,
        "client_secret": line_client_secret,
        "code_verifier": cv
    })
    res.raise_for_status()
    tokens = res.json()
    access_token = tokens.get("access_token")
    
    # 2. Get Profile
    res_prof = requests.get("https://api.line.me/v2/profile", headers={
        "Authorization": f"Bearer {access_token}"
    })
    res_prof.raise_for_status()
    profile = res_prof.json()
    
    line_user_id = profile.get("userId")
    if not line_user_id:
        raise ValueError("LINEプロフィールの取得に失敗しました。")
    
    # LINE ID から 決定的な UUID を生成して Supabase の ID として使う
    # これにより、同じ LINE ユーザーなら常に同じ UUID になる
    ns_line = uuid.UUID("ead04e57-acc3-4f93-b673-f11909a43063") # 固定の名前空間
    user_uuid = str(uuid.uuid5(ns_line, line_user_id))
    
    storage.pop(flow_id, None)
    
    return {
        "id": user_uuid,
        "display_name": profile.get("displayName"),
        "picture_url": profile.get("pictureUrl"),
        "email": "" # LINE profileからは通常emailは返らない
    }


def exchange_code_for_session(code: str, flow_id: str = ""):
    """OAuth コールバックのコードをセッションに交換する"""
    cv = ""
    if flow_id:
        storage = _pkce_storage()
        data = storage.get(flow_id)
        if data:
            ts = data.get("ts", 0.0)
            # 有効期限 10分
            if (time.time() - ts) < 600:
                cv = data.get("cv", "")
            storage.pop(flow_id, None)  # 使い捨て

    if not cv:
        raise ValueError("認証セッションが無効、または期限切れです。もう一度ログインしてください。")

    sb = get_supabase()
    return sb.auth.exchange_code_for_session({
        "auth_code": code,
        "code_verifier": cv,
    })


def sign_out():
    """ログアウト"""
    sb = get_supabase()
    sb.auth.sign_out()


# ============================================================
#  ユーザー
# ============================================================
def get_or_create_user(user_id: str, metadata: dict = None) -> dict:
    """ユーザーを取得、存在しなければ作成する。
    metadata: {'email': ..., 'display_name': ...}
    """
    sb = get_supabase()
    res = sb.table("users").select("*").eq("id", user_id).execute()
    if res.data:
        # 既に存在する場合、必要に応じて更新（またはそのまま返す）
        return res.data[0]
    
    # 新規作成
    now = datetime.now(timezone.utc).isoformat()
    email = metadata.get("email", "") if metadata else ""
    name = metadata.get("display_name", "") if metadata else ""
    
    sb.table("users").insert({
        "id": user_id,
        "created_at": now,
        "plan": "free",
        "contract_count": 0,
        "display_name": name,
        "email": email,
    }).execute()
    
    res = sb.table("users").select("*").eq("id", user_id).execute()
    return res.data[0]


def get_user(user_id: str):
    sb = get_supabase()
    res = sb.table("users").select("*").eq("id", user_id).execute()
    return res.data[0] if res.data else None


def save_user_profile(user_id: str, name: str, address: str, phone: str, email: str):
    sb = get_supabase()
    sb.table("users").update({
        "display_name": name,
        "address": address,
        "phone": phone,
        "email": email,
    }).eq("id", user_id).execute()


# ============================================================
#  テンプレート
# ============================================================
def get_templates(plan: str = "free") -> list:
    sb = get_supabase()
    if plan == "paid":
        res = sb.table("templates").select("*").execute()
    else:
        res = sb.table("templates").select("*").eq("is_paid_only", False).execute()
    return res.data or []


# ============================================================
#  契約
# ============================================================
def create_contract(
    creator_id: str,
    template_id: int,
    content: str,
    amount: str,
    contract_date: str,
) -> str:
    contract_id = str(uuid.uuid4())[:12]
    now = datetime.now(timezone.utc).isoformat()

    data = json.dumps({
        "id": contract_id,
        "creator_id": creator_id,
        "template_id": template_id,
        "content": content,
        "amount": amount,
        "contract_date": contract_date,
        "created_at": now,
    }, ensure_ascii=False)
    hash_val = hashlib.sha256(data.encode()).hexdigest()

    sb = get_supabase()
    sb.table("contracts").insert({
        "id": contract_id,
        "creator_id": creator_id,
        "template_id": template_id,
        "content": content,
        "amount": amount,
        "contract_date": contract_date,
        "status": "draft",
        "created_at": now,
        "hash": hash_val,
    }).execute()
    # 作成時点でカウントを増やす（未署名でも1件とする）
    user = get_user(creator_id)
    if user:
        sb.table("users").update({
            "contract_count": (user.get("contract_count") or 0) + 1
        }).eq("id", creator_id).execute()
    return contract_id


def get_contract(contract_id: str):
    sb = get_supabase()
    # contracts と templates を結合して取得
    res = sb.table("contracts").select(
        "*, templates(name, body, emoji)"
    ).eq("id", contract_id).execute()
    if not res.data:
        return None
    row = res.data[0]
    tmpl = row.pop("templates", {}) or {}
    row["template_name"] = tmpl.get("name", "")
    row["template_body"] = tmpl.get("body", "")
    row["template_emoji"] = tmpl.get("emoji", "📋")
    return row


def get_user_contracts(user_id: str) -> list:
    sb = get_supabase()
    res = sb.table("contracts").select(
        "*, templates(name, emoji)"
    ).eq("creator_id", user_id).order("created_at", desc=True).execute()
    rows = []
    for row in (res.data or []):
        tmpl = row.pop("templates", {}) or {}
        row["template_name"] = tmpl.get("name", "")
        row["template_emoji"] = tmpl.get("emoji", "📋")
        rows.append(row)
    return rows


def sign_contract(contract_id: str, signer_name: str, signer_ip: str):
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    sb.table("contracts").update({
        "signer_name": signer_name,
        "signer_ip": signer_ip,
        "status": "signed",
        "signed_at": now,
    }).eq("id", contract_id).execute()
    # カウントは create_contract 時に済み。署名時は増やさない


def reject_contract(contract_id: str, reason: str):
    sb = get_supabase()
    sb.table("contracts").update({
        "status": "rejected",
        "rejection_reason": reason,
    }).eq("id", contract_id).execute()


def delete_draft_contract(contract_id: str, creator_id: str):
    sb = get_supabase()
    sb.table("contracts").delete().eq("id", contract_id).eq(
        "creator_id", creator_id
    ).eq("status", "draft").execute()
