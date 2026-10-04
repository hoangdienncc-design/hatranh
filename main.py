import os
from flask import Flask, request
import requests
import google.genai as genai

app = Flask(__name__)

# ==========================================
# CẤU HÌNH
# ==========================================
VERIFY_TOKEN = "ha_tranh_verify_2026"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

print("=== KIỂM TRA CẤU HÌNH ===")
if not PAGE_ACCESS_TOKEN:
    print("❌ PAGE_ACCESS_TOKEN chưa đặt!")
else:
    print("✅ PAGE_ACCESS_TOKEN: OK")

client = None
MODEL_NAME = "gemini-2.0-flash"

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY chưa đặt!")
else:
    print(f"✅ GEMINI_API_KEY: OK | Model: {MODEL_NAME}")
    # === Cách dùng ĐÚNG của thư viện mới ===
    client = genai.Client(api_key=GEMINI_API_KEY)

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
# WEBHOOK
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
        return "Verification failed", 403

    # === NHẬN TIN NHẮN ===
    data = request.get_json()
    print(f"📩 Dữ liệu đầy đủ: {data}")

    if not data or data.get("object") != "page":
        return "Không phải sự kiện Trang", 200

    for entry in data.get("entry", []):
        messaging_list = entry.get("messaging", [])
        for evt in messaging_list:
            sender_id = evt.get("sender", {}).get("id")
            message = evt.get("message", {})

            if message.get("is_echo", False):
                print("ℹ️ Bỏ qua tin nhắn từ chính bot")
                continue

            message_text = message.get("text") or ""
            print(f"💬 Nội dung nhận được: [{message_text}]")

            if message_text.strip():
                noi_dung = message_text.strip()
                print(f"✅ Xử lý câu hỏi: {noi_dung}")

                if not client:
                    tra_loi = "Xin lỗi, hệ thống AI chưa cấu hình xong khóa Gemini."
                else:
                    try:
                        cau_hoi = (
                            "Bạn là chuyên gia tư vấn đầu tư, đấu thầu và pháp lý doanh nghiệp. "
                            "Trả lời ngắn gọn, rõ ràng, lịch sự bằng tiếng Việt chuẩn.\n\n"
                            f"Khách hỏi: {noi_dung}"
                        )
                        
                        # === Gọi AI theo CÁCH MỚI ===
                        response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=cau_hoi
                        )
                        tra_loi = response.text.strip()
                        print(f"🤖 Trả lời AI: {tra_loi}")

                    except Exception as e:
                        tra_loi = f"Xin lỗi, có lỗi xử lý: {str(e)}"
                        print(f"❌ Lỗi AI: {e}")

                gui_ket_qua = gui_tin_facebook(sender_id, tra_loi)
                print(f"📤 Kết quả gửi: {gui_ket_qua}")

            else:
                gui_tin_facebook(sender_id, "Tôi chỉ hiểu nội dung chữ thôi. Bạn vui lòng gõ câu hỏi nhé 😊")

    return "EVENT_RECEIVED", 200

# ==========================================
# GỬI TIN NHẮN VỀ FACEBOOK
# ==========================================
def gui_tin_facebook(nguoi_nhan_id, noi_dung):
    if not PAGE_ACCESS_TOKEN:
        return "❌ PAGE_ACCESS_TOKEN chưa cấu hình"

    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    du_lieu = {
        "recipient": {"id": nguoi_nhan_id},
        "message": {"text": noi_dung}
    }

    try:
        res = requests.post(url, json=du_lieu, timeout=10)
        print(f"📡 Phản hồi Facebook: Mã {res.status_code}")
        return f"Thành công - Mã: {res.status_code}"
    except Exception as e:
        return f"Lỗi gửi: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
