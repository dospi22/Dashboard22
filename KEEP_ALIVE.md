# Come mantenere la Dashboard sempre attiva 🚀

La tua dashboard è ospitata su **Streamlit Community Cloud**, che mette in "pausa" le applicazioni se non ricevono visite per **7 giorni consecutivi**.

Per evitare che questo accada, puoi usare un servizio di "ping" gratuito che visita automaticamente il tuo sito ogni giorno.

### Opzione Consigliata: UptimeRobot (Gratis)

1. Vai su [uptimerobot.com](https://uptimerobot.com/) e crea un account gratuito.
2. Clicca su **"Add New Monitor"**.
3. Configura come segue:
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `WealthFlow Dashboard`
   - **URL (or IP)**: Inserisci l'URL della tua dashboard (es. `https://tuo-app.streamlit.app`)
   - **Monitoring Interval**: `Ogni 24 ore` (è sufficiente una volta al giorno per resettare il timer di inattività).
4. Clicca su **"Create Monitor"**.

### Perché succede?
Streamlit Cloud è un servizio gratuito che ottimizza le risorse. Se un'app non viene usata, viene "addormentata" per risparmiare energia. Questi servizi di ping simulano una visita, mantenendo l'app "sveglia" a tempo indefinito.

> [!TIP]
> Se ricevi un'email da Streamlit che dice "Your app has been put to sleep", clicca semplicemente sul link nell'email per riattivarla, oppure visita l'URL dell'app. Una volta configurato UptimeRobot, non dovresti più ricevere queste email.
