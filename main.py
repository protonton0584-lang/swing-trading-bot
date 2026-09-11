import os
import requests

def send_line_message(message):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")
    
    if not token or not user_id:
        print("Error: LINE credentials not found.")
        return
        
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"LINE API Response Status: {response.status_code}")
    print(response.text)

if __name__ == "__main__":
    print("Sending test message to LINE...")
    send_line_message("【テスト通知】GitHub Actionsからの接続テスト成功です！")
