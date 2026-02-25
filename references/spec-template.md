# spec.md テンプレート

mobileapp-builder スキルに渡す INPUT ファイルの標準フォーマット。

---

```markdown
# <App Name>

## 基本情報
- app_name: YourAppName
- bundle_id: com.yourcompany.yourappname
- version: 1.0
- price_monthly_usd: 4.99
- price_annual_usd: 19.99
- output_dir: ~/your-project/mobile-apps/yourappname

## コンセプト
感謝日記アプリ。毎日3つの感謝を記録することで、ネガティブ思考のループから抜け出す。
うつ・不安・自己嫌悪に悩む25-35歳のための習慣化ツール。

## 画面構成
- オンボーディング: 3ステップ（価値提案→習慣目標→通知許可）
- メイン画面: 今日の感謝3件入力 + 過去ログ一覧
- 通知: 毎夜21:00「今日の感謝を記録しよう」リマインダー
- 設定画面: 通知時刻変更 + Privacy Policy リンク

## Paywall
- monthly_price: $4.99/month
- annual_price: $19.99/year
- trial: 7日間無料
- cta_text: 無料で始める（7日間）

## メタデータ（ASC）
- title_en: Thankful - Gratitude Journal
- subtitle_en: Daily habit for happiness
- title_ja: Thankful - 感謝日記
- subtitle_ja: 幸福度を高める毎日の習慣
- keywords_en: gratitude,journal,happiness,mindfulness,diary,daily,habit,wellbeing,mental health,positive
- keywords_ja: 感謝,日記,幸福,マインドフルネス,習慣,メンタルヘルス,ポジティブ,毎日
- privacy_policy_url: https://yourdomain.com/privacy
```

---

## 必須フィールド一覧

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `app_name` | YES | Xcode プロジェクト名（英数字・ハイフン） |
| `bundle_id` | YES | `com.yourcompany.<name>` 形式（Apple Developer アカウントの Team ID ではなく、任意の逆ドメイン） |
| `version` | YES | `1.0` 固定（初回提出） |
| `price_monthly_usd` | YES | USD 価格（例: 4.99） |
| `price_annual_usd` | YES | USD 価格（例: 19.99） |
| `output_dir` | YES | 絶対パス。末尾スラッシュなし |
| `concept` | YES | 1-3行。誰の何の苦しみを減らすか |
| `paywall.cta_text` | YES | ペイウォールのメインボタン文言 |
| `metadata.title_en` | YES | 30文字以内 |

## 価格の決め方

| プラン | 推奨価格 |
|--------|---------|
| Monthly | $4.99 |
| Annual | $19.99（月換算 $1.66 ≒ 66% off） |

**根拠:** RevenueCat Industry Benchmark 2024 — iOS消費者アプリの中央値は $4.99/月。
Annual は Monthly の 3-4ヶ月相当が解約率を下げる最適ポイント。
