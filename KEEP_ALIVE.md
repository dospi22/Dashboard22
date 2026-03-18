# Come mantenere la Dashboard sempre attiva 🚀

La tua dashboard è ospitata su **Streamlit Community Cloud**, che mette in "pausa" le applicazioni se non ricevono visite per **7 giorni consecutivi**. In alcuni casi, questo può accadere anche più frequentemente.

Per evitare che questo accada, abbiamo implementato un sistema di **automazione tramite GitHub Actions** che visita il sito per te ogni ora.

### Configurazione (DA FARE UNA VOLTA)

Per attivare l'automazione, segui questi passaggi sul tuo repository GitHub:

1. Vai su **Settings** (Impostazioni) del tuo repository su GitHub.
2. Nella barra laterale sinistra, clicca su **Secrets and variables** -> **Actions**.
3. Clicca sul pulsante verde **"New repository secret"**.
4. Inserisci i seguenti dati:
   - **Name**: `DASHBOARD_URL`
   - **Secret**: Inserisci l'URL della tua dashboard (es. `https://tuo-app.streamlit.app`)
5. Clicca su **Add secret**.

Fatto! GitHub Actions ora visiterà la tua dashboard ogni ora, mantenendola "sveglia" a tempo indefinito.

### Alternativa: UptimeRobot (Gratis)

Se preferisci un servizio esterno:
1. Crea un account su [uptimerobot.com](https://uptimerobot.com/).
2. Aggiungi un monitor di tipo **HTTP(s)** con l'URL della tua dashboard.
3. Imposta un intervallo di monitoraggio di 1 ora.

---

> [!TIP]
> **Perché succede?** Streamlit Cloud è un servizio gratuito. Se un'app non viene usata, viene "addormentata" per risparmiare risorse. Il "ping" di GitHub Actions simula una visita, resettando il timer di inattività.

