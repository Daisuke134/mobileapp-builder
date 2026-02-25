# mobileapp-builder v3 — SDD Spec

## 概要（What & Why）

### What
mobileapp-builder を「誰でも使える App Factory」に改修する。具体的には：
1. **SKILL.md**: PHASE 0 アカウントオンボーディング追加 + SDD フェーズ（01〜04ファイル生成）追加
2. **jobs.json（Mac Mini）**: Anicca の 6:00 JST cron を追加（SSH → MacBook → builder 起動）

### Why
現状の mobileapp-builder は「全部セットアップ済みの人」しか使えない。
Apple Developer アカウントすら持っていない人がいきなり動かそうとすると途中でクラッシュする。
また、トレンド調査→スペック生成が自動化されておらず、人間がアイデアを渡す必要がある。

### 決定済みアーキテクチャ
```
Cron (6:00 JST, Anicca / Mac Mini)
    ↓
jobs.json → SSH to MacBook (cbns03@100.108.140.123)
    ↓
claude -p "Run mobileapp-builder skill. Build an iOS app." --dangerously-skip-permissions
    ↓
mobileapp-builder (Claude Code / MacBook) が全部やる
    ├── PHASE 0: ONBOARDING（アカウント確認・ガイド）
    ├── PHASE 1: TREND RESEARCH → 01-trend.md
    ├── PHASE 2: SDD → 02-spec.md + 03-plan.md + 04-tasks.md
    ├── 🛑 STOP 1: Slack 承認
    ├── PHASE 3〜12: 実装〜App Store 提出
    ├── 🛑 STOP 2: TestFlight 確認
    ├── 🛑 STOP 3: App Privacy 手動設定
    └── WAITING_FOR_REVIEW ✅
```

**Anicca がやること**: SSH コマンドを叩くだけ。mobileapp-planner スキルは作らない。

---

## 受け入れ条件

| # | 条件 | 確認方法 |
|---|------|---------|
| AC-1 | Apple Developer アカウントを持っていないユーザーが builder を起動すると、PHASE 0 で作成手順が表示され、「完了」と入力後に続行できる | 手動テスト |
| AC-2 | 全アカウント・ツール・環境変数が揃った後、PHASE 1 でトレンド調査が実行され `01-trend.md` が生成される | ファイル存在確認 |
| AC-3 | PHASE 2 完了後に `02-spec.md`, `03-plan.md`, `04-tasks.md` が生成される | ファイル存在確認 |
| AC-4 | STOP 1 で Slack に承認ボタンが届き、✅ で PHASE 3 が始まり、❌ で PHASE 1 からやり直しになる | Slack 確認 |
| AC-5 | Mac Mini の cron が 6:00 JST に発火し、MacBook で builder が起動する | jobs.json + Slack 通知確認 |
| AC-6 | 既存の PHASE 3〜12 ロジックに一切変更がない | diff 確認 |

---

## As-Is / To-Be

### SKILL.md の変更箇所

#### As-Is（現状）
```
PHASE 0: PRE-FLIGHT（サブスキル確認）
    - 必要なスキルが揃っているかサイレントチェック
    - 足りなければ npx skills add で自動インストール

PHASE 0: TREND RESEARCH
    - X / TikTok / App Store 調査
    - アプリアイデアを決定してユーザーにプロンプトで指示
```

#### To-Be（変更後）

**新規 PHASE 0: ACCOUNT ONBOARDING**（最初に追加）
```
STEP 1: Apple Developer Program
    - "developer.apple.com/account にアクセスしてアカウントの有無を確認"
    - なければ: enroll URL を提示 + "完了と入力してください" で待機
STEP 2: App Store Connect API Key
    - .p8 ファイルの存在確認 (ls ~/Downloads/AuthKey_*.p8)
    - なければ: ASC → Users and Access → Keys の手順を提示 + 待機
STEP 3: RevenueCat
    - REVENUECAT_API_KEY の存在確認
    - なければ: app.revenuecat.com URL + 取得手順 + 待機
STEP 4: Mixpanel
    - MIXPANEL_TOKEN の存在確認
    - なければ: URL + 手順 + 待機
STEP 5: X Developer (Bearer Token)
    - X_BEARER_TOKEN の存在確認
    - なければ: URL + 手順 + 待機
STEP 6: Apify
    - APIFY_TOKEN の存在確認
    - なければ: URL + 手順 + 待機
STEP 7: Gemini API Key
    - GEMINI_API_KEY の存在確認
    - なければ: URL + 手順 + 待機
STEP 8: OpenAI API Key (snapai用)
    - OPENAI_API_KEY の存在確認
    - なければ: URL + 手順 + 待機
STEP 9: Slack
    - SLACK_BOT_TOKEN / SLACK_APP_TOKEN / SLACK_CHANNEL_ID の確認
    - なければ: api.slack.com URL + 手順 + 待機
STEP 10: CLI ツール
    - asc, fastlane, greenlight, imagemagick, snapai, ios-deploy, Pillow, PyJWT
    - 不足分は brew install / pip install コマンドを提示 + 待機
STEP 11: Sub-skills
    - npx skills list で確認
    - 不足分は自動インストール（待機不要）
→ 全 STEP 通過で "✅ ONBOARDING 完了" → 次へ
```

**新規 PHASE 2: SDD（Spec-Driven Development）**（TREND RESEARCH 後に追加）
```
Input: 01-trend.md（PHASE 1 の出力）
Output:
    02-spec.md  — アプリ仕様（アプリ名、説明EN/JA、機能リスト、URL、画面一覧、Free/Pro差分）
    03-plan.md  — 技術設計（SwiftUI MVC、ファイル構成、Mixpanel events、RevenueCat Offering）
    04-tasks.md — Phase 3〜12 の全チェックリスト（タスク単位）
→ 生成完了 → STOP 1（Slack 承認）へ
```

**STOP 1 の Slack メッセージ内容（明確化）**
```
title: "📋 App Spec 承認 — {app_name}"
body:
    アプリ名: {name}
    カテゴリ: {category}
    概要: {description}
    主要機能: {features}
    ファイル: 02-spec.md / 03-plan.md / 04-tasks.md 参照
buttons: [✅ 承認して実装開始] [❌ やり直し]
```

### jobs.json の変更（Mac Mini）

**追記するジョブ:**
```json
{
  "id": "mobileapp-factory-6am",
  "agentId": "anicca",
  "schedule": {"kind": "cron", "expr": "0 6 * * *"},
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "Run this SSH command to start mobileapp-builder on MacBook: ssh -o StrictHostKeyChecking=no cbns03@100.108.140.123 \"claude -p 'Load and execute the mobileapp-builder skill. Research trends, generate a spec (SDD: 01-trend.md, 02-spec.md, 03-plan.md, 04-tasks.md), get Slack approval, then build and submit an iOS app to the App Store.' --dangerously-skip-permissions\" &"
  },
  "delivery": {"mode": "none"},
  "enabled": true
}
```

---

## テストマトリックス

| # | To-Be | テスト内容 | 確認方法 |
|---|-------|-----------|---------|
| T-1 | PHASE 0 ONBOARDING | Apple Dev アカウントなし状態でスキルを起動 → ガイドが出るか | 手動（アカウント確認 off） |
| T-2 | PHASE 0 ONBOARDING | 全アカウント揃い状態で起動 → PHASE 1 に進むか | 手動 |
| T-3 | PHASE 0 ONBOARDING | CLI ツール不足 → brew コマンドが提示されるか | 手動（greenlight を一時削除） |
| T-4 | PHASE 1 → 01-trend.md | PHASE 1 完了後 `01-trend.md` が生成されるか | ls + cat |
| T-5 | PHASE 2 SDD → 3ファイル | PHASE 2 完了後 3ファイル全部生成されるか | ls + cat |
| T-6 | STOP 1 Slack 承認 | Slack にボタン付きメッセージが届くか | Slack 確認 |
| T-7 | STOP 1 ❌ 拒否 | PHASE 1 からやり直しになるか | Slack ❌ → 観察 |
| T-8 | cron 発火 | Mac Mini cron が 6:00 JST に動くか | MacBook の claude プロセスを確認 |
| T-9 | 既存 PHASE 3〜12 無変更 | diff で変更がないか | git diff |

---

## 境界（やらないこと）

| やらないこと | 理由 |
|------------|------|
| mobileapp-planner スキルを作る | 不要（決定済み）。Anicca は cron のみ |
| PHASE 3〜12 のロジックを触る | 動いているものは触らない |
| Mac Mini に claude をインストール・認証 | Mac Mini の claude は未認証のため MacBook に SSH するのが正解 |
| 並列ビルド（複数 MacBook） | 今回は1台のみ。将来の拡張 |
| Slack メッセージ（ツイート等）を投稿 | 別タスク |

---

## 変更ファイル一覧

| ファイル | 場所 | 操作 |
|---------|------|------|
| `SKILL.md` | `/Users/cbns03/Downloads/mobileapp-builder/SKILL.md` | PHASE 0 ONBOARDING + PHASE 2 SDD を追加 |
| `jobs.json` | Mac Mini `/Users/anicca/.openclaw/cron/jobs.json` | python3 で部分追記（全上書き禁止） |

---

## 実行手順

```bash
# 1. SKILL.md の変更確認
cat /Users/cbns03/Downloads/mobileapp-builder/SKILL.md | grep -A5 "PHASE 0"

# 2. GitHub に push
cd /Users/cbns03/Downloads/mobileapp-builder && git push origin main

# 3. Mac Mini に jobs.json を追記
ssh anicca@100.99.82.95 "python3 -c \"
import json
with open('/Users/anicca/.openclaw/cron/jobs.json') as f:
    data = json.load(f)
print('Current jobs:', [j.get('id') for j in data])
\""

# 4. Anicca の cron 発火テスト
ssh anicca@100.99.82.95 "export PATH=/opt/homebrew/bin:$PATH && openclaw agent --message 'Run the mobileapp-factory SSH command to MacBook and confirm it started' --deliver"
```

---

## E2E 判定

| 項目 | 値 |
|------|-----|
| UI変更 | なし（SKILL.md はテキスト）|
| Maestro 必要 | 不要 |
| E2E確認方法 | Slack に承認ボタンが届くか + MacBook で builder プロセスが走るか |
