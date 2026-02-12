import requests
import base64

url = "https://script.google.com/macros/s/AKfycbzlsGmuTD6rmSCctztx1nd8Ti1kYYV-7x7cr0j-TjxGEZhSfqk1k8N1D3KsjKIbruyCXw/exec"

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

data = {
    "name": "Ahtesham",
    "time": 123,
    "user_current_image": encode_image("testing.png"),
    "user_badge_image": encode_image("testing.png")
}

r = requests.post(url, json=data)
print(r.text)
