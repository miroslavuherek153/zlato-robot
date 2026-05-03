import requests
from datetime import datetime

def send_discord(webhook_url, payload):
    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception as e:
        print(f"Chyba při odesílání na Discord: {e}")
