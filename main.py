import helper
import send_email
import send_feishu

def main():
    ideas = []
    for subreddit_config in helper.SUBREDDITS:
        subreddit_name = subreddit_config.get('name', 'Unknown')
        extracted_posts = helper.extract_posts(subreddit_config)
        
        # Only process if there are new posts
        if extracted_posts:
            content = helper.product_ideas_prompt(subreddit_name, extracted_posts)
            text = helper.send_ai_request(content)
            if text:  # Only add if AI returned valid response
                ideas.append(text)
            else:
                print(f"AI processing failed for {subreddit_name}")
        else:
            print(f"No new posts from {subreddit_name}")

    if ideas:
        best_ideas = helper.get_final_ideas(ideas)
        if best_ideas:
            html = helper.get_email_html(best_ideas)
            
            # Send email notification
            send_email.send_email(html)
            print("Email sent successfully!")
            
            # Send Feishu notification
            send_feishu.send_feishu(best_ideas)
        else:
            print("Failed to generate final ideas")
    else:
        print("No new product ideas to process today.")

if __name__ == "__main__":
    main()