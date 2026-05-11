# Reddit Product Ideas Extractor

This is an automated script that uses GitHub Actions and AI to extract potential product ideas from Reddit subreddits. It now uses **RSS feeds** instead of the Reddit API to avoid rate limiting and authentication issues.

## Features

- **RSS-based scraping**: Uses old.reddit.com RSS feeds to fetch posts without API authentication
- **SQLite database**: Tracks seen posts to avoid duplicates across runs
- **AI-powered extraction**: Uses OpenAI-compatible API to extract product ideas (supports OpenAI, OpenRouter, local LLMs, etc.)
- **Email notifications**: Sends curated top 10 ideas via Gmail
- **Feishu/Lark notifications**: Pushes ideas to Feishu groups via webhook (text and rich card formats)
- **Scheduled execution**: Runs daily at 23:30 UTC via GitHub Actions
- **Configurable subreddits**: Easy to add/remove subreddits with optional flair filters
- **Provider agnostic**: Switch between AI providers by changing environment variables

## How It Works

1. Fetches new posts from configured subreddits via RSS feeds
2. Stores posts in SQLite database to track what's been seen
3. Only processes **new posts** (not seen in previous runs)
4. Sends post content to AI for product idea extraction
5. Filters and ranks the top 10 best ideas
6. Generates HTML email and sends via Gmail SMTP

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd reddit-product-ideas
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file or set these as GitHub Secrets:

```bash
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
AI_API_KEY=your-ai-api-key
AI_BASE_URL=https://api.openai.com/v1  # Optional, defaults to OpenAI
AI_MODEL=gpt-3.5-turbo  # Optional, defaults to gpt-3.5-turbo
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx  # Optional
```

**Getting credentials:**
- **Gmail App Password**: https://myaccount.google.com/apppasswords
- **Feishu Webhook**: Create a bot in your Feishu group (see instructions below)
- **AI API Key**: Depends on your provider:
  - **OpenAI**: https://platform.openai.com/api-keys
  - **OpenRouter**: https://openrouter.ai/keys (supports multiple models)
  - **Local LLMs** (e.g., Ollama): `http://localhost:11434/v1` with any key
  - **Other providers**: Any service with OpenAI-compatible API

**Provider Examples:**
```bash
# OpenAI
AI_API_KEY=sk-your-openai-key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini

# OpenRouter (access to 100+ models)
AI_API_KEY=sk-or-your-openrouter-key
AI_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=openai/gpt-oss-120b:free

# Local Ollama
AI_API_KEY=ollama
AI_BASE_URL=http://localhost:11434/v1
AI_MODEL=llama3.2
```

### 4. Configure subreddits

Edit `helper.py` to customize which subreddits to monitor:

```python
SUBREDDITS = [
    {
        "name": "ProductHunters",
        "rss_url": "https://old.reddit.com/r/ProductHunters/new.rss"
    },
    # Example with flair filter:
    # {
    #     "name": "midsoledeals",
    #     "rss_url": "https://old.reddit.com/r/midsoledeals/search.rss?q=flair%3A%22New%20Balance%22&restrict_sr=1&sort=new"
    # }
]
```

## GitHub Actions Setup

1. Go to your repository Settings → Secrets and variables → Actions
2. Add the following secrets:
   - `EMAIL_USER`: Your Gmail address
   - `EMAIL_PASS`: Your Gmail app password
   - `AI_API_KEY`: Your AI provider API key
   - `AI_BASE_URL`: (Optional) API base URL, defaults to OpenAI
   - `AI_MODEL`: (Optional) Model name, defaults to gpt-3.5-turbo

The workflow runs automatically every day at 23:30 UTC, or you can trigger it manually using the "Run workflow" button.

## Feishu/Lark Setup

To receive notifications in Feishu (Lark):

1. **Create a Custom Bot** in your Feishu group:
   - Open your Feishu group chat
   - Click the group settings (⋮) → Add Bot → Custom Bot
   - Give it a name (e.g., "Product Ideas Bot")
   - Copy the generated Webhook URL

2. **Configure the webhook**:
   - In `.env` file or GitHub Secrets, add:
     ```bash
     FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_URL
     ```

3. **Optional: Enable security settings** (recommended for production):
   - In the bot settings, choose one of: Signatures, IP Whitelist, or Keywords
   - If using signatures, you'll need to modify `send_feishu.py` to include HMAC signing

The script will send both a simple text message and can be configured to send rich interactive cards with formatted content.

## Local Testing

```bash
# Clear any existing database for fresh test
rm -f reddit_posts.db debug.log

# Run the script
python main.py
```

## Files Structure

- `main.py` - Entry point, orchestrates the workflow
- `helper.py` - Core logic: RSS fetching, database management, AI integration (OpenAI-compatible)
- `send_email.py` - Email sending via Gmail SMTP
- `send_feishu.py` - Feishu/Lark notifications via webhook (text and interactive card formats)
- `requirements.txt` - Python dependencies
- `.github/workflows/reminder.yml` - GitHub Actions scheduled job
- `reddit_posts.db` - SQLite database (created on first run)
- `debug.log` - Debug logs (created on each run)

## Example Output

See the screenshot above for an example of the email output format.

## License

MIT
