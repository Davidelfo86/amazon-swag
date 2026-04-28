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

# --- LOGICA LOGIN/REGISTRAZIONE (Invariata per brevità, usa la tua esistente) ---
if st.session_state.user_auth is None:
    # ... (Inserire qui il blocco login/registrazione del tuo codice precedente) ...
    st.image("https://github.com/Davidelfo86/amazon-swag/blob/main/dlo8.png?raw=true", width=150)
    st.title("SWAG PROGRAM 2026")
    # Nota: Per brevità ho omesso il form di login, usa quello che hai già.
    st.info("Esegui il login per continuare.")
    with st.form("login_quick"):
        n = st.text_input("Nome")
        c = st.text_input("Cognome")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("ACCEDI"):
            st.session_state.user_auth = {"Nome": n, "Cognome": c}
            st.rerun()

# --- DASHBOARD PRINCIPALE ---
else:
    u = st.session_state.user_auth
    df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all").fillna("")
    
    # Calcolo totale reale basato sul LOG
    if not df_log.empty and 'Nome' in df_log.columns:
        storico = df_log[(df_log['Nome'].astype(str).str.lower() == u['Nome'].lower()) & 
                        (df_log['Cognome'].astype(str).str.lower() == u['Cognome'].lower())]
        totale_reale = int(pd.to_numeric(storico['Punti_Assegnati'], errors='coerce').sum())
    else:
        storico, totale_reale = pd.DataFrame(), 0
        
    st.title(f"Ciao, {u['Nome']}! 👋")

    # --- LISTA ADMIN ---
    ADMINS = [("davide", "salemi"), ("massimo", "borella"), ("angelo", "nisselino")]
    is_admin = (u['Nome'].lower(), u['Cognome'].lower()) in ADMINS

    # --- PANNELLO MANAGER CON AUDIT ---
    if is_admin:
        with st.expander("🛠️ PANNELLO MANAGER & AUDIT", expanded=False):
            df_ana = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
            
            st.markdown("### ➕ Assegnazione Rapida")
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
                    "Attività": azione.split(" (")[0],
                    "Assegnato_da": f"{u['Nome']} {u['Cognome']}" # Colonna F
                }])
                df_updated_log = pd.concat([df_log, new_entry], ignore_index=True)
                conn.update(worksheet="Log_Punti", data=df_updated_log)
                st.success(f"Assegnati {pts} punti a {collega}!")
                st.rerun()

            st.markdown("---")
            st.markdown("### 📋 Revisione Anagrafica (Punti Totali)")
            st.caption("Se modifichi i punti qui sotto, l'app ti chiederà il motivo al salvataggio.")
            
            # Editor per l'anagrafica
            edited_ana = st.data_editor(df_ana, use_container_width=True, hide_index=True)
            
            if st.button("💾 SALVA E RICONCILIA"):
                motivo_modifica = ""
                new_log_entries = []
                
                # Confronto riga per riga per trovare discrepanze
                for i in range(len(df_ana)):
                    old_val = pd.to_numeric(df_ana.iloc[i]['Punti_Totali'], errors='coerce') or 0
                    new_val = pd.to_numeric(edited_ana.iloc[i]['Punti_Totali'], errors='coerce') or 0
                    
                    if old_val != new_val:
                        diff = new_val - old_val
                        nome_comp = f"{edited_ana.iloc[i]['Nome']} {edited_ana.iloc[i]['Cognome']}"
                        
                        # Chiedi il motivo per questa specifica modifica
                        motivo = st.text_input(f"Motivo per variazione {diff} pts a {nome_comp}:", key=f"mot_{i}")
                        
                        if motivo:
                            new_log_entries.append({
                                "Data": datetime.now().strftime("%d/%m/%Y"),
                                "Nome": edited_ana.iloc[i]['Nome'],
                                "Cognome": edited_ana.iloc[i]['Cognome'],
                                "Punti_Assegnati": diff,
                                "Attività": f"MODIFICA MANUALE: {motivo}",
                                "Assegnato_da": f"{u['Nome']} {u['Cognome']}"
                            })
                        else:
                            st.warning(f"Inserisci un motivo per {nome_comp} prima di salvare!")
                            st.stop()
                
                if new_log_entries:
                    # Aggiorna Log e Anagrafica
                    df_final_log = pd.concat([df_log, pd.DataFrame(new_log_entries)], ignore_index=True)
                    conn.update(worksheet="Log_Punti", data=df_final_log)
                    conn.update(worksheet="Anagrafica", data=edited_ana)
                    st.success("Modifiche salvate e giustificate nel Log!")
                    st.rerun()
                else:
                    st.info("Nessuna modifica rilevata.")

    # --- INTERFACCIA UTENTE ---
    st.metric("IL TUO SALDO SWAG", f"{totale_reale} Punti")
    
    t_st, t_rg = st.tabs(["📋 STORICO", "📜 REGOLAMENTO"])
    with t_st:
        if not storico.empty:
            # Mostriamo anche chi ha assegnato i punti nello storico
            st.dataframe(storico[["Data", "Punti_Assegnati", "Attività", "Assegnato_da"]][::-1], 
                         use_container_width=True, hide_index=True)
        else:
            st.info("Nessuna attività registrata.")

    # Tasto Logout
    if st.button("🚪 ESCI"):
        st.query_params.clear()
        st.session_state.user_auth = None
        st.rerun()

    st.caption("Amazon SWAG Program 2026")
