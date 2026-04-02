import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Configurazione Pagina
st.set_page_config(
    page_title="Amazon SWAG 2026", 
    page_icon="📦", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# 2. CSS per stile Amazon
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stSidebar"] {display: none;}
    .stButton>button {
        background-color: #FF9900;
        color: #232F3E;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        width: 100%;
        height: 3em;
    }
    div[data-testid="stMetricValue"] {
        color: #FF9900;
        font-size: 3rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNZIONE PER AGGIORNARE IL FOGLIO ANAGRAFICA ---
def aggiorna_punti_totali_su_gsheet(nome, cognome, nuovo_totale):
    try:
        df_ana = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
        # Trova la riga corrispondente e aggiorna il valore
        mask = (df_ana['Nome'].str.lower() == nome.lower()) & (df_ana['Cognome'].str.lower() == cognome.lower())
        if not df_ana[mask].empty:
            df_ana.loc[mask, 'Punti_Totali'] = nuovo_totale
            conn.update(worksheet="Anagrafica", data=df_ana)
    except:
        pass

# --- SISTEMA DI MEMORIA (Auto-Login) ---
if 'user_auth' not in st.session_state:
    params = st.query_params
    if "user_n" in params and "user_c" in params:
        st.session_state.user_auth = {"Nome": params["user_n"], "Cognome": params["user_c"]}
    else:
        st.session_state.user_auth = None

# --- PAGINA 1: LOGIN / REGISTRAZIONE ---
if st.session_state.user_auth is None:
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", width=120)
    st.title("SWAG PROGRAM 2026")
    
    tab_login, tab_reg = st.tabs(["🔑 ACCEDI", "📝 ISCRIVITI"])
    
    with tab_login:
        with st.form("login_form"):
            l_nome = st.text_input("Il tuo Nome").strip()
            l_cognome = st.text_input("Il tuo Cognome").strip()
            if st.form_submit_button("ENTRA NEL TUO PROFILO"):
                df = conn.read(worksheet="Anagrafica", ttl=0)
                check = df[(df['Nome'].str.lower() == l_nome.lower()) & (df['Cognome'].str.lower() == l_cognome.lower())]
                if not check.empty:
                    st.session_state.user_auth = {"Nome": l_nome, "Cognome": l_cognome}
                    st.query_params["user_n"] = l_nome
                    st.query_params["user_c"] = l_cognome
                    st.rerun()
                else:
                    st.error("Profilo non trovato.")

    with tab_reg:
        with st.form("reg_form"):
            r_nome = st.text_input("Nome").strip()
            r_cognome = st.text_input("Cognome").strip()
            r_email = st.text_input("Email")
            if st.form_submit_button("CREA ACCOUNT"):
                if r_nome and r_cognome:
                    df = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
                    nuovo = pd.DataFrame([{"Nome": r_nome, "Cognome": r_cognome, "Email": r_email, "Punti_Totali": 0}])
                    conn.update(worksheet="Anagrafica", data=pd.concat([df, nuovo], ignore_index=True))
                    st.session_state.user_auth = {"Nome": r_nome, "Cognome": r_cognome}
                    st.query_params["user_n"] = r_nome
                    st.query_params["user_c"] = r_cognome
                    st.rerun()

# --- PAGINA 2: DASHBOARD ---
else:
    u = st.session_state.user_auth
    
    # Recupero dati e calcolo
    try:
        df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all")
        storico = df_log[(df_log['Nome'].str.lower() == u['Nome'].lower()) & (df_log['Cognome'].str.lower() == u['Cognome'].lower())]
        totale_calcolato = int(pd.to_numeric(storico['Punti_Assegnati'], errors='coerce').sum())
        
        # AGGIORNAMENTO INCROCIATO: Scrive il totale nel foglio Anagrafica se è diverso
        aggiorna_punti_totali_su_gsheet(u['Nome'], u['Cognome'], totale_calcolato)
        
    except:
        totale_calcolato = 0
        storico = pd.DataFrame()

    st.title(f"Ciao, {u['Nome']}! 👋")
    st.metric("IL TUO SALDO SWAG", f"{totale_calcolato} Punti")
    
    col_agg, col_esc = st.columns(2)
    with col_agg:
        if st.button("🔄 AGGIORNA"): st.rerun()
    with col_esc:
        if st.button("🚪 ESCI"):
            st.session_state.user_auth = None
            st.query_params.clear()
            st.rerun()

    t_storico, t_regolamento = st.tabs(["📋 STORICO", "📜 REGOLAMENTO"])
    
    with t_storico:
        if not storico.empty:
            st.dataframe(storico[["Data", "Punti_Assegnati", "Attività"]][::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Nessuna attività registrata.")

    with t_regolamento:
        st.subheader("Regolamento 2026")
        # ... (Il resto del regolamento rimane invariato)
        with st.expander("🤝 HR & DEVELOPMENT"):
            st.write("Peak Hero (+5), Prime Day (+3), GB/BB (+6), Ambassador (+3), Gemba (+3), Fun Events (+3), Away Team (+15), VOA Best Idea (+10)")
        with st.expander("⭐ QUALITY"):
            st.write("Gold NOV (+2), Silver NOV (+1)")
        with st.expander("🦺 SAFETY"):
            st.write("Kaizen Idea (+10), Safety Hero (+10)")
        with st.expander("🏢 DELIVERY STATION"):
            st.write("Birthday (+5), DS Anniversary (+3), Top 10 Scorecard (+7), Buddy (+5)")
        with st.expander("🌱 SUSTAINABILITY"):
            st.write("Sustainability Idea (+1), Sustainability Implementation (+3)")

    st.caption("Amazon SWAG 2026")
