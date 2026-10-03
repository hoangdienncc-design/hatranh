import os
from flask import Flask, request
import requests
import google.generativeai as genai

app = Flask(__name__)

# Cấu hình Token và API Key
VERIFY_TOKEN = "do_chatbot_messenger_2026"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "NHAP_PAGE_ACCESS_TOKEN_CUA_BAN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "NHAP_GEMINI_API_KEY_CUA_BAN")

# Cấu hình Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@app.route("/", methods=["GET"])
def home():
    return "Bot Tư Vấn Đầu Tư & Đấu Thầu đang hoạt động!", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Xác thực webhook với Facebook
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode and token:
            if mode == "subscribe" and token == VERIFY_TOKEN:
                return challenge, 200
            else:
                return "Verification failed", 403
        return "Hello World", 200

    elif request.method == "POST":
        data = request.json
        if data.get("object") == "page":
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event.get("sender", {}).get("id")
                    
                    if messaging_event.get("message") and not messaging_event["message"].get("is_echo"):
                        message_text = messaging_event["message"].get("text")
                        if message_text:
                            handle_message(sender_id, message_text)
                            
        return "EVENT_RECEIVED", 200

def handle_message(recipient_id, message_text):
    system_prompt = (
        "Bạn là một chuyên gia tư vấn đầu tư, đấu thầu và pháp lý doanh nghiệp chuyên nghiệp. "
        "Hãy tư vấn rõ ràng, chính xác, ngắn gọn và lịch sự bằng tiếng Việt."
    )
    try:
        chat = model.start_chat(history=[])
        response = chat.send_message(f"{system_prompt}\n\nKhách hàng hỏi: {message_text}")
        reply_text = response.text
    except Exception as e:
        reply_text = f"Xin lỗi, hệ thống đang bận: {str(e)}"

    # Gửi tin nhắn phản hồi qua Facebook Messenger API
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": reply_text}
    }
    headers = {"Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
