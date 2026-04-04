import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configurazione iniziale
st.set_page_config(page_title="Amazon SWAG 2026", page_icon="📦", layout="centered", initial_sidebar_state="collapsed")

# CSS Amazon Style (Nasconde tutto il superfluo)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stAppDeployButton {display:none;} [data-testid="stSidebar"] {display: none;}
    .stButton>button { background-color: #FF9900; color: #232F3E; border-radius: 8px; font-weight: bold; width: 100%; height: 3.5em; border: none; }
    div[data-testid="stMetricValue"] { color: #FF9900; font-size: 3rem !important; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# Elenco Attività e Punti
ATTIVITA_PREMI = {
    "Peak Hero (+5)": 5, "Prime Day Hero (+3)": 3, "GB/BB Conversion (+6)": 6,
    "Active Ambassador (+3)": 3, "Gemba Walk (+3)": 3, "Fun Events (+3)": 3,
    "Away Team (+15)": 15, "VOA Best Idea (+10)": 10, "Gold NOV (+2)": 2,
    "Silver NOV (+1)": 1, "Kaizen Implementation (+10)": 10, "Safety Hero (+10)": 10,
    "Happy Birthday (+5)": 5, "DS Anniversary (+3)": 3, "Top 10 Scorecard (+7)": 7,
    "Buddy DS (+5)": 5, "Sustainability Idea (+1)": 1, "Sustainability Impl. (+3)": 3
}

# Funzione per sincronizzare il totale nel foglio Anagrafica (Corretta con astype)
def sync_totale(nome, cognome, punti):
    try:
        df = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
        mask = (df['Nome'].astype(str).str.lower() == str(nome).lower()) & (df['Cognome'].astype(str).str.lower() == str(cognome).lower())
        if not df[mask].empty:
            df.loc[mask, 'Punti_Totali'] = punti
            conn.update(worksheet="Anagrafica", data=df)
    except: pass

# Gestione Sessione e Auto-Login
if 'user_auth' not in st.session_state:
    p = st.query_params
    st.session_state.user_auth = {"Nome": p["user_n"], "Cognome": p["user_c"]} if "user_n" in p else None

# --- FLUSSO PAGINE ---
if st.session_state.user_auth is None:
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", width=120)
    st.title("SWAG PROGRAM 2026")
    t_login, t_iscr = st.tabs(["🔑 ACCEDI", "📝 ISCRIVITI"])
    
    with t_login:
        with st.form("login"):
            n, c = st.text_input("Nome").strip(), st.text_input("Cognome").strip()
            if st.form_submit_button("ENTRA"):
                df_a = conn.read(worksheet="Anagrafica", ttl=0)
                # Corretto con astype(str)
                if not df_a[(df_a['Nome'].astype(str).str.lower() == n.lower()) & (df_a['Cognome'].astype(str).str.lower() == c.lower())].empty:
                    st.session_state.user_auth = {"Nome": n, "Cognome": c}
                    st.query_params["user_n"], st.query_params["user_c"] = n, c
                    st.rerun()
                else: st.error("Account non trovato.")
    
    with t_iscr:
        with st.form("reg"):
            rn, rc, re = st.text_input("Nome").strip(), st.text_input("Cognome").strip(), st.text_input("Email")
            if st.form_submit_button("CREA PROFILO"):
                if rn and rc:
                    df_a = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
                    new = pd.DataFrame([{"Nome":rn, "Cognome":rc, "Email":re, "Punti_Totali":0}])
                    conn.update(worksheet="Anagrafica", data=pd.concat([df_a, new], ignore_index=True))
                    st.session_state.user_auth = {"Nome":rn, "Cognome":rc}
                    st.query_params["user_n"], st.query_params["user_c"] = rn, rc
                    st.rerun()

else:
    u = st.session_state.user_auth
    
    # Caricamento Dati (Corretto con astype)
    df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all").fillna("")
    if not df_log.empty and 'Nome' in df_log.columns and 'Cognome' in df_log.columns:
        storico = df_log[(df_log['Nome'].astype(str).str.lower() == u['Nome'].lower()) & (df_log['Cognome'].astype(str).str.lower() == u['Cognome'].lower())]
        totale = int(pd.to_numeric(storico['Punti_Assegnati'], errors='coerce').sum())
    else:
        storico = pd.DataFrame()
        totale = 0
        
    sync_totale(u['Nome'], u['Cognome'], totale)

    st.title(f"Ciao, {u['Nome']}! 👋")

    # --- PANNELLO MANAGER (SOLO PER DAVIDE SALEMI) ---
    if u['Nome'].lower() == "davide" and u['Cognome'].lower() == "salemi":
        with st.expander("🛠️ PANNELLO MANAGER", expanded=True):
            df_ana = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all")
            nomi_colleghi = (df_ana['Nome'].astype(str) + " " + df_ana['Cognome'].astype(str)).tolist()
            
            collega = st.selectbox("A chi vuoi assegnare i punti?", nomi_colleghi)
            azione = st.selectbox("Seleziona attività:", list(ATTIVITA_PREMI.keys()))
            
            if st.button("ASSEGNA PUNTI"):
                n_c, c_c = collega.split(" ", 1)
                pts = ATTIVITA_PREMI[azione]
                new_row = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Nome": n_c, "Cognome": c_c,
                    "Punti_Assegnati": pts,
                    "Attività": azione.split(" (")[0]
                }])
                conn.update(worksheet="Log_Punti", data=pd.concat([df_log, new_row], ignore_index=True))
                st.success(f"Fatto! {pts} punti inviati a {n_c}.")
                st.balloons()
                st.rerun()

    # --- VISUALIZZAZIONE UTENTE ---
    st.metric("IL TUO SALDO SWAG", f"{totale} Punti")
    
    col1, col2 = st.columns(2)
    with col1: 
        if st.button("🔄 AGGIORNA"): st.rerun()
    with col2:
        if st.button("🚪 ESCI"):
            st.query_params.clear()
            st.session_state.user_auth = None
            st.rerun()

    t_st, t_rg = st.tabs(["📋 STORICO", "📜 REGOLAMENTO"])
    with t_st:
        if not storico.empty: st.dataframe(storico[["Data", "Punti_Assegnati", "Attività"]][::-1], use_container_width=True, hide_index=True)
        else: st.info("Ancora nessun punto registrato.")
    
    with t_rg:
        st.subheader("Come guadagnare punti")
        for c, items in {"HR": [("Peak Hero", 5)], "Safety": [("Safety Hero", 10)]}.items():
            with st.expander(c):
                for n, p in items: st.write(f"**{n}** ➔ +{p} Punti")

    st.caption("Amazon SWAG 2026")
