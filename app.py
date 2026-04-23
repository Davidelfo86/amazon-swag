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

# 2. CSS Amazon Style & Logo Telefono
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
    if "user_n" in p and "user_c" in p:
        st.session_state.user_auth = {"Nome": p["user_n"], "Cognome": p["user_c"]}
    else:
        st.session_state.user_auth = None

# --- PAGINA 1: LOGIN E REGISTRAZIONE ---
if st.session_state.user_auth is None:
    st.image("https://github.com/Davidelfo86/amazon-swag/blob/main/dlo8.png?raw=true", width=150)
    st.title("SWAG PROGRAM 2026")
    st.markdown("### Benvenuto! Accedi per gestire i tuoi punti.")
    
    t_login, t_iscr = st.tabs(["🔑 ACCEDI", "📝 ISCRIVITI"])
    
    with t_login:
        with st.form("login"):
            n = st.text_input("Nome", key="log_n").strip()
            c = st.text_input("Cognome", key="log_c").strip()
            p_input = st.text_input("Password", key="log_p", type="password").strip()
            
            if st.form_submit_button("ENTRA NEL TUO PROFILO"):
                df_a = conn.read(worksheet="Anagrafica", ttl=0).fillna("")
                user_row = df_a[(df_a['Nome'].astype(str).str.lower() == n.lower()) & 
                                (df_a['Cognome'].astype(str).str.lower() == c.lower())]
                
                if not user_row.empty:
                    pwd_salvata = str(user_row.iloc[0]['Password']).strip()
                    
                    # Gestione primo accesso o password mancante
                    if pwd_salvata == "":
                        if p_input == "":
                            st.warning("Profilo senza password. Inseriscine una ora per attuarlo.")
                        else:
                            idx = user_row.index[0]
                            df_a.at[idx, 'Password'] = p_input
                            conn.update(worksheet="Anagrafica", data=df_a)
                            st.success("Password impostata! Accesso in corso...")
                            st.session_state.user_auth = {"Nome": n, "Cognome": c}
                            st.query_params["user_n"], st.query_params["user_c"] = n, c
                            st.rerun()
                    
                    elif p_input == pwd_salvata:
                        st.session_state.user_auth = {"Nome": n, "Cognome": c}
                        st.query_params["user_n"], st.query_params["user_c"] = n, c
                        st.rerun()
                    else:
                        st.error("Password errata.")
                else:
                    st.error("Account non trovato.")

    with t_iscr:
        with st.form("reg"):
            rn = st.text_input("Nome", key="reg_n").strip()
            rc = st.text_input("Cognome", key="reg_c").strip()
            rp = st.text_input("Scegli una Password", key="reg_p", type="password").strip()
            
            if st.form_submit_button("CREA PROFILO"):
                if rn and rc and rp:
                    df_a = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
                    esiste = not df_a[(df_a['Nome'].astype(str).str.lower() == rn.lower()) & 
                                      (df_a['Cognome'].astype(str).str.lower() == rc.lower())].empty
                    if esiste:
                        st.error("Utente già registrato.")
                    else:
                        new_user = pd.DataFrame([{"Nome":rn, "Cognome":rc, "Password":rp, "Punti_Totali":0}])
                        conn.update(worksheet="Anagrafica", data=pd.concat([df_a, new_user], ignore_index=True))
                        st.session_state.user_auth = {"Nome":rn, "Cognome":rc}
                        st.query_params["user_n"], st.query_params["user_c"] = rn, rc
                        st.rerun()
                else:
                    st.warning("Compila tutti i campi.")

# --- PAGINA 2: DASHBOARD UTENTE & PANNELLO MANAGER ---
else:
    u = st.session_state.user_auth
    df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all").fillna("")
    
    if not df_log.empty and 'Nome' in df_log.columns:
        storico = df_log[(df_log['Nome'].astype(str).str.lower() == u['Nome'].lower()) & 
                        (df_log['Cognome'].astype(str).str.lower() == u['Cognome'].lower())]
        totale = int(pd.to_numeric(storico['Punti_Assegnati'], errors='coerce').sum())
    else:
        storico, totale = pd.DataFrame(), 0
        
    sync_totale(u['Nome'], u['Cognome'], totale)
    st.title(f"Ciao, {u['Nome']}! 👋")

    # --- PANNELLO MANAGER SEGRETO ---
    if u['Nome'].lower() == "davide" and u['Cognome'].lower() == "salemi":
        with st.expander("🛠️ PANNELLO MANAGER", expanded=False):
            st.markdown("### ➕ Assegna Punti")
            df_ana = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all")
            nomi_colleghi = (df_ana['Nome'].astype(str) + " " + df_ana['Cognome'].astype(str)).tolist()
            
            collega = st.selectbox("Seleziona dipendente:", nomi_colleghi)
            azione = st.selectbox("Attività:", list(ATTIVITA_PREMI.keys()))
            
            if st.button("CONFERMA ASSEGNAZIONE"):
                n_c, c_c = collega.split(" ", 1)
                pts = ATTIVITA_PREMI[azione]
                new_entry = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Nome": n_c, "Cognome": c_c,
                    "Punti_Assegnati": pts,
                    "Attività": azione.split(" (")[0]
                }])
                conn.update(worksheet="Log_Punti", data=pd.concat([df_log, new_entry], ignore_index=True))
                st.success(f"Assegnati {pts} punti!")
                st.rerun()

            st.markdown("---")
            st.markdown("### 📋 Modifica Registro")
            updated_log = st.data_editor(df_log, num_rows="dynamic", use_container_width=True, hide_index=True)
            if st.button("💾 SALVA MODIFICHE"):
                conn.update(worksheet="Log_Punti", data=updated_log)
                st.success("Registro aggiornato!")
                st.rerun()

    # --- INTERFACCIA UTENTE ---
    st.metric("IL TUO SALDO SWAG", f"{totale} Punti")
    
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("🔄 AGGIORNA"): st.rerun()
    with c2:
        if st.button("🚪 ESCI"):
            st.query_params.clear()
            st.session_state.user_auth = None
            st.rerun()

    t_st, t_rg = st.tabs(["📋 STORICO", "📜 REGOLAMENTO"])
    
    with t_st:
        if not storico.empty: 
            st.dataframe(storico[["Data", "Punti_Assegnati", "Attività"]][::-1], use_container_width=True, hide_index=True)
        else: 
            st.info("Nessuna attività registrata.")
    
    with t_rg:
        st.subheader("Come guadagnare punti")
        regole = {
            "🤝 HR & DEVELOPMENT": [("Peak Hero", "+5"), ("Prime Day Hero", "+3"), ("Away Team", "+15")],
            "⭐ QUALITY & SAFETY": [("Gold NOV", "+2"), ("Safety Hero", "+10"), ("Kaizen Idea", "+10")]
        }
        for cat, voci in regole.items():
            with st.expander(cat):
                for t, p in voci: st.write(f"**{t}**: {p} punti")

    st.caption("Amazon SWAG Program 2026")
