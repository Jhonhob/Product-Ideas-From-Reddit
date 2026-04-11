import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()
# SUBREDDITS = [
#     "ProductHunters",
#     "Entrepreneur",
#     "Startup_Ideas",
#     "SaaS",
#     "microsaas",
#     "problems",
#     "passive_income"
#     ]
SUBREDDITS = [
    "ProductHunters"
    ]

def product_ideas_prompt(subreddit,content):
    PROMPT = f'''You are Given with the content of the {subreddit} subreddit you have to extract out potential product ideas, just give the ideas and no other text and make sure the its short and simple,
the content:
{content}
'''
    return PROMPT


def extract_posts(subreddit):
    url = f"https://api.reddit.com/r/{subreddit}/new"

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; my-bot/1.0)"
    }

    response = requests.get(url, headers=headers)

    print("Status Code:", response.status_code)

    if response.status_code != 200:
        print("Error response:", response.text[:200])
        return ""

    try:
        data = response.json()
    except Exception as e:
        print("JSON failed:", e)
        print("Raw response:", response.text[:200])
        return ""

    posts = []

    for index, post in enumerate(data.get("data", {}).get("children", [])):
        title = post["data"].get("title", "")
        body = post["data"].get("selftext", "").replace("\n", "")
        posts.append(f"Post {index+1}: {title}\nBody {index+1}: {body}\n\n")

    return "".join(posts)


def send_ai_request(prompt):
    API_KEY = os.getenv("GEMINI_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={API_KEY}"
    payload = json.dumps({
    "contents": [
        {
        "parts": [
            {
            "text": f"{prompt}"
            }
        ]
        }
    ]
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    json_response = json.loads(response.text)

    text = json_response["candidates"][0]["content"]["parts"][0]["text"]
    return text


def get_final_ideas(content_list):
    all_ideas = "\n".join(content_list)
    prompt = f'''You are given with multiple product ideas, filter out the top 10 best ideas that could work out and give that to me and don't add any additional text in the response than just the ideas,
the content:
{all_ideas}
'''
    final_ideas = send_ai_request(prompt)
    return final_ideas

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