import os
from flask import Flask, request
import requests
import google.generativeai as genai

app = Flask(__name__)

VERIFY_TOKEN = "ha_tranh_verify_2026"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# === KIỂM TRA CƠ BẢN ===
if not PAGE_ACCESS_TOKEN:
    print("❌ PAGE_ACCESS_TOKEN trống!")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY trống!")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("✅ Cấu hình thành công")

chat_sessions = {}

# === CÁC TRANG THÔNG TIN ===
@app.route("/")
def home():
    return "✅ Bot HaTranh đang chạy!", 200

@app.route("/privacy")
def privacy():
    return "<h1>Chính sách riêng tư</h1><p>Chỉ thu thập nội dung để trả lời.</p>", 200

@app.route("/terms")
def terms():
    return "<h1>Điều khoản</h1><p>Thông tin tham khảo.</p>", 200

@app.route("/delete-data")
def delete_data():
    return "<h1>Xóa dữ liệu</h1><p>Liên hệ: hoangdienncc@gmail.com</p>", 200

# === WEBHOOK CHÍNH ===
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Xác minh Webhook OK")
            return str(challenge), 200
        return "❌ Sai mã xác minh", 403

    # === NHẬN TIN NHẮN ===
    data = request.get_json()
    print("📩 Nhận dữ liệu:", data)

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for evt in entry.get("messaging", []):
                sender_id = evt.get("sender", {}).get("id")
                message = evt.get("message", {})
                
                # Bỏ qua tin nhắn do chính bot gửi
                if message.get("is_echo"):
                    print("ℹ️ Bỏ qua tin nhắn phản hồi từ chính bot")
                    return "OK", 200
                
                message_text = message.get("text", "").strip()
                print(f"💬 Từ {sender_id}: {message_text}")

                if message_text:
                    # Gọi AI
                    try:
                        if sender_id not in chat_sessions:
                            chat_sessions[sender_id] = model.start_chat(history=[])
                        
                        cau_hoi = f"Bạn là chuyên gia tư vấn đầu tư, đấu thầu, pháp lý doanh nghiệp. Trả lời ngắn gọn lịch sự bằng tiếng Việt.\n\nKhách hỏi: {message_text}"
                        phan_hoi = chat_sessions[sender_id].send_message(cau_hoi)
                        tra_loi = phan_hoi.text.strip()
                        print(f"🤖 Trả lời: {tra_loi}")
                    except Exception as e:
                        tra_loi = f"Xin lỗi có lỗi: {str(e)}"
                        print(f"❌ Lỗi AI: {e}")

                    # Gửi trả lời
                    gui_ket_qua = gui_tin_facebook(sender_id, tra_loi)
                    print(f"📤 Kết quả gửi: {gui_ket_qua}")
                else:
                    gui_tin_facebook(sender_id, "Tôi chưa xem được ảnh/file, vui lòng gõ chữ nhé 😊")
    return "OK", 200

def gui_tin_facebook(nguoi_nhan_id, noi_dung):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    du_lieu = {
        "recipient": {"id": nguoi_nhan_id},
        "message": {"text": noi_dung}
    }
    try:
        res = requests.post(url, json=du_lieu, timeout=10)
        return f"Thành công - Mã {res.status_code}"
    except Exception as e:
        return f"Lỗi: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
