---
name: mobileapp-builder
description: Builds and ships a Swift/SwiftUI iOS app to the App Store from a spec.md file. Handles all 12 phases autonomously: Xcode scaffold → SwiftUI implementation → ASC subscription setup (175-territory pricing, localizations, review screenshots) → app assets → preflight gate → submission. Use when given a spec.md and told to build and ship an app, or when triggered by app-factory cron.
---

# mobileapp-builder

Given a `spec.md`, autonomously build and ship a Swift/SwiftUI iOS app to the App Store.

**Full spec:** `.cursor/plans/ios/1.6.3/mobileapp-builder-spec.md`

---

## INPUT

```
spec.md path (required fields: app_name, bundle_id, version, price_monthly_usd,
price_annual_usd, output_dir, concept, screens, paywall, metadata)
```

See `references/spec-template.md` for the full spec.md format.

---

## OUTPUT

`asc review submissions-list` → state = `WAITING_FOR_REVIEW`

---

## CRITICAL RULES (違反 = リジェクト確定)

| # | ルール |
|---|--------|
| 1 | **提出前に全サブスクが READY_TO_SUBMIT**。MISSING_METADATA のまま提出 → Guideline 2.1 拒否 |
| 2 | **IAP pricing は全175カ国**。US のみは Guideline 2.1 拒否 |
| 3 | **Superwall 使用禁止**。RevenueCat のみ |
| 4 | **xcodebuild 直接実行禁止**。Fastlane のみ |
| 5 | **PHASE 8 が STOP ゲート**。blocking=0 + READY_TO_SUBMIT でなければ絶対に次に進まない |
| 6 | **availability set は pricing の前**。順序を逆にすると全pricing call が Apple 500エラーで失敗する |
| 7 | **Privacy Policy URL は en-US AND ja 両方必須**。片方だけでは submit 時にエラー |
| 8 | **RC Offerings は TestFlight 前に設定必須**。未設定だと「Apple IAP key is invalid」エラーで課金不可 |
| 9 | **locale は `ja`（`ja-JP` は無効）**。ASC API は `ja-JP` を拒否する |
| 10 | **IAP key は同一 Apple Developer アカウントで使い回し**。新規作成不要。`AuthKey_AY9BT5R8NU.p8` を流用 |
| 11 | **Paywall コピーは必ずコードから実機能を確認してから書く**。存在しない機能を訴求するのは罪（Apple レビュー違反 + ユーザー詐欺）。`FreePlanService.swift`, `SubscriptionManager.swift` を必ず読め |
| 12 | **Mixpanel 必須**。全新規アプリに Mixpanel SDK を組み込み、`paywall_viewed`（`offering_id` プロパティ付き）を送信すること。Mixpanel なしでは paywall-ab スキルによる A/B 評価が不可能 |
| 13 | **RevenueCat → Mixpanel 連携必須**。RC Dashboard で「Send data to Mixpanel」を有効化し、`presented_offering_id` が `rc_trial_started_event` に含まれることを確認すること。未設定 = A/B 変換追跡ゼロ |
| 14 | **スクショ撮影シミュレータは iPhone SE 3rd gen 必須**。iPhone 14+ は Dynamic Island（黒い丸）が写り込む。`xcrun simctl list devices | grep "SE (3rd"` で UDID を確認して使う |
| 15 | **Pencil テキストノードに `width: "fill_container"` 必須**。未設定だとテキストがフレーム外にはみ出す。日本語ヘッドラインの `fontSize` は **22以下**（28は14文字でオーバーフロー） |
| 16 | **Pencil 画像キャッシュ問題**。同じパスのファイルを上書きしても Pencil はキャッシュした旧版を使い続ける。画像差し替え時は**必ず新しいファイル名**を使うこと |
| 17 | **`mcp__pencil__get_screenshot` はディスクに保存しない**。返ってくるのは MCP レスポンス内の base64 のみ。ASC アップロード用ファイルは別途シミュレータから `xcrun simctl io` で取得すること |
| 18 | **App Privacy（データの使用方法）は ASC API で設定不可**。`/v1/apps/{id}/appDataUsages` は 404 を返す。PHASE 12 の前にユーザーに手動設定させること。設定手順は PHASE 11.5 参照 |
| 19 | **ISSUER_ID は Fastfile の `API_ISSUER_ID` を使う**。間違った ID は全 curl 呼び出しが 401 を返す。正しい ID: `f53272d9-c12d-4d9d-811c-4eb658284e74`。ASC 画面の「キー ID」と混同しない |
| 20 | **アイコンはビルド前に配置する**。ビルド後にアイコンを変更した場合は `CURRENT_PROJECT_VERSION` をバンプして再ビルドが必要。「The bundle version must be higher than the previously uploaded version」エラーが出たらバンプして再アップロード |
| 21 | **Playwright + Chrome 競合**。Chrome 起動中に Playwright を実行すると「既存のブラウザセッションで開いています」エラー。先に `pkill -f "Google Chrome"` で Chrome を終了してから Playwright を起動 |
| 22 | **`asc submit create --confirm` が正解の提出方法**。`PATCH reviewSubmissions.state` は 409 を返す。`asc review submissions-list` で確認できる ID は `appStoreVersionSubmissions` とは別物 |

---

## ⚠️ Paywall コピー作成ルール（必読）

**Paywall に書く機能は全てコードに実在すること。存在しない機能を訴求してはいけない。**

Paywall 作成・更新の前に以下を確認する（Anicca の場合）:

| ファイル | 確認する内容 |
|---------|------------|
| `FreePlanService.swift` | Free の制限（本数・時刻・ルールベース） |
| `LLMNudgeService.swift` | Pro の AI 機能 |
| `NudgeStatsManager.swift` | フィードバック学習の仕組み |
| `SubscriptionInfo.swift` | Free/Pro の差分定義 |

新規アプリの場合: `PaywallView` がある画面と `SubscriptionManager` 相当のファイルを読んで、
Free と Pro の実際の差分を確認してからコピーを書く。

**禁止パターン（実在しないのに書く）:**
- ❌ "30-day insight reports" — 分析機能がなければ書くな
- ❌ "Progress tracking" — 進捗画面がなければ書くな
- ❌ "Premium support" — サポートチームがなければ書くな
- ❌ "All features unlocked" — 意味がない。何が解禁されるか具体的に書け

---

## 14 PHASES

### PHASE 0: TREND RESEARCH
```
x-research + tiktok-research + apify-trend-analysis スキルを並列実行

[x-research]
  X (Twitter) でバズってるキーワード・トレンドトピックを調査
  → 「今週 JP/EN でバズってるメンタル・健康・生産性系のキーワード TOP5」

[tiktok-research]
  TikTok で伸びているショート動画のテーマ・フック・視聴者の悩みを調査
  → 「今週バズってる動画のテーマ TOP5 + 共通するペイン」

[apify-trend-analysis]
  App Store カテゴリ別ランキング + Google Trends を調査
  → 「今上位に入っているアプリジャンル + 検索ボリューム増加中のトピック」

3つの結果を統合して判断:
  - 共通して出てくるテーマ = 今作るべきアプリのジャンル
  - アプリアイデアを1つに絞る（選択肢提示禁止。1つに決める）

OUTPUT → .cursor/app-factory/{slug}/01-trend.md
  - 決定したアプリアイデア（タイトル仮 + 一言説明）
  - 根拠（どのトレンドデータから判断したか）
  - slug（例: sleep-tracker、breath-calm 等）
```

### PHASE 0.5: SPEC 生成（SDD）
```
01-trend.md を読んで spec.md を自動生成する
スラッシュコマンド不要。以下の手順をそのまま実行する。

Step 1: spec.md の全フィールドを埋める（PHASE 1 の必須フィールドを全部）
  - app_name, bundle_id, version, output_dir
  - price_monthly_usd: 9.99, price_annual_usd: 49.99（デフォルト）
  - paywall.cta_text_en / paywall.cta_text_ja
  - metadata: title_en/ja, subtitle_en/ja, description_en/ja, keywords_en/ja
  - urls.privacy_en: "https://aniccaai.com/{slug}/privacy/en"
  - urls.privacy_ja: "https://aniccaai.com/{slug}/privacy/ja"
  - urls.terms: "https://www.apple.com/legal/internet-services/itunes/dev/stdeula/"
  - urls.landing: "https://aniccaai.com/{slug}"
  - localization: "os_language"
  - supported_locales: ["en", "ja"]
  - concept: （1行説明。スクショヘッドライン生成に使う）
  - 画面構成（Onboarding / Main / Paywall / Settings）

Step 2: plan.md を生成（技術設計）
  - アーキテクチャ（SwiftUI MVC）
  - ファイル構成
  - API / RevenueCat 設計

Step 3: tasks.md を生成（実装タスクリスト）
  - 依存順に並んだチェックボックス形式
  - PHASE 2〜12 の各フェーズに対応するタスクを網羅

OUTPUT →
  .cursor/app-factory/{slug}/02-spec.md   ← PHASE 1 が読む
  .cursor/app-factory/{slug}/03-plan.md
  .cursor/app-factory/{slug}/04-tasks.md
```

### PHASE 1: VALIDATE INPUT
```
spec.md の必須フィールド確認（全項目 MUST — 1つでも欠ければ STOP）

■ 技術
  - app_name, bundle_id, version, output_dir

■ 課金
  - price_monthly_usd, price_annual_usd
  - paywall.cta_text_en, paywall.cta_text_ja

■ App Store メタデータ（EN + JA 両方必須）
  - metadata.title_en, metadata.title_ja
  - metadata.subtitle_en, metadata.subtitle_ja
  - metadata.description_en, metadata.description_ja
  - metadata.keywords_en, metadata.keywords_ja

■ URL（アプリ専用 URL 必須 — 全アプリ共通 URL 禁止）
  - urls.privacy_en   例: "https://aniccaai.com/thankful/privacy/en"
  - urls.privacy_ja   例: "https://aniccaai.com/thankful/privacy/ja"
  - urls.terms        固定値: "https://www.apple.com/legal/internet-services/itunes/dev/stdeula/"
  - urls.landing      例: "https://aniccaai.com/thankful"

■ ローカライズ方針
  - localization: "os_language"  （日本語OS→日本語、その他→英語）
  - supported_locales: ["en", "ja"]

■ コンセプト
  - concept  （1行説明。スクショヘッドライン生成に使う）

欠けていれば STOP + 不足フィールドを報告
```

### PHASE 2: SCAFFOLD
```bash
# 新規 Xcode プロジェクトを output_dir に作成
mkdir -p <output_dir>/<app_name>ios
# Bundle ID / バージョン / チーム ID を project.pbxproj に設定
# RevenueCat SDK を SPM で追加
# PrivacyInfo.xcprivacy を追加（必須）
```

### PHASE 3: BUILD
```
ralph-autonomous-dev で SwiftUI 実装

■ 必須実装（1つでも欠ければ PHASE 11 で STOP）

  コア機能:
  - spec の画面構成・コア機能を実装
  - 通知: UserNotifications で APNs 登録 + 通知カタログ
  - Paywall: RevenueCat SDK のみ（Superwall 禁止）
  - Paywall の accessibilityIdentifier（必須 5要素）:
      paywall_plan_monthly / paywall_plan_yearly
      paywall_cta / paywall_skip / paywall_restore

  ローカライズ（OS言語対応 — 必須）:
  - Localizable.strings を EN + JA 両方作成
  - 表示言語は OS 言語に自動追従（Locale.current で判定）
  - 日本語 OS → 日本語 UI、その他 OS → 英語 UI
  - Paywall コピーも EN/JA 両対応（spec.md の paywall.cta_text_en/ja を使う）
  - ハードコード日本語・英語テキスト禁止。全て Localizable.strings 経由

  Settings 画面（必須）:
  - Privacy Policy リンク → spec.md の urls.privacy_en / urls.privacy_ja（OS言語で切替）
  - Terms of Use リンク → spec.md の urls.terms（Apple 標準 EULA 固定）
    URL: https://www.apple.com/legal/internet-services/itunes/dev/stdeula/

  ■ PHASE 9 スクショパイプラインの前提セットアップ（必須 — これがないと PHASE 9 Step 2 が動かない）

  1. ScreenshotTests.swift を作成
     ファイル: <output_dir>/<slug>UITests/ScreenshotTests.swift
     内容: XCUITest でアプリを起動し、各画面をスクロール・遷移してスクショを撮影するテストケース
     テストケース:
       - testScreenshot_Main   : メイン画面
       - testScreenshot_Streak : カレンダー/ストリーク画面（存在する場合）
       - testScreenshot_Paywall: Paywall 画面（paywall_skip で到達可能にすること）
     accessibilityIdentifier を使って各画面に確実に到達すること

  2. Makefile に generate-store-screenshots ターゲットを追加
     場所: <output_dir>/Makefile
     コマンド:
       generate-store-screenshots:
         xcodebuild test -project <app_name>.xcodeproj -scheme <app_name>UITests \
           -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 16 Pro Max' \
           -resultBundlePath docs/screenshots/output.xcresult
         python3 docs/screenshots/scripts/extract_screenshots.py
         python3 docs/screenshots/scripts/process_screenshots.py

  3. extract_screenshots.py + process_screenshots.py を docs/screenshots/scripts/ に配置
     - extract_screenshots.py: xcresulttool で output.xcresult から PNG を抽出 → docs/screenshots/raw/
     - process_screenshots.py: PIL で 1290×2796 に合成（ヘッドラインを screenshots.yaml から読む）
     - screenshots.yaml: 各画面のヘッドライン + カラー設定

  ⚠️ これらのセットアップが完了してから PHASE 9 Step 2 に進む。スキップ禁止。
```

### PHASE 3.5: PRIVACY POLICY & LANDING PAGE デプロイ
```
aniccaai.com/{slug}/ のページを作成して Netlify にデプロイする
PHASE 4 の前に必須（URL が死んでいると ASC Privacy URL 設定が通らない）

■ 作成するページ（apps/landing/ に追加）

  1. aniccaai.com/{slug}/                    ← ランディングページ
     - アプリ名・コンセプト・App Store リンク
     - EN のみでよい（LP は英語）

  2. aniccaai.com/{slug}/privacy/en          ← Privacy Policy（英語）
     - アプリ名・収集するデータ・用途を記載
     - 既存 aniccaai.com/privacy を テンプレートとして流用し app_name を置換

  3. aniccaai.com/{slug}/privacy/ja          ← Privacy Policy（日本語）
     - 同上の日本語版

  4. aniccaai.com/{slug}/terms               ← Terms of Use
     - Apple 標準 EULA へリダイレクト
     - URL: https://www.apple.com/legal/internet-services/itunes/dev/stdeula/

■ デプロイ手順

  # 1. apps/landing/ にページファイルを作成（HTML or Markdown）
  # 2. dev ブランチに push → Netlify が自動デプロイ
  git add -A && git commit -m "feat: add {slug} landing + privacy pages" && git push origin dev

  # 3. URL が生きているか確認（PHASE 11 GATE 4 と同じチェック）
  curl -I "https://aniccaai.com/{slug}/privacy/en" | grep "200\|301"
  curl -I "https://aniccaai.com/{slug}/privacy/ja" | grep "200\|301"
  # 200 or 301 でなければ STOP + Netlify のビルドログを確認
```

### PHASE 4: ASC APP SETUP
```bash
asc apps create --bundle-id "<bundle_id>" --name "<app_name>" \
  --primary-locale en-US --sku "<sku>"

# Privacy Policy URL を en-US AND ja 両方に設定（片方だけでは submit 時にエラー）
# locale は必ず "ja"（"ja-JP" は ASC で無効）
APP_INFO_ID=$(asc apps info list --app "<APP_ID>" --output json | \
  python3 -c "import sys,json;d=json.load(sys.stdin);print(d['data'][0]['id'])")

TOKEN=$(python3 -c "
import jwt,time,pathlib
key=pathlib.Path.home().joinpath('Downloads/AuthKey_D637C7RGFN.p8').read_text()
payload={'iss':'f53272d9-c12d-4d9d-811c-4eb658284e74','iat':int(time.time()),'exp':int(time.time())+1200,'aud':'appstoreconnect-v1'}
print(jwt.encode(payload,key,algorithm='ES256',headers={'kid':'D637C7RGFN','typ':'JWT'}))
")

# en-US Privacy URL
curl -s -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "https://api.appstoreconnect.apple.com/v1/appInfoLocalizations/<EN_LOC_ID>" \
  -d '{"data":{"type":"appInfoLocalizations","id":"<EN_LOC_ID>","attributes":{"privacyPolicyUrl":"https://aniccaai.com/privacy"}}}'

# ja Privacy URL（locale = "ja" 確認必須）
curl -s -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "https://api.appstoreconnect.apple.com/v1/appInfoLocalizations/<JA_LOC_ID>" \
  -d '{"data":{"type":"appInfoLocalizations","id":"<JA_LOC_ID>","attributes":{"privacyPolicyUrl":"https://aniccaai.com/privacy"}}}'

asc subscriptions groups create --app "<APP_ID>" --reference-name "Premium"

asc subscriptions create --group "<GROUP_ID>" --name "Monthly" \
  --product-id "<bundle_id>.premium.monthly" --period ONE_MONTH --level 2

asc subscriptions create --group "<GROUP_ID>" --name "Annual" \
  --product-id "<bundle_id>.premium.yearly" --period ONE_YEAR --level 1

# ★ availability を pricing の前に必ず設定（これなしでpricingは全件Apple 500エラー）
asc subscriptions availability set --id "<MONTHLY_ID>" \
  --available-in-new-territories --territory USA,JPN

asc subscriptions availability set --id "<ANNUAL_ID>" \
  --available-in-new-territories --territory USA,JPN
```

### PHASE 4.5: RC OFFERINGS SETUP（TestFlight 前に必須）
```
RC Dashboard → Thankful プロジェクト
  → Offerings → New Offering → identifier: "default"
  → Packages を追加:
      $rc_annual  → Apple Product ID: <bundle_id>.premium.yearly
      $rc_monthly → Apple Product ID: <bundle_id>.premium.monthly
  → Offering を Current に設定

確認: Offerings が "current" に設定されていること
未設定 = TestFlight で「Apple IAP key is invalid」エラー

IAP Key: AY9BT5R8NU（同一 Apple Developer アカウントで全アプリ共通、新規作成不要）
p8 file: ~/Downloads/AuthKey_AY9BT5R8NU.p8 を RC にアップロード済みであること確認
```

### PHASE 5: IAP PRICING ★最重要
```bash
# US 価格ポイント ID を取得してから scripts/add_prices.py を実行
python3 .claude/skills/mobileapp-builder/scripts/add_prices.py \
  --annual-sub "<ANNUAL_ID>" \
  --annual-pp "<ANNUAL_US_PP_ID>" \
  --monthly-sub "<MONTHLY_ID>" \
  --monthly-pp "<MONTHLY_US_PP_ID>"

# 確認（175 でなければ STOP）
asc subscriptions prices list --id "<MONTHLY_ID>" --paginate | \
  python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d['data']))"
```

詳細手順 → `references/iap-bible.md` の「価格ポイント ID の取得方法」

### PHASE 6: IAP LOCALIZATION
```bash
asc subscriptions localizations create --subscription-id "<MONTHLY_ID>" \
  --locale "en-US" --name "<app_name> Monthly" \
  --description "Unlock all features with monthly subscription."

asc subscriptions localizations create --subscription-id "<MONTHLY_ID>" \
  --locale "ja" --name "<app_name> 月額プラン" \
  --description "月額プランで全機能を解放します。"

# Annual も同様（en-US + ja）
```

### PHASE 7: IAP REVIEW SCREENSHOT

> **⚠️ 絶対ルール（2026-02-24 実機検証済み）**
>
> | ルール | 理由 |
> |--------|------|
> | **リサイズ禁止** | `900×1956` 等の任意リサイズ → Apple「寸法が正しくありません」エラーで即拒否 |
> | **ネイティブ解像度をそのまま使う** | iPhone 16 Pro Max シミュレータ = **1320×2868**。これが Apple 標準サイズ |
> | **JPEG変換のみ** | `sips -s format jpeg`（`-z` フラグ使用禁止） |
> | **CLI が full upload** | `asc subscriptions review-screenshots create --file` = reserve+PUT+commit を内部で全実行 |
> | **width=0 は正常** | upload 直後は常に `imageAsset.width=0`。Apple 非同期処理中。再アップロード不要 |
> | **`asc subscriptions images create` は使わない** | プロモーショナル広告用。IAP review screenshot とは別物 |

**ステップ 1: Booted シミュレータの UDID を取得**
```bash
xcrun simctl list devices | grep Booted
# 例: iPhone 16 Pro Max (AF68C54D-D527-4A19-B4D1-5DEF182D8DE5) (Booted)
# UDID をメモする
```

**ステップ 2: Maestro MCP でアプリを起動しペイウォール画面まで遷移**

Maestro MCP（`mcp__maestro__launch_app` + `mcp__maestro__run_flow`）を使う。
CLI（`maestro test`）は禁止。MCP 経由のみ。

```
# 2-1. アプリ起動
mcp__maestro__launch_app(device_id="<UDID>", appId="<BUNDLE_ID>")

# 2-2. オンボーディング → ペイウォールまで遷移（順番通りに実行）
# Anicca の場合の実証済みフロー:
mcp__maestro__run_flow(device_id="<UDID>", flow_yaml="""
appId: <BUNDLE_ID>
---
- tapOn:
    id: "onboarding-welcome-cta"
""")

# 苦しみ選択画面: 何か1つ選んで「次へ」
mcp__maestro__run_flow(device_id="<UDID>", flow_yaml="""
appId: <BUNDLE_ID>
---
- tapOn: "夜更かし"
- waitForAnimationToEnd
- tapOn: "次へ"
""")

# ライブデモ画面: primary action をタップ
mcp__maestro__run_flow(device_id="<UDID>", flow_yaml="""
appId: <BUNDLE_ID>
---
- tapOn:
    id: "nudge-primary-action"
- waitForAnimationToEnd
""")

# 通知許可画面: 許可ボタンをタップ → ペイウォール表示
mcp__maestro__run_flow(device_id="<UDID>", flow_yaml="""
appId: <BUNDLE_ID>
---
- tapOn:
    id: "onboarding-notifications-allow"
- waitForAnimationToEnd
""")
```

別アプリで画面構成が異なる場合は `mcp__maestro__inspect_view_hierarchy` でペイウォール画面の要素を確認してから遷移する。

**ステップ 3: ペイウォール画面のスクリーンショットを撮影 → JPEG変換**
```bash
# PNG 撮影（ネイティブ解像度: iPhone 16 Pro Max = 1320×2868）
xcrun simctl io "<UDID>" screenshot /tmp/paywall-review.png

# JPEG変換のみ（-z リサイズフラグは絶対に使わない）
sips -s format jpeg /tmp/paywall-review.png --out /tmp/paywall-review.jpg

# サイズ確認（1320×2868 であることを確認）
identify /tmp/paywall-review.jpg 2>/dev/null || sips -g pixelWidth -g pixelHeight /tmp/paywall-review.jpg
```

**ステップ 4: Monthly と Annual 両方にアップロード**
```bash
# Monthly
asc subscriptions review-screenshots create \
  --subscription-id "<MONTHLY_SUB_ID>" \
  --file /tmp/paywall-review.jpg

# Annual
asc subscriptions review-screenshots create \
  --subscription-id "<ANNUAL_SUB_ID>" \
  --file /tmp/paywall-review.jpg

# 成功判定: JSON レスポンスに fileSize > 0 があれば OK
# width=0, height=0 は正常（Apple が非同期で処理中）
```

**エラーハンドリング**

| エラー | 原因 | 対処 |
|--------|------|------|
| `寸法が正しくありません` | リサイズした | 削除して正しいサイズで再アップロード |
| `Screenshot already exists` | 既に存在する | 既存を削除してから再アップロード |
| `Element not found` (Maestro) | 画面遷移が違う | `inspect_view_hierarchy` で現在の画面を確認 |

```bash
# 既存削除（"already exists" 時）
# まず既存 ID を取得
python3 -c "
import os, time, json, requests
import jwt as pyjwt
KEY_ID='<KEY_ID>'; ISSUER_ID='<ISSUER_ID>'
PRIVATE_KEY=open(os.path.expanduser('~/.asc/private_keys/AuthKey_<KEY_ID>.p8')).read()
payload={'iss':ISSUER_ID,'iat':int(time.time()),'exp':int(time.time())+1200,'aud':'appstoreconnect-v1'}
token=pyjwt.encode(payload,PRIVATE_KEY,algorithm='ES256',headers={'kid':KEY_ID})
h={'Authorization':f'Bearer {token}','Content-Type':'application/json'}
r=requests.get('https://api.appstoreconnect.apple.com/v1/subscriptions/<SUB_ID>/appStoreReviewScreenshot',headers=h)
print(r.json()['data']['id'])
"
# → ID を取得したら削除
asc subscriptions review-screenshots delete --id "<EXISTING_ID>" --confirm
# その後 ステップ 4 を再実行
```

### PHASE 8: IAP VALIDATE ★STOP GATE
```bash
# blocking=0 確認
asc validate subscriptions --app "<APP_ID>"
# blocking > 0 なら PHASE 5-7 に戻る

# READY_TO_SUBMIT 確認（両方必須）
asc subscriptions get --id "<MONTHLY_ID>"  # state = READY_TO_SUBMIT ?
asc subscriptions get --id "<ANNUAL_ID>"   # state = READY_TO_SUBMIT ?
# どちらかが MISSING_METADATA なら絶対に次に進まない
```

### PHASE 9: APP ASSETS

#### Step 1: アイコン生成（`app-icon` スキルを使う）

**スキル:** `code-with-beto/skills@app-icon`（インストール: `npx skills add code-with-beto/skills@app-icon -g -y`）

```bash
# Step 1-A: SnapAI の設定確認（OpenAI key が必要）
npx snapai config --show
# → "Not configured" ならユーザーに OpenAI key を要求して設定:
#   npx snapai config --openai-api-key sk-xxxxxxxx

# Step 1-B: SnapAI で 1024×1024 PNG を生成（透過背景）
npx snapai icon \
  --prompt "<app_name> iOS app icon. Minimalist design. <concept_1_line>. Central symbol fills 70% of canvas. No text. Premium, App Store ready." \
  --background transparent \
  --output-format png \
  --style minimalism \
  --quality high
# → ./assets/icon-[timestamp].png に保存される
# ⚠️ 重要: SnapAI は --background transparent を指定しても白背景で出力する。
#   プロンプトで "gradient background" を指定しても無視される。
#   必ず Step 1-C で ImageMagick を使って背景を追加する。

# ⛔ SnapAI 未設定の場合はここで停止。フォールバックなし。
# → ユーザーに「OpenAI API key が必要です: npx snapai config --openai-api-key sk-xxxx」と伝える

# Step 1-C: ImageMagick でグラデーション背景を追加（必須 — App Store は透過NG）
# brew install imagemagick  # 未インストールの場合
ICON_SRC="./assets/icon-[timestamp].png"

# 1. 白背景をアルファ透過に変換
convert "$ICON_SRC" -fuzz 5% -transparent white /tmp/icon-transparent.png

# 2. グラデーション背景を作成してアイコンと合成
convert -size 1024x1024 \
  gradient:"#F5A623-#E8563A" \
  /tmp/icon-transparent.png \
  -compose over -composite \
  /tmp/icon-final.png

# 3. 結果をユーザーに見せて確認（必須 — OKが出るまで色変更して繰り返す）
open /tmp/icon-final.png

# Step 1-D: Xcode xcassets に配置（Swift/Xcode プロジェクト用）
cp /tmp/icon-final.png \
  <output_dir>/<app_name>ios/<app_name>/Assets.xcassets/AppIcon.appiconset/icon.png
# ※ Contents.json の "filename": "icon.png" と一致していること確認
```

**注意: app-icon スキルは本来 Expo 向け（Step 4 以降の iOS 26 .icon フォルダ / app.json は Swift/Xcode では不要）。PNG 生成（Step 3）だけを使う。**

#### Step 2: スクショ生成（screenshot-creator スキル）

→ `.claude/skills/screenshot-creator/SKILL.md` を読んで Step 0〜7 を実行する
  （A/B テストではなく新規生成のため、screenshot-ab の PHASE 1/2 はスキップ）

**⚠️ Pencil 設計の絶対ルール（違反 = テキスト崩れ / 画像表示バグ）:**

| ルール | 理由 |
|--------|------|
| テキストノードに必ず `width: "fill_container"` | 未設定だとフレーム外にはみ出す |
| 日本語ヘッドラインは `fontSize: 22` 以下 | 28px × 14文字でオーバーフロー確認済み |
| 親フレームに `layout: "vertical"` を明記 | 省略すると CaptionArea/MockupArea が横並びになる |
| 画像差し替えは**必ず新しいファイル名** | 同じパスの上書きはPencilキャッシュで反映されない |
| `get_screenshot` = MCP base64のみ（ファイル保存されない） | ASC用ファイルはシミュレータ撮影で別途取得 |

```
[シミュレータ準備（Dynamic Island 除去）]
0. iPhone SE 3rd gen を使う（Dynamic Island/ノッチなし）
   UDID: xcrun simctl list devices | grep "SE (3rd"
   → CBA51D41-D404-4843-AA18-738C5068FFE4 等

   iPhone 14+ を使う場合、Dynamic Island 除去が必要:
   xcrun simctl io "<UDID>" screenshot /tmp/screen_raw.png
   python3 -c "
   from PIL import Image
   img = Image.open('/tmp/screen_raw.png')
   crop = img.crop((0, 185, img.width, img.height))
   crop.save('/tmp/screen_home_v2.png')  # ★新しいファイル名で保存
   "

[EN スクショ]
1. screenshot-creator Step 1: ヒアリング（アプリ名・機能・ターゲット・言語=英語）

2. screenshot-creator Step 2〜3: スタイルガイド取得 + 英語コピー作成
   出力: screen1/2/3 の英語キャプション（採点 8/10 以上で確定）

3. screenshot-creator Step 4: Pencil .pen ファイルにデザイン構築
   raw スクリーンショット確認: docs/screenshots/raw/screen1~3.png が存在するか
   なければ: make capture-only で XCUITest 撮影のみ実行

4. screenshot-creator Step 5〜6: spec-validator（10項目 PASS）→ quality-reviewer（7/10+）

5. screenshot-creator Step 7: PNG 書き出し

   **⚠️ ファイル保存パス絶対ルール（2026-02-24 確定）**

   | 禁止 | 正しいパス |
   |------|-----------|
   | `/tmp/screen1.png` など `/tmp/` 以下 | 禁止。再起動で消える |
   | Node.js スクリプト自作 | 禁止 |
   | HTTP API 直接叩く | 禁止 |

   **正しいパス（プロジェクト内に必ず保存）:**
   ```
   {output_dir}/docs/screenshots/raw/screen1~3.png       ← シミュレータ生PNG（iPhone SE推奨）
   {output_dir}/docs/screenshots/processed/screen1~3.png ← Pencil合成済み
   {output_dir}/docs/screenshots/resized/screen1~3.png   ← ASCアップロード用（1290×2796）
   ```

   **ASC アップロード用ファイルの確保手順（get_screenshot ではなく以下を使う）:**
   ```bash
   # 1. シミュレータから直接 PNG を取得
   xcrun simctl io "<SE_UDID>" screenshot docs/screenshots/raw/screen1.png

   # 2. PIL で DI クロップ（iPhone SE は不要）
   # python3 -c "from PIL import Image; img=Image.open('raw/screen1.png'); img.crop((0,185,img.width,img.height)).save('processed/screen1.png')"

   # 3. App Store 必須サイズにリサイズ
   sips -z 2796 1290 docs/screenshots/processed/screen1.png \
     --out docs/screenshots/resized/en-US/screen1.png
   ```

   出力確認: docs/screenshots/resized/en-US/screen1~3.png（プロジェクト内）

6. Slack 承認（slack-approval スキル）:
   → .claude/skills/slack-approval/SKILL.md を読んで requestApproval() を実行
   → title: "📸 App Store スクリーンショット確認 [EN]"
   → approved → Step 7 へ / denied → Step 1 から再実行

⚠️ ハードゲート（絶対ルール）:
   processed/ の画像を open コマンドで実際に開いて、ヘッドラインテキストが入っているか目視確認する。
   ヘッドラインなし → ASC アップロード禁止。Step 1 から再実行。

[JA スクショ]
7. screenshot-creator Step 1〜7 を日本語コピーで再実行
   出力: docs/screenshots/resized/ja/screen1~3.png（JA 版）

8. Slack 承認（slack-approval スキル）:
   → title: "📸 App Store スクリーンショット確認 [JA]"
   → approved → ASC アップロードへ / denied → Step 7 から再実行

⚠️ ハードゲート（JA も同じ）:
   resized/ja/ の画像を open コマンドで実際に開いて日本語ヘッドラインが入っているか確認。
   入っていない場合は ASC アップロード禁止。
```

#### Step 3: ASC アップロード（EN + JA）

**⚠️ リサイズ必須（スキップ禁止）**
`pencil_export.py` の出力は 780×1688。App Store は **1290×2796** を要求する。

```bash
# ★ リサイズ（必須 — これなしでアップロードすると "invalid screenshot dimensions" で却下）
mkdir -p docs/screenshots/resized/en-US docs/screenshots/resized/ja

for i in 1 2 3; do
  sips -z 2796 1290 docs/screenshots/processed/en/screen${i}.png \
    --out docs/screenshots/resized/en-US/screen${i}.png
  sips -z 2796 1290 docs/screenshots/processed/ja/screen${i}.png \
    --out docs/screenshots/resized/ja/screen${i}.png
done

# EN スクショ（locale: en-US）
asc screenshots upload --app-id "<APP_ID>" --locale en-US \
  --files docs/screenshots/resized/en-US/screen1.png \
          docs/screenshots/resized/en-US/screen2.png \
          docs/screenshots/resized/en-US/screen3.png

# JA スクショ（locale: ja）
asc screenshots upload --app-id "<APP_ID>" --locale ja \
  --files docs/screenshots/resized/ja/screen1.png \
          docs/screenshots/resized/ja/screen2.png \
          docs/screenshots/resized/ja/screen3.png
```

**注意:** `asc screenshots upload` は version localization（初回提出時）用。PPO Treatment localization に使う場合は `screenshot-ab` スキルの Step 7-3 を参照（Apple API 直接呼び出しが必要）。

#### Step 4: App Store メタデータ入力
```bash
# EN メタデータ
asc metadata update --app "<APP_ID>" --locale en-US \
  --title "<metadata.title_en>" \
  --subtitle "<metadata.subtitle_en>" \
  --description "<metadata.description_en>" \
  --keywords "<metadata.keywords_en>"

# JA メタデータ（locale は必ず "ja"。"ja-JP" は無効）
asc metadata update --app "<APP_ID>" --locale ja \
  --title "<metadata.title_ja>" \
  --subtitle "<metadata.subtitle_ja>" \
  --description "<metadata.description_ja>" \
  --keywords "<metadata.keywords_ja>"
```

### PHASE 10: BUILD & UPLOAD
```bash
cd <output_dir>/<app_name>ios
FASTLANE_SKIP_UPDATE_CHECK=1 fastlane set_version version:<version>
FASTLANE_SKIP_UPDATE_CHECK=1 FASTLANE_OPT_OUT_CRASH_REPORTING=1 fastlane release
# processingState = VALID になるまで待機

# ★ 必須: TestFlight ベータグループに配布（この手順を省くとテスターがビルドを見れない）
# ビルドIDを取得
BUILD_ID=$(asc builds list --app "<APP_ID>" --sort -uploadedDate --limit 1 | \
  python3 -c "import sys,json;d=json.load(sys.stdin);print(d['data'][0]['id'])")

# 全ベータグループのIDを取得して追加
asc beta-groups list --app "<APP_ID>" | \
  python3 -c "import sys,json;d=json.load(sys.stdin);[print(g['id']) for g in d['data']]" | \
  xargs -I{} asc builds add-groups --build "$BUILD_ID" --group {}
# → "Successfully added 1 group(s)" が各グループ分出ればOK
```

### PHASE 11: PREFLIGHT GATE
```bash
# GATE 1: Greenlight
greenlight preflight <app_dir>  # CRITICAL = 0 でなければ STOP

# GATE 2: IAP（D6-D10）
# D6: prices 175件 / D7: screenshot 存在 / D8: en-US localization
# D9: READY_TO_SUBMIT / D10: validate blocking=0
asc validate subscriptions --app "<APP_ID>"

# GATE 3: コード品質チェック（自動）
grep -r "Lorem\|lorem\|placeholder\|TODO\|FIXME" <app_dir>/Sources/ && echo "FAIL" || echo "PASS"

# GATE 4: 外部リンク生死確認（自動）
curl -I "<urls.privacy_en>" -o /dev/null -s -w "%{http_code}" | grep -q "200\|301\|302" || echo "FAIL: privacy_en URL dead"
curl -I "<urls.privacy_ja>" -o /dev/null -s -w "%{http_code}" | grep -q "200\|301\|302" || echo "FAIL: privacy_ja URL dead"
curl -I "https://www.apple.com/legal/internet-services/itunes/dev/stdeula/" -o /dev/null -s -w "%{http_code}" | grep -q "200" || echo "FAIL: EULA URL dead"

# GATE 5: スクショ確認（自動）
asc screenshots list --app "<APP_ID>" --locale en-US | python3 -c "import sys,json;d=json.load(sys.stdin);print('PASS' if len(d['data'])>=3 else 'FAIL: EN screenshots <3')"
asc screenshots list --app "<APP_ID>" --locale ja | python3 -c "import sys,json;d=json.load(sys.stdin);print('PASS' if len(d['data'])>=3 else 'FAIL: JA screenshots <3')"

# GATE 1〜5 全て PASS でなければ STOP。1つでも FAIL → 修正して再実行
```

### PHASE 11.5: APP PRIVACY 手動設定（PHASE 12 の前に必須 — API で設定不可）

> **⚠️ 重要（2026-02-24 実機検証）: App Privacy は ASC API で設定できない**
> `/v1/apps/{id}/appDataUsages` は 404 を返す。ユーザーが ASC Web で手動設定するまで先に進まない。

ユーザーに以下を伝えてから待機する:

```
【ユーザー作業】App Privacy の設定（App Store Connect Web — 所要2分）

1. https://appstoreconnect.apple.com → My Apps → <app_name> を開く
2. 左メニュー「App Privacy」をクリック
3.「データの使用方法を編集」ボタンをクリック
4. 収集するデータカテゴリを選択:
   □ Identifiers（Device ID → Third-Party Advertising, Analytics, App Functionality）
   □ Usage Data（Product Interaction → Analytics）
   ※ 日記エントリー・アファメーションは収集しない（ローカル保存のみ）
5. 各カテゴリで「このデータをユーザーのアカウントやデバイスにリンクしているか？」→「いいえ」
6.「完了」→「保存」
7. 完了したらエージェントに「App Privacy 設定完了」と伝える

設定できるカテゴリの例（アプリによって異なる）:
  - 分析（Identifiers, Usage Data）
  - RevenueCat（Purchase History）
  - 収集しない（Health/Fitness, Sensitive Info など）
```

ユーザーが「完了」と言ったら PHASE 12 に進む。

### PHASE 12: SUBMIT
```bash
VERSION_ID=$(asc versions list --app "<APP_ID>" | \
  python3 -c "import sys,json;d=json.load(sys.stdin);print(d['data'][0]['id'])")

BUILD_ID=$(asc builds list --app "<APP_ID>" --sort -uploadedDate --limit 1 | \
  python3 -c "import sys,json;d=json.load(sys.stdin);print(d['data'][0]['id'])")

asc submit create --app "<APP_ID>" \
  --version-id "$VERSION_ID" --build "$BUILD_ID" --confirm

# 確認: state = WAITING_FOR_REVIEW ✅
asc review submissions-list --app "<APP_ID>"
```

---

## 参照ファイル

| ファイル | いつ読む |
|---------|---------|
| `references/iap-bible.md` | PHASE 4-8 の詳細手順・価格ポイント取得方法 |
| `references/spec-template.md` | PHASE 1 の INPUT 確認 |
| `references/submission-checklist.md` | PHASE 11 のゲートチェック全項目 |
| `scripts/add_prices.py` | PHASE 5 の価格設定実行 |
