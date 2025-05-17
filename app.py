import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ตั้งค่า Flask และ LINE Bot
app = Flask(__name__)
line_bot_api = LineBotApi('YOUR_LINE_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_LINE_CHANNEL_SECRET')

# เชื่อมต่อ Google Sheet จาก Environment Variable
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Pole_data").sheet1
    print("✅ เชื่อมต่อ Google Sheet สำเร็จ")
except Exception as e:
    print(f"❌ ไม่สามารถเชื่อมต่อ Google Sheet: {e}")
    sheet = None

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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    print(f"💬 ข้อความที่รับมา: {text}")

    if not text.startswith("!"):
        return

    if sheet is None:
        reply = "ไม่สามารถเชื่อมต่อ Google Sheet ได้ค่ะ"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    phone = text.replace("!", "").strip()
    records = sheet.get_all_records()
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
            matches.append(f"!{phone} เป็น a_number ของเสา {pole} ตำแหน่ง {scene} คู่สายคือ {b_number} ในช่วงเวลา {start_time} ใช้เวลา {duration} วินาที")
        elif phone == bot_b:
            matches.append(f"!{phone} เป็น b_number ของเสา {pole} ตำแหน่ง {scene} คู่สายคือ {a_number} ในช่วงเวลา {start_time} ใช้เวลา {duration} วินาที")

    reply = "\n\n".join(matches) if matches else "ไม่พบข้อมูลค่ะ"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    print("🚀 Flask server กำลังทำงานที่ http://0.0.0.0:5000")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)