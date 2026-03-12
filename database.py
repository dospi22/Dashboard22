import sqlite3
import os
from datetime import datetime

DB_PATH = 'wealthflow.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Tabelle delle Impostazioni
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # Macro-Categorie (Asset Classes)
    c.execute('''
        CREATE TABLE IF NOT EXISTS asset_classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            target_percentage REAL
        )
    ''')

    # Portafoglio
    c.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE,
            name TEXT,
            asset_class_id INTEGER,
            quantity REAL,
            avg_price REAL,
            currency TEXT,
            FOREIGN KEY(asset_class_id) REFERENCES asset_classes(id)
        )
    ''')

    # Storico Valore Portafoglio
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            total_value REAL,
            invested_capital REAL
        )
    ''')

    # Cache prezi giornalieri per limitare chiamate API
    c.execute('''
        CREATE TABLE IF NOT EXISTS price_cache (
            ticker TEXT PRIMARY KEY,
            price REAL,
            last_updated TEXT
        )
    ''')
    
    # Inserimento impostazioni di default se non esistono
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('tolerance', '5')")

    conn.commit()
    conn.close()

# --- SETTINGS CRUD ---
def get_setting(key, default=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return float(row[0]) if row else default

def update_setting(key, value):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

# --- ASSET CLASSES CRUD ---
def get_asset_classes():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, target_percentage FROM asset_classes")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "target_percentage": r[2]} for r in rows]

def add_asset_class(name, target_percentage):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO asset_classes (name, target_percentage) VALUES (?, ?)", (name, target_percentage))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Ignora i duplicati
    finally:
        conn.close()

def delete_asset_class(class_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM asset_classes WHERE id=?", (class_id,))
    # Resetta la classe per gli asset che la usavano
    c.execute("UPDATE portfolio SET asset_class_id=NULL WHERE asset_class_id=?", (class_id,))
    conn.commit()
    conn.close()


# --- PORTFOLIO CRUD ---
def get_portfolio():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT p.id, p.ticker, p.name, p.quantity, p.avg_price, p.currency, c.name, p.asset_class_id
        FROM portfolio p
        LEFT JOIN asset_classes c ON p.asset_class_id = c.id
    ''')
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "ticker": r[1], "name": r[2], "quantity": r[3], "avg_price": r[4], 
             "currency": r[5], "asset_class": r[6], "asset_class_id": r[7]} for r in rows]

def add_portfolio_item(ticker, name, asset_class_id, quantity, avg_price, currency):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO portfolio (ticker, name, asset_class_id, quantity, avg_price, currency)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (ticker, name, asset_class_id, quantity, avg_price, currency))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Ticker già esistente
    finally:
        conn.close()

def update_portfolio_item(item_id, quantity, avg_price, asset_class_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE portfolio 
        SET quantity=?, avg_price=?, asset_class_id=?
        WHERE id=?
    ''', (quantity, avg_price, asset_class_id, item_id))
    conn.commit()
    conn.close()

def delete_portfolio_item(item_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM portfolio WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

# --- HISTORY CRUD ---
def get_history():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT date, total_value, invested_capital FROM history ORDER BY date ASC")
    rows = c.fetchall()
    conn.close()
    return [{"date": r[0], "total_value": r[1], "invested_capital": r[2]} for r in rows]

def add_history_snapshot(date_str, total_value, invested_capital):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO history (date, total_value, invested_capital)
        VALUES (?, ?, ?)
    ''', (date_str, total_value, invested_capital))
    conn.commit()
    conn.close()

def delete_history_snapshot(date_str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM history WHERE date=?", (date_str,))
    conn.commit()
    conn.close()

# --- CACHE ---
def get_cached_price(ticker):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT price, last_updated FROM price_cache WHERE ticker=?", (ticker,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"price": row[0], "last_updated": row[1]}
    return None

def update_cached_price(ticker, price):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO price_cache (ticker, price, last_updated)
        VALUES (?, ?, ?)
    ''', (ticker, price, now_str))
    conn.commit()
    conn.close()

# Inizializza il DB all'importazione (oppure lo chiamiamo esplicitamente da app.py)
if not os.path.exists(DB_PATH):
    init_db()
