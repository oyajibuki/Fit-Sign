import sqlite3
import uuid
import hashlib
import json
from datetime import datetime

DB_PATH = "fitsign.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        created_at DATETIME,
        plan TEXT DEFAULT 'free',
        contract_count INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        emoji TEXT,
        body TEXT,
        description TEXT,
        is_paid_only BOOLEAN DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS contracts (
        id TEXT PRIMARY KEY,
        creator_id TEXT,
        template_id INTEGER,
        content TEXT,
        amount TEXT,
        contract_date TEXT,
        signer_name TEXT,
        signer_ip TEXT,
        status TEXT DEFAULT 'draft',
        created_at DATETIME,
        signed_at DATETIME,
        hash TEXT
    )
    """)

    # Insert default templates
    c.execute("SELECT COUNT(*) FROM templates")
    if c.fetchone()[0] == 0:
        templates = [
            (
                "業務委託契約",
                "📋",
                """業務委託契約書

本日、以下の内容について委託者と受託者は合意しました。

■ 業務内容：{content}
■ 報酬金額：{amount}円
■ 契約日：{contract_date}

受託者は上記業務を誠実に遂行し、委託者は定められた報酬を支払うことを約束します。
詳細な条件については利用規約に準じます。

上記内容について双方合意しました。""",
                "継続的な業務委託に",
                0,
            ),
            (
                "単発業務合意書",
                "⚡",
                """単発業務合意書

以下の単発業務について合意します。

■ 業務内容：{content}
■ 報酬金額：{amount}円
■ 実施日：{contract_date}

本合意に基づき、業務完了後速やかに報酬をお支払いいただきます。

上記内容について双方合意しました。""",
                "1回限りの仕事に",
                0,
            ),
            (
                "同意書",
                "✅",
                """同意書

以下の内容について同意します。

■ 内容：{content}
■ 条件：{amount}
■ 日付：{contract_date}

本同意書に記載の内容を十分に理解した上で、自らの意思で同意します。

上記内容について双方合意しました。""",
                "各種同意・確認に",
                0,
            ),
        ]
        c.executemany(
            "INSERT INTO templates (name, emoji, body, description, is_paid_only) VALUES (?, ?, ?, ?, ?)",
            templates,
        )

    conn.commit()
    conn.close()


def get_or_create_user(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute(
            "INSERT INTO users (id, created_at, plan, contract_count) VALUES (?, ?, 'free', 0)",
            (user_id, datetime.now().isoformat()),
        )
        conn.commit()
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
    conn.close()
    return dict(user)


def get_user(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None


def upgrade_to_paid(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET plan = 'paid' WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_templates(plan="free"):
    conn = get_conn()
    c = conn.cursor()
    if plan == "paid":
        c.execute("SELECT * FROM templates")
    else:
        c.execute("SELECT * FROM templates WHERE is_paid_only = 0")
    templates = [dict(t) for t in c.fetchall()]
    conn.close()
    return templates


def create_contract(creator_id, template_id, content, amount, contract_date):
    contract_id = str(uuid.uuid4())[:12]
    now = datetime.now().isoformat()

    data = json.dumps(
        {
            "id": contract_id,
            "creator_id": creator_id,
            "template_id": template_id,
            "content": content,
            "amount": amount,
            "contract_date": contract_date,
            "created_at": now,
        },
        ensure_ascii=False,
    )
    hash_val = hashlib.sha256(data.encode()).hexdigest()

    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
    INSERT INTO contracts (id, creator_id, template_id, content, amount, contract_date, status, created_at, hash)
    VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?)
    """,
        (contract_id, creator_id, template_id, content, amount, contract_date, now, hash_val),
    )
    conn.commit()
    conn.close()
    return contract_id


def get_contract(contract_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
    SELECT c.*, t.name as template_name, t.body as template_body, t.emoji as template_emoji
    FROM contracts c
    JOIN templates t ON c.template_id = t.id
    WHERE c.id = ?
    """,
        (contract_id,),
    )
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def sign_contract(contract_id, signer_name, signer_ip):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute(
        """
    UPDATE contracts SET signer_name = ?, signer_ip = ?, status = 'signed', signed_at = ?
    WHERE id = ?
    """,
        (signer_name, signer_ip, now, contract_id),
    )
    c.execute("SELECT creator_id FROM contracts WHERE id = ?", (contract_id,))
    row = c.fetchone()
    if row:
        c.execute(
            "UPDATE users SET contract_count = contract_count + 1 WHERE id = ?",
            (row["creator_id"],),
        )
    conn.commit()
    conn.close()


def get_user_contracts(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
    SELECT c.*, t.name as template_name, t.emoji as template_emoji
    FROM contracts c
    JOIN templates t ON c.template_id = t.id
    WHERE c.creator_id = ?
    ORDER BY c.created_at DESC
    """,
        (user_id,),
    )
    contracts = [dict(r) for r in c.fetchall()]
    conn.close()
    return contracts


def delete_draft_contract(contract_id, creator_id):
    """Delete a draft contract (only drafts can be deleted)."""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "DELETE FROM contracts WHERE id = ? AND creator_id = ? AND status = 'draft'",
        (contract_id, creator_id),
    )
    conn.commit()
    conn.close()
