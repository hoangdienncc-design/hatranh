import os
from flask import Flask, request
import requests
import google.generativeai as genai

app = Flask(__name__)

# ==========================================
# CẤU HÌNH
# ==========================================
VERIFY_TOKEN = "ha_tranh_verify_2026"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Kiểm tra biến môi trường
print("=== KIỂM TRA CẤU HÌNH ===")
if not PAGE_ACCESS_TOKEN:
    print("❌ PAGE_ACCESS_TOKEN chưa đặt!")
else:
    print("✅ PAGE_ACCESS_TOKEN: OK")

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY chưa đặt!")
else:
    print("✅ GEMINI_API_KEY: OK")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

chat_sessions = {}

# ==========================================
# CÁC TRANG THÔNG TIN
# ==========================================
@app.route("/", methods=["GET"])
def home():
    return "✅ Bot HaTranh đang hoạt động!", 200

@app.route("/privacy", methods=["GET"])
def privacy():
    return "<h1>Chính sách riêng tư</h1><p>Chỉ thu thập nội dung hội thoại để trả lời.</p>", 200

@app.route("/terms", methods=["GET"])
def terms():
    return "<h1>Điều khoản dịch vụ</h1><p>Thông tin chỉ mang tính tham khảo.</p>", 200

@app.route("/delete-data", methods=["GET"])
def delete_data():
    return "<h1>Yêu cầu xóa dữ liệu</h1><p>Liên hệ: hoangdienncc@gmail.com</p>", 200

# ==========================================
# WEBHOOK — ĐƯỜNG DẪN CHÍNH
# ==========================================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    print(f"=== Yêu cầu đến /webhook | Phương thức: {request.method} ===")

    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        print(f"mode={mode}, token={token}, challenge={challenge}")
        
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Xác minh Webhook THÀNH CÔNG!")
            return str(challenge), 200
        else:
            print("❌ Xác minh THẤT BẠI — Kiểm tra lại VERIFY_TOKEN")
            return "Verification failed", 403

    # === Nhận tin nhắn từ Facebook ===
    data = request.get_json()
    print(f"📩 Dữ liệu nhận được: {data}")

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for evt in entry.get("messaging", []):
                sender_id = evt.get("sender", {}).get("id")
                message = evt.get("message", {})
                
                # Bỏ qua tin nhắn do chính bot gửi
                if message.get("is_echo"):
                    print("ℹ️ Bỏ qua tin nhắn từ chính bot")
                    return "OK", 200
                
                message_text = message.get("text", "").strip()
                print(f"💬 Tin nhắn từ {sender_id}: {message_text}")

                if message_text:
                    # Gọi AI
                    try:
                        if sender_id not in chat_sessions:
                            chat_sessions[sender_id] = model.start_chat(history=[])
                        
                        cau_hoi = (
                            "Bạn là chuyên gia tư vấn đầu tư, đấu thầu và pháp lý doanh nghiệp. "
                            "Trả lời rõ ràng, ngắn gọn, lịch sự bằng tiếng Việt chuẩn.\n\n"
                            f"Khách hỏi: {message_text}"
                        )
                        phan_hoi = chat_sessions[sender_id].send_message(cau_hoi)
                        tra_loi = phan_hoi.text.strip()
                        print(f"🤖 Câu trả lời: {tra_loi}")
                    except Exception as e:
                        tra_loi = f"Xin lỗi, hệ thống đang bận: {str(e)}"
                        print(f"❌ Lỗi gọi AI: {e}")

                    # Gửi trả lời về Facebook
                    gui_ket_qua = gui_tin_facebook(sender_id, tra_loi)
                    print(f"📤 Kết quả gửi FB: {gui_ket_qua}")
                else:
                    gui_tin_facebook(sender_id, "Xin lỗi, tôi chưa xem được ảnh/file. Vui lòng gõ chữ nhé 😊")
    return "EVENT_RECEIVED", 200

# ==========================================
# GỬI TIN NHẮN VỀ FACEBOOK
# ==========================================
def gui_tin_facebook(nguoi_nhan_id, noi_dung):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    du_lieu = {
        "recipient": {"id": nguoi_nhan_id},
        "message": {"text": noi_dung}
    }
    try:
        res = requests.post(url, json=du_lieu, timeout=10)
        return f"Thành công - Mã trạng thái: {res.status_code}"
    except Exception as e:
        return f"Lỗi: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
