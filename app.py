import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import importlib

# Import custom modules
import database as db
importlib.reload(db)
import data_engine as de

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="DASBOARD 22",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZZATO (REDESIGN) ---
st.markdown("""
<style>
    /* Sfondo principale e contenitore */
    .stApp {
        background-color: #0e1117;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px; /* Larghezza massima simile all'immagine */
    }
    
    /* Layout KPI Cards */
    .kpi-container {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin-bottom: 25px;
    }
    
    .kpi-card {
        background-color: #1a1b1f; /* Colore dark grigio */
        border: 1px solid #2d2e32;
        border-radius: 12px;
        padding: 20px;
        flex: 1;
        min-width: 250px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
    }
    
    .kpi-title {
        color: #8c8d92;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 5px;
    }
    
    .kpi-value {
        color: #ffffff;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    
    .kpi-badge {
        display: inline-block;
        background-color: rgba(0, 200, 83, 0.15); /* Sfondo verde tenue */
        color: #00e676; /* Verde acceso */
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        width: fit-content;
    }
    .kpi-badge.negative {
        background-color: rgba(255, 61, 113, 0.15);
        color: #ff3d71;
    }
    
    /* Stili specifici per icone (posizionate assolute in alto a dx) */
    .kpi-icon {
        position: absolute;
        top: 20px;
        right: 20px;
        font-size: 20px;
    }
    
    /* Divisore trasparente e invisibile per spazio */
    hr {
        border-top: 1px solid #2d2e32;
        margin-top: 25px;
        margin-bottom: 25px;
    }
    
</style>
""", unsafe_allow_html=True)

# --- INIZIALIZZAZIONE ---
# db.init_db() - Non più necessario con Supabase

# --- INIZIALIZZAZIONE SESSIONE ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'user_token' not in st.session_state:
    st.session_state.user_token = None
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = 'login'
if 'force_price_update' not in st.session_state:
    st.session_state.force_price_update = False

# Tenta di ripristinare la sessione da URL se possibile (Persistence)
query_params = st.query_params
if st.session_state.user_token is None and "token" in query_params:
    saved_token = query_params["token"]
    # In una versione reale, dovremmo validare il token, 
    # ma qui ci fidiamo del fatto che Supabase lo gestirà nelle chiamate DB.
    # Se il token è scaduto, le chiamate db falliranno e st.error mostrerà il problema.
    st.session_state.user_token = saved_token
    if "uid" in query_params: st.session_state.user_id = query_params["uid"]
    if "name" in query_params: st.session_state.user_name = query_params["name"]

def logout():
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_token = None
    st.session_state.auth_mode = 'login'
    st.query_params.clear() # Pulisce URL
    st.rerun()

# CSS Premium per il Login (Glassmorphism & Centering)
st.markdown("""
<style>
    /* Nascondi elementi Streamlit che disturbano il focus */
    [data-testid="stHeader"] { visibility: hidden; }
    [data-testid="stSidebarNav"] { display: none; }
    
    /* Reset padding container per centramento */
    .main .block-container {
        padding-top: 0;
        padding-bottom: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        background-color: #0e1117;
        background-image: radial-gradient(circle at 20% 30%, rgba(79, 70, 229, 0.1) 0%, transparent 50%),
                          radial-gradient(circle at 80% 70%, rgba(124, 58, 237, 0.1) 0%, transparent 50%);
    }

    .stApp {
        background: transparent;
    }

    .auth-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        max-width: 420px;
        animation: fadeIn 0.8s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .auth-card {
        background: rgba(26, 27, 31, 0.6);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 28px;
        padding: 45px;
        width: 100%;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }

    .auth-header {
        text-align: center;
        margin-bottom: 30px;
    }

    .auth-header h1 {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 8px;
        background: linear-gradient(90deg, #fff, #a5b4fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .auth-header p {
        color: #94a3b8;
        font-size: 0.95rem;
    }

    /* Styling Input Fields */
    .stTextInput > div > div > input {
        background-color: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 12px 16px !important;
    }

    /* Bottoni */
    .stButton > button {
        width: 100%;
        border-radius: 14px !important;
        height: 3.2em !important;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        margin-top: 10px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 20px -5px rgba(79, 70, 229, 0.5) !important;
        filter: brightness(1.1) !important;
    }

    .secondary-btn > button {
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #94a3b8 !important;
        margin-top: 20px !important;
    }

    .secondary-btn > button:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

if st.session_state.user_token is None:
    # Mostra Logo se presente
    logo_html = ""
    if os.path.exists("assets/logo.png"):
        logo_path = "assets/logo.png"
        import base64
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="100" style="margin-bottom: 20px;">'

    if st.session_state.auth_mode == 'login':
        st.markdown(f"""
            <div class="auth-wrapper">
                {logo_html}
                <div class="auth-card">
                    <div class="auth-header">
                        <h1>Benvenuto 👋</h1>
                        <p>Inserisci le tue credenziali per accedere</p>
                    </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="nome@esempio.it")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Accedi")
            if submitted:
                if not email or not password:
                    st.error("Inserisci email e password")
                else:
                    res = db.auth_login(email, password)
                    if res['success']:
                        st.session_state.user_id = res['user_id']
                        st.session_state.user_name = res['name']
                        st.session_state.user_token = res['token']
                        # Salva sessione in URL (Persistence)
                        st.query_params.update({
                            "token": res['token'],
                            "uid": res['user_id'],
                            "name": res['name']
                        })
                        st.success("Accesso effettuato!")
                        st.rerun()
                    else:
                        st.error(f"Errore: {res['error']}")
        
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("Non hai un account? Registrati ora"):
            st.session_state.auth_mode = 'signup'
            st.rerun()
        st.markdown('</div></div></div>', unsafe_allow_html=True)
        st.stop()
    else:
        st.markdown(f"""
            <div class="auth-wrapper">
                {logo_html}
                <div class="auth-card">
                    <div class="auth-header">
                        <h1>Crea Account ✨</h1>
                        <p>Inizia a gestire il tuo patrimonio oggi</p>
                    </div>
        """, unsafe_allow_html=True)
        
        with st.form("signup_form"):
            new_name = st.text_input("Nome Completo", placeholder="Mario Rossi")
            new_email = st.text_input("Email", placeholder="mario@esempio.it")
            new_password = st.text_input("Password", type="password", placeholder="Minimo 6 caratteri")
            submitted = st.form_submit_button("Crea il mio account")
            if submitted:
                if len(new_password) < 6:
                    st.error("La password deve avere almeno 6 caratteri.")
                elif not new_name or not new_email:
                    st.error("Compila tutti i campi.")
                else:
                    res = db.auth_signup(new_email, new_password, new_name)
                    if res['success']:
                        st.success("Registrazione completata! Ora puoi accedere.")
                        st.session_state.auth_mode = 'login'
                        st.info("⚠️ Controlla la tua email per confermare l'account (se richiesto).")
                    else:
                        st.error(f"Errore: {res['error']}")
        
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("Hai già un account? Accedi"):
            st.session_state.auth_mode = 'login'
            st.rerun()
        st.markdown('</div></div></div>', unsafe_allow_html=True)
        st.stop()

# --- DATI E LOGICA (CACHE) ---
@st.cache_data(ttl=600) # Cache per 10 minuti
def get_user_data(uid, token):
    return {
        "asset_classes": db.get_asset_classes(uid, token=token),
        "portfolio_items": db.get_portfolio(uid, token=token),
        "history_data": db.get_history(uid, token=token)
    }

@st.cache_data(ttl=3600) # Cache per 1 ora
def get_user_settings(uid, token):
    return db.get_setting(uid, "tolerance", token=token, default=5.0)

user_id = st.session_state.user_id
user_name = st.session_state.user_name
user_token = st.session_state.user_token

# Caricamento Dati (con Cache)
with st.spinner('Caricamento dati...'):
    data = get_user_data(user_id, user_token)
    asset_classes = data["asset_classes"]
    portfolio_items = data["portfolio_items"]
    history_data = data["history_data"]
    rebalance_tolerance = get_user_settings(user_id, user_token)

# Dizionario helper per Asset Classes
ac_dict = {ac['id']: ac for ac in asset_classes}
ac_names = {ac['id']: ac['name'] for ac in asset_classes}

# Elaborazione Dati Portafoglio (Fetching prezzi e metriche)
tickers = [item['ticker'] for item in portfolio_items]

# Spinner visuale solo se ci sono ticker da aggiornare
with st.spinner('Aggiornamento prezzi live...'):
    current_prices = de.get_current_prices(tickers, force_update=st.session_state.force_price_update)
    # Resettiamo il flag dopo l'uso
    st.session_state.force_price_update = False
    
port_data = de.calculate_portfolio_metrics(portfolio_items, current_prices)

# --- SIDEBAR: CONFIGURAZIONE & INSERIMENTO ---
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            padding-top: 0rem;
        }
        [data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    # Mostra Logo
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=120)
    
    st.write(f"👤 Ciao, **{user_name}**")
    if st.button("Esci (Logout)"):
        logout()
    
    st.divider()
    st.header("⚙️ Configurazione")
    
    # 1. Tolleranza Ribilanciamento
    new_tolerance = st.slider("Tolleranza Ribilanciamento (%)", min_value=1.0, max_value=20.0, value=rebalance_tolerance, step=0.5,
                              help="Deviazione massima consentita prima che un asset richieda bilanciamento.")
    if new_tolerance != rebalance_tolerance:
        db.update_setting(user_id, 'tolerance', new_tolerance, token=user_token)
        get_user_settings.clear() # Svuota cache impostazioni
        st.session_state['tolerance'] = new_tolerance # Force refresh
        st.rerun()

    st.divider()
    # 2. Asset Allocation
    st.subheader("Asset Allocation Target")
    
    # Form per aggiungere una nuova Asset Class
    with st.expander("Aggiungi Asset Class", expanded=False):
        with st.form("add_ac_form", clear_on_submit=True):
            ac_name = st.text_input("Nome Categoria (es. Azionari Globali)")
            ac_target = st.number_input("Target (%)", min_value=0.0, max_value=100.0, step=1.0)
            if st.form_submit_button("Aggiungi"):
                if ac_name:
                    res = db.add_asset_class(user_id, ac_name, ac_target, token=user_token)
                    if isinstance(res, dict) and 'error' in res:
                        st.error(f"Errore: {res.get('details', 'Sconosciuto')}")
                    else:
                        get_user_data.clear() # Svuota cache per ricaricare nuove AC
                        st.success(f"{ac_name} aggiunta!")
                        st.rerun()

    # Tabella visualizzazione Asset Classes
    if asset_classes:
        df_ac = pd.DataFrame(asset_classes)
        # Visualizzazione compatta
        st.dataframe(df_ac[['name', 'target_percentage']].rename(columns={'name':'Categoria', 'target_percentage':'Target %'}), hide_index=True)
        
        # Elimina Asset Class
        del_ac_id = st.selectbox("Elimina Categoria", options=[0] + [ac['id'] for ac in asset_classes], format_func=lambda x: "Seleziona..." if x==0 else ac_names.get(x, ""))
        if del_ac_id != 0 and st.button("Rimuovi Categoria"):
            db.delete_asset_class(user_id, del_ac_id, token=user_token)
            st.cache_data.clear() # Svuota TUTTA la cache per sicurezza
            st.rerun()
    else:
        st.info("Nessuna Asset Class definita. Aggiungine una per iniziare.")

    st.divider()

    # 3. Aggiunta Ticker
    st.subheader("➕ Aggiungi Asset/Ticker")
    ac_options = [(ac['id'], ac['name']) for ac in asset_classes]
    
    with st.form("add_ticker_form", clear_on_submit=True):
        new_ticker = st.text_input("Ticker Symbol (es. AAPL, VWCE.MI)").upper()
        
        selected_ac = st.selectbox(
            "Asset Class",
            options=[opt[0] for opt in ac_options] if ac_options else [],
            format_func=lambda x: next((opt[1] for opt in ac_options if opt[0] == x), ""),
            disabled=not ac_options
        )
        
        col1, col2 = st.columns(2)
        with col1:
            qty = st.number_input("Quantità", min_value=0.0001, format="%.4f")
        with col2:
            avg_p = st.number_input("Prezzo di Carico (€)", min_value=0.01, format="%.2f")
            
        submitted = st.form_submit_button("Valida & Aggiungi")
        
        if submitted:
            if not ac_options:
                st.error("Devi prima creare una Asset Class!")
            elif new_ticker:
                with st.spinner("Validazione in corso..."):
                    val_result = de.validate_ticker(new_ticker)
                    
                    if val_result['valid']:
                        asset_name = val_result['name']
                        asset_curr = val_result['currency']
                        
                        success = db.add_portfolio_item(
                            user_id=user_id,
                            ticker=new_ticker,
                            name=asset_name,
                            asset_class_id=selected_ac,
                            quantity=qty,
                            avg_price=avg_p,
                            currency=asset_curr,
                            token=user_token
                        )
                        if success:
                            st.cache_data.clear() # Refresh totale
                            st.success(f"Aggiunto: {asset_name}")
                            st.rerun()

                        else:
                            st.error("Errore: Il ticker esiste già nel portafoglio.")
                    else:
                        st.error(val_result['error'])


# --- LOGICA KPI PRE-HTML ---
best_performer = "N/A"
best_pl = 0
total_positions = len(port_data['items'])

if total_positions > 0:
    for item in port_data['items']:
        if item['pl_perc'] > best_pl:
            best_pl = item['pl_perc']
            best_performer = item['ticker']

# Snapshot logica spostata nella sidebar per UI pulita
with st.sidebar:
    st.divider()
    st.write("Cattura Storico Odierno:")
    if st.button("📸 Salva Snapshot", use_container_width=True):
        if port_data['total_current_value'] > 0:
            today_str = datetime.now().strftime("%Y-%m-%d")
            db.add_history_snapshot(user_id, today_str, port_data['total_current_value'], 0, token=user_token)
            st.cache_data.clear()
            st.success("Snapshot salvato con successo!")
            st.rerun()
        else:
            st.warning("Portafoglio vuoto. Impossibile salvare snapshot.")
    
    with st.expander("✍️ Inserimento Manuale Storico"):
        hist_date = st.date_input("Data", value=datetime.now())
        hist_val = st.number_input("Valore Totale ($)", min_value=0.0, step=100.0)
        
        if st.button("Salva Storico Manuale", use_container_width=True):
            if hist_val > 0:
                date_str = hist_date.strftime("%Y-%m-%d")
                db.add_history_snapshot(user_id, date_str, hist_val, 0, token=user_token)
                st.cache_data.clear()
                st.success(f"Dato del {date_str} salvato!")
                st.rerun()
            else:
                st.error("Inserisci un valore valido.")
                
    with st.expander("🗑️ Elimina Dato Storico"):
        history_list = history_data
        if not history_list:
            st.info("Nessun dato storico presente.")
        else:
            hist_to_del = st.selectbox(
                "Seleziona data da eliminare", 
                options=[h['date'] for h in history_list]
            )
            if st.button("Conferma Eliminazione", use_container_width=True):
                db.delete_history_snapshot(user_id, hist_to_del, token=user_token)
                st.cache_data.clear()
                st.success(f"Record del {hist_to_del} eliminato!")
                st.rerun()

# --- RENDERING DASHBOARD (HTML CUSTOM KPI) ---
st.markdown("<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'><div></div>", unsafe_allow_html=True)
col_head1, col_head2 = st.columns([1, 1])

if col_head1.button("🔄 Aggiorna Prezzi di Mercato", use_container_width=False):
    st.session_state.force_price_update = True
    st.cache_data.clear()
    st.rerun()

# Mostra orario ultimo aggiornamento se disponibile
if current_prices:
    # Prendi il primo timestamp disponibile (assumiamo aggiornamento bulk)
    sample_item = next(iter(current_prices.values()), {})
    sample_time = sample_item.get('last_update', 'N/A')
    col_head2.markdown(f"<p style='color: #8c8d92; font-size: 0.85rem; margin-top: 10px; text-align: right;'>Ultimo Aggiornamento: <b>{sample_time}</b></p>", unsafe_allow_html=True)

# Creiamo una variabile stringa helper per la visibilità per non far impazzire le f-string con le graffe CSS
visibility_style = "hidden" if best_pl == 0 else "visible"

# Costruiamo le classi condizionali in anticipo
badge1_class = "" if port_data['total_pl_eur'] >= 0 else "negative"
badge2_class = "" if port_data['total_pl_perc'] >= 0 else "negative"
badge4_class = "" if best_pl >= 0 else "negative"

sign1 = "+" if port_data['total_pl_eur'] >= 0 else ""
sign2 = "+" if port_data['total_pl_perc'] >= 0 else ""

html_content = f"""<div class="kpi-container">
    
    <!-- KPI 1: Portfolio Value (Total) -->
    <div class="kpi-card">
        <div class="kpi-title">Portfolio Value</div>
        <div class="kpi-icon" style="color: #a259ff;">💲</div>
        <div class="kpi-value">${port_data['total_current_value']:,.2f}</div>
        <div class="kpi-badge {badge1_class}">
            {sign1}${port_data['total_pl_eur']:,.2f} ({port_data['total_pl_perc']:,.2f}%)
        </div>
    </div>
    
    <!-- KPI 2: Total Return / Day Change (simulated) -->
    <div class="kpi-card">
        <div class="kpi-title">Total Return</div>
        <div class="kpi-icon" style="color: #00e676;">📈</div>
        <div class="kpi-value">${port_data['total_pl_eur']:,.2f}</div>
        <div class="kpi-badge {badge2_class}">
            {sign2}{port_data['total_pl_perc']:,.2f}%
        </div>
    </div>
    
    <!-- KPI 3: Total Positions -->
    <div class="kpi-card">
        <div class="kpi-title">Total Positions</div>
        <div class="kpi-icon" style="color: #3366ff;">⏱️</div>
        <div class="kpi-value">{total_positions}</div>
        <div style="height: 24px;"></div> <!-- Spazio vuoto per allineamento -->
    </div>
    
    <!-- KPI 4: Best Performer -->
    <div class="kpi-card">
        <div class="kpi-title">Best Performer</div>
        <div class="kpi-icon" style="color: #ffaa00;">⚡</div>
        <div class="kpi-value">{best_performer}</div>
        <div class="kpi-badge {badge4_class}" style="visibility: {visibility_style};">
            +{best_pl:,.2f}%
        </div>
    </div>
    
</div>""".strip()
st.html(html_content)


# --- SEZIONE CHARTS (HISTORY & COMPOSITION) ---
# Dividiamo lo schermo in due colonne principali (2/3 storic, 1/3 ciambella)
col_chart_left, col_chart_right = st.columns([2, 1], gap="large")

# 1. GRAFICO EVOLUZIONE (LEFT)
with col_chart_left:
    st.markdown("<h3 style='color: white; font-size: 1.2rem; font-weight: 600; margin-bottom: 20px;'>Portfolio History</h3>", unsafe_allow_html=True)
    
    # history_data è già stato caricato sopra, ma se vogliamo rifarlo per sicurezza:
    # (Meglio usare quello già caricato per performance)
    
    if not history_data:
        st.info("Nessun dato storico trovato. Usa il pulsante 'Salva Snapshot' nella sidebar.")
    else:
        df_hist = pd.DataFrame(history_data)
        df_hist['date'] = pd.to_datetime(df_hist['date'])
        df_hist = df_hist.sort_values('date')
        
        # FIX: Filtriamo record "sporchi" che sballano le percentuali (dust values)
        df_hist['total_value'] = df_hist['total_value'].astype(float)
        
        # Troviamo il primo punto "significativo" per evitare il bug 100k%
        # Saliamo a 100$ per essere più sicuri se l'utente ha conti piccoli di prova
        df_significant = df_hist[df_hist['total_value'] > 100.0]
        
        if df_significant.empty:
            # Se nessuno è > 100, prendiamo quello che c'è > 0.1
            df_significant = df_hist[df_hist['total_value'] > 0.1]
            
        if df_significant.empty:
            st.warning("Dati storici insufficienti per il grafico.")
        else:
            # Usiamo solo i dati a partire dal primo punto significativo
            df_plot = df_hist[df_hist['date'] >= df_significant.iloc[0]['date']].copy()
            
            # Calcolo Rendimento Semplice (Relative Growth)
            baseline_val = float(df_plot.iloc[0]['total_value'])
            df_plot['return_perc'] = df_plot['total_value'].apply(
                lambda x: round(((float(x) / baseline_val) - 1) * 100, 2) if baseline_val > 0 else 0
            )
            
            # --- PLOTLY DUAL AXIS CHART ---
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            fig_hist = make_subplots(specs=[[{"secondary_y": True}]])

            # 1. Area Chart per Valore Assoluto ($)
            fig_hist.add_trace(
                go.Scatter(
                    x=df_plot['date'], 
                    y=df_plot['total_value'],
                    name="Valore ($)",
                    fill='tozeroy',
                    line=dict(color='rgba(162, 89, 255, 0.3)', width=1),
                    hovertemplate="Valore: $%{y:,.2f}<extra></extra>"
                ),
                secondary_y=False,
            )

            # 2. Line Chart per Rendimento (%)
            fig_hist.add_trace(
                go.Scatter(
                    x=df_plot['date'], 
                    y=df_plot['return_perc'],
                    name="Rendimento (%)",
                    line=dict(color='#a259ff', width=3, shape='spline'),
                    hovertemplate="Rendimento: %{y:.2f}%<extra></extra>"
                ),
                secondary_y=True,
            )

        fig_hist.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0),
            hovermode="x unified",
            showlegend=False,
            xaxis=dict(
                showgrid=False,
                color="#8c8d92",
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(label="ALL", step="all")
                    ]),
                    bgcolor="#1a1b1f",
                    activecolor="#2d2e32",
                    font=dict(color="white", size=10)
                )
            ),
            yaxis=dict(
                title="", # Wealth
                showgrid=True,
                gridcolor='#2d2e32',
                gridwidth=1,
                griddash='dash',
                color="#8c8d92",
                tickprefix="$"
            ),
            yaxis2=dict(
                title="", # Return
                showgrid=False,
                color="#a259ff",
                ticksuffix="%"
            ),
            height=400
        )
        
        # Card contenitore stilizzata
        con = st.container(border=True)
        with con:
            st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})

# 2. GRAFICO CIAMBELLA (RIGHT)
with col_chart_right:
    st.markdown("<h3 style='color: white; font-size: 1.2rem; font-weight: 600; margin-bottom: 20px;'>Portfolio Composition</h3>", unsafe_allow_html=True)
    
    if not port_data['items']:
         st.info("Portafoglio vuoto.")
    else:
        df_port = pd.DataFrame(port_data['items'])
        
        # Raggruppa per Ticker per mostrare i componenti individuali
        df_comp = df_port.groupby('ticker')['total_value'].sum().reset_index()
        
        # Colori personalizzati vivaci
        custom_colors = ['#00C853', '#0091EA', '#FFAB00', '#B388FF', '#FF5252', '#00BFA5', '#FF4081']
        
        fig_donut = px.pie(
            df_comp, 
            values='total_value', 
            names='ticker',
            hole=0.7,
            color_discrete_sequence=custom_colors
        )
        
        fig_donut.update_traces(
            textposition='inside',
            textinfo='percent', # Mostriamo le percentuali come richiesto
            hovertemplate="<b>%{label}</b><br>Value: $%{value:,.2f}<br>Weight: %{percent}<extra></extra>",
            marker=dict(line=dict(color='#1a1b1f', width=2)) # Bordo tra le fette
        )
        
        fig_donut.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.1,
                xanchor="center",
                x=0.5,
                font=dict(color="#8c8d92", size=11)
            ),
            height=350
        )
        
        con2 = st.container(border=True)
        with con2:
            st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
            
st.markdown("---")

# --- TABELLA PORTAFOGLIO & RIBILANCIAMENTO (Mantenuto ma pulito) ---
st.subheader("Holdings & Rebalancing")

if not port_data['items']:
    st.info("Aggiungi asset dalla sidebar per iniziare.")
else:
    df = pd.DataFrame(port_data['items'])
    ac_current_values = df.groupby('asset_class_id')['total_value'].sum().to_dict()
    
    portfolio_display = []
    rebalance_warnings = []
    
    for _, row in df.iterrows():
        ac_id = row['asset_class_id']
        ac_info = ac_dict.get(ac_id, {"name": "Sconosciuta", "target_percentage": 0.0})
        
        ac_current_weight = (ac_current_values.get(ac_id, 0) / port_data['total_current_value'] * 100) if port_data['total_current_value'] > 0 else 0
        target_weight = ac_info['target_percentage']
        
        deviation = ac_current_weight - target_weight
        needs_rebalance = abs(deviation) > rebalance_tolerance
        
        if needs_rebalance:
            status = "🚨 Sbilanciato" 
            if deviation < 0:
                rebalance_warnings.append(f"**{ac_info['name']}** è sotto-pesata ({ac_current_weight:.1f}% vs {target_weight:.1f}%)")
            else:
                rebalance_warnings.append(f"**{ac_info['name']}** è sovra-pesata ({ac_current_weight:.1f}% vs {target_weight:.1f}%)")
        else:
            status = "✅ OK"
            
        portfolio_display.append({
            "ID": row['id'], 
            "Ticker": row['ticker'],
            "Nome": row['name'][:30] + "..." if len(row['name']) > 30 else row['name'],
            "Categoria": ac_info['name'],
            "Quantità": row['quantity'],
            "Prezzo ($)": f"{row['current_price']:.2f}",
            "Valore ($)": row['total_value'],
            "P/L (%)": row['pl_perc'],
            "Status": status
        })
        
    df_display = pd.DataFrame(portfolio_display)
    
    def color_pl(val):
        color = '#00e676' if val > 0 else '#ff3d71' if val < 0 else 'gray'
        return f'color: {color}'
        
    def highlight_status(val):
        color = 'rgba(255, 61, 113, 0.2)' if "Sbilanciato" in str(val) else ''
        return f'background-color: {color}'

    styled_df = df_display.drop(columns=['ID']).style.format({
        "Valore ($)": "{:,.2f}",
        "P/L (%)": "{:,.2f}%"
    }).map(color_pl, subset=['P/L (%)']).map(highlight_status, subset=['Status'])
        
    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=min(400, (len(df_display)+1)*35 + 40))
    
    # Edit / Delete riga
    with st.expander("Modifica / Elimina Posizione"):
        selected_item = st.selectbox(
            "Seleziona Ticker da gestire", 
            options=[0] + port_data['items'], 
            format_func=lambda x: "Seleziona..." if x==0 else x['ticker']
        )
        
        if selected_item != 0:
            st.markdown(f"### Gestione **{selected_item['ticker']}**")
            col_u1, col_u2 = st.columns(2)
            
            new_qty = col_u1.number_input(
                "Nuova Quantità", 
                value=float(selected_item['quantity']), 
                step=0.01, 
                format="%.6f"
            )
            new_avg = col_u2.number_input(
                "Nuovo Prezzo Medio ($)", 
                value=float(selected_item['avg_price']), 
                step=0.01
            )
            
            # Permetti anche di cambiare categoria
            ac_options = asset_classes
            current_ac_index = 0
            for i, ac in enumerate(ac_options):
                if ac['id'] == selected_item['asset_class_id']:
                    current_ac_index = i
                    break
            
            new_ac = st.selectbox(
                "Sposta in Categoria", 
                options=ac_options, 
                index=current_ac_index,
                format_func=lambda x: x['name']
            )
            
            btn_col1, btn_col2 = st.columns([1, 1])
            
            if btn_col1.button("💾 Aggiorna Posizione", use_container_width=True):
                res = db.update_portfolio_item(user_id, selected_item['id'], new_qty, new_avg, new_ac['id'], token=user_token)
                st.cache_data.clear() # Svuota TUTTA la cache
                st.success("Modifica inviata! Ricaricamento in corso...")
                st.rerun()
                
            if btn_col2.button("🗑️ Elimina Definitivamente", use_container_width=True):
                db.delete_portfolio_item(user_id, selected_item['id'], token=user_token)
                st.cache_data.clear()
                st.rerun()
            
    # --- MODULO PAC / RIBILANCIAMENTO ---
    st.markdown("---")
    st.subheader("Smart Rebalancing Actions")
    
    col_pac1, col_pac2 = st.columns([1, 2])
    
    with col_pac1:
        if rebalance_warnings:
            st.warning("⚠️ Tolleranza Superata (±" + str(rebalance_tolerance) + "%)")
            for w in set(rebalance_warnings):
                st.write(f"- {w}")
        else:
            st.success(f"Portafoglio bilanciato (±{rebalance_tolerance}%).")
            
        pac_amount = st.number_input("Nuova liquidità ($)", min_value=0.0, step=100.0)
    
    with col_pac2:
        st.write("📊 **Suggerimenti Ribilanciamento:**")
        
        # LOGICA: (Valore Attuale + Nuova Liquidità) * Target%
        total_future_value = port_data['total_current_value'] + pac_amount
        rebalance_actions = []
        
        for ac in asset_classes:
            ac_id = ac['id']
            target_val = total_future_value * (ac['target_percentage'] / 100.0)
            current_val = ac_current_values.get(ac_id, 0)
            diff = target_val - current_val
            
            # Soglia minima di fuffa (es. $1) per non suggerire micro-transazioni
            if abs(diff) > 1.0:
                rebalance_actions.append({
                    "Azione": "🟢 Compra" if diff > 0 else "🔴 Vendi",
                    "Categoria": ac['name'],
                    "Importo ($)": abs(diff)
                })
        
        if rebalance_actions:
            df_reb = pd.DataFrame(rebalance_actions)
            
            def color_actions(val):
                if "Compra" in str(val): return 'color: #00e676'
                if "Vendi" in str(val): return 'color: #ff3d71'
                return ''

            st.dataframe(
                df_reb.style.format({"Importo ($)": "{:,.2f}"}).map(color_actions, subset=['Azione']),
                use_container_width=True, hide_index=True
            )
            
            if pac_amount == 0:
                st.caption("ℹ️ *I suggerimenti sopra presuppongono la vendita di asset in eccesso per finanziare gli acquisti sottopesati.*")
            else:
                st.caption(f"ℹ️ *Suggerimenti ottimizzati includendo i ${pac_amount:,.2f} di nuova liquidità.*")
        else:
            st.info("Nessuna azione necessaria. Il portafoglio è perfettamente allineato.")

# EOF
