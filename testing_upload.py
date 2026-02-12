import requests
import base64, os
from dotenv import load_dotenv

load_dotenv()

url=os.getenv("GOOGLE_APPS_SCRIPT_URL", "")

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

data = {
    "name": "Ahtesham",
    "time": 123,
    "user_current_image": encode_image("testing.png"),
    "user_badge_image": encode_image("skelton.jpg")
}

r = requests.post(url, json=data)
print(r.text)
