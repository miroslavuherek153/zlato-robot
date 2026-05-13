import json
import os
from src.robot import analyze_xauusd

def main():
    try:
        data = analyze_xauusd()
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Analýza hotova: {data['akce']} (Cena: {data['cena']})")
    except Exception as e:
        print(f"Chyba: {e}")

if __name__ == "__main__":
    main()
