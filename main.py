import os
from flask import Flask, request
import requests
import google.generativeai as genai

app = Flask(__name__)

VERIFY_TOKEN = "ha_tranh_verify_2026"

# === Lấy từ biến môi trường — KHÔNG VIẾT TRỰC TIẾP KHÓA VÀO CODE ===
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Kiểm tra xem có được đặt chưa
if not PAGE_ACCESS_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Thiếu biến môi trường PAGE_ACCESS_TOKEN hoặc GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

chat_sessions = {}

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
            print("✅ Xác minh Webhook THÀNH CÔNG")
            return str(challenge), 200
        return "❌ Xác minh thất bại", 403

    data = request.get_json()
    print("📩 Nhận từ FB:", data)

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for evt in entry.get("messaging", []):
                sender_id = evt.get("sender", {}).get("id")
                if evt.get("message") and not evt["message"].get("is_echo"):
                    message_text = evt["message"].get("text", "").strip()
                    if message_text:
                        tra_loi = lay_cau_tra_loi(sender_id, message_text)
                        gui_tin_facebook(sender_id, tra_loi)
                    else:
                        gui_tin_facebook(sender_id, "Xin lỗi, tôi chưa xem được ảnh/file. Bạn vui lòng gõ chữ hỏi nhé 😊")
    return "OK", 200

def lay_cau_tra_loi(nguoi_gui_id, noi_dung):
    system_prompt = (
        "Bạn là chuyên gia tư vấn đầu tư, đấu thầu và pháp lý doanh nghiệp. "
        "Trả lời rõ ràng, chính xác, ngắn gọn, lịch sự, dùng tiếng Việt chuẩn."
    )
    if nguoi_gui_id not in chat_sessions:
        chat_sessions[nguoi_gui_id] = model.start_chat(history=[])
    try:
        phan_hoi = chat_sessions[nguoi_gui_id].send_message(
            f"{system_prompt}\n\nCâu hỏi: {noi_dung}"
        )
        return phan_hoi.text.strip()
    except Exception as e:
        print(f"❌ Lỗi AI: {e}")
        return "Xin lỗi, hệ thống đang bận. Bạn hỏi lại sau nhé 😊"

def gui_tin_facebook(nguoi_nhan_id, noi_dung):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    du_lieu = {"recipient": {"id": nguoi_nhan_id}, "message": {"text": noi_dung}}
    try:
        res = requests.post(url, json=du_lieu, timeout=10)
        print(f"✅ Đã gửi → {nguoi_nhan_id}: {res.status_code}")
    except Exception as e:
        print(f"❌ Lỗi gửi FB: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
