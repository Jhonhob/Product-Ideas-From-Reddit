import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def send_feishu(content):
    """
    Send product ideas to Feishu (Lark) via webhook.
    
    Environment variables required:
    - FEISHU_WEBHOOK_URL: Feishu bot webhook URL
    
    Args:
        content: String containing the product ideas to send
    """
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    
    if not webhook_url:
        print("Error: FEISHU_WEBHOOK_URL not found in environment variables")
        return False
    
    # Format content for Feishu message
    # Split content into lines and format as interactive message
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    # Create text content with proper formatting
    text_content = "🚀 **Reddit Product Ideas**\n\n"
    for i, line in enumerate(lines[:15], 1):  # Limit to 15 items for readability
        # Remove markdown bullets and add emoji
        clean_line = line.replace('- ', '').replace('* ', '').replace('• ', '')
        if clean_line.startswith(f"{i}.") or clean_line.startswith(f"{i}、"):
            text_content += f"{clean_line}\n"
        else:
            text_content += f"{i}. {clean_line}\n"
    
    if len(lines) > 15:
        text_content += f"\n... and {len(lines) - 15} more ideas"
    
    # Feishu message payload (text type)
    payload = {
        "msg_type": "text",
        "content": {
            "text": text_content
        }
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(webhook_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Check Feishu response
        if result.get('StatusCode') == 0 or result.get('code') == 0 or 'ok' in str(result).lower():
            print("Feishu notification sent successfully!")
            return True
        else:
            print(f"Feishu API returned error: {result}")
            return False
            
    except requests.exceptions.Timeout:
        print("Error: Feishu request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error: Feishu request failed - {e}")
        return False
    except Exception as e:
        print(f"Error: Failed to send Feishu notification - {e}")
        return False


def send_feishu_card(content):
    """
    Send product ideas to Feishu as an interactive card (richer format).
    
    Args:
        content: String containing the product ideas to send
    """
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    
    if not webhook_url:
        print("Error: FEISHU_WEBHOOK_URL not found in environment variables")
        return False
    
    # Split content into lines
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    # Build elements array for the card
    elements = []
    
    # Add header
    elements.append({
        "tag": "header",
        "template": "blue",
        "title": {
            "content": "🚀 Reddit Product Ideas",
            "tag": "plain_text"
        }
    })
    
    # Add idea list (limit to 10 for card format)
    for i, line in enumerate(lines[:10], 1):
        clean_line = line.replace('- ', '').replace('* ', '').replace('• ', '')
        elements.append({
            "tag": "div",
            "text": {
                "content": f"**{i}.** {clean_line}",
                "tag": "lark_md"
            }
        })
    
    if len(lines) > 10:
        elements.append({
            "tag": "div",
            "text": {
                "content": f"\n... and {len(lines) - 10} more ideas",
                "tag": "lark_md"
            }
        })
    
    # Add footer note
    elements.append({
        "tag": "hr"
    })
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": f"Generated at {os.popen('date').read().strip()}"
            }
        ]
    })
    
    # Feishu card message payload
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "elements": elements
        }
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(webhook_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('StatusCode') == 0 or result.get('code') == 0 or 'ok' in str(result).lower():
            print("Feishu card notification sent successfully!")
            return True
        else:
            print(f"Feishu API returned error: {result}")
            return False
            
    except Exception as e:
        print(f"Error: Failed to send Feishu card notification - {e}")
        return False
