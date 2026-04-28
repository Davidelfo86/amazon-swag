import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Configurazione
st.set_page_config(
    page_title="Amazon SWAG 2026", 
    page_icon="https://github.com/Davidelfo86/amazon-swag/blob/main/dlo8.png?raw=true", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# 2. CSS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stAppDeployButton {display:none;} [data-testid="stSidebar"] {display: none;}
    .stButton>button { background-color: #FF9900; color: #232F3E; border-radius: 8px; font-weight: bold; width: 100%; height: 3.5em; border: none; }
    div[data-testid="stMetricValue"] { color: #FF9900; font-size: 3rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #f0f2f6; border-radius: 5px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Attività
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

# 4. Auth
if 'user_auth' not in st.session_state:
    p = st.query_params
    st.session_state.user_auth = {"Nome": p["user_n"], "Cognome": p["user_c"]} if "user_n" in p else None

# --- LOGIN / REGISTRAZIONE ---
if st.session_state.user_auth is None:
    st.image("https://github.com/Davidelfo86/amazon-swag/blob/main/dlo8.png?raw=true", width=150)
    st.title("SWAG PROGRAM 2026")
    t_login, t_iscr = st.tabs(["🔑 ACCEDI", "📝 ISCRIVITI"])
    
    with t_login:
        with st.form("login"):
            n_in = st.text_input("Nome").strip(); c_in = st.text_input("Cognome").strip(); p_in = st.text_input("Password", type="password").strip()
            if st.form_submit_button("ENTRA"):
                df_a = conn.read(worksheet="Anagrafica", ttl=0).fillna("")
                user = df_a[(df_a['Nome'].str.lower() == n_in.lower()) & (df_a['Cognome'].str.lower() == c_in.lower())]
                if not user.empty and (str(user.iloc[0]['Password']) == "" or p_in == str(user.iloc[0]['Password'])):
                    st.session_state.user_auth = {"Nome": n_in, "Cognome": c_in}
                    st.query_params.update(user_n=n_in, user_c=c_in); st.rerun()
                else: st.error("Dati errati")

    with t_iscr:
        with st.form("reg"):
            rn = st.text_input("Nome"); rc = st.text_input("Cognome"); rp = st.text_input("Password", type="password")
            if st.form_submit_button("CREA PROFILO"):
                df_a = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
                if rn and rc and rp:
                    new_u = pd.DataFrame([{"Nome":rn, "Cognome":rc, "Password":rp, "Punti_Totali":0}])
                    conn.update(worksheet="Anagrafica", data=pd.concat([df_a, new_u], ignore_index=True))
                    st.success("Creato! Accedi ora.")

# --- DASHBOARD ---
else:
    u = st.session_state.user_auth
    df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all").fillna("")
    storico = df_log[(df_log['Nome'].str.lower() == u['Nome'].lower()) & (df_log['Cognome'].str.lower() == u['Cognome'].lower())]
    totale = int(pd.to_numeric(storico['Punti_Assegnati'], errors='coerce').sum())
        
    st.title(f"Ciao, {u['Nome']}! 👋")
    st.metric("IL TUO SALDO SWAG", f"{totale} Punti")

    # --- PANNELLO MANAGER ---
    ADMINS = [("davide", "salemi"), ("massimo", "borella"), ("angelo", "nisselino")]
    if (u['Nome'].lower(), u['Cognome'].lower()) in ADMINS:
        with st.expander("🛠️ PANNELLO MANAGER", expanded=False):
            df_ana = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
            
            # ASSEGNAZIONE
            collega = st.selectbox("Dipendente:", (df_ana['Nome'] + " " + df_ana['Cognome']).tolist())
            azione = st.selectbox("Attività:", list(ATTIVITA_PREMI.keys()))
            
            if st.button("CONFERMA ASSEGNAZIONE"):
                n_c, c_c = collega.split(" ", 1)
                pts = ATTIVITA_PREMI[azione]
                
                # 1. Scrittura Log
                new_entry = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y"), "Nome": n_c, "Cognome": c_c, "Punti_Assegnati": pts, "Attività": azione.split(" (")[0], "Assegnato_da": f"{u['Nome']} {u['Cognome']}"}])
                df_log_up = pd.concat([df_log, new_entry], ignore_index=True)
                conn.update(worksheet="Log_Punti", data=df_log_up)
                
                # 2. AGGIORNAMENTO AUTOMATICO TOTALE IN ANAGRAFICA (IMPORTANTE!)
                idx = df_ana[(df_ana['Nome'] == n_c) & (df_ana['Cognome'] == c_c)].index[0]
                df_ana.at[idx, 'Punti_Totali'] = int(pd.to_numeric(df_log_up[(df_log_up['Nome']==n_c) & (df_log_up['Cognome']==c_c)]['Punti_Assegnati']).sum())
                conn.update(worksheet="Anagrafica", data=df_ana)
                
                st.success("Punti registrati e Anagrafica aggiornata!"); st.rerun()

            # RIEPILOGO
            st.markdown("---")
            st.markdown("#### 📊 Situazione Punti Globale")
            df_sum = df_log_up.groupby(['Nome', 'Cognome'])['Punti_Assegnati'].sum().reset_index() if 'df_log_up' in locals() else df_log.groupby(['Nome', 'Cognome'])['Punti_Assegnati'].sum().reset_index()
            st.dataframe(df_sum.sort_values(by='Punti_Assegnati', ascending=False), use_container_width=True, hide_index=True)

    # --- TABS ---
    t_st, t_rg = st.tabs(["📋 STORICO", "📜 REGOLAMENTO"])
    with t_st:
        if not storico.empty: st.dataframe(storico[["Data", "Punti_Assegnati", "Attività", "Assegnato_da"]][::-1], use_container_width=True, hide_index=True)
        else: st.info("Nessuna attività.")
    
    with t_rg:
        st.subheader("🎯 Regole")
        c1, c2 = st.columns(2)
        with c1:
            with st.expander("🚀 EVENTI", expanded=True): st.write("**Peak Hero**: +5 pts"); st.write("**Away Team**: +15 pts")
        with c2:
            with st.expander("🛡️ SAFETY", expanded=True): st.write("**Safety Hero**: +10 pts"); st.write("**Gold NOV**: +2 pts")

    if st.button("🚪 ESCI"):
        st.query_params.clear(); st.session_state.user_auth = None; st.rerun()
