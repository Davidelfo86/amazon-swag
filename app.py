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

# 3. Dizionario Attività
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

# --- PAGINA 1: LOGIN E REGISTRAZIONE ---
if st.session_state.user_auth is None:
    st.image("https://github.com/Davidelfo86/amazon-swag/blob/main/dlo8.png?raw=true", width=150)
    st.title("SWAG PROGRAM 2026")
    
    t_login, t_iscr = st.tabs(["🔑 ACCEDI", "📝 ISCRIVITI"])
    
    with t_login:
        with st.form("login"):
            n = st.text_input("Nome").strip()
            c = st.text_input("Cognome").strip()
            p_input = st.text_input("Password", type="password").strip()
            if st.form_submit_button("ENTRA NEL TUO PROFILO"):
                df_a = conn.read(worksheet="Anagrafica", ttl=0).fillna("")
                user_row = df_a[(df_a['Nome'].astype(str).str.lower() == n.lower()) & 
                                (df_a['Cognome'].astype(str).str.lower() == c.lower())]
                
                if not user_row.empty:
                    pwd_salvata = str(user_row.iloc[0]['Password']).strip()
                    if pwd_salvata == "" or p_input == pwd_salvata:
                        st.session_state.user_auth = {"Nome": n, "Cognome": c}
                        st.query_params["user_n"], st.query_params["user_c"] = n, c
                        st.rerun()
                    else:
                        st.error("Password errata.")
                else:
                    st.error("Account non trovato.")

    with t_iscr:
        with st.form("reg"):
            rn = st.text_input("Nome (Nuovo)").strip()
            rc = st.text_input("Cognome (Nuovo)").strip()
            rp = st.text_input("Scegli Password", type="password").strip()
            if st.form_submit_button("CREA PROFILO"):
                df_a = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
                esiste = not df_a[(df_a['Nome'].astype(str).str.lower() == rn.lower()) & 
                                  (df_a['Cognome'].astype(str).str.lower() == rc.lower())].empty
                if esiste:
                    st.error("Utente già registrato.")
                else:
                    new_user = pd.DataFrame([{"Nome":rn, "Cognome":rc, "Password":rp, "Punti_Totali":0}])
                    conn.update(worksheet="Anagrafica", data=pd.concat([df_a, new_user], ignore_index=True))
                    st.success("Profilo creato! Ora puoi accedere.")

# --- PAGINA 2: DASHBOARD E PANNELLO MANAGER ---
else:
    u = st.session_state.user_auth
    df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all").fillna("")
    
    # Calcolo totale basato sul LOG
    storico = df_log[(df_log['Nome'].astype(str).str.lower() == u['Nome'].lower()) & 
                    (df_log['Cognome'].astype(str).str.lower() == u['Cognome'].lower())]
    totale = int(pd.to_numeric(storico['Punti_Assegnati'], errors='coerce').sum())
        
    st.title(f"Ciao, {u['Nome']}! 👋")
    st.metric("IL TUO SALDO SWAG", f"{totale} Punti")

    # --- ADMIN CHECK ---
    ADMINS = [("davide", "salemi"), ("massimo", "borella"), ("angelo", "nisselino")]
    is_admin = (u['Nome'].lower(), u['Cognome'].lower()) in ADMINS

    if is_admin:
        with st.expander("🛠️ PANNELLO MANAGER & AUDIT", expanded=False):
            df_ana = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
            
            # 1. Assegnazione rapida
            collega = st.selectbox("Seleziona dipendente:", (df_ana['Nome'] + " " + df_ana['Cognome']).tolist())
            azione = st.selectbox("Attività:", list(ATTIVITA_PREMI.keys()))
            
            if st.button("CONFERMA ASSEGNAZIONE"):
                n_c, c_c = collega.split(" ", 1)
                pts = ATTIVITA_PREMI[azione]
                new_entry = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Nome": n_c, "Cognome": c_c, "Punti_Assegnati": pts,
                    "Attività": azione.split(" (")[0], "Assegnato_da": f"{u['Nome']} {u['Cognome']}"
                }])
                conn.update(worksheet="Log_Punti", data=pd.concat([df_log, new_entry], ignore_index=True))
                st.success("Punti assegnati!")
                st.rerun()

            # 2. Modifica Anagrafica con Audit
            st.markdown("---")
            st.markdown("### 📋 Modifica Punti Totali (Audit)")
            edited_ana = st.data_editor(df_ana, use_container_width=True, hide_index=True)
            
            if st.button("💾 SALVA E GIUSTIFICA"):
                for i in range(len(df_ana)):
                    old_v = pd.to_numeric(df_ana.iloc[i]['Punti_Totali'], errors='coerce') or 0
                    new_v = pd.to_numeric(edited_ana.iloc[i]['Punti_Totali'], errors='coerce') or 0
                    if old_v != new_v:
                        diff = new_v - old_v
                        motivo = st.text_input(f"Motivo per {diff} pts a {edited_ana.iloc[i]['Nome']}:", key=f"m_{i}")
                        if motivo:
                            rec = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y"), 
                                "Nome": edited_ana.iloc[i]['Nome'], "Cognome": edited_ana.iloc[i]['Cognome'], 
                                "Punti_Assegnati": diff, "Attività": f"MANUALE: {motivo}", "Assegnato_da": f"{u['Nome']} {u['Cognome']}"}])
                            conn.update(worksheet="Log_Punti", data=pd.concat([df_log, rec], ignore_index=True))
                            conn.update(worksheet="Anagrafica", data=edited_ana)
                            st.rerun()
                        else:
                            st.warning("Inserisci il motivo!")
                            st.stop()

    # --- TABS: STORICO E REGOLAMENTO ---
    t_st, t_rg = st.tabs(["📋 STORICO", "📜 REGOLAMENTO"])
    
    with t_st:
        if not storico.empty:
            st.dataframe(storico[["Data", "Punti_Assegnati", "Attività", "Assegnato_da"]][::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Ancora nessun punto registrato.")

    with t_rg:
        st.subheader("🎯 Come guadagnare punti")
        c1, c2 = st.columns(2)
        with c1:
            with st.expander("🚀 EVENTI", expanded=True):
                st.write("**Peak Hero**: +5 pts")
                st.write("**Away Team**: +15 pts")
            with st.expander("💡 INNOVAZIONE"):
                st.write("**Kaizen Idea**: +10 pts")
                st.write("**VOA Best Idea**: +10 pts")
        with c2:
            with st.expander("🛡️ SAFETY", expanded=True):
                st.write("**Safety Hero**: +10 pts")
                st.write("**Gold NOV**: +2 pts")
            with st.expander("🎂 ALTRO"):
                st.write("**Happy Birthday**: +5 pts")
                st.write("**Buddy DS**: +5 pts")

    if st.button("🚪 ESCI"):
        st.query_params.clear()
        st.session_state.user_auth = None
        st.rerun()
