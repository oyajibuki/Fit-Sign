# FitSign ✍️

**スマホ2台で30秒契約。** PDF不要、その場で作ってその場で締結。

## デプロイ手順（Streamlit Community Cloud）

### 1. GitHubにpush
```bash
git init
git add .
git commit -m "FitSign POC v1.0"
git remote add origin https://github.com/YOUR_USERNAME/fitsign.git
git push -u origin main
```

### 2. Streamlit Cloud設定
1. https://share.streamlit.io にアクセス
2. 「New app」→ GitHubリポジトリを選択
3. Main file path: `app.py`
4. Deploy

### 3. BASE_URL設定（重要！）
デプロイ後、QRコードのURLが正しく生成されるよう設定：
- アプリ内「契約一覧 → 開発者設定 → BASE_URL」に
  デプロイされたURL（例: `https://fitsign.streamlit.app`）を入力

または Streamlit Secrets に設定:
```toml
# .streamlit/secrets.toml
BASE_URL = "https://your-app-name.streamlit.app"
```

## 機能

- ✅ テンプレート選択（業務委託・単発業務・同意書）
- ✅ 契約作成（3項目入力）
- ✅ QRコード生成
- ✅ QRから署名（スマホ対応）
- ✅ 契約一覧・状態管理
- ✅ PDF生成・ダウンロード
- ✅ SHA-256 改ざんチェック
- ✅ 無料3件 / 有料100件の制限

## 有料プラン切り替え（手動）

1. 「契約一覧」→「開発者設定」→「有料プランに変更（テスト用）」
2. またはSQLiteを直接編集: `UPDATE users SET plan='paid' WHERE id='USER_ID'`

## DB直接操作

```bash
sqlite3 fitsign.db
.tables
SELECT * FROM users;
UPDATE users SET plan='paid' WHERE id='USER_ID_HERE';
```

## 移行条件

| 条件 | 移行先 |
|------|-------|
| 有料5人達成 | Stripe実装 |
| 同時利用増加 | VPS + FastAPI |
| 月契約1000件超 | Supabase + Next.js |
