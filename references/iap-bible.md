# IAP Bible — サブスクリプション設定完全手順

Daily Dhamma の3回リジェクト経験から得た全知識。

---

## なぜ IAP がリジェクトの最大要因か

Apple Guideline 2.1 は「IAP products not submitted for review」で発動する。
原因は必ず以下の3つのどれか：

| 原因 | 症状 | 修正 |
|------|------|------|
| 175カ国価格なし | MISSING_METADATA から抜けられない | add_prices.py で一括追加 |
| App Review Screenshot なし | MISSING_METADATA のまま | 各サブスクに1枚ずつアップロード |
| en-US ローカライゼーションなし | MISSING_METADATA のまま | en-US を必ず設定 |
| MISSING_METADATA のまま提出 | 提出時スナップショットで封じ込め | PHASE 8 ゲートで防止 |

---

## 価格ポイント ID の取得方法

```bash
# Step 1: Monthly の US 価格ポイント一覧を取得
asc subscriptions price-points list \
  --subscription-id "<MONTHLY_SUB_ID>" \
  --paginate 2>&1 | python3 -c "
import sys, json
d = json.load(sys.stdin)
for pp in d['data']:
    attrs = pp['attributes']
    if attrs.get('territory') == 'USA':
        print(pp['id'], attrs.get('customerPrice'), attrs.get('territory'))
"

# Step 2: $4.99 に対応する price point ID を確認
# 出力例: eyJzIjoiNjc1OTM4OTE1MCIsInQiOiJVU0EiLCJwIjoiMTAwNjIifQ 4.99 USA

# Step 3: そのIDが Equalization API 用の base price point ID
```

---

## Equalization API の仕組み

```bash
# US 価格ポイントから全175カ国の等価価格を取得
asc subscriptions price-points equalizations \
  --id "<US_PRICE_POINT_ID>" \
  --paginate

# 出力: 175カ国分の price point ID が返ってくる
# 各エントリを asc subscriptions prices add で追加する
```

---

## add_prices.py の使い方

```bash
# 引数で Monthly と Annual の両方を一括処理
python3 .claude/skills/mobileapp-builder/scripts/add_prices.py \
  --annual-sub "ANNUAL_SUBSCRIPTION_ID" \
  --annual-pp "ANNUAL_US_PRICE_POINT_ID" \
  --monthly-sub "MONTHLY_SUBSCRIPTION_ID" \
  --monthly-pp "MONTHLY_US_PRICE_POINT_ID"

# 期待される出力:
# === Annual ===
# Total equalized territories: 174
# DONE: ok:174, skip:0, fail:0
#
# === Monthly ===
# Total equalized territories: 174
# DONE: ok:174, skip:0, fail:0
```

---

## READY_TO_SUBMIT への遷移条件

サブスクリプションが MISSING_METADATA → READY_TO_SUBMIT になるには、
**以下の3つが全部揃う必要がある**：

```
1. 少なくとも1つのテリトリーに価格設定（175カ国が推奨）
2. en-US ローカライゼーション（name フィールドが必須）
3. App Store Review Screenshot（1枚）
```

**確認コマンド:**
```bash
asc subscriptions get --id "<SUB_ID>" | \
  python3 -c "import sys,json;d=json.load(sys.stdin);print(d['data']['attributes']['state'])"
# READY_TO_SUBMIT が出るまで修正を繰り返す
```

---

## 初回サブスクリプション提出のルール（Apple 公式）

> 「最初のサブスクリプションは、新しいアプリバージョンと共に提出する必要があります」

- 初回は `asc submit create` でアプリバージョンと一緒に提出（単独提出不可）
- 2回目以降は単独でも提出可能

**正しい提出コマンド:**
```bash
# NG: サブスクだけ先に提出しようとすると FIRST_SUBSCRIPTION_MUST_BE_SUBMITTED_ON_VERSION エラー
asc subscriptions submit --subscription-id "XXX"  # ← 初回はこれだけではダメ

# OK: アプリバージョンと一緒に提出
asc submit create --app "APP_ID" --version-id "VERSION_ID" --build "BUILD_ID" --confirm
```

---

## Apple がスナップショットするタイミング

`asc submit create` を実行した瞬間に、Apple は全サブスクリプションの状態をスナップショットする。

- 提出時に MISSING_METADATA → そのサブスクは審査に含まれない → Guideline 2.1 拒否
- 提出後に READY_TO_SUBMIT に変わっても手遅れ
- **解決策: キャンセル → 再提出**

```bash
# 間違って提出した場合の修正
asc review submissions-cancel --id "<SUBMISSION_ID>" --confirm
# → READY_TO_SUBMIT に直す
# → 再提出
asc submit create --app "APP_ID" --version-id "VERSION_ID" --build "BUILD_ID" --confirm
```

---

## App Review Screenshot

**正しいコマンド: `asc subscriptions review-screenshots create`**

> ⚠️ 過去の誤り（2026-02-24）: `asc subscriptions images create` を使って FAILED になり「API が壊れている」と誤認した。
> `subscriptions images` は**プロモーショナル画像**用（別物）。
> IAP Review Screenshot には `subscriptions review-screenshots` を使う。

```bash
# ★ 正しいコマンド
asc subscriptions review-screenshots create \
  --subscription-id "<MONTHLY_SUB_ID>" \
  --file "./paywall-review.png"

asc subscriptions review-screenshots create \
  --subscription-id "<ANNUAL_SUB_ID>" \
  --file "./paywall-review.png"

# "already exists" = 正常（既にアップロード済み）
```

**画像サイズ要件:** 900×1956 ピクセル（iPhone 縦向き相当）

| コマンド | 用途 | 注意 |
|---------|------|------|
| `asc subscriptions review-screenshots create` | IAP App Review Screenshot | ✅ 正しい |
| `asc subscriptions images create` | プロモーショナル画像（販促用） | ❌ IAP スクリーンショットではない |

---

## よくあるエラーと対処

| エラー | 原因 | 対処 |
|--------|------|------|
| `FIRST_SUBSCRIPTION_MUST_BE_SUBMITTED_ON_VERSION` | 初回サブスクを単独提出しようとした | `asc submit create` でアプリと一緒に提出 |
| `SUBSCRIPTION_ALREADY_SUBMITTED` | 既に提出済み | キャンセルして再提出、または `asc submit create` を使う |
| `Screenshot already exists` | スクショが既にある | エラーではない。正常動作 |
| `missing pricing for N territories` | N カ国分の価格が未設定 | add_prices.py を実行 |
| state = MISSING_METADATA が変わらない | 価格 or screenshot or en-US ローカライズのどれかが欠けている | 3つ全部確認 |
| screenshot state = FAILED (width:0, height:0) | API経由アップロードのS3処理失敗 | ASC Web から手動アップロード（上記参照） |
