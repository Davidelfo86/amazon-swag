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

# 2. CSS per uno stile Amazon pulito e senza fronzoli
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
    /* Stile per i Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

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
    
    st.markdown("""
    ### Benvenuto nel portale SWAG!
    Riconosciamo il tuo impegno. Accumula punti e scopri i vantaggi riservati ai migliori.
    """)
    
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
                    st.error("Profilo non trovato. Controlla i dati o iscriviti.")

    with tab_reg:
        with st.form("reg_form"):
            r_nome = st.text_input("Nome").strip()
            r_cognome = st.text_input("Cognome").strip()
            r_email = st.text_input("Email")
            if st.form_submit_button("CREA ACCOUNT"):
                if r_nome and r_cognome:
                    try:
                        df = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
                        nuovo = pd.DataFrame([{"Nome": r_nome, "Cognome": r_cognome, "Email": r_email, "Punti_Totali": 0}])
                        conn.update(worksheet="Anagrafica", data=pd.concat([df, nuovo], ignore_index=True))
                        st.session_state.user_auth = {"Nome": r_nome, "Cognome": r_cognome}
                        st.query_params["user_n"] = r_nome
                        st.query_params["user_c"] = r_cognome
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: {e}")

# --- PAGINA 2: DASHBOARD ---
else:
    u = st.session_state.user_auth
    st.title(f"Ciao, {u['Nome']}! 👋")
    
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
            st.query_params.clear()
            st.rerun()

    t_storico, t_regolamento = st.tabs(["📋 STORICO", "📜 REGOLAMENTO"])
    
    with t_storico:
        if not storico.empty:
            st.dataframe(storico[["Data", "Punti_Assegnati", "Attività"]][::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Nessuna attività registrata. Partecipa per accumulare punti!")

    with t_regolamento:
        st.subheader("Criteri di Assegnazione Punti 2026")

        with st.expander("🤝 HR & PERSONAL DEVELOPMENT"):
            st.markdown("""
            * **Peak Hero:** Per chi ha partecipato al periodo di Peak ➔ **+5 Swaggies**
            * **Prime Day Hero:** Per chi ha partecipato al Prime Day ➔ **+3 Swaggies**
            * **GB/BB Conversion:** Per gli SA che passano da Green Badge a Blue Badge ➔ **+6 Swaggies**
            * **Active Ambassador:** Per chiunque partecipi come Ambassador attivo almeno una volta al mese ➔ **+3 Swaggies**
            * **Night Activities / Gemba Walk:** Per gli SA che partecipano alla camminata Gemba o attività notturne del mese ➔ **+3 Swaggies**
            * **Active Participation in Fun Events:** Per tutti gli SA che partecipano attivamente agli eventi "Fun" ➔ **+3 Swaggies**
            * **Away Team Member:** Per tutti i membri del team Away coinvolti nel lancio di una nuova DS ➔ **+15 Swaggies**
            * **Voice of Associates Best Idea:** Per l'SA che propone la migliore idea di miglioramento tramite la bacheca VOA ➔ **+10 Swaggies**
            """)

        with st.expander("⭐ QUALITY"):
            st.markdown("""
            * **Gold NOV:** Se la Delivery Station mantiene un risultato NOV mensile sotto i 15 DPMO (per tutti) ➔ **+2 Swaggies**
            * **Silver NOV:** Se la Delivery Station mantiene un risultato NOV mensile sotto i 30 DPMO (per tutti) ➔ **+1 Swaggie**
            """)

        with st.expander("🦺 SAFETY"):
            st.markdown("""
            * **Kaizen Idea Implementation:** Implementazione concreta di un'idea Kaizen ➔ **+10 Swaggies**
            * **Safety Hero:** Premio per l'eroe della sicurezza del mese ➔ **+10 Swaggies**
            """)

        with st.expander("🏢 DELIVERY STATION DEVELOPMENT"):
            st.markdown("""
            * **Happy Birthday:** Auguri dal team SWAG per il tuo compleanno ➔ **+5 Swaggies**
            * **Delivery Station Birthday:** Per tutti i membri della DS nell'anniversario dell'apertura ➔ **+3 Swaggies**
            * **WW Scorecard Top 10:** Per aver contribuito a portare la DS nella Top 10 della scorecard mensile mondiale ➔ **+7 Swaggies**
            * **Buddy DS:** Per i membri del team che aiutano a formare i neo-assunti lanciando un nuovo sito ➔ **+5 Swaggies**
            """)

        with st.expander("🌱 SUSTAINABILITY"):
            st.markdown("""
            * **Kaizen Sustainability Idea:** Per gli SA che propongono idee Kaizen sulla sostenibilità (valutate dal team OPS) ➔ **+1 Swaggie**
            * **Kaizen Sustainability Implementation:** Implementazione concreta di un'idea Kaizen focalizzata sulla sostenibilità ➔ **+3 Swaggies**
            """)

    st.caption("Amazon SWAG 2026 - Riservato ai dipendenti della Delivery Station")
