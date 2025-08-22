import os
import time
import threading
import uuid
import random
import json
from datetime import datetime
from dotenv import load_dotenv
import requests
from flask import Flask, send_file
from PIL import Image

# --- Load environment variables ---
load_dotenv()
LINE_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")

# --- Flask app to serve image ---
app = Flask(__name__)
IMAGE_PATH = "goodmorning.png"  # temp image

@app.route("/goodmorning.png")
def serve_image():
    return send_file(IMAGE_PATH, mimetype="image/png")

# Load quotes
with open("quotes.json", encoding="utf-8") as f:
    quotes_data = json.load(f)

# Map weekday
WEEKDAY_MAP = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}

# Pick a random image
def pick_today_image():
    today = get_today_name()
    base_dir = os.path.dirname(__file__)
    bg_folder = os.path.join(base_dir, "backgrounds", today.lower())
    if os.path.exists(bg_folder):
        images = [os.path.join(bg_folder, f) for f in os.listdir(bg_folder)
                  if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        if images:
            return random.choice(images)
        else:
            print(f"No images found in {bg_folder}")
    else:
        print(f"Folder not found: {bg_folder}")
    return None

# format image to LINE format
def prepare_image_for_line(src_path):
    with Image.open(src_path) as img:
        max_size = (1024, 1024)
        img.thumbnail(max_size, Image.LANCZOS)
        img.save(IMAGE_PATH, optimize=True, quality=90)

# using LINE broadcast
def broadcast_with_quote_and_image(image_url, text_quote):
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}",
    }

    # Send text first
    text_payload = {"messages": [{"type": "text", "text": text_quote}]}
    response = requests.post(url, headers=headers, json=text_payload)
    if response.status_code == 200:
        print("Text broadcast sent successfully!")
    else:
        print(f"Failed to send text. Status: {response.status_code}, Response: {response.text}")

    # Send image second
    image_payload = {
        "messages": [
            {"type": "image", "originalContentUrl": image_url, "previewImageUrl": image_url}
        ]
    }
    response = requests.post(url, headers=headers, json=image_payload)
    if response.status_code == 200:
        print("Image broadcast sent successfully!")
    else:
        print(f"Failed to send image. Status: {response.status_code}, Response: {response.text}")

# get current day
def get_today_name():
    weekday_index = datetime.now().weekday()
    return WEEKDAY_MAP.get(weekday_index, "Monday")

# schedule broadcast at 7 am
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
            else:
                print("No image found for today!")
            time.sleep(60)
        time.sleep(10)

# testing
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
            else:
                print("No image found for today!")

if __name__ == "__main__":
    public_url = "https://aarunsawad.onrender.com"

    # Start scheduler and test threads
    threading.Thread(target=scheduler, args=(public_url,), daemon=True).start()
    threading.Thread(target=test_mode, args=(public_url,), daemon=True).start()

    print("Broadcast bot running. Type 'test' to broadcast immediately.")
    app.run(port=5000)
