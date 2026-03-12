import urllib.request
import urllib.parse
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Carica variabili d'ambiente
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Root URL per REST API
REST_URL = f"{SUPABASE_URL}/rest/v1"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def _request(url, method="GET", data=None, extra_headers=None):
    headers = HEADERS.copy()
    if extra_headers:
        headers.update(extra_headers)
    
    req_data = None
    if data:
        req_data = json.dumps(data).encode("utf-8")
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body) if res_body else {}
    except Exception as e:
        # Fallback silenzioso o log minimo
        return None

# --- SETTINGS CRUD ---
def get_setting(key, default=None):
    url = f"{REST_URL}/settings?select=value&key=eq.{key}"
    res = _request(url)
    if res and len(res) > 0:
        return float(res[0]['value'])
    return default

def update_setting(key, value):
    url = f"{REST_URL}/settings"
    payload = {"key": key, "value": str(value)}
    _request(url, method="POST", data=payload, extra_headers={"Prefer": "resolution=merge-duplicates"})

# --- ASSET CLASSES CRUD ---
def get_asset_classes():
    url = f"{REST_URL}/asset_classes?select=id,name,target_percentage"
    return _request(url) or []

def add_asset_class(name, target_percentage):
    url = f"{REST_URL}/asset_classes"
    payload = {"name": name, "target_percentage": target_percentage}
    _request(url, method="POST", data=payload)

def delete_asset_class(class_id):
    url_ac = f"{REST_URL}/asset_classes?id=eq.{class_id}"
    url_p = f"{REST_URL}/portfolio?asset_class_id=eq.{class_id}"
    # Aggiorna portfolio a NULL
    _request(url_p, method="PATCH", data={"asset_class_id": None})
    # Elimina AC
    _request(url_ac, method="DELETE")

# --- PORTFOLIO CRUD ---
def get_portfolio():
    url = f"{REST_URL}/portfolio?select=id,ticker,name,quantity,avg_price,currency,asset_class_id,asset_classes(name)"
    data = _request(url) or []
    
    portfolio = []
    for r in data:
        portfolio.append({
            "id": r['id'],
            "ticker": r['ticker'],
            "name": r['name'],
            "quantity": r['quantity'],
            "avg_price": r['avg_price'],
            "currency": r['currency'],
            "asset_class": r['asset_classes']['name'] if r.get('asset_classes') else None,
            "asset_class_id": r['asset_class_id']
        })
    return portfolio

def add_portfolio_item(ticker, name, asset_class_id, quantity, avg_price, currency):
    url = f"{REST_URL}/portfolio"
    payload = {
        'ticker': ticker,
        'name': name,
        'asset_class_id': asset_class_id,
        'quantity': quantity,
        'avg_price': avg_price,
        'currency': currency
    }
    res = _request(url, method="POST", data=payload)
    return res is not None

def update_portfolio_item(item_id, quantity, avg_price, asset_class_id):
    url = f"{REST_URL}/portfolio?id=eq.{item_id}"
    payload = {
        'quantity': quantity,
        'avg_price': avg_price,
        'asset_class_id': asset_class_id
    }
    _request(url, method="PATCH", data=payload)

def delete_portfolio_item(item_id):
    url = f"{REST_URL}/portfolio?id=eq.{item_id}"
    _request(url, method="DELETE")

# --- HISTORY CRUD ---
def get_history():
    url = f"{REST_URL}/history?select=date,total_value,invested_capital&order=date.asc"
    return _request(url) or []

def add_history_snapshot(date_str, total_value, invested_capital):
    url = f"{REST_URL}/history"
    payload = {
        'date': date_str,
        'total_value': total_value,
        'invested_capital': invested_capital
    }
    _request(url, method="POST", data=payload, extra_headers={"Prefer": "resolution=merge-duplicates"})

def delete_history_snapshot(date_str):
    url = f"{REST_URL}/history?date=eq.{date_str}"
    _request(url, method="DELETE")

# --- CACHE ---
def get_cached_price(ticker):
    url = f"{REST_URL}/price_cache?select=price,last_updated&ticker=eq.{ticker}"
    res = _request(url)
    if res and len(res) > 0:
        return {"price": res[0]['price'], "last_updated": res[0]['last_updated']}
    return None

def update_cached_price(ticker, price):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url = f"{REST_URL}/price_cache"
    payload = {
        'ticker': ticker,
        'price': price,
        'last_updated': now_str
    }
    _request(url, method="POST", data=payload, extra_headers={"Prefer": "resolution=merge-duplicates"})
