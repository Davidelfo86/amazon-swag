import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Configurazione Pagina (Nascondiamo la barra laterale di default)
st.set_page_config(
    page_title="Amazon SWAG 2026", 
    page_icon="📦", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# 2. CSS personalizzato per nascondere menu, gattino GitHub e applicare stile Amazon
st.markdown("""
    <style>
    /* Nasconde il menu in alto a destra e il tasto deploy (gattino) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    
    # /* Nasconde completamente la sidebar */
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stSidebarNav"] {display: none;}
    
    /* Stile Bottoni e Colori Amazon */
    .stButton>button {
        background-color: #FF9900;
        color: #232F3E;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #e68a00;
        color: white;
    }
    .main {
        background-color: #f3f3f3;
    }
    div[data-testid="stMetricValue"] {
        color: #FF9900;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOGICA DI NAVIGAZIONE ---
if 'user_auth' not in st.session_state:
    st.session_state.user_auth = None

# --- PAGINA 1: INTRO E REGISTRAZIONE ---
if st.session_state.user_auth is None:
    # Header stile Amazon
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", width=150)
    st.title("📦 SWAG Program 2026")
    
    st.markdown("""
    ### Benvenuto nel futuro dell'eccellenza!
    Il programma **SWAG (Success Worth Achieving Goals)** è l'iniziativa esclusiva dedicata a chi fa la differenza ogni giorno. 
    Accumula punti partecipando attivamente alla vita della Delivery Station e riscattali con fantastici premi.
    
    *Sicurezza, Qualità e Impegno: i tuoi pilastri, i tuoi premi.*
    """)
    
    tab1, tab2 = st.tabs(["Iscriviti ora", "Accedi al tuo profilo"])
    
    with tab1:
        with st.form("iscrizione_form"):
            st.subheader("📝 Diventa un membro SWAG")
            nuovo_nome = st.text_input("Nome")
            nuovo_cognome = st.text_input("Cognome")
            nuova_email = st.text_input("Email (aziendale o personale)")
            btn_reg = st.form_submit_button("INIZIA ORA")
            
            if btn_reg:
                if nuovo_nome and nuovo_cognome:
                    try:
                        df = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
                        nuovo_utente = pd.DataFrame([{
                            "Nome": nuovo_nome, "Cognome": nuovo_cognome, 
                            "Email": nuova_email, "Punti_Totali": 0
                        }])
                        updated_df = pd.concat([df, nuovo_utente], ignore_index=True)
                        conn.update(worksheet="Anagrafica", data=updated_df)
                        
                        st.session_state.user_auth = {"Nome": nuovo_nome, "Cognome": nuovo_cognome}
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: {e}")
                else:
                    st.warning("Compila i campi obbligatori!")

    with tab2:
        with st.form("login_form"):
            st.subheader("🔑 Bentornato")
            login_nome = st.text_input("Inserisci il tuo Nome")
            login_cognome = st.text_input("Inserisci il tuo Cognome")
            btn_login = st.form_submit_button("ACCEDI AI MIEI PUNTI")
            
            if btn_login:
                df = conn.read(worksheet="Anagrafica", ttl=0)
                check = df[(df['Nome'].str.lower() == login_nome.lower()) & (df['Cognome'].str.lower() == login_cognome.lower())]
                if not check.empty:
                    st.session_state.user_auth = {"Nome": login_nome, "Cognome": login_cognome}
                    st.rerun()
                else:
                    st.error("Profilo non trovato. Verifica i dati o iscriviti.")

# --- PAGINA 2: DASHBOARD PUNTI ---
else:
    u = st.session_state.user_auth
    st.title(f"Ciao, {u['Nome']}! 👋")
    
    # 1. Calcolo Punti
    try:
        df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all")
        storico = df_log[(df_log['Nome'].str.lower() == u['Nome'].lower()) & (df_log['Cognome'].str.lower() == u['Cognome'].lower())]
        totale = int(pd.to_numeric(storico['Punti_Assegnati'], errors='coerce').sum())
    except:
        totale = 0
        storico = pd.DataFrame()

    st.metric("IL TUO SALDO SWAG", f"{totale} Punti")
    
    # Tasti rapidi
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Aggiorna Punti"):
            st.rerun()
    with col2:
        if st.button("🚪 Esci"):
            st.session_state.user_auth = None
            st.rerun()

    # Sezione Regolamento e Storico
    t1, t2 = st.tabs(["📋 Storico Attività", "📜 Regolamento 2026"])
    
    with t1:
        if not storico.empty:
            st.dataframe(storico[["Data", "Punti_Assegnati", "Attività"]].sort_index(ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Non hai ancora attività registrate. Partecipa agli eventi per guadagnare punti!")

    with t2:
        st.subheader("Come guadagnare SWAG Points")
        
        cat = {
            "🤝 HR & Sviluppo": [
                ("Peak Hero", 5), ("Prime Day Hero", 3), ("GB/BB Conversion", 6), 
                ("Active Ambassador", 3), ("Gemba Walk", 3), ("Away Team", 15)
            ],
            "🦺 Safety & Quality": [
                ("Kaizen Idea", 10), ("Safety Hero", 10), ("Gold NOV", 2), ("Silver NOV", 1)
            ],
            "🌱 Sustainability": [
                ("Sustainability Idea", 1), ("Sustainability Implementation", 3)
            ],
            "🎂 Special Events": [
                ("Compleanno", 5), ("Anniversario DS", 3), ("Top 10 Scorecard", 7)
            ]
        }
        
        for c, tasks in cat.items():
            with st.expander(c):
                for t, p in tasks:
                    st.write(f"**{t}** ➔ +{p} Swaggies")

    st.markdown("---")
    st.caption("Amazon SWAG Program 2026 - Riservato ai dipendenti")
