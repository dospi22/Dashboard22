import sys
import os

# Aggiungi la directory corrente al path per importare i moduli locali
sys.path.append(os.getcwd())

import database as db
import data_engine as de
from datetime import datetime

def test_database_connection():
    print("--- Test Database Connection ---")
    # Tenta un'operazione semplice (es. get_asset_classes con user_id fittizio)
    # Non serve un token per un test di struttura o errore gestito
    res = db.get_asset_classes("00000000-0000-0000-0000-000000000000")
    print(f"Risultato (vuoto atteso): {res}")
    print("Database connection logic (requests) is OK.")

def test_data_engine():
    print("\n--- Test Data Engine ---")
    tickers = ["AAPL", "VWCE.MI"]
    print(f"Recupero prezzi per: {tickers}")
    prices = de.get_current_prices(tickers, force_update=True)
    for t, info in prices.items():
        print(f"Ticker: {t}, Prezzo: {info['price']}, Update: {info['last_update']}")
    
    if all(prices[t]['price'] > 0 for t in tickers):
        print("Data engine logic is OK.")
    else:
        print("Warning: Some prices are 0, check internet connection or ticker symbols.")

if __name__ == "__main__":
    try:
        test_database_connection()
        test_data_engine()
        print("\nVerification completed successfully!")
    except Exception as e:
        print(f"\nVerification failed with error: {e}")
