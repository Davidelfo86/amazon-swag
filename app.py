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

# 2. CSS Amazon Style & Disclaimer
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stAppDeployButton {display:none;} [data-testid="stSidebar"] {display: none;}
    .stButton>button { background-color: #FF9900; color: #232F3E; border-radius: 8px; font-weight: bold; width: 100%; height: 3.5em; border: none; }
    div[data-testid="stMetricValue"] { color: #FF9900; font-size: 3rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #f0f2f6; border-radius: 5px; padding: 10px; }
    .disclaimer { font-size: 0.8rem; color: #666; font-style: italic; border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Dizionario Completo Attività (Tutte le 18 voci)
ATTIVITA_PREMI = {
    "Peak Hero (+5)": 5, "Prime Day Hero (+3)": 3, "GB/BB Conversion (+6)": 6,
    "Active Ambassador (+3)": 3, "Night activities (+3)": 3, "Gemba Walk (+3)": 3, "Fun Events (+3)": 3,
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
    st.info("**Iniziativa Indipendente**: Questa app è gestita per promuovere il coinvolgimento e il divertimento nella Station. Non è un tool ufficiale aziendale.")

    t_log, t_reg = st.tabs(["🔑 ACCEDI", "📝 ISCRIVITI"])
    with t_log:
        with st.form("login"):
            n_in = st.text_input("Nome").strip(); c_in = st.text_input("Cognome").strip(); p_in = st.text_input("Password", type="password").strip()
            if st.form_submit_button("ENTRA"):
                df_a = conn.read(worksheet="Anagrafica", ttl=0).fillna("")
                df_a['Nome'] = df_a['Nome'].astype(str); df_a['Cognome'] = df_a['Cognome'].astype(str)
                u_row = df_a[(df_a['Nome'].str.lower() == n_in.lower()) & (df_a['Cognome'].str.lower() == c_in.lower())]
                if not u_row.empty and (str(u_row.iloc[0]['Password']) == "" or p_in == str(u_row.iloc[0]['Password'])):
                    st.session_state.user_auth = {"Nome": n_in, "Cognome": c_in}
                    st.query_params.update(user_n=n_in, user_c=c_in); st.rerun()
                else: st.error("Credenziali errate")

    with t_reg:
        with st.form("reg"):
            rn = st.text_input("Nome").strip(); rc = st.text_input("Cognome").strip(); rp = st.text_input("Scegli Password", type="password").strip()
            if st.form_submit_button("CREA PROFILO"):
                if rn and rc and rp:
                    df_a = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
                    df_a['Nome'] = df_a['Nome'].astype(str); df_a['Cognome'] = df_a['Cognome'].astype(str)
                    if not df_a[(df_a['Nome'].str.lower() == rn.lower()) & (df_a['Cognome'].str.lower() == rc.lower())].empty:
                        st.error("Esisti già!")
                    else:
                        new_u = pd.DataFrame([{"Nome":rn, "Cognome":rc, "Password":rp, "Punti_Totali":0}])
                        conn.update(worksheet="Anagrafica", data=pd.concat([df_a, new_u], ignore_index=True))
                        st.success("Registrato! Accedi ora.")

# --- DASHBOARD ---
else:
    u = st.session_state.user_auth
    df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all").fillna("")
    
    if not df_log.empty:
        df_log['Nome'] = df_log['Nome'].astype(str); df_log['Cognome'] = df_log['Cognome'].astype(str)
        storico = df_log[(df_log['Nome'].str.lower() == str(u['Nome']).lower()) & (df_log['Cognome'].str.lower() == str(u['Cognome']).lower())]
    else: storico = pd.DataFrame()

    totale = int(pd.to_numeric(storico['Punti_Assegnati'], errors='coerce').sum()) if not storico.empty else 0
    st.title(f"Ciao, {u['Nome']}! 👋")
    st.metric("IL TUO SALDO SWAG", f"{totale} Punti")

    # --- PANNELLO MANAGER ---
    ADMINS = [("davide", "salemi"), ("massimo", "borella"), ("angelo", "nisselino")]
    if (u['Nome'].lower(), u['Cognome'].lower()) in ADMINS:
        with st.expander("🛠️ PANNELLO MANAGER", expanded=False):
            df_ana = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
            
            st.markdown("#### ➕ Assegna Punti")
            collega = st.selectbox("Seleziona dipendente:", (df_ana['Nome'].astype(str) + " " + df_ana['Cognome'].astype(str)).tolist())
            azione = st.selectbox("Attività:", list(ATTIVITA_PREMI.keys()))
            
            if st.button("CONFERMA ASSEGNAZIONE"):
                n_c, c_c = collega.split(" ", 1); pts = ATTIVITA_PREMI[azione]
                new_l = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y"), "Nome": n_c, "Cognome": c_c, "Punti_Assegnati": pts, "Attività": azione.split(" (")[0], "Assegnato_da": f"{u['Nome']} {u['Cognome']}"}])
                df_log_up = pd.concat([df_log, new_l], ignore_index=True)
                conn.update(worksheet="Log_Punti", data=df_log_up)
                
                # Sincro Anagrafica
                new_tot = int(pd.to_numeric(df_log_up[(df_log_up['Nome'] == n_c) & (df_log_up['Cognome'] == c_c)]['Punti_Assegnati']).sum())
                df_ana['Nome'] = df_ana['Nome'].astype(str); df_ana['Cognome'] = df_ana['Cognome'].astype(str)
                idx = df_ana[(df_ana['Nome'] == n_c) & (df_ana['Cognome'] == c_c)].index[0]
                df_ana.at[idx, 'Punti_Totali'] = new_tot
                conn.update(worksheet="Anagrafica", data=df_ana)
                st.success("Sincronizzato!"); st.rerun()

            st.markdown("---")
            st.markdown("#### 📊 Riepilogo Punti Dipendenti")
            if not df_log.empty:
                classifica = df_log.groupby(['Nome', 'Cognome'])['Punti_Assegnati'].sum().reset_index()
                st.dataframe(classifica.sort_values(by='Punti_Assegnati', ascending=False), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("#### 📜 Storico Globale Assegnazioni")
            if not df_log.empty:
                st.dataframe(df_log[::-1], use_container_width=True, hide_index=True)

    # --- TABS: UTENTE ---
    t_st, t_rg = st.tabs(["📋 IL TUO STORICO", "📜 REGOLAMENTO"])
    with t_st:
        if not storico.empty: st.dataframe(storico[["Data", "Punti_Assegnati", "Attività", "Assegnato_da"]][::-1], use_container_width=True, hide_index=True)
        else: st.info("Nessuna attività registrata.")

    with t_rg:
        st.subheader("🎯 Guida all'assegnazione Punti Swag")
        c1, c2 = st.columns(2)
        with c1:
            with st.expander("🚀 PEAK & OPERATIVITÀ", expanded=True):
                st.write("**Away Team (+15)**: Supporto presso altri siti di nuova apertura.")
                st.write("**WW Scorecard Top 10 (+7)**: TOP10 al mondo.")
                st.write("**GB/BB Conversion (+6)**: Passaggio di ruolo da GB a BB.")
                st.write("**Peak Hero (+5)**: Partecipazione al Peak.")
                st.write("**Prime Day Hero (+3)**: Partecipazione al Prime.")
                st.write("**Night activities/Gemba Walk monthy (+3)**: Partecipazione mensile alle Night Activities o Gemba Walk.")

            with st.expander("💡 INNOVAZIONE & KAIZEN"):
                st.write("**Kaizen Idea Implementation (+10)**: Idea realizzata con successo.")
                st.write("**VOA Best Idea (+10)**: La miglior proposta Voice of Associate.")
                st.write("**Kaizen Sustainability Impl. (+3)**: Miglioramento green realizzato.")
                st.write("**Kaizen Sustainability Idea (+1)**: Proposta di idea sostenibile.")

        with c2:
            with st.expander("🛡️ SAFETY & QUALITY", expanded=True):
                st.write("**Safety Hero (+10)**: Comportamento esemplare per la sicurezza.")
                st.write("**Gold NOV (+2)**: la Delivery Station riesce ad avere un risultato mensile di NOV inferiore a 15 DPMO.")
                st.write("**Silver NOV (+1)**: la Delivery Station riesce ad avere un risultato mensile di NOV inferiore a 30 DPMO.")

            with st.expander("🎂 COMMUNITY & TEAM"):
                st.write("**Happy Birthday (+5)**: Buon compleanno da parte di tutto il team!")
                st.write("**Buddy DS (+5)**: Supporto e formazione ai nuovi assunti.")
                st.write("**DS Birthday (+3)**: Compleanno della nostra DS.")
                st.write("**Active Ambassador (+3)**: Ambassador attivo almeno una volta nel mese.")
                st.write("**Active partecipation in Fun Events (+3)**: Partecipazione attiva agli eventi Fun.")

    if st.button("🚪 ESCI"):
        st.query_params.clear(); st.session_state.user_auth = None; st.rerun()

    st.markdown("""<div class="disclaimer">Iniziativa indipendente a scopo ludico. Non ufficiale Amazon.</div>""", unsafe_allow_html=True)
    st.caption("Amazon SWAG 2026 - Versione Gold 🏆")
