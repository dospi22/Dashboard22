import yfinance as yf
from datetime import datetime, time
import pytz
import logging
import numpy as np
import pandas as pd
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
            # Scarica dati per tutti i ticker mancanti in una volta sola
            data = yf.download(tickers_to_fetch, period="5d", group_by="ticker", threads=True, progress=False)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if data.empty:
                logger.warning(f"Download fallito: DataFrame vuoto per {tickers_to_fetch}")
            else:
                for ticker in tickers_to_fetch:
                    try:
                        # Gestione differente se yfinance ritorna Series (1 ticker) o DataFrame (n ticker)
                        ticker_data = data[ticker] if len(tickers_to_fetch) > 1 else data
                        
                        valid_rows = ticker_data['Close'].dropna()
                        if not valid_rows.empty:
                            price = float(valid_rows.iloc[-1])
                            results[ticker] = {'price': price, 'last_update': now_str}
                            update_cached_price(ticker, price)
                        else:
                            logger.warning(f"Nessun dato ticker per {ticker}")
                    except Exception as e:
                        logger.error(f"Errore ticker {ticker}: {e}")
        except Exception as e:
            logger.error(f"Errore API download: {e}")

    # Fallback finale per i ticker che ancora non hanno un prezzo
    for ticker in tickers:
        if ticker not in results or results[ticker]['price'] == 0:
            cached_data = get_cached_price(ticker)
            if cached_data:
                results[ticker] = {'price': cached_data['price'], 'last_update': cached_data['last_updated']}
            else:
                results[ticker] = results.get(ticker, {'price': 0.0, 'last_update': 'N/A'})
            
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

def calculate_risk_metrics(history_data):
    """
    Calcola Max Drawdown e Volatilità dal log storico.
    """
    if not history_data or len(history_data) < 2:
        return {"max_drawdown": 0.0, "volatility": 0.0}
    
    df = pd.DataFrame(history_data)
    df['total_value'] = df['total_value'].astype(float)
    
    # 1. Max Drawdown
    rolling_max = df['total_value'].cummax()
    drawdown = (df['total_value'] - rolling_max) / rolling_max
    max_drawdown = drawdown.min() * 100 # In percentuale
    
    # 2. Volatilità (Deviazione Standard dei rendimenti logaritmici)
    df['returns'] = df['total_value'].pct_change()
    volatility = df['returns'].std() * np.sqrt(252) * 100 if len(df) > 5 else 0.0
    
    return {
        "max_drawdown": abs(round(max_drawdown, 2)),
        "volatility": round(volatility, 2)
    }

def calculate_fire_status(total_value, monthly_expenses, withdrawal_rate=0.04):
    """
    Calcola il progresso verso l'indipendenza finanziaria (FIRE).
    Basato sulla regola del 4% (default).
    """
    if monthly_expenses <= 0:
        return {"percentage": 0.0, "target_capital": 0.0}
    
    annual_expenses = monthly_expenses * 12
    target_capital = annual_expenses / withdrawal_rate
    
    progress_perc = (total_value / target_capital) * 100 if target_capital > 0 else 0.0
    
    return {
        "percentage": min(round(progress_perc, 2), 100.0),
        "target_capital": round(target_capital, 2),
        "is_fire": total_value >= target_capital
    }

def get_milestones(total_invested, total_value):
    """
    Ritorna una lista di traguardi raggiunti.
    """
    milestones = []
    
    if total_invested <= 0: return milestones

    # Esempi di milestones
    if total_invested >= 1000: milestones.append("🌱 Primo Passo (1k€ investiti)")
    if total_invested >= 10000: milestones.append("🌳 Accumulatore (10k€ investiti)")
    if total_invested >= 50000: milestones.append("🏰 Fortezza (50k€ investiti)")
    if total_invested >= 100000: milestones.append("👑 Re degli Investimenti (100k€ investiti)")
    
    pl_perc = (total_value - total_invested) / total_invested * 100 if total_invested > 0 else 0
    if pl_perc >= 10: milestones.append("📈 Mente Fredda (+10% Gain)")
    if pl_perc >= 25: milestones.append("💎 Mani di Diamante (+25% Gain)")
    if pl_perc >= 50: milestones.append("🚀 Verso la Luna (+50% Gain)")
    
    return milestones

def get_portfolio_dna(port_data, asset_classes):
    """
    Analizza la composizione e i settori per determinare la 'personalità' del portafoglio.
    """
    if not port_data['items']:
        return {
            "type": "Vuoto",
            "description": "Inizia ad aggiungere asset per scoprire il tuo DNA finanziario.",
            "icon": "🌑",
            "sectors": {}
        }
    
    total_val = port_data['total_current_value']
    if total_val <= 0: return {"type": "Sconosciuto", "description": "Valore portafoglio nullo.", "icon": "❓", "sectors": {}}

    # keyword classification
    equities = 0.0
    fixed_income = 0.0
    cash = 0.0
    crypto = 0.0
    real_assets = 0.0
    
    ac_dict = {ac['id']: ac['name'].lower() for ac in asset_classes}
    
    for item in port_data['items']:
        name = ac_dict.get(item['asset_class_id'], "")
        val = item['total_value']
        
        if any(k in name for k in ['azion', 'equity', 'stock', 'share', 'etf']):
            # Distinguiamo crypto se possibile
            if 'crypto' in name or 'bitcoin' in name or 'eth' in name:
                crypto += val
            else:
                equities += val
        elif any(k in name for k in ['obblig', 'bond', 'fixed', 'titoli di stato']):
            fixed_income += val
        elif any(k in name for k in ['liquid', 'cash', 'conto', 'fondo']):
            cash += val
        elif any(k in name for k in ['oro', 'gold', 'commodity', 'reit', 'immobiliare']):
            real_assets += val
        else:
            equities += val # Default to equity if unsure
            
    p_equity = (equities / total_val) * 100
    p_fixed = (fixed_income / total_val) * 100
    p_crypto = (crypto / total_val) * 100
    
    # Logic for DNA Type
    if p_crypto > 25:
        dna_type = "Speculativo / Web3 High"
        description = "Il tuo portafoglio è fortemente esposto alla volatilità delle cripto. Elevato rischio, ma potenziale di crescita esplosivo."
        icon = "💎"
    elif p_equity > 85:
        dna_type = "Aggressivo (Full Equity)"
        description = "Massima esposizione azionaria. Sei orientato alla crescita a lungo termine e accetti forti oscillazioni di mercato."
        icon = "🦁"
    elif p_equity > 65:
        dna_type = "Crescita (Growth)"
        description = "Un portafoglio dinamico con una solida base azionaria, bilanciato da una piccola quota di protezione."
        icon = "🚀"
    elif p_equity > 40:
        dna_type = "Bilanciato"
        description = "Il classico equilibrio tra rischio e rendimento. Adatto a chi cerca crescita senza troppe preoccupazioni."
        icon = "⚖️"
    elif p_fixed > 60:
        dna_type = "Conservativo"
        description = "Priorità alla conservazione del capitale. Generi reddito costante con minimi drawdown."
        icon = "🛡️"
    elif cash > (total_val * 0.7):
        dna_type = "Prudente / Liquido"
        description = "Sei in modalità 'attesa'. Gran parte del tuo capitale è pronto per essere schierato quando ci saranno opportunità."
        icon = "🧊"
    else:
        dna_type = "Ibrido Personalizzato"
        description = "Hai una strategia peculiare che non rientra nei canoni standard. Un mix unico di asset."
        icon = "🧬"
        
    return {
        "type": dna_type,
        "description": description,
        "icon": icon,
        "percentages": {
            "Equity": round(p_equity, 1),
            "Fixed Income": round(p_fixed, 1),
            "Crypto": round(p_crypto, 1)
        }
    }
