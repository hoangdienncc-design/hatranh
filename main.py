import os
from flask import Flask, request
import requests
import google.generativeai as genai

app = Flask(__name__)

# ==========================================
# CẤU HÌNH — KHÔNG ĐỔI DÒNG NÀY
# ==========================================
VERIFY_TOKEN = "ha_tranh_verify_2026"

# Lấy từ biến môi trường trên Render
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Kiểm tra cấu hình
if not PAGE_ACCESS_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ Thiếu biến môi trường PAGE_ACCESS_TOKEN hoặc GEMINI_API_KEY — kiểm tra lại trên Render!")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Lưu lịch sử hội thoại theo người dùng
chat_sessions = {}

# ==========================================
# TRANG THÔNG TIN — ĐỂ ĐIỀN VÀO META
# ==========================================

@app.route("/", methods=["GET"])
def home():
    return """
    <html>
        <body style="font-family:Arial; max-width:800px; margin:50px auto; padding:0 20px; text-align:center;">
            <h1 style="color:#2c3e50;">✅ Bot HaTranh — Đang hoạt động</h1>
            <p>Trang chủ dịch vụ chatbot tư vấn đầu tư & đấu thầu.</p>
            <nav style="margin-top:30px;">
                <a href="/privacy" style="margin:0 10px;">Chính sách riêng tư</a> |
                <a href="/terms" style="margin:0 10px;">Điều khoản dịch vụ</a> |
                <a href="/delete-data" style="margin:0 10px;">Xóa dữ liệu</a>
            </nav>
        </body>
    </html>
    """, 200

@app.route("/privacy", methods=["GET"])
def privacy():
    return """
    <html>
        <body style="font-family:Arial; max-width:800px; margin:30px auto; padding:20px; line-height:1.7;">
            <h1 style="color:#2c3e50;">Chính sách riêng tư</h1>
            <p><strong>Cập nhật:</strong> 03/10/2026</p>
            
            <h3>1. Thông tin thu thập</h3>
            <p>Chúng tôi chỉ nhận nội dung tin nhắn bạn gửi qua Trang Facebook HaTranh để trả lời câu hỏi. Không thu thập thông tin cá nhân khác trừ khi bạn tự cung cấp trong nội dung hội thoại.</p>
            
            <h3>2. Mục đích sử dụng</h3>
            <p>Nội dung tin nhắn chỉ dùng để:</p>
            <ul>
                <li>Trả lời câu hỏi tư vấn đầu tư, đấu thầu, pháp lý doanh nghiệp</li>
                <li>Ghi nhớ ngữ cảnh hội thoại trong phiên làm việc</li>
            </ul>
            <p>Không bán, chia sẻ hoặc cung cấp dữ liệu cho bên thứ ba.</p>
            
            <h3>3. Bảo mật</h3>
            <p>Dữ liệu truyền qua kết nối mã hóa. Khóa API và Token được lưu an toàn trên biến môi trường, không hiển thị công khai.</p>
            
            <h3>4. Quyền của bạn</h3>
            <p>Bạn có thể yêu cầu xóa toàn bộ dữ liệu liên quan đến hội thoại bất kỳ lúc nào.</p>
            
            <h3>5. Liên hệ</h3>
            <p>Email: hoangdienncc@gmail.com</p>
        </body>
    </html>
    """, 200

@app.route("/terms", methods=["GET"])
def terms():
    return """
    <html>
        <body style="font-family:Arial; max-width:800px; margin:30px auto; padding:20px; line-height:1.7;">
            <h1 style="color:#2c3e50;">Điều khoản dịch vụ</h1>
            <p><strong>Cập nhật:</strong> 03/10/2026</p>
            
            <h3>1. Phạm vi dịch vụ</h3>
            <p>Bot HaTranh cung cấp thông tin và tư vấn tham khảo về lĩnh vực đầu tư, đấu thầu, pháp lý doanh nghiệp trên nền tảng Facebook Messenger.</p>
            
            <h3>2. Tính tham khảo</h3>
            <p>Nội dung trả lời chỉ mang tính tham khảo, không thay thế ý kiến chuyên gia hoặc văn bản pháp quy chính thức. Bạn nên xác minh lại từ nguồn tin cậy.</p>
            
            <h3>3. Trách nhiệm sử dụng</h3>
            <p>Chúng tôi không chịu trách nhiệm về quyết định đưa ra dựa trên thông tin bot cung cấp.</p>
            
            <h3>4. Liên hệ</h3>
            <p>Email: hoangdienncc@gmail.com</p>
        </body>
    </html>
    """, 200

@app.route("/delete-data", methods=["GET"])
def delete_data():
    return """
    <html>
        <body style="font-family:Arial; max-width:800px; margin:30px auto; padding:20px; line-height:1.7;">
            <h1 style="color:#2c3e50;">Yêu cầu xóa dữ liệu</h1>
            <p>Nếu bạn muốn xóa toàn bộ dữ liệu liên quan đến hội thoại của mình, vui lòng gửi yêu cầu qua:</p>
            <ul>
                <li><strong>Email:</strong> hoangdienncc@gmail.com</li>
                <li><strong>Tiêu đề:</strong> Yêu cầu xóa dữ liệu — [Tên/Tên tài khoản Facebook]</li>
            </ul>
            <p>Chúng tôi sẽ xử lý trong vòng 7 ngày làm việc.</p>
        </body>
    </html>
    """, 200

# ==========================================
# WEBHOOK — NHẬN & TRẢ LỜI TIN NHẮN
# ==========================================

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Xác minh với Meta
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Xác minh Webhook THÀNH CÔNG")
            return str(challenge), 200
        return "❌ Xác minh thất bại", 403

    # Nhận tin nhắn từ Facebook
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

# ==========================================
# XỬ LÝ TRẢ LỜI BẰNG GEMINI AI
# ==========================================

def lay_cau_tra_loi(nguoi_gui_id, noi_dung):
    system_prompt = (
        "Bạn là chuyên gia tư vấn đầu tư, đấu thầu và pháp lý doanh nghiệp. "
        "Trả lời rõ ràng, chính xác, ngắn gọn, lịch sự, dùng tiếng Việt chuẩn."
    )
    
    # Giữ hội thoại theo từng người dùng
    if nguoi_gui_id not in chat_sessions:
        chat_sessions[nguoi_gui_id] = model.start_chat(history=[])
    
    try:
        phan_hoi = chat_sessions[nguoi_gui_id].send_message(
            f"{system_prompt}\n\nCâu hỏi: {noi_dung}"
        )
        return phan_hoi.text.strip()
    except Exception as e:
        print(f"❌ Lỗi gọi AI: {e}")
        return "Xin lỗi, hệ thống đang bận. Bạn hỏi lại sau nhé 😊"

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
        print(f"✅ Đã gửi → {nguoi_nhan_id} | Trạng thái: {res.status_code}")
    except Exception as e:
        print(f"❌ Lỗi gửi FB: {e}")

# ==========================================
# CHẠY ỨNG DỤNG
# ==========================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
