import os
import time
import threading
import uuid
import random
import json
from datetime import datetime
from dotenv import load_dotenv
import requests
from flask import Flask, send_file, request
from PIL import Image

load_dotenv()
LINE_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")

app = Flask(__name__)
IMAGE_PATH = "goodmorning.png"  # temp image

@app.route("/goodmorning.png")
def serve_image():
    return send_file(IMAGE_PATH, mimetype="image/png")

with open("quotes.json", encoding="utf-8") as f:
    quotes_data = json.load(f)

WEEKDAY_MAP = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}

def get_today_name():
    return WEEKDAY_MAP.get(datetime.now().weekday(), "Monday")

def pick_today_image():
    today = get_today_name()
    base_dir = os.path.dirname(__file__)
    bg_folder = os.path.join(base_dir, "backgrounds", today.lower())
    if os.path.exists(bg_folder):
        images = [os.path.join(bg_folder, f) for f in os.listdir(bg_folder)
                  if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        if images:
            return random.choice(images)
    return None

def prepare_image_for_line(src_path):
    with Image.open(src_path) as img:
        max_size = (1024, 1024)
        img.thumbnail(max_size, Image.LANCZOS)
        img.save(IMAGE_PATH, optimize=True, quality=90)

def broadcast_with_quote_and_image(image_url, text_quote):
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}",
    }
    # Send text first
    requests.post(url, headers=headers, json={"messages": [{"type": "text", "text": text_quote}]})
    # Send image second
    requests.post(url, headers=headers, json={
        "messages": [{"type": "image", "originalContentUrl": image_url, "previewImageUrl": image_url}]
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json()
    print("Webhook received:", body)
    return "Webhook received", 200

def scheduler(public_url):
    while True:
        now = datetime.now()
        if now.hour == 7 and now.minute == 0:
            image_path = pick_today_image()
            if image_path:
                prepare_image_for_line(image_path)
                today = get_today_name()
                quote_list = quotes_data.get(today, ["Good Morning! ☀️"])
                quote = random.choice(quote_list)
                broadcast_with_quote_and_image(f"{public_url}/goodmorning.png", quote)
            time.sleep(60)
        time.sleep(10)

def test_mode(public_url):
    while True:
        cmd = input("Type 'test' to broadcast today's image and quote now: ")
        if cmd.lower() == "test":
            image_path = pick_today_image()
            if image_path:
                prepare_image_for_line(image_path)
                today = get_today_name()
                quote_list = quotes_data.get(today, ["Good Morning! ☀️"])
                quote = random.choice(quote_list)
                broadcast_with_quote_and_image(f"{public_url}/goodmorning.png", quote)

if __name__ == "__main__":
    public_url = "https://aarunsawad.onrender.com"  # Replace with your Render public URL
    threading.Thread(target=scheduler, args=(public_url,), daemon=True).start()
    threading.Thread(target=test_mode, args=(public_url,), daemon=True).start()
    print("Bot running. Listening for LINE events + 7AM broadcast.")
    app.run(port=5000)