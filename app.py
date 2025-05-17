import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ตั้งค่า Flask และ LINE Bot
app = Flask(__name__)
line_bot_api = LineBotApi('NZHEhwr0u8rMyNFB11oR5vW91zs0Nmmnn6ogjsgJXMjiIqgrUyJ3N+wyYn7BaDxo4Sg2N5YV+HicFLABN1lFBSwnLjRqNk4UfuPnLNCa3CH0aNYXXi8TWzxhBZQDWl7YAO582bUH3pKppAl0r0+gvAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('bfaf94cda0fc4fa34441d55bb78488ed')

# เชื่อมต่อ Google Sheet
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name("Pole.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Pole_data").sheet1
    print("✅ เชื่อมต่อ Google Sheet สำเร็จ")
except Exception as e:
    print(f"❌ ไม่สามารถเชื่อมต่อ Google Sheet: {e}")
    sheet = None

# รับ webhook จาก LINE
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print("📩 ได้รับข้อความจาก LINE:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ ลายเซ็นไม่ถูกต้อง (ตรวจสอบ Channel Secret)")
        abort(400)
    return 'OK'

# ตอบกลับเมื่อมีข้อความเข้ามา
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    print(f"💬 ข้อความที่รับมา: {text}")

    # ✅ เพิ่มเงื่อนไข: ตอบเฉพาะเมื่อพิมพ์ขึ้นต้นด้วย !
    if not text.startswith("!"):
        return

    if sheet is None:
        reply = "ไม่สามารถเชื่อมต่อ Google Sheet ได้ค่ะ"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    records = sheet.get_all_records()
    phone = text.replace("!", "").strip()
    matches = []

    for row in records:
        bot_a = str(row.get("Bot_a_number", "")).replace("!", "").strip()
        bot_b = str(row.get("Bot_b_number", "")).replace("!", "").strip()
        a_number = row.get("a_number", "-")
        b_number = row.get("b_number", "-")
        pole = row.get("Pole", "-")
        scene = row.get("Name of the scene", "-")
        start_time = row.get("start time", "-")
        duration = row.get("duration", "-")

        if phone == bot_a:
            msg = f"!{phone} เป็น a_number ของเสา {pole} ตำแหน่ง {scene} " \
                  f"คู่สายคือ {b_number} ในช่วงเวลา {start_time} ใช้เวลา {duration} วินาที"
            matches.append(msg)

        elif phone == bot_b:
            msg = f"!{phone} เป็น b_number ของเสา {pole} ตำแหน่ง {scene} " \
                  f"คู่สายคือ {a_number} ในช่วงเวลา {start_time} ใช้เวลา {duration} วินาที"
            matches.append(msg)

    if matches:
        reply = "\n\n".join(matches)
    else:
        reply = "ไม่พบข้อมูลค่ะ"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

# เริ่มรัน Flask app
if __name__ == "__main__":
    print("🚀 Flask server กำลังทำงานที่ http://127.0.0.1:5000")
    app.run(debug=True)
