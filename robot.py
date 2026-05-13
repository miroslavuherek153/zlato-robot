import json
from src.robot import analyze_xauusd

def main():
    print("Spouštím analýzu XAUUSD...")
    vysledek = analyze_xauusd()
    
    with open("data.json", "w") as f:
        json.dump(vysledek, f, indent=4)
        
    print(f"Hotovo. Akce: {vysledek['akce']} při ceně {vysledek['cena']}")

if __name__ == "__main__":
    main()
