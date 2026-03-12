try:
    import database
    print("Database module imported successfully.")
    import pandas as pd
    print("Pandas imported successfully.")
    import yfinance as yf
    print("yfinance imported successfully.")
    
    classes = database.get_asset_classes()
    print("Asset classes fetched:", classes)
except Exception as e:
    print("Error during test:", e)
    import traceback
    traceback.print_exc()
