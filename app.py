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

# 2. CSS per nascondere menu e personalizzare stile Amazon
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stSidebar"] {display: none;}
    
    /* Stile Bottoni Amazon */
    .stButton>button {
        background-color: #FF9900;
        color: #232F3E;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        width: 100%;
        height: 3em;
    }
    .stButton>button:hover {
        background-color: #e68a00;
        color: white;
    }
    div[data-testid="stMetricValue"] {
        color: #FF9900;
        font-size: 3rem !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- SISTEMA DI MEMORIA (Auto-Login) ---
# Controlliamo se ci sono credenziali salvate nell'URL (Query Params)
if 'user_auth' not in st.session_state:
    params = st.query_params
    if "user_n" in params and "user_c" in params:
        st.session_state.user_auth = {"Nome": params["user_n"], "Cognome": params["user_c"]}
    else:
        st.session_state.user_auth = None

# --- PAGINA 1: INTRO E LOGIN/REGISTRAZIONE ---
if st.session_state.user_auth is None:
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", width=120)
    st.title("SWAG PROGRAM 2026") # Pacco rimosso per stare su una riga
    
    st.markdown("""
    ### Benvenuto nel portale SWAG! 📦
    Partecipa, accumula punti e scala la classifica della Delivery Station.
    """)
    
    tab_login, tab_reg = st.tabs(["🔑 ACCEDI", "📝 ISCRIVITI"])
    
    with tab_login:
        with st.form("login_form"):
            l_nome = st.text_input("Il tuo Nome")
            l_cognome = st.text_input("Il tuo Cognome")
            if st.form_submit_button("ENTRA NEL TUO PROFILO"):
                df = conn.read(worksheet="Anagrafica", ttl=0)
                check = df[(df['Nome'].str.lower() == l_nome.strip().lower()) & (df['Cognome'].str.lower() == l_cognome.strip().lower())]
                if not check.empty:
                    st.session_state.user_auth = {"Nome": l_nome.strip(), "Cognome": l_cognome.strip()}
                    # Salviamo nell'URL per il prossimo accesso
                    st.query_params["user_n"] = l_nome.strip()
                    st.query_params["user_c"] = l_cognome.strip()
                    st.rerun()
                else:
                    st.error("Profilo non trovato. Controlla i dati o iscriviti.")

    with tab_reg:
        with st.form("reg_form"):
            r_nome = st.text_input("Nome")
            r_cognome = st.text_input("Cognome")
            r_email = st.text_input("Email")
            if st.form_submit_button("CREA ACCOUNT"):
                if r_nome and r_cognome:
                    try:
                        df = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
                        nuovo = pd.DataFrame([{"Nome": r_nome.strip(), "Cognome": r_cognome.strip(), "Email": r_email, "Punti_Totali": 0}])
                        conn.update(worksheet="Anagrafica", data=pd.concat([df, nuovo], ignore_index=True))
                        st.session_state.user_auth = {"Nome": r_nome.strip(), "Cognome": r_cognome.strip()}
                        st.query_params["user_n"] = r_nome.strip()
                        st.query_params["user_c"] = r_cognome.strip()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: {e}")

# --- PAGINA 2: DASHBOARD UTENTE ---
else:
    u = st.session_state.user_auth
    st.title(f"Ciao, {u['Nome']}! 👋")
    
    # Recupero dati e calcolo somma
    try:
        df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all")
        storico = df_log[(df_log['Nome'].str.lower() == u['Nome'].lower()) & (df_log['Cognome'].str.lower() == u['Cognome'].lower())]
        totale = int(pd.to_numeric(storico['Punti_Assegnati'], errors='coerce').sum())
    except:
        totale = 0
        storico = pd.DataFrame()

    st.metric("IL TUO SALDO SWAG", f"{totale} Punti")
    
    col_agg, col_esc = st.columns(2)
    with col_agg:
        if st.button("🔄 AGGIORNA"): st.rerun()
    with col_esc:
        if st.button("🚪 ESCI"):
            st.session_state.user_auth = None
            st.query_params.clear() # Cancella la memoria
            st.rerun()

    t_storico, t_regolamento = st.tabs(["📋 STORICO", "📜 REGOLAMENTO"])
    
    with t_storico:
        if not storico.empty:
            st.dataframe(storico[["Data", "Punti_Assegnati", "Attività"]][::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Nessuna attività registrata. Inizia subito a guadagnare punti!")

    with t_regolamento:
        st.subheader("Come guadagnare punti nel 2026")
        categorie = {
            "🤝 HR & Development": [("Peak Hero", 5), ("Prime Day Hero", 3), ("Away Team", 15), ("Ambassador", 3)],
            "🦺 Safety & Quality": [("Kaizen Idea", 10), ("Safety Hero", 10), ("Gold NOV", 2)],
            "🎂 Special": [("Compleanno", 5), ("Anniversario DS", 3)]
        }
        for cat, items in categorie.items():
            with st.expander(cat):
                for n, p in items: st.write(f"**{n}** ➔ +{p} Punti")

    st.caption("Amazon SWAG 2026 - Il tuo portale premi ufficiale")
