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

# URL Root per REST e Auth
REST_URL = f"{SUPABASE_URL}/rest/v1"
AUTH_URL = f"{SUPABASE_URL}/auth/v1"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

import requests

def _request(url, method="GET", data=None, extra_headers=None, custom_auth=None):
    headers = HEADERS.copy()
    if extra_headers:
        headers.update(extra_headers)
    if custom_auth:
        headers["Authorization"] = f"Bearer {custom_auth}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return {"error": True, "details": f"Metodo {method} non supportato"}

        if response.text:
            try:
                res_data = response.json()
            except:
                res_data = {"text": response.text}
        else:
            res_data = {}

        if response.status_code >= 400:
            return {"error": True, "details": res_data, "status_code": response.status_code}
        
        return res_data

    except Exception as e:
        return {"error": True, "details": str(e)}

# --- AUTHENTICATION ---

def auth_signup(email, password, name):
    url = f"{AUTH_URL}/signup"
    payload = {
        "email": email,
        "password": password,
        "data": {"full_name": name}
    }
    res = _request(url, method="POST", data=payload)
    if res and "error" not in res:
        return {"success": True, "user": res}
    return {"success": False, "error": res.get("details", "Errore ignoto")}

def auth_login(email, password):
    url = f"{AUTH_URL}/token?grant_type=password"
    payload = {
        "email": email,
        "password": password
    }
    res = _request(url, method="POST", data=payload)
    if res and "access_token" in res:
        return {
            "success": True, 
            "token": res["access_token"], 
            "user_id": res["user"]["id"],
            "name": res["user"]["user_metadata"].get("full_name", email)
        }
    return {"success": False, "error": res.get("details", "Credenziali non valide")}

# --- SETTINGS CRUD (Filtro user_id) ---

def get_setting(user_id, key, token=None, default=None):
    try:
        url = f"{REST_URL}/settings?select=value&key=eq.{key}&user_id=eq.{user_id}"
        res = _request(url, custom_auth=token)
        if res and not isinstance(res, dict) and len(res) > 0:
            return float(res[0]['value'])
    except Exception:
        pass
    return default

def update_setting(user_id, key, value, token=None):
    url = f"{REST_URL}/settings"
    payload = {"user_id": user_id, "key": key, "value": str(value)}
    _request(url, method="POST", data=payload, extra_headers={"Prefer": "resolution=merge-duplicates"}, custom_auth=token)

# --- ASSET CLASSES CRUD (Filtro user_id) ---

def get_asset_classes(user_id, token=None):
    url = f"{REST_URL}/asset_classes?select=id,name,target_percentage&user_id=eq.{user_id}"
    res = _request(url, custom_auth=token)
    return res if isinstance(res, list) else []

def add_asset_class(user_id, name, target_percentage, token=None):
    url = f"{REST_URL}/asset_classes"
    payload = {"user_id": user_id, "name": name, "target_percentage": target_percentage}
    res = _request(url, method="POST", data=payload, custom_auth=token)
    return res

def delete_asset_class(user_id, class_id, token=None):
    url_ac = f"{REST_URL}/asset_classes?id=eq.{class_id}&user_id=eq.{user_id}"
    url_p = f"{REST_URL}/portfolio?asset_class_id=eq.{class_id}&user_id=eq.{user_id}"
    # Aggiorna portfolio a NULL per quegli asset
    _request(url_p, method="PATCH", data={"asset_class_id": None}, custom_auth=token)
    # Elimina AC
    _request(url_ac, method="DELETE", custom_auth=token)

# --- PORTFOLIO CRUD (Filtro user_id) ---

def get_portfolio(user_id, token=None):
    url = f"{REST_URL}/portfolio?select=id,ticker,name,quantity,avg_price,currency,asset_class_id,asset_classes(name)&user_id=eq.{user_id}"
    data = _request(url, custom_auth=token)
    if not isinstance(data, list): data = []
    
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

def add_portfolio_item(user_id, ticker, name, asset_class_id, quantity, avg_price, currency, token=None):
    url = f"{REST_URL}/portfolio"
    payload = {
        'user_id': user_id,
        'ticker': ticker,
        'name': name,
        'asset_class_id': asset_class_id,
        'quantity': quantity,
        'avg_price': avg_price,
        'currency': currency
    }
    res = _request(url, method="POST", data=payload, custom_auth=token)
    return res is not None and "error" not in res

def update_portfolio_item(user_id, item_id, quantity, avg_price, asset_class_id, token=None):
    url = f"{REST_URL}/portfolio?id=eq.{item_id}&user_id=eq.{user_id}"
    payload = {
        'quantity': quantity,
        'avg_price': avg_price,
        'asset_class_id': asset_class_id
    }
    _request(url, method="PATCH", data=payload, custom_auth=token)

def delete_portfolio_item(user_id, item_id, token=None):
    url = f"{REST_URL}/portfolio?id=eq.{item_id}&user_id=eq.{user_id}"
    _request(url, method="DELETE", custom_auth=token)

# --- HISTORY CRUD (Filtro user_id) ---

def get_history(user_id, token=None):
    url = f"{REST_URL}/history?select=date,total_value,invested_capital&user_id=eq.{user_id}&order=date.asc"
    res = _request(url, custom_auth=token)
    return res if isinstance(res, list) else []

def add_history_snapshot(user_id, date_str, total_value, invested_capital, token=None):
    url = f"{REST_URL}/history"
    payload = {
        'user_id': user_id,
        'date': date_str,
        'total_value': total_value,
        'invested_capital': invested_capital
    }
    _request(url, method="POST", data=payload, extra_headers={"Prefer": "resolution=merge-duplicates"}, custom_auth=token)

def delete_history_snapshot(user_id, date_str, token=None):
    url = f"{REST_URL}/history?date=eq.{date_str}&user_id=eq.{user_id}"
    _request(url, method="DELETE", custom_auth=token)

# --- CACHE --- (La cache prezzi è globale, non serve user_id per ora)

def get_cached_price(ticker):
    try:
        url = f"{REST_URL}/price_cache?select=price,last_updated&ticker=eq.{ticker}"
        res = _request(url)
        if res and isinstance(res, list) and len(res) > 0:
            return {"price": res[0]['price'], "last_updated": res[0]['last_updated']}
    except Exception:
        pass
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
