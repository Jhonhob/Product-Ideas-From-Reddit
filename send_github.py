import os
import requests
from dotenv import load_dotenv

load_dotenv()

def is_github_configured():
    """Check if GitHub token and repository info are available"""
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")  # Format: owner/repo
    
    if not token:
        print("❌ GITHUB_TOKEN not configured")
        return False
    
    if not repo:
        print("❌ GITHUB_REPOSITORY not configured")
        return False
    
    print(f"✅ GitHub configured for repository: {repo}")
    return True

def send_github_issue(content):
    """
    Create a GitHub Issue with product ideas.
    
    Environment variables required:
    - GITHUB_TOKEN: GitHub Personal Access Token or automatic workflow token
    - GITHUB_REPOSITORY: Repository name (automatically set in GitHub Actions)
    
    Args:
        content: String containing the product ideas
        
    Returns:
        bool: True if issue created successfully, False otherwise
    """
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY", "")
    
    print("\n--- GitHub Issues Configuration Check ---")
    print(f"GITHUB_TOKEN: {'✅ SET' if token else '❌ NOT SET'}")
    print(f"GITHUB_REPOSITORY: {'✅ SET' if repo else '❌ NOT SET'}")
    
    if not token:
        print("❌ Error: GITHUB_TOKEN is required but not set")
        return False
    
    if not repo:
        print("❌ Error: GITHUB_REPOSITORY is required but not set")
        return False
    
    # Parse repository into owner and repo name
    try:
        owner, repo_name = repo.split("/")
    except ValueError:
        print(f"❌ Error: Invalid GITHUB_REPOSITORY format: {repo}")
        print("   Expected format: owner/repo (e.g., octocat/Hello-World)")
        return False
    
    # Format content for GitHub Issue
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    # Build issue body with markdown formatting
    issue_body = "## 🚀 Reddit Product Ideas\n\n"
    issue_body += f"*Generated automatically from Reddit posts*\n\n"
    issue_body += "---\n\n"
    
    for i, line in enumerate(lines[:20], 1):  # Limit to 20 items
        clean_line = line.replace('- ', '').replace('* ', '').replace('• ', '')
        if clean_line.startswith(f"{i}.") or clean_line.startswith(f"{i}、"):
            issue_body += f"{clean_line}\n"
        else:
            issue_body += f"{i}. {clean_line}\n"
    
    if len(lines) > 20:
        issue_body += f"\n... and {len(lines) - 20} more ideas (see full list in email/notification)"
    
    issue_body += "\n\n---\n*This issue was created automatically by the Product Ideas From Reddit workflow*"
    
    # Create issue title with date
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    issue_title = f"📋 Product Ideas - {today}"
    
    # GitHub API endpoint
    url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "title": issue_title,
        "body": issue_body,
        "labels": ["product-ideas", "automated"]
    }
    
    print(f"\n📤 Creating GitHub Issue in {owner}/{repo_name}...")
    print(f"   Title: {issue_title}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        issue_data = response.json()
        issue_number = issue_data.get('number', 'N/A')
        issue_url = issue_data.get('html_url', 'N/A')
        
        print("✅ GitHub Issue created successfully!")
        print(f"   Issue #{issue_number}: {issue_url}")
        return True
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ Failed to create GitHub Issue: HTTP {e.response.status_code}")
        if e.response.status_code == 401:
            print("   💡 Hint: GITHUB_TOKEN may be invalid or expired")
        elif e.response.status_code == 403:
            print("   💡 Hint: Token may not have permission to create issues")
        elif e.response.status_code == 404:
            print(f"   💡 Hint: Repository {owner}/{repo_name} not found or token lacks access")
        print(f"   Response: {e.response.text}")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


def close_duplicate_issues():
    """
    Optional: Close previous open issues with similar titles to avoid clutter.
    This keeps only the latest issue open.
    """
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY", "")
    
    if not token or not repo:
        return
    
    try:
        owner, repo_name = repo.split("/")
    except ValueError:
        return
    
    url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get all open issues with "Product Ideas" label
    params = {
        "state": "open",
        "labels": "product-ideas"
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    if response.status_code != 200:
        return
    
    issues = response.json()
    
    # Close all but the most recent one
    if len(issues) > 1:
        # Sort by creation date, keep the newest
        issues_sorted = sorted(issues, key=lambda x: x['created_at'], reverse=True)
        
        for issue in issues_sorted[1:]:  # Skip the first (newest)
            close_url = issue['url']
            close_payload = {"state": "closed"}
            
            try:
                requests.patch(close_url, headers=headers, json=close_payload, timeout=10)
                print(f"   Closed duplicate issue #{issue['number']}")
            except:
                pass
