import os
from flask import Flask, request
import requests
import google.genai as genai

app = Flask(__name__)

VERIFY_TOKEN = "ha_tranh_verify_2026"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

print("=== KIỂM TRA CẤU HÌNH ===")
if not PAGE_ACCESS_TOKEN:
    print("❌ PAGE_ACCESS_TOKEN chưa đặt!")
else:
    print("✅ PAGE_ACCESS_TOKEN: OK")

client = None
# === SỬA: Dùng tên mô hình đúng theo thông báo ===
MODEL_NAME = "gemini-3.8-flash"

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY chưa đặt!")
else:
    print(f"✅ GEMINI_API_KEY: OK | Model: {MODEL_NAME}")
    client = genai.Client(api_key=GEMINI_API_KEY)

@app.route("/", methods=["GET"])
def home():
    return "✅ Bot HaTranh đang hoạt động!", 200

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
        return "Không phải sự kiện Trang", 200

    for entry in data.get("entry", []):
        for evt in entry.get("messaging", []):
            sender_id = evt.get("sender", {}).get("id")
            message = evt.get("message", {})

            if message.get("is_echo", False):
                continue

            message_text = message.get("text") or ""
            print(f"💬 Tin nhắn: [{message_text}]")

            if message_text.strip():
                if not client:
                    tra_loi = "Xin lỗi, hệ thống AI chưa cấu hình xong."
                else:
                    try:
                        cau_hoi = (
                            "Bạn là chuyên gia tư vấn đầu tư, đấu thầu và pháp lý doanh nghiệp. "
                            "Trả lời ngắn gọn, rõ ràng, lịch sự bằng tiếng Việt chuẩn.\n\n"
                            f"Khách hỏi: {message_text.strip()}"
                        )
                        
                        response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=cau_hoi
                        )
                        tra_loi = response.text.strip()
                        print(f"🤖 Trả lời AI: {tra_loi}")

                    except Exception as e:
                        tra_loi = f"Xin lỗi, có lỗi: {str(e)[:100]}"
                        print(f"❌ Lỗi: {e}")

                gui_tin_facebook(sender_id, tra_loi)
            else:
                gui_tin_facebook(sender_id, "Tôi chỉ hiểu nội dung chữ thôi. Bạn vui lòng gõ câu hỏi nhé 😊")

    return "OK", 200

def gui_tin_facebook(nguoi_nhan_id, noi_dung):
    if not PAGE_ACCESS_TOKEN:
        return
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    try:
        requests.post(url, json={
            "recipient": {"id": nguoi_nhan_id},
            "message": {"text": noi_dung[:2000]}
        }, timeout=10)
    except Exception as e:
        print(f"❌ Lỗi gửi tin: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
