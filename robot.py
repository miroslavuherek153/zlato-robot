import json
from src.robot import analyzuj_zlato

def main():
    try:
        print("Spouštím technickou analýzu XAUUSD...")
        vysledek = analyzuj_zlato()
        
        # Uložení pro tvůj dashboard.html
        with open("data.json", "w") as f:
            json.dump(vysledek, f, indent=4)
            
        print(f"Hotovo! Trend: {vysledek['trend']}, Akce: {vysledek['akce']}")
        if vysledek['akce'] != "ČEKAT":
            print(f"VSTUP: {vysledek['cena']} | SL: {vysledek['sl']} | TP: {vysledek['tp']}")

    except Exception as e:
        print(f"Chyba: {e}")

if __name__ == "__main__":
    main()
