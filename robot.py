import json
from src.robot import analyzuj_xauusd

def main():
    print("--- 🔍 ZLATO ANALÝZA START ---")
    try:
        data = analyzuj_xauusd()
        
        # Uložíme výsledek pro dashboard
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Aktuální cena: {data['cena']} USD")
        print(f"Signál: {data['akce']}")
        if data['akce'] != "ČEKAT":
            print(f"🎯 SL: {data['sl']} | TP: {data['tp']}")
            
    except Exception as e:
        print(f"❌ Chyba: {e}")

if __name__ == "__main__":
    main()
