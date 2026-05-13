import json
import os
from src.robot import analyzuj_xauusd

def main():
    print("--- ZLATO ROBOT: Startuji analýzu ---")
    
    try:
        # Spuštění analýzy z mozku v src/
        vysledek = analyzuj_xauusd()
        
        # Uložení výsledku do data.json pro tvůj webový dashboard
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(vysledek, f, indent=4, ensure_ascii=False)
            
        # Výpis do konzole pro kontrolu v GitHub Actions
        print(f"TRH: {vysledek['trend']}")
        print(f"AKCE: {vysledek['akce']}")
        if vysledek['sl'] > 0:
            print(f"VSTUP: {vysledek['cena']} | SL: {vysledek['sl']} | TP: {vysledek['tp']}")
        print("--- Analýza dokončena a uložena do data.json ---")

    except Exception as e:
        print(f"KRITICKÁ CHYBA: {e}")

if __name__ == "__main__":
    main()
