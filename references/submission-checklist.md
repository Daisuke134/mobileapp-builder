# App Store 提出前チェックリスト

mobileapp-builder PHASE 11 で実行する全項目。1件でも FAIL → STOP。

---

## A: コード品質

| # | チェック項目 | コマンド |
|---|------------|---------|
| A1 | Greenlight CRITICAL = 0 | `greenlight preflight <app_dir>` |
| A2 | PrivacyInfo.xcprivacy 存在確認 | Greenlight が検出 |
| A3 | Privacy Policy リンク（Settings画面） | Greenlight が検出 |

---

## B: ビルド

| # | チェック項目 | コマンド |
|---|------------|---------|
| B1 | ビルドが VALID（processingState = VALID） | `asc builds list --app <APP_ID> --sort -uploadedDate --limit 1` |
| B2 | バージョンが存在 | `asc versions list --app <APP_ID>` |

---

## C: RevenueCat

| # | チェック項目 | 確認方法 |
|---|------------|---------|
| C1 | Monthly product が RevenueCat に登録済み | RC Dashboard |
| C2 | Annual product が RevenueCat に登録済み | RC Dashboard |
| C3 | Offering に Monthly + Annual の両パッケージ | RC Dashboard |

---

## D: IAP（最重要 — Guideline 2.1 拒否防止）

| # | チェック項目 | コマンド |
|---|------------|---------|
| D1 | `asc validate subscriptions` blocking = 0 | `asc validate subscriptions --app <APP_ID>` |
| D2 | Monthly: state = READY_TO_SUBMIT | `asc subscriptions get --id <MONTHLY_ID>` |
| D3 | Annual: state = READY_TO_SUBMIT | `asc subscriptions get --id <ANNUAL_ID>` |
| D4 | Monthly: 175 territories 価格設定済み | `asc subscriptions prices list --id <MONTHLY_ID> --paginate \| python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d['data']))"` |
| D5 | Annual: 175 territories 価格設定済み | `asc subscriptions prices list --id <ANNUAL_ID> --paginate \| python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d['data']))"` |
| D6 | Monthly: App Review Screenshot 添付済み | `asc subscriptions review-screenshots create --subscription-id <MONTHLY_ID> --file ./paywall-review.png` → "already exists" |
| D7 | Annual: App Review Screenshot 添付済み | `asc subscriptions review-screenshots create --subscription-id <ANNUAL_ID> --file ./paywall-review.png` → "already exists" |
| D8 | Monthly: en-US ローカライゼーション設定済み | `asc subscriptions localizations list --subscription-id <MONTHLY_ID>` |
| D9 | Annual: en-US ローカライゼーション設定済み | `asc subscriptions localizations list --subscription-id <ANNUAL_ID>` |

---

## E: アプリメタデータ

| # | チェック項目 | コマンド |
|---|------------|---------|
| E1 | en-US タイトル・サブタイトル・説明文設定済み | `asc localizations list --version <VERSION_ID>` |
| E2 | ja タイトル・サブタイトル・説明文設定済み | 同上 |
| E3 | キーワード設定済み（en-US + ja） | 同上 |
| E4 | App Store スクリーンショット 3枚（1290×2796） | ASC でスクショ確認 |
| E5 | アイコン（1024×1024）設定済み | Xcode プロジェクト内確認 |
| E6 | Privacy Policy URL 設定済み | `asc app-infos list --app <APP_ID>` |

---

## F: 提出前の最終確認

| # | チェック項目 | 方法 |
|---|------------|------|
| F1 | 全 D チェック（D1-D9）が PASS した後に提出する | フェーズ順序を守る |
| F2 | キャンセル→再提出ではなく初回提出 | MISSING_METADATA のまま提出していない |

---

## よくあるリジェクト理由と防ぎ方

| リジェクト理由 | 防ぐチェック | 対処 |
|--------------|------------|------|
| Guideline 2.1（IAP products not submitted for review） | D1-D9 全部 PASS | `add_prices.py` + screenshot + localization |
| Guideline 5.1.1（Privacy Policy） | A3, E6 | Settings 画面に Privacy Policy リンク追加 |
| Guideline 2.3.3（Metadata misrepresentation） | E1-E4 | スクショと実機能が一致しているか確認 |
| PrivacyInfo.xcprivacy 不足 | A2 | Greenlight が検出するので CRITICAL=0 を確認 |
