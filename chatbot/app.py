from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)


ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
TEMPLATE_NAME = os.getenv('WHATSAPP_TEMPLATE_NAME')  # e.g., 'hello_world'
LANGUAGE_CODE = os.getenv('WHATSAPP_TEMPLATE_LANG', 'en_US')

@app.route("/", methods=["GET"])
def home():
    return "SasaBot Webhook is live!"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        
        VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")  
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403

    if request.method == "POST":
        data = request.json
        try:
            message = data["entry"][0]["changes"][0]["value"]["messages"][0]
            phone_number_id = data["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
            sender_phone = message["from"]
            msg_text = message["text"]["body"].lower()

            if msg_text == "hello":
                url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
                headers = {
                    "Authorization": f"Bearer {ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "to": sender_phone,
                    "type": "template",
                    "template": {
                        "name": TEMPLATE_NAME,
                        "language": { "code": LANGUAGE_CODE }
                    }
                }
                res = requests.post(url, json=payload, headers=headers)
                print("Template sent:", res.status_code, res.text)

        except Exception as e:
            print("Error:", e)

        return jsonify(status="received"), 200

if __name__ == "__main__":
    app.run(debug=True)
