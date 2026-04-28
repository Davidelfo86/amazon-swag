import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Configurazione Iniziale
st.set_page_config(
    page_title="Amazon SWAG 2026", 
    page_icon="https://github.com/Davidelfo86/amazon-swag/blob/main/dlo8.png?raw=true", 
    layout="centered"
)

# 2. CSS Amazon Style
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stAppDeployButton {display:none;} [data-testid="stSidebar"] {display: none;}
    .stButton>button { background-color: #FF9900; color: #232F3E; border-radius: 8px; font-weight: bold; width: 100%; height: 3.5em; border: none; }
    div[data-testid="stMetricValue"] { color: #FF9900; font-size: 3rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #f0f2f6; border-radius: 5px; padding: 10px; }
    /* Stile per il Disclaimer */
    .disclaimer { font-size: 0.8rem; color: #666; font-style: italic; border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Catalogo Attività
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

# 4. Gestione Autenticazione
if 'user_auth' not in st.session_state:
    params = st.query_params
    if "user_n" in params and "user_c" in params:
        st.session_state.user_auth = {"Nome": params["user_n"], "Cognome": params["user_c"]}
    else:
        st.session_state.user_auth = None

# --- FLUSSO LOGIN / REGISTRAZIONE ---
if st.session_state.user_auth is None:
    st.image("https://github.com/Davidelfo86/amazon-swag/blob/main/dlo8.png?raw=true", width=150)
    st.title("SWAG PROGRAM 2026")
    
    # MESSAGGIO DI AVVISO (DISCLAIMER)
    st.info("**Nota sull'iniziativa**: Questa è un'iniziativa indipendente creata per promuovere il coinvolgimento e il divertimento all'interno della Station. Non è un tool ufficiale aziendale né un sistema di valutazione formale.")

    t_log, t_reg = st.tabs(["🔑 ACCEDI", "📝 ISCRIVITI"])
    
    with t_log:
        with st.form("login_form"):
            n_in = st.text_input("Nome").strip()
            c_in = st.text_input("Cognome").strip()
            p_in = st.text_input("Password", type="password").strip()
            if st.form_submit_button("ENTRA"):
                df_a = conn.read(worksheet="Anagrafica", ttl=0).fillna("")
                # FIX: Forza colonne a stringa per evitare AttributeError
                df_a['Nome'] = df_a['Nome'].astype(str)
                df_a['Cognome'] = df_a['Cognome'].astype(str)
                
                u_row = df_a[(df_a['Nome'].str.lower() == n_in.lower()) & (df_a['Cognome'].str.lower() == c_in.lower())]
                if not u_row.empty:
                    pwd_db = str(u_row.iloc[0]['Password']).strip()
                    if pwd_db == "" or p_in == pwd_db:
                        st.session_state.user_auth = {"Nome": n_in, "Cognome": c_in}
                        st.query_params.update(user_n=n_in, user_c=c_in)
                        st.rerun()
                    else: st.error("Password errata.")
                else: st.error("Utente non trovato.")

    with t_reg:
        with st.form("reg_form"):
            rn = st.text_input("Nome").strip()
            rc = st.text_input("Cognome").strip()
            rp = st.text_input("Scegli Password", type="password").strip()
            if st.form_submit_button("CREA PROFILO"):
                if rn and rc and rp:
                    df_a = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
                    df_a['Nome'] = df_a['Nome'].astype(str)
                    df_a['Cognome'] = df_a['Cognome'].astype(str)
                    
                    if not df_a[(df_a['Nome'].str.lower() == rn.lower()) & (df_a['Cognome'].str.lower() == rc.lower())].empty:
                        st.error("Utente già esistente.")
                    else:
                        new_u = pd.DataFrame([{"Nome":rn, "Cognome":rc, "Password":rp, "Punti_Totali":0}])
                        conn.update(worksheet="Anagrafica", data=pd.concat([df_a, new_u], ignore_index=True))
                        st.success("Registrazione completata! Ora puoi accedere.")
                else: st.warning("Compila tutti i campi.")

# --- DASHBOARD UTENTE ---
else:
    u = st.session_state.user_auth
    # Carico i log
    df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all").fillna("")
    
    # FIX: Forza colonne a stringa per il calcolo dello storico
    if not df_log.empty:
        df_log['Nome'] = df_log['Nome'].astype(str)
        df_log['Cognome'] = df_log['Cognome'].astype(str)
        storico = df_log[(df_log['Nome'].str.lower() == str(u['Nome']).lower()) & (df_log['Cognome'].str.lower() == str(u['Cognome']).lower())]
    else:
        storico = pd.DataFrame()

    totale_attuale = int(pd.to_numeric(storico['Punti_Assegnati'], errors='coerce').sum()) if not storico.empty else 0
        
    st.title(f"Ciao, {u['Nome']}! 👋")
    st.metric("IL TUO SALDO SWAG", f"{totale_attuale} Punti")

    # --- PANNELLO MANAGER ---
    ADMINS = [("davide", "salemi"), ("massimo", "borella"), ("angelo", "nisselino")]
    if (u['Nome'].lower(), u['Cognome'].lower()) in ADMINS:
        with st.expander("🛠️ PANNELLO MANAGER", expanded=False):
            df_ana = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
            
            st.markdown("#### ➕ Assegna Punti")
            lista_colleghi = (df_ana['Nome'].astype(str) + " " + df_ana['Cognome'].astype(str)).tolist()
            collega_scelto = st.selectbox("Seleziona dipendente:", lista_colleghi)
            attivita_scelta = st.selectbox("Attività svolta:", list(ATTIVITA_PREMI.keys()))
            
            if st.button("CONFERMA E SINCRONIZZA"):
                nome_c, cognome_c = collega_scelto.split(" ", 1)
                punti_da_dare = ATTIVITA_PREMI[attivita_scelta]
                
                nuova_riga_log = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Nome": nome_c, "Cognome": cognome_c,
                    "Punti_Assegnati": punti_da_dare,
                    "Attività": attivita_scelta.split(" (")[0],
                    "Assegnato_da": f"{u['Nome']} {u['Cognome']}"
                }])
                df_log_nuovo = pd.concat([df_log, nuova_riga_log], ignore_index=True)
                conn.update(worksheet="Log_Punti", data=df_log_nuovo)
                
                nuovo_totale = int(pd.to_numeric(df_log_nuovo[(df_log_nuovo['Nome'] == nome_c) & (df_log_nuovo['Cognome'] == cognome_c)]['Punti_Assegnati']).sum())
                idx_ana = df_ana[(df_ana['Nome'].astype(str) == nome_c) & (df_ana['Cognome'].astype(str) == cognome_c)].index[0]
                df_ana.at[idx_ana, 'Punti_Totali'] = nuovo_totale
                conn.update(worksheet="Anagrafica", data=df_ana)
                
                st.success(f"Punti registrati! Anagrafica aggiornata.")
                st.rerun()

            st.markdown("---")
            st.markdown("#### 📊 Riepilogo Globale (Sola Lettura)")
            if not df_log.empty:
                classifica = df_log.groupby(['Nome', 'Cognome'])['Punti_Assegnati'].sum().reset_index()
                st.dataframe(classifica.sort_values(by='Punti_Assegnati', ascending=False), use_container_width=True, hide_index=True)

    # --- STORICO E REGOLAMENTO ---
    tab_storico, tab_regole = st.tabs(["📋 IL TUO STORICO", "📜 REGOLAMENTO"])
    
    with tab_storico:
        if not storico.empty:
            st.dataframe(storico[["Data", "Punti_Assegnati", "Attività", "Assegnato_da"]][::-1], use_container_width=True, hide_index=True)
        else: st.info("Ancora nessuna attività registrata.")
        
    with tab_regole:
        st.subheader("🎯 Come guadagnare punti")
        c1, c2 = st.columns(2)
        with c1:
            with st.expander("🚀 EVENTI", expanded=True):
                st.write("**Peak Hero**: +5"); st.write("**Away Team**: +15")
        with c2:
            with st.expander("🛡️ SAFETY", expanded=True):
                st.write("**Safety Hero**: +10"); st.write("**Gold NOV**: +2")

    # --- FOOTER ---
    if st.button("🚪 ESCI"):
        st.query_params.clear()
        st.session_state.user_auth = None
        st.rerun()

    # Disclaimer finale piccolo
    st.markdown("""<div class="disclaimer">Questa applicazione è un progetto indipendente a scopo ludico e di engagement interno. Non è un'applicazione ufficiale Amazon.</div>""", unsafe_allow_html=True)
    st.caption("Amazon SWAG 2026 - Versione Gold 🏆")
