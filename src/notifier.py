import requests
import json

def send_discord(webhook_url, payload):
    headers = {"Content-Type": "application/json"}
    try:
        requests.post(webhook_url, data=json.dumps(payload), headers=headers, timeout=5)
    except Exception as e:
        print(f"Chyba při odesílání na Discord: {e}")
