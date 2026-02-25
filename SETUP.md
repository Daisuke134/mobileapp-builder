# mobileapp-builder — Complete Setup Guide

> **Goal:** After completing this guide, running `"build an app"` in Claude Code will autonomously ship an iOS app to the App Store with 3 human approvals.

Run the checker first to see what's missing:
```bash
bash ~/.claude/skills/mobileapp-builder/scripts/check-prerequisites.sh
```

---

## Section 1: Required Accounts

Create these accounts before anything else (most are free):

| # | Account | URL | Cost | Wait |
|---|---------|-----|------|------|
| 1 | **Apple Developer Program** | [developer.apple.com/enroll](https://developer.apple.com/enroll) | $99/year | ⚠️ 24-48時間かかる場合あり。最初に申請すること |
| 2 | **App Store Connect API Key** | ASC → Users and Access → Integrations → Keys → + | Free | ⚠️ .p8 は1度しかダウンロードできない。必ず安全な場所に保存 |
| 3 | **RevenueCat** | [app.revenuecat.com](https://app.revenuecat.com) | Free (up to $2.5k MRR) | 即時 |
| 4 | **Mixpanel** | [mixpanel.com/register](https://mixpanel.com/register) | Free (20M events/month) | 即時 |
| 5 | **X Developer Portal** | [developer.twitter.com](https://developer.twitter.com) | Free tier available | 即時 |
| 6 | **Apify** | [apify.com](https://apify.com) | Free ($5 credit included) | 即時 |
| 7 | **Google Cloud (Gemini API)** | [console.cloud.google.com](https://console.cloud.google.com) | Free tier available | 即時 |
| 8 | **OpenAI** | [platform.openai.com](https://platform.openai.com) | Pay-per-use | 即時 |
| 9 | **Slack workspace** | [slack.com](https://slack.com) | Free | 即時 |
| 10 | **ドメイン（Privacy Policy 用）** | 任意のレジストラ（Namecheap, Google Domains等） | ~$10/年 | 即時。ホスティング先も必要（GitHub Pages 等） |

---

## Section 2: Environment Variables

Save all keys to `~/.config/mobileapp-builder/.env`:

```bash
mkdir -p ~/.config/mobileapp-builder
```

Then add to `~/.config/mobileapp-builder/.env`:

```bash
# ── Apple / App Store Connect ────────────────────────────────────────
# Get from: ASC → Users and Access → Integrations → Keys → +
ASC_KEY_ID=<YOUR_KEY_ID>
ASC_ISSUER_ID=<YOUR_ISSUER_ID>
ASC_KEY_PATH=~/Downloads/AuthKey_<YOUR_KEY_ID>.p8   # downloaded .p8 file path

# ── RevenueCat ────────────────────────────────────────────────────────
# Get from: RC Dashboard → Project Settings → API Keys → Secret Keys
REVENUECAT_API_KEY=sk_...

# ── Mixpanel ─────────────────────────────────────────────────────────
# Get from: Mixpanel → Project Settings → Project Token
MIXPANEL_TOKEN=abc123

# ── X (Twitter) Research ─────────────────────────────────────────────
# Get from: developer.twitter.com → App → Keys and tokens → Bearer Token
X_BEARER_TOKEN=AAAA...

# ── Apify (TikTok + Trend Analysis) ──────────────────────────────────
# Get from: apify.com → Settings → Integrations → API token
APIFY_TOKEN=apify_api_...

# ── Gemini (TikTok Research AI analysis) ─────────────────────────────
# Get from: console.cloud.google.com → APIs & Services → Credentials
GEMINI_API_KEY=AIza...

# ── OpenAI (icon generation via snapai) ──────────────────────────────
# Get from: platform.openai.com → API keys
OPENAI_API_KEY=sk-...

# ── Slack (approval notifications) ───────────────────────────────────
# Get from: api.slack.com → Your Apps → OAuth & Permissions
SLACK_BOT_TOKEN=xoxb-...
# Get from: api.slack.com → Your Apps → Basic Information → App-Level Tokens
SLACK_APP_TOKEN=xapp-...
# The channel ID where you want approval notifications (right-click channel → Copy link)
SLACK_CHANNEL_ID=C...

# ── Privacy Policy Domain ────────────────────────────────────────────────
# Your domain where Privacy Policy + Landing Page will be hosted
# PHASE 3.5 will generate pages at: https://$PRIVACY_POLICY_DOMAIN/{slug}/privacy/en
PRIVACY_POLICY_DOMAIN=yourdomain.com
```

To load the env automatically, add to your `~/.zshrc` or `~/.bashrc`:
```bash
[ -f ~/.config/mobileapp-builder/.env ] && source ~/.config/mobileapp-builder/.env
```

---

## Section 3: Xcode（最初にインストール）

**Xcode 16+ が必須。** インストールには 20〜40GB のディスクスペースと 30〜60分かかる。

```bash
# Mac App Store から Xcode をインストール（または xcode-select --install）
# インストール後、必ず Command Line Tools も設定する:
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -runFirstLaunch  # 初回ライセンス承諾
xcodebuild -version              # Xcode 16.x が表示されれば OK
```

---

## Section 4: CLI Tools

Install one by one:

```bash
# 1. asc — App Store Connect CLI
brew install nickvdyck/tap/asc

# 2. fastlane — Build automation
brew install fastlane

# 3. greenlight — Pre-submission scanner
cd /tmp && git clone https://github.com/RevylAI/greenlight.git \
  && cd greenlight && make build \
  && sudo cp build/greenlight /usr/local/bin/
# Verify:
greenlight --version

# 4. imagemagick — Image processing
brew install imagemagick

# 5. snapai — AI icon generation
npm install -g snapai
npx snapai config --openai-api-key "$OPENAI_API_KEY"

# 6. Python libraries
pip3 install Pillow requests PyJWT

# 7. ios-deploy — Device deployment
brew install ios-deploy

# 8. Verify everything
bash ~/.claude/skills/mobileapp-builder/scripts/check-prerequisites.sh
```

---

## Section 5: MCP Servers (Claude Code)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```jsonc
{
  "mcpServers": {
    "pencil": {
      "command": "npx",
      "args": ["-y", "@pencil-so/mcp"]
    },
    "maestro": {
      "command": "npx",
      "args": ["-y", "@maestro-org/mcp-server"]
    }
  }
}
```

After editing, **restart Claude Code**, then verify:
- Type `mcp__pencil__get_editor_state` — should not return "tool not found"
- Type `mcp__maestro__list_devices` — should list your simulators

---

## Section 6: Claude Code Sub-skills

Install all required skills:

```bash
# Main skill
npx skills add Daisuke134/mobileapp-builder -g -y

# Sub-skills (all required)
npx skills add Daisuke134/anicca-products@x-research -g -y
npx skills add Daisuke134/anicca-products@tiktok-research -g -y
npx skills add Daisuke134/anicca-products@apify-trend-analysis -g -y
npx skills add Daisuke134/anicca-products@ralph-autonomous-dev -g -y
npx skills add Daisuke134/anicca-products@screenshot-creator -g -y
npx skills add Daisuke134/anicca-products@slack-approval -g -y
npx skills add code-with-beto/skills@app-icon -g -y
```

Verify:
```bash
npx skills list | grep -E "mobileapp-builder|x-research|tiktok-research|apify|ralph|screenshot-creator|slack-approval|app-icon"
```

---

## Section 7: Fastlane Configuration

Every app built by mobileapp-builder needs these variables in its `Fastfile`:

```ruby
# Set these at the top of your Fastfile
API_KEY_ID     = ENV["ASC_KEY_ID"]      # from ~/.config/mobileapp-builder/.env
API_ISSUER_ID  = ENV["ASC_ISSUER_ID"]  # from ~/.config/mobileapp-builder/.env
API_KEY_PATH   = ENV["ASC_KEY_PATH"]   # from ~/.config/mobileapp-builder/.env
```

The mobileapp-builder scaffold (PHASE 2) will auto-generate the Fastfile with these env vars if you have `ASC_KEY_ID`, `ASC_ISSUER_ID`, and `ASC_KEY_PATH` set in your environment.

**Fastlane Appfile（初回のみ設定）:**
```ruby
# aniccaios/fastlane/Appfile
apple_id "your@email.com"           # Apple ID (Apple Developer Program のメアド)
itc_team_id "XXXXXXXXXX"            # ASC → Users → Your name → Team ID で確認
team_id "XXXXXXXXXX"                # Apple Developer Portal → Membership → Team ID
```

---

## Section 8: Slack App Setup (for approval notifications)

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. Name: `mobileapp-builder`, select your workspace
3. **OAuth & Permissions** → Bot Token Scopes → Add:
   - `chat:write`
   - `chat:write.public`
4. **App-Level Tokens** → Generate Token → Scope: `connections:write` → copy `xapp-...` token
5. **Install to Workspace** → copy `xoxb-...` bot token
6. Add bot to your approval channel: `/invite @mobileapp-builder`
7. Copy the channel ID (right-click channel → **Copy link** → extract `C...` at the end)

---

## Section 9: Final Verification

Run the full check:
```bash
bash ~/.claude/skills/mobileapp-builder/scripts/check-prerequisites.sh
```

All items should show ✅. Then test in Claude Code:
```
"Build an iOS app about [your idea]"
```

The agent will:
1. Research trends (PHASE 0)
2. Generate spec.md → **STOP 1**: ask your approval in Slack
3. Build the app (PHASE 2–9)
4. Upload to TestFlight → **STOP 2**: ask you to test
5. Preflight scan → **STOP 3**: ask you to set App Privacy in ASC Web
6. Submit → `WAITING_FOR_REVIEW` ✅
