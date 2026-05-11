import helper
import send_email
import send_github

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
            
            # Send email notification (only if EMAIL_USER is configured)
            if send_email.is_email_configured():
                send_email.send_email(html)
                print("Email sent successfully!")
            else:
                print("Email notification skipped (EMAIL_USER not configured)")
            
            # Send GitHub Issues notification
            print("\n--- Sending GitHub Issues Notification ---")
            github_result = send_github.send_github_issue(best_ideas)
            if github_result:
                print("✅ GitHub Issues notification completed successfully")
            else:
                print("❌ GitHub Issues notification failed - check error messages above")
        else:
            print("Failed to generate final ideas")
    else:
        print("No new product ideas to process today.")
    
    # Commit database changes to git for incremental updates tracking
    print("\n--- Committing Database Changes ---")
    helper.commit_db_to_git()

if __name__ == "__main__":
    main()