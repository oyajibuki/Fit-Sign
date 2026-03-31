import uuid
import hashlib
import json
from datetime import datetime, timezone

import streamlit as st
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
#  ユーザー
# ============================================================
def get_or_create_user(user_id: str) -> dict:
    sb = get_supabase()
    res = sb.table("users").select("*").eq("id", user_id).execute()
    if res.data:
        return res.data[0]
    now = datetime.now(timezone.utc).isoformat()
    sb.table("users").insert({
        "id": user_id,
        "created_at": now,
        "plan": "free",
        "contract_count": 0,
        "display_name": "",
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
    # contract_count をインクリメント
    res = sb.table("contracts").select("creator_id").eq("id", contract_id).execute()
    if res.data:
        creator_id = res.data[0]["creator_id"]
        user = get_user(creator_id)
        if user:
            sb.table("users").update({
                "contract_count": (user.get("contract_count") or 0) + 1
            }).eq("id", creator_id).execute()


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
