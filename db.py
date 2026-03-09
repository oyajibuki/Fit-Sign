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
        contract_count INTEGER DEFAULT 0,
        display_name TEXT DEFAULT '',
        address TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        email TEXT DEFAULT ''
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
        rejection_reason TEXT,
        created_at DATETIME,
        signed_at DATETIME,
        hash TEXT
    )
    """)

    # Insert default templates if empty
    c.execute("SELECT COUNT(*) FROM templates")
    if c.fetchone()[0] == 0:
        templates = [
            (
                "業務委託契約",
                "📋",
                """業務委託契約書

委託者（以下「甲」という。）と受託者（以下「乙」という。）は、以下の内容について業務委託契約を締結する。

第1条（委託業務）
甲は乙に対し、以下の業務を委託する。
• 業務内容：{content}

第2条（委託期間）
契約期間は、{contract_date} より開始し、別途定めるまでとする。

第3条（委託料）
甲は乙に対し、委託料として {amount} を支払う。支払条件は別途協議の上定める。

第4条（守秘義務）
乙は、本契約に関連して知り得た甲の機密情報を契約期間中および契約終了後も第三者に漏洩してはならない。

【甲】委託者：{creator_name}
【乙】受託者：{signer_name}

上記内容を確認の上、契約日以て本契約を承諾する。""",
                "継続的な業務委託に",
                0,
            ),
            (
                "請負契約",
                "⚡",
                """請負契約書

発注者（以下「甲」という。）と請負人（以下「乙」という。）は、以下の内容について請負契約を締結する。

第1条（仕事の内容）
乙は甲に対し、以下の仕事を完成することを約束する。
• 仕事内容：{content}

第2条（完成期限）
乙は上記仕事を、{contract_date}までに完成し、甲に引き渡すものとする。

第3条（請負代金）
甲は乙に対して請負代金 {amount} を仕事の完成・引渡し後に支払う。

第4条（大幅な修正・変更）
甲が仕事の内容を大幅に変更する場合には、別途協議の上追加請負代金を支払うものとする。

【甲】発注者：{creator_name}
【乙】請負人：{signer_name}

上記内容を確認の上、契約日以て本契約を承諾する。""",
                "成果物の納品がある仕事に",
                0,
            ),
            (
                "同意書",
                "✅",
                """同意書

内容：{content}
日付：{contract_date}

同意受領者（甲）：{creator_name}
同意者（乙）：{signer_name}

私は、上記の内容を十分に理解した上で、自らの意思で同意の意思表示をします。この同意は自由意志に基づき、強迫・調略等によるものではありません。""",
                "各種同意・確認に",
                0,
            ),
        ]
        c.executemany(
            "INSERT INTO templates (name, emoji, body, description, is_paid_only) VALUES (?, ?, ?, ?, ?)",
            templates,
        )

    conn.commit()

    # Safe migrations - silently add columns if they don't exist
    for sql in [
        "ALTER TABLE users ADD COLUMN display_name TEXT DEFAULT ''",
        "ALTER TABLE users ADD COLUMN address TEXT DEFAULT ''",
        "ALTER TABLE users ADD COLUMN phone TEXT DEFAULT ''",
        "ALTER TABLE users ADD COLUMN email TEXT DEFAULT ''",
        "ALTER TABLE contracts ADD COLUMN rejection_reason TEXT",
    ]:
        try:
            c.execute(sql)
            conn.commit()
        except Exception:
            pass  # Column already exists

    conn.close()


def save_user_profile(user_id, name, address, phone, email):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET display_name = ?, address = ?, phone = ?, email = ? WHERE id = ?",
        (name, address, phone, email, user_id),
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
            "INSERT INTO users (id, created_at, plan, contract_count, display_name) VALUES (?, ?, 'free', 0, '')",
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


def reject_contract(contract_id, reason):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
    UPDATE contracts SET status = 'rejected', rejection_reason = ?
    WHERE id = ?
    """,
        (reason, contract_id),
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
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "DELETE FROM contracts WHERE id = ? AND creator_id = ? AND status = 'draft'",
        (contract_id, creator_id),
    )
    conn.commit()
    conn.close()
