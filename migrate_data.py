import sqlite3
import database
import os

DB_PATH = 'wealthflow.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print("Local database not found. Skipping migration.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("--- Start Migration ---")

    # 1. Settings
    c.execute("SELECT key, value FROM settings")
    for k, v in c.fetchall():
        print(f"Migrating setting: {k}")
        database.update_setting(k, v)

    # 2. Asset Classes
    c.execute("SELECT name, target_percentage FROM asset_classes")
    for name, target in c.fetchall():
        print(f"Migrating Asset Class: {name}")
        database.add_asset_class(name, target)

    # 3. Portfolio
    # Riapriamo le asset classes da Supabase per avere gli ID corretti
    sb_classes = {ac['name']: ac['id'] for ac in database.get_asset_classes()}
    
    c.execute("SELECT ticker, name, quantity, avg_price, currency, asset_class_id FROM portfolio")
    for ticker, name, qty, avg, curr, old_ac_id in c.fetchall():
        # Recupera il nome della vecchia AC
        c2 = conn.cursor()
        c2.execute("SELECT name FROM asset_classes WHERE id=?", (old_ac_id,))
        ac_name_row = c2.fetchone()
        ac_name = ac_name_row[0] if ac_name_row else None
        
        new_ac_id = sb_classes.get(ac_name)
        print(f"Migrating Portfolio Item: {ticker}")
        database.add_portfolio_item(ticker, name, new_ac_id, qty, avg, curr)

    # 4. History
    c.execute("SELECT date, total_value, invested_capital FROM history")
    for d, tv, ic in c.fetchall():
        print(f"Migrating History: {d}")
        database.add_history_snapshot(d, tv, ic)

    print("--- Migration Finished ---")
    conn.close()

if __name__ == "__main__":
    migrate()
