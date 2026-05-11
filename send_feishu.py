import os
import json
import lark_oapi as lark
from lark_oapi.api.im.v1 import *
from dotenv import load_dotenv

load_dotenv()

# Cache for tenant_access_token
_token_cache = {
    'token': None,
    'expire_time': 0
}

def get_tenant_access_token():
    """
    Get tenant access token using AppID and AppSecret.
    Uses caching to avoid unnecessary API calls.
    """
    import time
    
    # Check cache first
    current_time = time.time()
    if _token_cache['token'] and current_time < _token_cache['expire_time']:
        return _token_cache['token']
    
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    
    if not app_id or not app_secret:
        print("Error: FEISHU_APP_ID or FEISHU_APP_SECRET not found in environment variables")
        return None
    
    # Create client
    client = lark.ws.Client.default(app_id=app_id, app_secret=app_secret)
    
    # Build request
    request = TenantAccessTokenRequest.builder() \
        .request(TenantAccessTokenRequestBody.builder()
            .app_id(app_id)
            .app_secret(app_secret)
            .build()) \
        .build()
    
    # Send request
    response = client.im.v1.tenant_access_token.create(request)
    
    if not response.success():
        print(f"Failed to get tenant access token: {response.code} - {response.msg}")
        return None
    
    # Cache the token (expires in 2 hours, we'll refresh at 90 minutes)
    expires_in = response.data.expires_in
    _token_cache['token'] = response.data.tenant_access_token
    _token_cache['expire_time'] = current_time + expires_in - 300  # Refresh 5 minutes early
    
    print("Successfully obtained tenant access token")
    return _token_cache['token']


def send_feishu(content):
    """
    Send product ideas to Feishu (Lark) using official SDK.
    
    Environment variables required:
    - FEISHU_APP_ID: Feishu app ID
    - FEISHU_APP_SECRET: Feishu app secret
    - FEISHU_CHAT_ID: Target chat ID (group chat ID or open_id)
    
    Args:
        content: String containing the product ideas to send
    """
    # Check all required environment variables first
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    chat_id = os.getenv("FEISHU_CHAT_ID")
    
    print("\n--- Feishu Configuration Check ---")
    print(f"FEISHU_APP_ID: {'✅ SET' if app_id else '❌ NOT SET'}")
    print(f"FEISHU_APP_SECRET: {'✅ SET' if app_secret else '❌ NOT SET'}")
    print(f"FEISHU_CHAT_ID: {'✅ SET' if chat_id else '❌ NOT SET'}")
    
    if not chat_id:
        print("❌ Error: FEISHU_CHAT_ID is required but not set")
        return False
    
    if not app_id or not app_secret:
        print("❌ Error: FEISHU_APP_ID and FEISHU_APP_SECRET are required but not set")
        return False
    
    print(f"✅ All Feishu credentials configured")
    print(f"   Chat ID: {chat_id}")
    
    token = get_tenant_access_token()
    if not token:
        print("❌ Failed to get tenant access token")
        return False
    
    # Create client with token
    client = lark.ws.Client.default(
        app_id=os.getenv("FEISHU_APP_ID"),
        app_secret=os.getenv("FEISHU_APP_SECRET")
    )
    
    # Format content for Feishu message
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    # Create text content with proper formatting
    text_content = "🚀 **Reddit Product Ideas**\n\n"
    for i, line in enumerate(lines[:15], 1):  # Limit to 15 items for readability
        clean_line = line.replace('- ', '').replace('* ', '').replace('• ', '')
        if clean_line.startswith(f"{i}.") or clean_line.startswith(f"{i}、"):
            text_content += f"{clean_line}\n"
        else:
            text_content += f"{i}. {clean_line}\n"
    
    if len(lines) > 15:
        text_content += f"\n... and {len(lines) - 15} more ideas"
    
    # Build request
    request = CreateMessageRequest.builder() \
        .request(CreateMessageRequestBody.builder()
            .receive_id(chat_id)
            .msg_type("text")
            .content(json.dumps({"text": text_content}))
            .build()) \
        .query_params(CreateMessageQueryParams.builder()
            .receive_id_type("chat_id")
            .build()) \
        .build()
    
    # Send request
    print(f"\n📤 Sending message to Feishu chat: {chat_id}")
    response = client.im.v1.message.create(request)
    
    if not response.success():
        print(f"❌ Failed to send Feishu message: {response.code} - {response.msg}")
        print(f"   Error details: {response}")
        # Check for common error codes
        if response.code == 99991663:
            print("   💡 Hint: chat_id may be incorrect or the bot may not be added to the group")
        elif response.code == 99991661:
            print("   💡 Hint: Invalid tenant_access_token, check FEISHU_APP_ID and FEISHU_APP_SECRET")
        elif response.code == 99991664:
            print("   💡 Hint: Bot doesn't have permission to send messages to this chat")
        return False
    
    print("✅ Feishu notification sent successfully!")
    print(f"   Message ID: {response.data.message_id if hasattr(response.data, 'message_id') else 'N/A'}")
    return True


def send_feishu_card(content):
    """
    Send product ideas to Feishu as an interactive card using official SDK.
    
    Args:
        content: String containing the product ideas to send
    """
    chat_id = os.getenv("FEISHU_CHAT_ID")
    
    if not chat_id:
        print("Error: FEISHU_CHAT_ID not found in environment variables")
        return False
    
    token = get_tenant_access_token()
    if not token:
        return False
    
    # Create client with token
    client = lark.ws.Client.default(
        app_id=os.getenv("FEISHU_APP_ID"),
        app_secret=os.getenv("FEISHU_APP_SECRET")
    )
    
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
                "content": "Generated by Reddit Product Scanner"
            }
        ]
    })
    
    # Build card content
    card_content = {
        "config": {
            "wide_screen_mode": True
        },
        "elements": elements
    }
    
    # Build request
    request = CreateMessageRequest.builder() \
        .request(CreateMessageRequestBody.builder()
            .receive_id(chat_id)
            .msg_type("interactive")
            .content(json.dumps(card_content))
            .build()) \
        .query_params(CreateMessageQueryParams.builder()
            .receive_id_type("chat_id")
            .build()) \
        .build()
    
    # Send request
    response = client.im.v1.message.create(request)
    
    if not response.success():
        print(f"Failed to send Feishu card message: {response.code} - {response.msg}")
        return False
    
    print("Feishu card notification sent successfully!")
    return True
