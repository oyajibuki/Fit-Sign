-- ============================================================
-- FitSign RLS 適用スクリプト
-- Supabase SQL Editor で実行してください
--
-- 前提：アプリ（Streamlit / db.py）は service_role キーで接続しており、
--       service_role は RLS を常にバイパスする。
--       クライアント側（React 等）から PostgREST を叩くコードは現状存在しない。
--       → users / contracts / templates は「ポリシーなしで RLS 有効」= anon 完全遮断
--         でアプリの動作に一切影響しない。
-- ============================================================

-- ── STEP 0: 現状確認（先に実行して結果を確認することを推奨）──────
-- RLS の有効/無効
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND tablename IN ('users', 'contracts', 'templates');

-- 既存ポリシー（緩いポリシーが残っていないか）
SELECT schemaname, tablename, policyname, roles, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'public' AND tablename IN ('users', 'contracts', 'templates');


-- ── STEP 1: 既存の緩いポリシーを全削除 ──────────────────────────
-- （STEP 0 でポリシーが 0 件だった場合はスキップして問題ない）
DO $$
DECLARE r RECORD;
BEGIN
    FOR r IN
        SELECT policyname, tablename
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename IN ('users', 'contracts', 'templates')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', r.policyname, r.tablename);
    END LOOP;
END $$;


-- ── STEP 2: RLS 有効化（ポリシーなし = anon / authenticated を全遮断）──
ALTER TABLE public.users     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.templates ENABLE ROW LEVEL SECURITY;

-- テーブル所有者もバイパスさせない（万一 postgres ロール経由で
-- PostgREST が動いても素通りしないようにする保険。service_role は影響を受けない）
ALTER TABLE public.users     FORCE ROW LEVEL SECURITY;
ALTER TABLE public.contracts FORCE ROW LEVEL SECURITY;
ALTER TABLE public.templates FORCE ROW LEVEL SECURITY;


-- ── STEP 3: anon / authenticated からテーブル権限自体を剥奪（多層防御）──
-- RLS が将来うっかり無効化されても素通りしなくなる。
-- Supabase のデフォルト GRANT を打ち消す形。
REVOKE ALL ON public.users     FROM anon, authenticated;
REVOKE ALL ON public.contracts FROM anon, authenticated;
REVOKE ALL ON public.templates FROM anon, authenticated;
-- SERIAL の裏にあるシーケンスも締める
REVOKE ALL ON SEQUENCE public.templates_id_seq FROM anon, authenticated;


-- ── STEP 4: 検証 ─────────────────────────────────────────────
-- rowsecurity が全て true、ポリシー 0 件、であることを確認
SELECT tablename, rowsecurity, relforcerowsecurity
FROM pg_tables t
JOIN pg_class c ON c.relname = t.tablename
WHERE t.schemaname = 'public' AND t.tablename IN ('users', 'contracts', 'templates');

SELECT count(*) AS remaining_policies
FROM pg_policies
WHERE schemaname = 'public' AND tablename IN ('users', 'contracts', 'templates');


-- ============================================================
-- 【オプション】templates をクライアントから読ませたくなった場合のみ
-- （現状 React 側に Supabase 呼び出しは無いので不要）
-- ============================================================
-- GRANT SELECT ON public.templates TO anon, authenticated;
-- CREATE POLICY "templates_public_read"
--   ON public.templates FOR SELECT
--   TO anon, authenticated
--   USING (is_paid_only = false);


-- ============================================================
-- 【将来の参考】クライアント直アクセス（anon キー + Supabase Auth）へ
-- 移行する場合のポリシー案。
--
-- ※ 重要な前提条件：
--   現在 LINE ログインは Supabase Auth を通さない自前実装で、
--   users.id は uuid5(LINE userId) の自前 UUID。auth.uid() とは一致しない。
--   下記ポリシーを使うには、まず LINE ログインを Supabase Auth 配下に
--   戻す（または Supabase Auth のカスタムトークンを発行する）必要がある。
--   それをせずに適用すると LINE ユーザーが全員締め出される。
-- ============================================================
-- GRANT SELECT, UPDATE ON public.users TO authenticated;
-- CREATE POLICY "users_self_select" ON public.users
--   FOR SELECT TO authenticated USING (id = auth.uid()::text);
-- CREATE POLICY "users_self_update" ON public.users
--   FOR UPDATE TO authenticated
--   USING (id = auth.uid()::text) WITH CHECK (id = auth.uid()::text);
--
-- GRANT SELECT, INSERT, UPDATE, DELETE ON public.contracts TO authenticated;
-- CREATE POLICY "contracts_owner_all" ON public.contracts
--   FOR ALL TO authenticated
--   USING (creator_id = auth.uid()::text) WITH CHECK (creator_id = auth.uid()::text);
--
-- ※ 署名ページ（page=sign）は未ログインの相手方がアクセスするため、
--   contracts への anon SELECT/UPDATE ポリシーが別途必要になるが、
--   契約ID だけを条件にすると「ID を知っている誰でも読める/署名できる」
--   ことになり RLS の意味がほぼ無くなる。
--   → 署名フローはクライアント直アクセスにせず、サーバー側
--     （現在の Streamlit / または Edge Function）経由に留めるのが正解。
