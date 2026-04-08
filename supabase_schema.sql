-- ============================================================
-- FitSign Supabase スキーマ
-- Supabase SQL Editor でこのファイルを実行してください
-- ============================================================

-- ── users ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id           TEXT PRIMARY KEY,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    plan         TEXT DEFAULT 'free',
    contract_count INTEGER DEFAULT 0,
    display_name TEXT DEFAULT '',
    address      TEXT DEFAULT '',
    phone        TEXT DEFAULT '',
    email        TEXT DEFAULT ''
);

-- ── templates ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS templates (
    id           SERIAL PRIMARY KEY,
    name         TEXT,
    emoji        TEXT,
    body         TEXT,
    description  TEXT,
    is_paid_only BOOLEAN DEFAULT FALSE
);

-- ── contracts ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contracts (
    id               TEXT PRIMARY KEY,
    creator_id       TEXT REFERENCES users(id),
    template_id      INTEGER REFERENCES templates(id),
    content          TEXT,
    amount           TEXT,
    contract_date    TEXT,
    signer_name      TEXT,
    signer_ip        TEXT,
    status           TEXT DEFAULT 'draft',
    rejection_reason TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    signed_at        TIMESTAMPTZ,
    hash             TEXT
);

-- ── デフォルトテンプレートの投入 ───────────────────────────
INSERT INTO templates (name, emoji, body, description, is_paid_only) VALUES
(
    '業務委託契約',
    '📋',
    '業務委託契約書（準委任型）

第1条（目的）
委託者（以下「甲」という）は、受託者（以下「乙」という）に対し、第2条に定める業務（以下「本業務」という）を委託し、乙はこれを受託する。

第2条（業務内容・善管注意義務）
1. 乙は、以下の業務を行う。
　業務内容： {content}
2. 乙は、専門的な知識と経験に基づき、善良なる管理者の注意義務をもって本業務を誠実に遂行するものとする。本契約は成果物の完成を約束するものではない。

第3条（契約期間）
本契約の有効期間は、{start_date} から {end_date} までとする。ただし、期間満了の14日前までに甲または乙から異議の申し出がない場合、本契約は同一条件でさらに1ヶ月更新されるものとし、以後も同様とする。

第4条（報酬および支払方法）
甲は乙に対し、業務遂行の対価として {payment_unit} 金 {amount} 円（税別）を支払う。毎月末日を締め日とし、翌月末日までに乙の指定する銀行口座に振り込むものとする。

第5条（報告義務）
乙は、甲の求めがあった場合、速やかに本業務の遂行状況を甲に報告しなければならない。

第6条（秘密保持）
乙は、本業務の遂行に関連して甲から開示された秘密情報を、第三者に漏洩または開示してはならない。',
    '継続的な業務委託に',
    FALSE
),
(
    '単発業務合意書',
    '⚡',
    '業務委託契約書（請負型）

第1条（目的）
委託者（以下「甲」という）は、受託者（以下「乙」という）に対し、第2条に定める業務（以下「本業務」という）を委託し、乙はこれを受託する。

第2条（業務内容および成果物）
本業務の内容および納入すべき成果物は、以下の通りとする。
業務内容： {content}

第3条（納期および納品方法）
乙は、{deadline} までに、前条の成果物を甲の指定する方法により納品する。

第4条（検収）
1. 甲は、成果物の納品後7日以内に検査を行い、その結果を乙に通知する。
2. 成果物に仕様との不一致がある場合、乙は無償で修正を行う。
3. 期間内に甲から通知がない場合、検収は合格したものとみなす。

第5条（報酬および支払方法）
甲は乙に対し、本業務の対価として 金 {amount} 円（税別）を支払う。支払いは検収完了月の翌月末日までに、乙の指定する銀行口座に振り込むものとする。

第6条（契約不適合責任）
検収完了後3ヶ月以内に成果物に隠れた瑕疵（バグや不具合等）が発見された場合、乙は速やかに無償で修補を行うものとする。

第7条（著作権等の帰属）
成果物に関する著作権（著作権法第27条および第28条の権利を含む）は、甲からの報酬の支払いが完了した時点で、乙から甲へ移転する。',
    '成果物の納品がある仕事に',
    FALSE
),
(
    '同意書',
    '✅',
    '業務に関する同意書

私（以下「同意者」という）は、貴社との間で実施する以下の業務に関し、以下の事項を遵守することに同意いたします。
対象業務： {content}

第1条（目的）
本同意書は、本件を実施するにあたり、双方が遵守すべき基本的な事項を定めることを目的とする。

第2条（秘密保持）
同意者は、本件に関して貴社から提供された一切の技術上、営業上その他の情報（以下「秘密情報」という）を厳重に管理し、貴社の事前の書面による承諾なく、第三者に開示または漏洩しないものとする。

第3条（権利の帰属・許諾）
本件に関連して同意者が提供したデータ、画像、成果物等の著作権や使用権については、貴社が本件の目的の範囲内で自由に利用することを許諾する。

第4条（禁止事項）
同意者は、本件を通じて得た情報や関係を利用して、貴社の不利益となる行為（競合行為、顧客の引き抜き等）を行ってはならない。

第5条（損害賠償）
同意者が本同意書の定めに違反し、貴社に損害を与えた場合、同意者はその損害を賠償する責任を負うものとする。',
    '各種同意・確認に',
    FALSE
)
ON CONFLICT DO NOTHING;

-- ── RLS（Row Level Security）────────────────────────────
-- service_role key は RLS を自動バイパスするため Streamlit の動作に影響なし
-- ポリシーなしで有効化 = anon/authenticated による直接アクセスをすべて遮断
ALTER TABLE users     ENABLE ROW LEVEL SECURITY;
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE contracts ENABLE ROW LEVEL SECURITY;
