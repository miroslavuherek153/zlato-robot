import json
from datetime import datetime

def save_json(symbol, data):
    try:
        with open("data.json", "r") as f:
            all_data = json.load(f)
    except:
        all_data = {}

    all_data[symbol] = data
    all_data["updated"] = datetime.utcnow().isoformat()

    with open("data.json", "w") as f:
        json.dump(all_data, f, indent=4)
