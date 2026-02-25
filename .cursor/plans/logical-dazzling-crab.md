# [SUPERSEDED] → 新スペック: mobileapp-builder-v3-spec.md を参照

# mobileapp-factory 実装プラン（旧版）

## Context

mobileapp-builder（14フェーズ全自動 iOS App Store 提出スキル）を、誰でも使えるようにし、かつ Anicca（Mac Mini）が毎日 7:00 JST に自動起動する「App Factory」を構築する。

### 解決する問題

| 問題 | 解決策 |
|------|--------|
| Prerequisites が不明でセットアップできない | PHASE 0 PRE-FLIGHT をインタラクティブウィザードに改修 |
| Anicca が毎日自動でアプリを作れない | Mac Mini に mobileapp-factory スキル + cron を追加 |
| Tweet で告知したいが説明が複雑すぎる | 「コピペ1行」で動く体験に設計 |

### アーキテクチャ決定（ベストプラクティス準拠）

**Anicca = トリガーのみ / Claude Code = 全14フェーズ実行（モノリス）**

```
Anicca (Mac Mini) — 07:00 JST cron
    ↓ SSH to MacBook
    claude -p "Use mobileapp-builder..." --dangerously-skip-permissions
    ↓
Claude Code (MacBook) — PHASE 0〜12 全自動実行
    ↓ STOP 1/2/3 で Slack 承認
App Store → WAITING_FOR_REVIEW ✅
```

**分割しない理由:**
- 14フェーズは実証済みで変更禁止
- Xcode / Fastlane / ios-deploy は MacBook 専用ツール → Mac Mini では実行不可
- Anicca は「SSH trigger + Slack通知」の2ステップのみ

**cron 式の注意:** 既存 jobs.json（trend-hunter: `"0 5 * * *"` = 5:00 JST）から、OpenClaw は Asia/Tokyo 基準で cron を解釈する。7:00 JST = `"0 7 * * *"`。

---

## 変更ファイル（3ファイル）

| ファイル | 場所 | 操作 |
|---------|------|------|
| `SKILL.md` | `/Users/cbns03/Downloads/mobileapp-builder/SKILL.md` | PHASE 0 PRE-FLIGHT 節だけ置換 |
| `mobileapp-factory/SKILL.md` | `/Users/anicca/.openclaw/skills/mobileapp-factory/SKILL.md` | 新規作成（SSH経由） |
| `jobs.json` | `/Users/anicca/.openclaw/cron/jobs.json` | 部分追記（python3 json.load → json.dump） |

**14フェーズのロジック（PHASE 1〜12）は一切触らない。**

---

## 1. SKILL.md — PHASE 0 PRE-FLIGHT 節の置換

置換対象（現在の `### PHASE 0: PRE-FLIGHT（サブスキル確認）` ブロック全体）:

```markdown
### PHASE 0: PRE-FLIGHT（セットアップウィザード）

PRE-FLIGHT はサイレントチェックではなくガイド付きウィザードとして実行する。
問題が1つでも見つかれば、ユーザーに解決手順を提示し、確認を取ってから次の項目へ進む。
全 STEP が PASS になるまで PHASE 0 TREND RESEARCH に進まない。

---

#### STEP 1: Sub-skills（自動インストール）

# まずすべてのスキルをチェックし、足りなければ自動インストール
required_skills=(x-research tiktok-research apify-trend-analysis ralph-autonomous-dev screenshot-creator slack-approval)
for skill in "${required_skills[@]}"; do
  if ! npx skills list 2>/dev/null | grep -q "$skill"; then
    echo "⏳ Installing: $skill"
    npx skills add Daisuke134/anicca-products@$skill -g -y
  fi
done
if ! npx skills list 2>/dev/null | grep -q "app-icon"; then
  npx skills add code-with-beto/skills@app-icon -g -y
fi
echo "✅ All sub-skills ready."

---

#### STEP 2: CLI Tools

check_tool() {
  local name="$1"; local cmd="$2"; local install="$3"
  if eval "$cmd" &>/dev/null 2>&1; then echo "✅ $name"
  else echo "❌ $name → $install"; return 1; fi
}

TOOL_FAIL=0
check_tool "asc"         "asc --version"            "brew install nickvdyck/tap/asc"      || TOOL_FAIL=1
check_tool "fastlane"    "fastlane --version"        "brew install fastlane"               || TOOL_FAIL=1
check_tool "greenlight"  "greenlight --version"      "cd /tmp && git clone https://github.com/RevylAI/greenlight.git && cd greenlight && make build && sudo cp build/greenlight /usr/local/bin/" || TOOL_FAIL=1
check_tool "imagemagick" "convert --version"         "brew install imagemagick"            || TOOL_FAIL=1
check_tool "snapai"      "npx snapai --version"      "npm install -g snapai"               || TOOL_FAIL=1
check_tool "ios-deploy"  "ios-deploy --version"      "brew install ios-deploy"             || TOOL_FAIL=1
check_tool "Pillow"      "python3 -c 'import PIL'"   "pip3 install Pillow"                 || TOOL_FAIL=1
check_tool "PyJWT"       "python3 -c 'import jwt'"   "pip3 install PyJWT"                  || TOOL_FAIL=1
check_tool "requests"    "python3 -c 'import requests'" "pip3 install requests"            || TOOL_FAIL=1

if [ "$TOOL_FAIL" -ne 0 ]; then
  echo ""
  echo "⚠️  上記の CLI ツールが不足しています。インストール後「完了」と入力してください。"
  # ← ユーザー入力待ち。「完了」を受けたら STEP 2 を再実行し PASS になったら STEP 3 へ
fi

---

#### STEP 3: 環境変数

ENV_FILE="$HOME/.config/mobileapp-builder/.env"
[ -f "$ENV_FILE" ] && source "$ENV_FILE"

ENV_FAIL=0
check_env() {
  local name="$1"; local link="$2"; local hint="$3"
  if [ -n "${!name:-}" ]; then echo "✅ $name"
  else echo "❌ $name → $link ($hint)"; ENV_FAIL=1; fi
}

check_env ASC_KEY_ID         "https://appstoreconnect.apple.com → Users and Access → Integrations → Keys" "キーID（例: D637C7RGFN）"
check_env ASC_ISSUER_ID      "同上"                                                                        "Issuer ID（UUID形式）"
check_env ASC_KEY_PATH       "上記ページで .p8 ダウンロード → ~/Downloads/ に保存"                        "例: ~/Downloads/AuthKey_XXXXXX.p8"
check_env REVENUECAT_API_KEY "https://app.revenuecat.com → Project Settings → API Keys"                   "sk_ で始まるキー"
check_env MIXPANEL_TOKEN     "https://mixpanel.com → Project Settings → Project Token"                    "英数字トークン"
check_env X_BEARER_TOKEN     "https://developer.twitter.com → App → Bearer Token"                        "AAAA... で始まる"
check_env APIFY_TOKEN        "https://console.apify.com → Settings → Integrations"                       "apify_api_ で始まる"
check_env GEMINI_API_KEY     "https://console.cloud.google.com → APIs & Services → Credentials"           "AIza... で始まる"
check_env OPENAI_API_KEY     "https://platform.openai.com → API keys"                                    "sk- で始まる"
check_env SLACK_BOT_TOKEN    "https://api.slack.com/apps → OAuth & Permissions"                          "xoxb- で始まる"
check_env SLACK_APP_TOKEN    "https://api.slack.com/apps → Basic Information → App-Level Tokens"         "xapp- で始まる"
check_env SLACK_CHANNEL_ID   "Slack でチャンネル右クリック → リンクをコピー → 末尾 C... 部分"             "例: C0123456789"

if [ "$ENV_FAIL" -ne 0 ]; then
  echo ""
  echo "⚠️  環境変数が不足しています。設定方法:"
  echo "   1. mkdir -p ~/.config/mobileapp-builder"
  echo "   2. 上のリンクから各キーを取得"
  echo "   3. ~/.config/mobileapp-builder/.env に: export 変数名=値"
  echo "   4. source ~/.config/mobileapp-builder/.env"
  echo "   設定が完了したら「完了」と入力してください。"
  # ← ユーザー入力待ち。「完了」を受けたら STEP 3 を再実行し PASS になったら STEP 4 へ
fi

---

#### STEP 4: ASC API Key (.p8)

if ls ~/Downloads/AuthKey_*.p8 &>/dev/null 2>&1; then
  echo "✅ ASC API Key (.p8) 確認済み"
else
  echo "❌ .p8 ファイルが ~/Downloads に見つかりません"
  echo ""
  echo "   取得手順:"
  echo "   1. https://appstoreconnect.apple.com を開く"
  echo "   2. Users and Access → Integrations → Keys → + ボタン"
  echo "   3. 名前: mobileapp-builder / アクセス: App Manager"
  echo "   4. ダウンロード → ~/Downloads/ に保存"
  echo "   5. ASC_KEY_ID と ASC_KEY_PATH を .env に追記"
  echo "   完了したら「完了」と入力してください。"
  # ← ユーザー入力待ち
fi

---

#### STEP 5: snapai 設定

[ -n "${OPENAI_API_KEY:-}" ] && npx snapai config --openai-api-key "$OPENAI_API_KEY" && echo "✅ snapai 設定済み"

---

#### PRE-FLIGHT 完了

echo "✅ PRE-FLIGHT 完了。全チェック通過。PHASE 0 TREND RESEARCH を開始します。"
```

---

## 2. mobileapp-factory/SKILL.md（Mac Mini に新規作成）

```markdown
---
name: mobileapp-factory
description: Triggers mobileapp-builder on MacBook via SSH to autonomously build and ship one iOS app per day. Use when triggered by app-factory cron at 07:00 JST, or told to "run mobileapp-factory", "trigger daily app build", "start app factory".
---

# mobileapp-factory

Mac Mini から MacBook に SSH して mobileapp-builder を起動する。
Anicca のロールは「SSH トリガー + Slack 通知」の2ステップのみ。

---

## STEP 1: MacBook で Claude Code を起動

```bash
ssh -o StrictHostKeyChecking=no cbns03@100.108.140.123 \
  "claude -p 'Use the mobileapp-builder skill. Research current trends, generate a spec for one iOS app, and execute all 14 phases through to App Store submission. Start with PHASE 0 PRE-FLIGHT.' \
  --dangerously-skip-permissions" &
echo "✅ mobileapp-builder started on MacBook (background)"
```

SSH が確立されたら次のステップへ（完了を待たない。実行は3-8時間かかる）。

## STEP 2: Slack #metrics に起動報告

```bash
SLACK_TOKEN=$(grep SLACK_BOT_TOKEN /Users/anicca/.openclaw/.env | cut -d= -f2- | tr -d '"')
curl -s -X POST 'https://slack.com/api/chat.postMessage' \
  -H "Authorization: Bearer $SLACK_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "channel": "C091G3PKHL2",
    "text": "🏭 *mobileapp-factory 起動* — MacBook で mobileapp-builder を開始。\nトレンド調査 → スペック生成 → Slack 承認（STOP 1）の順で進みます。"
  }'
```

## STEP 3: 完了（このスキルはここで終了）

mobileapp-builder は MacBook 上で独立して実行される。
3つの STOP ゲートで Slack に承認依頼が届く。承認次第で次フェーズへ継続。

| 項目 | 値 |
|------|-----|
| MacBook SSH | cbns03@100.108.140.123 |
| 所要時間 | 3-8 時間 |
| Slack 承認チャンネル | #metrics (C091G3PKHL2) |
```

---

## 3. jobs.json への追記（部分編集、SSH 経由）

**操作方法:** 全書き換え禁止。以下の python3 スクリプトで安全に追記。

```bash
# Mac Mini 上で実行
python3 -c "
import json
with open('/Users/anicca/.openclaw/cron/jobs.json') as f:
    data = json.load(f)
new_job = {
  'id': 'mobileapp-factory-morning',
  'agentId': 'anicca',
  'schedule': {'kind': 'cron', 'expr': '0 7 * * *'},
  'sessionTarget': 'isolated',
  'wakeMode': 'now',
  'payload': {
    'kind': 'agentTurn',
    'message': 'Execute the mobileapp-factory skill. Read /Users/anicca/.openclaw/skills/mobileapp-factory/SKILL.md and perform all steps.'
  },
  'delivery': {'mode': 'none'},
  'enabled': True
}
if not any(j.get('id') == 'mobileapp-factory-morning' for j in data):
    data.append(new_job)
    with open('/Users/anicca/.openclaw/cron/jobs.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print('✅ Added mobileapp-factory-morning')
else:
    print('Already exists, skipped')
"
```

**cron 式:** `"0 7 * * *"` — 既存 jobs.json が JST 基準（trend-hunter: `0 5 * * *` = 5:00 JST）を確認済み。

---

## 4. Slack/Twitter メッセージ（コピペ用）

### X (Twitter)
```
Claude Codeスキル公開

「Build an iOS app」と言うだけで
✅ トレンド調査（X+TikTok+App Store）
✅ SwiftUI実装 → TestFlight → App Store提出

人間がやること: 3回の承認だけ。

npx skills add Daisuke134/mobileapp-builder -g -y

github.com/Daisuke134/mobileapp-builder
```

### Slack（グループ向け）
```
🏭 mobileapp-builder を公開しました

Claude Code に「Build an iOS app」と言うだけで
トレンド調査 → Xcode実装 → App Store提出 が全自動で動きます。

【あなたがやること：3回だけ】
1. スペック承認（Slackに通知が届く）
2. TestFlightテスト（Slackに通知が届く）
3. App Privacy設定（ASC Webで2分）

インストール：
npx skills add Daisuke134/mobileapp-builder -g -y

Claude Codeで言う：
"Build an iOS app"

→ github.com/Daisuke134/mobileapp-builder
```

**設計方針:** Prerequisitesをメッセージに書かない（スキルの PHASE 0 ウィザードが全部聞く）。最低限の摩擦で始められる体験。

---

## 実施順序

| # | 作業 | 場所 |
|---|------|------|
| 1 | `SKILL.md` の PHASE 0 PRE-FLIGHT 節を置換 | MacBook（`~/Downloads/mobileapp-builder/`） |
| 2 | GitHub に push | MacBook |
| 3 | Mac Mini に `mobileapp-factory/SKILL.md` を作成 | SSH → Mac Mini |
| 4 | `jobs.json` に cron ジョブを追記（python3） | SSH → Mac Mini |
| 5 | 手動テスト（`openclaw agent --message "Execute mobileapp-factory skill" --deliver`） | MacBook → Mac Mini |
| 6 | Slack メッセージ投稿 | MacBook |

---

## 検証方法

| 確認項目 | コマンド |
|---------|---------|
| mobileapp-factory スキル存在確認 | `ssh anicca@100.99.82.95 "ls /Users/anicca/.openclaw/skills/mobileapp-factory/"` |
| cron ジョブ追加確認 | `ssh anicca@100.99.82.95 "cat /Users/anicca/.openclaw/cron/jobs.json | python3 -m json.tool | grep mobileapp"` |
| Anicca 手動発火テスト | `ssh anicca@100.99.82.95 "export PATH=/opt/homebrew/bin:$PATH && openclaw agent --message 'Execute mobileapp-factory skill' --deliver"` |
| MacBook で Slack 通知確認 | #metrics チャンネルに「mobileapp-factory 起動」が届くか |
