import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Configurazione iniziale della pagina
st.set_page_config(
    page_title="Amazon SWAG 2026", 
    page_icon="https://github.com/Davidelfo86/amazon-swag/blob/main/dlo8.png?raw=true", 
    layout="centered", 
    initial_sidebar_state="collapsed"
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
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Dizionario Attività (Usato dal Manager per assegnare punti)
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

# 4. Gestione Sessione
if 'user_auth' not in st.session_state:
    p = st.query_params
    if "user_n" in p and "user_c" in p:
        st.session_state.user_auth = {"Nome": p["user_n"], "Cognome": p["user_c"]}
    else:
        st.session_state.user_auth = None

# --- PAGINA LOGIN (Semplificata per il ripristino) ---
if st.session_state.user_auth is None:
    st.image("https://github.com/Davidelfo86/amazon-swag/blob/main/dlo8.png?raw=true", width=150)
    st.title("SWAG PROGRAM 2026")
    with st.form("login"):
        n = st.text_input("Nome").strip()
        c = st.text_input("Cognome").strip()
        if st.form_submit_button("ACCEDI"):
            st.session_state.user_auth = {"Nome": n, "Cognome": c}
            st.rerun()

# --- DASHBOARD UTENTE ---
else:
    u = st.session_state.user_auth
    df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all").fillna("")
    
    # Calcolo Totale
    storico = df_log[(df_log['Nome'].astype(str).str.lower() == u['Nome'].lower()) & 
                    (df_log['Cognome'].astype(str).str.lower() == u['Cognome'].lower())]
    totale = int(pd.to_numeric(storico['Punti_Assegnati'], errors='coerce').sum())
        
    st.title(f"Ciao, {u['Nome']}! 👋")
    st.metric("IL TUO SALDO SWAG", f"{totale} Punti")

    # --- PANNELLO MANAGER (Lista Admin) ---
    ADMINS = [("davide", "salemi"), ("massimo", "borella"), ("angelo", "nisselino")]
    if (u['Nome'].lower(), u['Cognome'].lower()) in ADMINS:
        with st.expander("🛠️ PANNELLO MANAGER", expanded=False):
            # (Qui va il codice del pannello manager che abbiamo sviluppato prima)
            st.write("Funzioni di gestione attive.")

    # --- SEZIONE TABS: STORICO E REGOLAMENTO ---
    t_st, t_rg = st.tabs(["📋 IL TUO STORICO", "📜 REGOLAMENTO COMPLETO"])
    
    with t_st:
        if not storico.empty: 
            st.dataframe(storico[["Data", "Punti_Assegnati", "Attività", "Assegnato_da"]][::-1], use_container_width=True, hide_index=True)
        else: 
            st.info("Non hai ancora attività registrate. Mettiti in gioco!")
    
    with t_rg:
        st.subheader("🎯 Come guadagnare punti Swag")
        st.markdown("Partecipa attivamente alla vita in Station per accumulare punti e riscattare i premi.")
        
        # Categorie Regolamento
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("🚀 EVENTI & PEAK", expanded=True):
                st.write("**Peak Hero**: +5 pts")
                st.write("**Prime Day Hero**: +3 pts")
                st.write("**Away Team Member**: +15 pts")
                st.write("**Fun Events**: +3 pts")

            with st.expander("💡 INNOVAZIONE"):
                st.write("**Kaizen Idea Implementation**: +10 pts")
                st.write("**Voice of Associates (Best Idea)**: +10 pts")
                st.write("**Kaizen Sustainability**: +1 a +3 pts")

        with col2:
            with st.expander("🛡️ SAFETY & QUALITY", expanded=True):
                st.write("**Safety Hero**: +10 pts")
                st.write("**Gold NOV**: +2 pts")
                st.write("**Silver NOV**: +1 pts")
                st.write("**WW Scorecard Top 10**: +7 pts")

            with st.expander("🎂 SPECIAL & COMMUNITY"):
                st.write("**Happy Birthday**: +5 pts")
                st.write("**DS Birthday**: +3 pts")
                st.write("**Buddy DS**: +5 pts")
                st.write("**Active Ambassador**: +3 pts")

    # Tasti di servizio
    st.markdown("---")
    if st.button("🚪 ESCI"):
        st.session_state.user_auth = None
        st.query_params.clear()
        st.rerun()

    st.caption("Amazon SWAG Program 2026 - Versione 2.1")
