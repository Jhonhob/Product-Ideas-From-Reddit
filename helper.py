import json
import os
import requests
import sqlite3
import subprocess
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configurable subreddits with their RSS URLs and optional flair filters
SUBREDDITS = [
    {
        "name": "ProductHunters",
        "rss_url": "https://old.reddit.com/r/ProductHunters/new.rss"
    },
    # Example with flair filter:
    # {
    #     "name": "midsoledeals",
    #     "rss_url": "https://old.reddit.com/r/midsoledeals/search.rss?q=flair%3A%22New%20Balance%22%20OR%20flair%3A%22Adidas%22&restrict_sr=1&sort=new"
    # }
]

DB_NAME = 'reddit_posts.db'

def log_debug(message):
    with open('debug.log', 'a') as f:
        f.write(f"{datetime.now()}: {message}\n")
    print(message)

def get_user_agent():
    try:
        user_agents = requests.get(
            "https://techfanetechnologies.github.io/latest-user-agent/user_agents.json"
        ).json()
        return user_agents[-2]
    except Exception as e:
        log_debug(f"Error fetching user agent: {e}")
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id TEXT PRIMARY KEY,
        title TEXT,
        link TEXT,
        published TEXT,
        author TEXT,
        thumbnail TEXT,
        first_seen TEXT,
        last_seen TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_time TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def fetch_posts_from_rss(rss_url):
    user_agent = get_user_agent()
    headers = {"user-agent": user_agent}
    
    log_debug(f"Fetching RSS feed from {rss_url}")
    response = requests.get(rss_url, headers=headers)
    
    if response.status_code != 200:
        log_debug(f"Error: Received status code {response.status_code}")
        return []
    
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        log_debug(f"XML parsing error: {e}")
        return []
    
    namespaces = {
        'atom': 'http://www.w3.org/2005/Atom',
        'media': 'http://search.yahoo.com/mrss/'
    }
    
    posts = []
    for entry in root.findall('atom:entry', namespaces):
        post = {
            'id': entry.find('atom:id', namespaces).text if entry.find('atom:id', namespaces) is not None else '',
            'title': entry.find('atom:title', namespaces).text if entry.find('atom:title', namespaces) is not None else '',
            'link': entry.find('atom:link', namespaces).attrib.get('href', '') if entry.find('atom:link', namespaces) is not None else '',
            'published': entry.find('atom:published', namespaces).text if entry.find('atom:published', namespaces) is not None else '',
            'author': entry.find('atom:author/atom:name', namespaces).text if entry.find('atom:author/atom:name', namespaces) is not None else '',
            'thumbnail': entry.find('media:thumbnail', namespaces).attrib.get('url', '') if entry.find('media:thumbnail', namespaces) is not None else ''
        }
        posts.append(post)
    
    return posts

def update_database(posts):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    current_time = datetime.now().isoformat()
    
    new_posts = []
    updated_posts = []
    
    for post in posts:
        cursor.execute('SELECT id, last_seen FROM posts WHERE id = ?', (post['id'],))
        result = cursor.fetchone()
        
        if result is None:
            cursor.execute('''
            INSERT INTO posts (id, title, link, published, author, thumbnail, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (post['id'], post['title'], post['link'], post['published'], post['author'], post['thumbnail'], current_time, current_time))
            new_posts.append(post)
        else:
            cursor.execute('UPDATE posts SET last_seen = ? WHERE id = ?', (current_time, post['id']))
            updated_posts.append(post)
    
    cursor.execute('INSERT INTO runs (run_time) VALUES (?)', (current_time,))
    
    conn.commit()
    conn.close()
    
    return new_posts, updated_posts


def commit_db_to_git():
    """Commit the database to git for incremental updates tracking"""
    try:
        # Check if there are changes to commit
        result = subprocess.run(
            ['git', 'diff', '--quiet', DB_NAME],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:  # There are changes
            subprocess.run(['git', 'add', DB_NAME], capture_output=True)
            subprocess.run(
                ['git', 'commit', '-m', f'Update reddit_posts.db - {datetime.now().isoformat()}'],
                capture_output=True,
                text=True
            )
            log_debug("Database committed to git successfully")
        else:
            log_debug("No database changes to commit")
    except Exception as e:
        log_debug(f"Failed to commit database to git: {e}")

def extract_posts(subreddit_config):
    """Fetch posts from RSS and update database, return new posts content for AI processing"""
    init_db()
    
    rss_url = subreddit_config.get('rss_url', f"https://old.reddit.com/r/{subreddit_config['name']}/new.rss")
    current_posts = fetch_posts_from_rss(rss_url)
    new_posts, updated_posts = update_database(current_posts)
    
    log_debug(f"Found {len(new_posts)} new posts from {subreddit_config['name']}")
    log_debug(f"Updated {len(updated_posts)} existing posts")
    
    # Format new posts for AI processing
    posts_content = []
    for index, post in enumerate(new_posts):
        title = post.get('title', '')
        link = post.get('link', '')
        author = post.get('author', '')
        posts_content.append(f"Post {index+1}: {title}\nLink: {link}\nAuthor: {author}\n\n")
    
    return "".join(posts_content) if posts_content else ""


def product_ideas_prompt(subreddit, content):
    PROMPT = f'''You are Given with the content of the {subreddit} subreddit you have to extract out potential product ideas, just give the ideas description and no other text and make sure the its short and simple,
the content:
{content}
'''
    return PROMPT


def send_ai_request(prompt, retries=3):
    """
    Send AI request using OpenAI-compatible interface with retry logic.
    Supports any provider with OpenAI-compatible API (OpenRouter, OpenAI, local LLMs, etc.)
    
    Environment variables required:
    - AI_API_KEY: API key for the AI provider
    - AI_BASE_URL: Base URL for the API (default: https://api.openai.com/v1)
    - AI_MODEL: Model name to use (default: gpt-3.5-turbo)
    """
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip('/')
    model = os.getenv("AI_MODEL", "gpt-3.5-turbo")
    
    if not api_key:
        log_debug("Error: AI_API_KEY not found in environment variables")
        return ""
    
    url = f"{base_url}/chat/completions"

    payload = json.dumps({
      "model": model,
      "messages": [
        {
          "role": "user",
          "content": prompt
        }
      ]
    })
    headers = {
      'Content-Type': 'application/json',
      'Authorization': f'Bearer {api_key}'
    }

    for attempt in range(retries):
        try:
            log_debug(f"Sending AI request (attempt {attempt + 1}/{retries})...")
            response = requests.request("POST", url, headers=headers, data=payload, timeout=60)
            response.raise_for_status()
            json_response = response.json()
            print("Response Raw", json_response)
            
            if "choices" not in json_response or len(json_response["choices"]) == 0:
                log_debug(f"Error: No choices in response: {json_response}")
                return ""
            
            text = json_response["choices"][0]["message"]["content"]
            print("\n\nResponse Content", text)
            return text
        except requests.exceptions.Timeout:
            log_debug(f"Error: Request timed out (attempt {attempt + 1}/{retries})")
            if attempt == retries - 1:
                return ""
            time.sleep(2 ** attempt)  # Exponential backoff
        except requests.exceptions.RequestException as e:
            log_debug(f"Error: Request failed - {e} (attempt {attempt + 1}/{retries})")
            if attempt == retries - 1:
                return ""
            time.sleep(1)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            log_debug(f"Error: Failed to parse response - {e}")
            return ""
    
    return ""

def get_final_ideas(content_list):
    all_ideas = "\n".join(content_list)
    prompt = f'''You are a data extraction and filtering system. Extract ONLY actual product ideas (products, services, tools, platforms) from the Reddit posts below.

RULES:
1. Exclude generic posts like "share what you're working on", advice requests, feedback requests, or discussion threads
2. Only include posts that describe a specific product/service/tool/platform
3. For each valid product idea, output ONE line with a brief description in this format: "ProductName: short description"
4. Output MAXIMUM 10 ideas (or fewer if less than 10 valid ideas exist)
5. DO NOT include any explanations, reasoning, analysis, introductions, conclusions, or meta-text
6. DO NOT include phrases like "Here are the ideas", "Based on the content", "I found", etc.
7. Output ONLY the list of product ideas, nothing else
8. DO NOT output any thinking process, reasoning steps, or internal monologue

Reddit posts content:
{all_ideas}

Output (only product ideas, one per line, no other text):
'''
    final_ideas = send_ai_request(prompt)
    
    # Post-process to filter out any non-idea lines (thinking process, explanations, etc.)
    filtered_lines = []
    for line in final_ideas.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Skip lines that look like thinking/reasoning/explanation
        skip_patterns = [
            "let me", "i need to", "based on", "here are", "i will", "first,", "second,", 
            "looking at", "analyzing", "considering", "exclude", "include", "rule", 
            "step ", "thought ", "reasoning", "analysis", "conclusion", "summary",
            "the user", "the content", "post update", "task ", "#", "(", ")", 
            "actually", "probably", "maybe", "should", "could", "would",
            "we have", "there are", "out of these", "thus", "therefore",
            "now,", "so,", "but", "however", "moreover", "additionally"
        ]
        line_lower = line.lower()
        if any(pattern in line_lower for pattern in skip_patterns):
            continue
        # Only keep lines that look like product ideas (contain colon or look like a name + description)
        if ":" in line and len(line) > 5:
            filtered_lines.append(line)
        elif len(line) > 10 and not line_lower.startswith(("the", "a", "an", "this", "that")):
            # Fallback: keep substantial lines that don't start with common words
            filtered_lines.append(line)
    
    return "\n".join(filtered_lines)

def get_email_html(content):
    ideas_list = content.split("\n")
    all_ideas_html_list = []
    for idea in ideas_list:
        all_ideas_html_list.append(f'<div style="border-bottom:1px solid #f1f5f9; padding:14px 0; color:#374151;">{idea}</div>')
    all_ideas_html = "\n".join(all_ideas_html_list)
    basehtml = f'''<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Ideas</title>
</head>
<body style="margin:0; padding:0; background:#f9fafb; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
    <tr>
      <td align="center">

    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:14px; overflow:hidden; border:1px solid #e5e7eb;">

      <!-- Header -->
      <tr>
        <td style="padding:28px; text-align:center; background:linear-gradient(135deg,#eef2ff,#f5f3ff);">
          <h1 style="margin:0; color:#111827; font-size:22px;">
            Startup Ideas From Reddit
          </h1>
        </td>
      </tr>

      <!-- List -->
      <tr>
        <td style="padding:24px;">
          {all_ideas_html}

        </td>
      </tr>

    </table>

  </td>
</tr>

  </table>

</body>
</html>
'''
    return basehtml