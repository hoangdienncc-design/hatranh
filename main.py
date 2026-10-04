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

# === Chọn mô hình chắc chắn hoạt động ===
MODEL_NAME = "gemini-1.5-flash-002"  # Nếu vẫn lỗi → đổi thành "gemini-2.5-flash"

print("=== KIỂM TRA CẤU HÌNH ===")
if not PAGE_ACCESS_TOKEN:
    print("❌ PAGE_ACCESS_TOKEN chưa đặt!")
else:
    print("✅ PAGE_ACCESS_TOKEN: OK")

client = None
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY chưa đặt!")
else:
    print(f"✅ GEMINI_API_KEY: OK | Model: {MODEL_NAME}")
    client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# CÁC TRANG
# ==========================================
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
        return "OK", 200

    for entry in data.get("entry", []):
        for evt in entry.get("messaging", []):
            sender_id = evt.get("sender", {}).get("id")
            message = evt.get("message", {})

            if message.get("is_echo", False):
                print("ℹ️ Bỏ qua tin nhắn từ chính bot")
                continue

            message_text = message.get("text") or ""
            print(f"💬 Tin nhắn từ {sender_id}: [{message_text}]")

            if message_text.strip():
                noi_dung = message_text.strip()
                if not client:
                    tra_loi = "Xin lỗi, hệ thống AI chưa sẵn sàng."
                else:
                    try:
                        cau_hoi = (
                            "Bạn là chuyên gia tư vấn đầu tư, đấu thầu và pháp lý doanh nghiệp. "
                            "Trả lời ngắn gọn, rõ ràng, lịch sự bằng tiếng Việt chuẩn.\n\n"
                            f"Khách hỏi: {noi_dung}"
                        )
                        response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=cau_hoi
                        )
                        tra_loi = response.text.strip()
                        print(f"🤖 Trả lời AI: {tra_loi}")
                    except Exception as e:
                        tra_loi = f"Xin lỗi, có lỗi: {str(e)[:150]}"
                        print(f"❌ Lỗi AI: {e}")

                gui_ket_qua = gui_tin_facebook(sender_id, tra_loi)
                print(f"📤 Kết quả gửi: {gui_ket_qua}")
            else:
                gui_tin_facebook(sender_id, "Tôi chỉ hiểu nội dung chữ thôi. Bạn vui lòng gõ câu hỏi nhé 😊")

    return "OK", 200

# ==========================================
# GỬI TIN NHẮN VỀ FACEBOOK
# ==========================================
def gui_tin_facebook(nguoi_nhan_id, noi_dung):
    if not PAGE_ACCESS_TOKEN:
        return "❌ PAGE_ACCESS_TOKEN trống"
    
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    du_lieu = {
        "recipient": {"id": nguoi_nhan_id},
        "message": {"text": noi_dung[:2000]}
    }
    
    try:
        res = requests.post(url, json=du_lieu, timeout=10)
        print(f"📡 Facebook: Mã {res.status_code} | {res.text[:200]}")
        return f"Mã {res.status_code}"
    except Exception as e:
        return f"Lỗi: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
