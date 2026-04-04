import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Configurazione iniziale della pagina (Icona aggiornata con il link diretto)
st.set_page_config(
    page_title="Amazon SWAG 2026", 
    page_icon="https://github.com/Davidelfo86/amazon-swag/blob/main/dlo8.png?raw=true", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# 2. CSS Amazon Style & Logo Telefono (Con link diretto)
st.markdown("""
    <link rel="apple-touch-icon" href="https://github.com/Davidelfo86/amazon-swag/blob/main/dlo8.png?raw=true">
    <link rel="icon" href="https://github.com/Davidelfo86/amazon-swag/blob/main/dlo8.png?raw=true">
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stAppDeployButton {display:none;} [data-testid="stSidebar"] {display: none;}
    .stButton>button { background-color: #FF9900; color: #232F3E; border-radius: 8px; font-weight: bold; width: 100%; height: 3.5em; border: none; }
    .stButton>button:hover { background-color: #e68a00; color: white; }
    div[data-testid="stMetricValue"] { color: #FF9900; font-size: 3rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #f0f2f6; border-radius: 5px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Dizionario Attività (Pannello Manager)
ATTIVITA_PREMI = {
    "Peak Hero (+5)": 5, "Prime Day Hero (+3)": 3, "GB/BB Conversion (+6)": 6,
    "Active Ambassador (+3)": 3, "Night activities / Gemba Walk (+3)": 3, "Fun Events (+3)": 3,
    "Away Team member (+15)": 15, "Voice of Associates best idea (+10)": 10, 
    "Gold NOV (+2)": 2, "Silver NOV (+1)": 1, 
    "Kaizen Idea Implementation (+10)": 10, "Safety Hero (+10)": 10,
    "Happy Birthday (+5)": 5, "Delivery Station Birthday (+3)": 3, 
    "WW Scorecard Top 10 (+7)": 7, "Buddy DS (+5)": 5, 
    "Kaizen Sustainability Idea (+1)": 1, "Kaizen Sustainability Implementation (+3)": 3
}

# 4. Funzione per sincronizzare il totale nel foglio Anagrafica
def sync_totale(nome, cognome, punti):
    try:
        df = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
        mask = (df['Nome'].astype(str).str.lower() == str(nome).lower()) & (df['Cognome'].astype(str).str.lower() == str(cognome).lower())
        if not df[mask].empty:
            df.loc[mask, 'Punti_Totali'] = punti
            conn.update(worksheet="Anagrafica", data=df)
    except: pass

# 5. Gestione Sessione e Auto-Login
if 'user_auth' not in st.session_state:
    p = st.query_params
    st.session_state.user_auth = {"Nome": p["user_n"], "Cognome": p["user_c"]} if "user_n" in p else None

# --- PAGINA 1: LOGIN E REGISTRAZIONE ---
if st.session_state.user_auth is None:
    # IL TUO LOGO DENTRO L'APP
    st.image("https://github.com/Davidelfo86/amazon-swag/blob/main/dlo8.png?raw=true", width=150)
    st.title("SWAG PROGRAM 2026")
    st.markdown("""
    ### Benvenuto nel portale SWAG!
    Riconosciamo il tuo impegno. Accumula punti e scopri i vantaggi riservati ai migliori.
    """)
    
    t_login, t_iscr = st.tabs(["🔑 ACCEDI", "📝 ISCRIVITI"])
    
    with t_login:
        with st.form("login"):
            n, c = st.text_input("Nome").strip(), st.text_input("Cognome").strip()
            if st.form_submit_button("ENTRA NEL TUO PROFILO"):
                df_a = conn.read(worksheet="Anagrafica", ttl=0)
                if not df_a[(df_a['Nome'].astype(str).str.lower() == n.lower()) & (df_a['Cognome'].astype(str).str.lower() == c.lower())].empty:
                    st.session_state.user_auth = {"Nome": n, "Cognome": c}
                    st.query_params["user_n"], st.query_params["user_c"] = n, c
                    st.rerun()
                else: st.error("Account non trovato. Controlla i dati o iscriviti.")
    
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

# --- PAGINA 2: DASHBOARD UTENTE & PANNELLO MANAGER ---
else:
    u = st.session_state.user_auth
    
    # Lettura Log_Punti e Calcolo Saldo
    df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all").fillna("")
    if not df_log.empty and 'Nome' in df_log.columns and 'Cognome' in df_log.columns:
        storico = df_log[(df_log['Nome'].astype(str).str.lower() == u['Nome'].lower()) & (df_log['Cognome'].astype(str).str.lower() == u['Cognome'].lower())]
        totale = int(pd.to_numeric(storico['Punti_Assegnati'], errors='coerce').sum())
    else:
        storico = pd.DataFrame()
        totale = 0
        
    # Allineamento con il foglio Anagrafica
    sync_totale(u['Nome'], u['Cognome'], totale)

    st.title(f"Ciao, {u['Nome']}! 👋")

    # --- PANNELLO MANAGER SEGRETO (Solo per Davide Salemi) ---
    if u['Nome'].lower() == "davide" and u['Cognome'].lower() == "salemi":
        with st.expander("🛠️ PANNELLO MANAGER (Riservato)", expanded=True):
            st.write("Da qui puoi assegnare i punti ai dipendenti in modo ufficiale.")
            df_ana = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all")
            nomi_colleghi = (df_ana['Nome'].astype(str) + " " + df_ana['Cognome'].astype(str)).tolist()
            
            collega = st.selectbox("A chi vuoi assegnare i punti?", nomi_colleghi)
            azione = st.selectbox("Seleziona attività ufficiale:", list(ATTIVITA_PREMI.keys()))
            
            if st.button("ASSEGNA PUNTI AL DIPENDENTE"):
                n_c, c_c = collega.split(" ", 1)
                pts = ATTIVITA_PREMI[azione]
                new_row = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Nome": n_c, "Cognome": c_c,
                    "Punti_Assegnati": pts,
                    "Attività": azione.split(" (")[0]
                }])
                conn.update(worksheet="Log_Punti", data=pd.concat([df_log, new_row], ignore_index=True))
                st.success(f"Fatto! {pts} punti inviati a {n_c} {c_c}.")
                st.balloons()
                st.rerun()

    # --- INTERFACCIA STANDARD PER TUTTI ---
    st.metric("IL TUO SALDO SWAG", f"{totale} Punti")
    
    col1, col2 = st.columns(2)
    with col1: 
        if st.button("🔄 AGGIORNA SALDO"): st.rerun()
    with col2:
        if st.button("🚪 ESCI"):
            st.query_params.clear()
            st.session_state.user_auth = None
            st.rerun()

    t_st, t_rg = st.tabs(["📋 STORICO ATTIVITÀ", "📜 REGOLAMENTO 2026"])
    
    with t_st:
        if not storico.empty: 
            st.dataframe(storico[["Data", "Punti_Assegnati", "Attività"]][::-1], use_container_width=True, hide_index=True)
        else: 
            st.info("Non hai ancora attività registrate. Partecipa agli eventi per guadagnare punti!")
    
    # --- REGOLAMENTO COMPLETO ---
    with t_rg:
        st.subheader("Come guadagnare punti")
        
        regole = {
            "🤝 HR & PERSONAL DEVELOPMENT": [
                ("Peak Hero", "Per chi ha partecipato al periodo di Peak", 5),
                ("Prime Day Hero", "Per chi ha partecipato al Prime Day", 3),
                ("GB/BB Conversion", "Per gli SA che passano da Green Badge a Blue Badge", 6),
                ("Active Ambassador", "Per chi partecipa come ambassador attivo almeno una volta al mese", 3),
                ("Night activities / Gemba Walk", "Per gli SA che partecipano alla Gemba Walk mensile o attività notturne", 3),
                ("Fun Events", "Per tutti gli SA che partecipano attivamente agli eventi Fun", 3),
                ("Away Team member", "Per i membri dell'Away team per il lancio di una nuova DS", 15),
                ("Voice of Associates best idea", "Per l'SA che propone la migliore idea di miglioramento tramite bacheca VOA", 10)
            ],
            "⭐ QUALITY": [
                ("Gold NOV", "Se la DS mantiene un risultato mensile NOV sotto i 15 DPMO (per tutti)", 2),
                ("Silver NOV", "Se la DS mantiene un risultato mensile NOV sotto i 30 DPMO (per tutti)", 1)
            ],
            "🦺 SAFETY": [
                ("Kaizen Idea Implementation", "Implementazione concreta di un'idea Kaizen", 10),
                ("Safety Hero", "Premio meritato per l'eroe Safety del mese", 10)
            ],
            "🏢 DELIVERY STATION DEVELOPMENT": [
                ("Happy Birthday", "Auguri dal team SWAG per il tuo compleanno", 5),
                ("Delivery Station Birthday", "Per tutti i dipendenti nell'anniversario dell'apertura della DS", 3),
                ("WW Scorecard Top 10", "Per aver contribuito a raggiungere la TOP 10 mondiale nella scorecard", 7),
                ("Buddy DS", "Per i membri che aiutano a formare i neo-assunti lanciando un nuovo sito", 5)
            ],
            "🌱 SUSTAINABILITY": [
                ("Kaizen Sustainability Idea", "Per proposte Kaizen sulla sostenibilità valutate dal team OPS", 1),
                ("Kaizen Sustainability Implementation", "Implementazione concreta di un'idea Kaizen sulla sostenibilità", 3)
            ]
        }

        for categoria, voci in regole.items():
            with st.expander(categoria):
                for titolo, desc, punti in voci:
                    st.markdown(f"**{titolo}** ➔ **+{punti} Swaggies** \n*{desc}*")

    st.caption("Amazon SWAG Program 2026 - Piattaforma Ufficiale")
