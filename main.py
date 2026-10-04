import os
from flask import Flask, request
import requests
from openai import OpenAI

app = Flask(__name__)

VERIFY_TOKEN = "ha_tranh_verify_2026"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")

MODEL_NAME = "openai/gpt-3.5-turbo"

print("=== KIỂM TRA CẤU HÌNH ===")
if not PAGE_ACCESS_TOKEN:
    print("❌ PAGE_ACCESS_TOKEN chưa đặt!")
else:
    print("✅ PAGE_ACCESS_TOKEN: OK")

client = None
if not OPENROUTER_KEY:
    print("❌ OPENROUTER_KEY chưa có!")
else:
    print(f"✅ OPENROUTER_KEY: OK | Model: {MODEL_NAME}")
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_KEY
    )

@app.route("/", methods=["GET"])
def home():
    return "✅ Bot HaTranh đang hoạt động với OpenRouter!", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Xác minh Webhook THÀNH CÔNG!")
            return str(challenge), 200
        return "Verification failed", 403

    data = request.get_json()
    print(f"📩 Nhận dữ liệu: {data}")
    if not data or data.get("object") != "page":
        return "OK", 200

    for entry in data.get("entry", []):
        for evt in entry.get("messaging", []):
            sender_id = evt.get("sender", {}).get("id")
            message = evt.get("message", {})
            if message.get("is_echo", False):
                continue

            message_text = message.get("text", "").strip()
            print(f"💬 Tin nhắn từ {sender_id}: [{message_text}]")

            if message_text:
                if not client:
                    tra_loi = "Xin lỗi, hệ thống AI chưa cấu hình khóa đúng."
                else:
                    try:
                        response = client.chat.completions.create(
                            model=MODEL_NAME,
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "Bạn là chuyên gia tư vấn đầu tư, đấu thầu và pháp lý doanh nghiệp. "
                                        "Trả lời ngắn gọn, lịch sự, dễ hiểu bằng tiếng Việt."
                                    )
                                },
                                {"role": "user", "content": message_text}
                            ],
                            temperature=0.7,
                            max_tokens=800
                        )
                        tra_loi = response.choices[0].message.content.strip()
                        print(f"🤖 Trả lời AI: {tra_loi}")
                    except Exception as e:
                        tra_loi = f"Xin lỗi, có lỗi: {str(e)[:150]}"
                        print(f"❌ Lỗi AI: {e}")
                gui_tin_facebook(sender_id, tra_loi)
            else:
                gui_tin_facebook(sender_id, "Tôi chỉ hiểu nội dung chữ thôi. Bạn vui lòng gõ câu hỏi nhé 😊")
    return "OK", 200

def gui_tin_facebook(nguoi_nhan_id, noi_dung):
    if not PAGE_ACCESS_TOKEN:
        return "❌ PAGE_ACCESS_TOKEN trống"
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    try:
        res = requests.post(url, json={
            "recipient": {"id": nguoi_nhan_id},
            "message": {"text": noi_dung[:2000]}
        }, timeout=10)
        print(f"📡 Facebook: Mã {res.status_code}")
        return f"Mã {res.status_code}"
    except Exception as e:
        return f"Lỗi: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
