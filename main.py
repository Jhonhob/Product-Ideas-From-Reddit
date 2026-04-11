import helper
import send_email

ideas = []
for subreddit in helper.SUBREDDITS:
    extracted_posts = helper.extract_posts(subreddit)
    content = helper.product_ideas_prompt(subreddit,extracted_posts)
    text = helper.send_ai_request(content)
    ideas.append(text)

best_ideas = helper.get_final_ideas(ideas)
html = helper.get_email_html(best_ideas)
send_email.send_email(html)