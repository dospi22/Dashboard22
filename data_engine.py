import yfinance as yf
from datetime import datetime, time
import pytz
import logging
import streamlit as st
from database import get_cached_price, update_cached_price

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_ticker(ticker_symbol):
    """
    Verifica se un ticker è valido usando yfinance.
    Ritorna un dizionario con 'name' e 'currency' se valido,
    altrimenti solleva un'eccezione o ritorna None.
    """
    try:
        # Crea l'oggetto Ticker
        ticker_obj = yf.Ticker(ticker_symbol)
        
        # Prova a prendere le info base. Se il ticker non esiste, o 'info' è vuoto o fallisce.
        info = ticker_obj.info
        
        # 'regularMarketPrice' o 'currentPrice' sono buoni indicatori che il ticker esiste e scambia
        if 'shortName' in info:
            name = info.get('longName', info.get('shortName', ticker_symbol))
            currency = info.get('currency', 'EUR')
            # Forziamo a controllare se c'è un prezzo, per evitare falsi positivi
            price = info.get('currentPrice', info.get('regularMarketPreviousClose', None))
            
            if price is not None:
                # Piccolo salvataggio in cache inziale
                update_cached_price(ticker_symbol, price)
                return {
                    "valid": True,
                    "name": name,
                    "currency": currency,
                    "price": price
                }
            
        return {"valid": False, "error": "Ticker non trovato o senza dati di prezzo associati."}

    except Exception as e:
        logger.error(f"Errore validazione ticker {ticker_symbol}: {e}")
        return {"valid": False, "error": "Ticker non trovato. Verifica il suffisso (es. .MI per Milano, .DE per Francoforte)"}


def should_update_price(last_updated_str):
    """
    Determina se è necessario aggiornare i prezzi tramite API basandosi sulle regole:
    - Se l'ultimo aggiornamento è precedente ad oggi -> SI
    - Se oggi, aggiorna se siamo dopo le 10:00 ma l'ultimo update era prima delle 10:00
    - Se oggi, aggiorna se siamo dopo le 21:00 ma l'ultimo update era prima delle 21:00
    """
    if not last_updated_str:
        return True
        
    try:
        last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        
        # Se è di un giorno precedente, aggiorna sicuramente
        if last_updated.date() < now.date():
            return True
            
        # Stesso giorno. Controlliamo le finestre (10:00 e 21:00)
        time_10 = time(10, 0)
        time_21 = time(21, 0)
        
        now_time = now.time()
        last_time = last_updated.time()
        
        # Se ora è dopo le 10, ma l'ultimo update era prima
        if now_time >= time_10 and last_time < time_10:
            return True
            
        # Se ora è dopo le 21, ma l'ultimo update era prima
        if now_time >= time_21 and last_time < time_21:
            return True
            
        # In tutti gli altri casi del giorno corrente, usa la cache
        return False
        
    except Exception as e:
        logger.error(f"Errore parsing data cache: {e}")
        return True # In caso di errore, forza l'aggiornamento

def get_current_prices(tickers, force_update=False):
    """
    Recupera i prezzi per una lista di tickers.
    Restituisce un dizionario {ticker: {'price': p, 'last_update': t}}
    """
    if not tickers:
        return {}
        
    results = {}
    tickers_to_fetch = []
    
    # 1. Controlla la cache (SQL) per ogni ticker
    for ticker in tickers:
        cached_data = get_cached_price(ticker)
        if cached_data and not force_update:
            if should_update_price(cached_data['last_updated']):
                tickers_to_fetch.append(ticker)
            else:
                results[ticker] = {
                    'price': cached_data['price'],
                    'last_update': cached_data['last_updated']
                }
        else:
            tickers_to_fetch.append(ticker)
            
    # 2. Se abbiamo ticker da scaricare
    if tickers_to_fetch:
        try:
            data = yf.download(tickers_to_fetch, period="1d", group_by="ticker", threads=True, progress=False)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for ticker in tickers_to_fetch:
                try:
                    if len(tickers_to_fetch) == 1:
                        price = float(data['Close'].iloc[-1])
                    else:
                        price = float(data[ticker]['Close'].iloc[-1])
                        
                    results[ticker] = {'price': price, 'last_update': now_str}
                    update_cached_price(ticker, price)
                except Exception as e:
                    cached_data = get_cached_price(ticker)
                    if cached_data:
                        results[ticker] = {'price': cached_data['price'], 'last_update': cached_data['last_updated']}
                    else:
                        results[ticker] = {'price': 0.0, 'last_update': 'N/A'}
        except Exception as e:
            logger.error(f"Errore API bulk download: {e}")
            
    return results

def calculate_portfolio_metrics(portfolio_items, current_prices):
    """
    Calcola le metriche complete del portafoglio estendendo i dati di base.
    """
    total_invested = 0.0
    total_current_value = 0.0
    
    enriched_portfolio = []
    
    for item in portfolio_items:
        ticker = item['ticker']
        quantity = item['quantity']
        avg_price = item['avg_price']
        
        # Modifica per supportare dizionario di risultati {price, last_update}
        price_info = current_prices.get(ticker, {'price': 0.0, 'last_update': 'N/A'})
        current_price = price_info['price']
        
        # Calcoli riga
        invested = quantity * avg_price
        current_value = quantity * current_price
        
        pl_eur = current_value - invested
        pl_perc = (pl_eur / invested * 100) if invested > 0 else 0.0
        
        enriched_item = item.copy()
        enriched_item['current_price'] = current_price
        enriched_item['total_value'] = current_value
        enriched_item['pl_eur'] = pl_eur
        enriched_item['pl_perc'] = pl_perc
        
        enriched_portfolio.append(enriched_item)
        
        # Totali
        total_invested += invested
        total_current_value += current_value
        
    total_pl_eur = total_current_value - total_invested
    total_pl_perc = (total_pl_eur / total_invested * 100) if total_invested > 0 else 0.0
    
    return {
        "items": enriched_portfolio,
        "total_invested": total_invested,
        "total_current_value": total_current_value,
        "total_pl_eur": total_pl_eur,
        "total_pl_perc": total_pl_perc
    }
