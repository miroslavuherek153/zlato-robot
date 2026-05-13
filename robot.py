import json
import os
from src.robot import analyzuj_xauusd

def spustit_analýzu():
    print("--- 🔍 ZLATO-ROBOT: Startuji analýzu trhu ---")
    
    try:
        # Voláme mozek aplikace
        vysledek = analyzuj_xauusd()
        
        # Uložíme výsledek do JSONu pro tvůj dashboard
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(vysledek, f, indent=4, ensure_ascii=False)
            
        # Výpis pro tebe do konzole
        print(f"Aktuální cena: {vysledek['cena']} USD")
        print(f"Hlavní trend: {vysledek['trend']}")
        print(f"DOPORUČENÍ: {vysledek['akce']}")
        
        if vysledek['akce'] != "ČEKAT":
            print(f"🎯 Vstup: {vysledek['cena']}")
            print(f"🛑 Stop-Loss: {vysledek['sl']}")
            print(f"💰 Take-Profit: {vysledek['tp']}")
        
        print(f"💡 Důvod: {vysledek['duvod']}")
        print("--- ✅ Analýza dokončena a data uložena ---")

    except Exception as e:
        print(f"❌ CHYBA: {str(e)}")

if __name__ == "__main__":
    spustit_analýzu()
