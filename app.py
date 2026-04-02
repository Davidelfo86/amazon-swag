import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Configurazione Pagina
st.set_page_config(page_title="Amazon SWAG", page_icon="📦", layout="centered")

st.title("📦 Amazon SWAG Program")
st.markdown("---")

# 2. Collegamento al tuo Google Sheet
url = "https://docs.google.com/spreadsheets/d/1zcW2RmucH-zrPNphehPjYmohf8cj-_-TQST2iwvNmfU/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Menu di navigazione
scelta = st.sidebar.radio("Vai a:", ["Iscrizione", "I miei Punti", "Regolamento"])

# --- SEZIONE ISCRIZIONE ---
if scelta == "Iscrizione":
    st.header("📝 Registrati al programma")
    with st.form("form_registro", clear_on_submit=True):
        nome = st.text_input("Nome")
        cognome = st.text_input("Cognome")
        email = st.text_input("Email (opzionale)")
        submit = st.form_submit_button("Invia Registrazione")
        
        if submit:
            if nome and cognome:
                # Legge i dati attuali dal foglio Anagrafica
                df_anagrafica = conn.read(spreadsheet=url, worksheet="Anagrafica")
                # Crea la nuova riga
                nuovo_utente = pd.DataFrame([{"Nome": nome, "Cognome": cognome, "Email": email, "Punti_Totali": 0}])
                # Aggiorna il foglio Anagrafica
                updated_df = pd.concat([df_anagrafica, nuovo_utente], ignore_index=True)
                conn.update(spreadsheet=url, data=updated_df, worksheet="Anagrafica")
                
                st.success(f"Benvenuto {nome}! Ti sei registrato correttamente.")
                st.balloons()
            else:
                st.error("Inserisci Nome e Cognome!")

# --- SEZIONE I MIEI PUNTI ---
elif scelta == "I miei Punti":
    st.header("💰 Controlla il tuo Saldo e Storico")
    
    # Carichiamo i dati dai due fogli
    df_totali = conn.read(spreadsheet=url, worksheet="Anagrafica")
    df_log = conn.read(spreadsheet=url, worksheet="Log_Punti")
    
    if not df_totali.empty:
        # Creiamo una lista di nomi per la ricerca
        lista_nomi = (df_totali['Nome'] + " " + df_totali['Cognome']).tolist()
        utente_sel = st.selectbox("Seleziona il tuo nome e cognome:", lista_nomi)
        
        if utente_sel:
            # Separiamo nome e cognome dalla selezione
            n_sel, c_sel = utente_sel.split(" ", 1)
            
            # Recupero Punti Totali dal foglio Anagrafica
            punti_tot = df_totali.loc[(df_totali['Nome'] == n_sel) & (df_totali['Cognome'] == c_sel), 'Punti_Totali'].values[0]
            st.metric(label="Saldo Attuale SWAG", value=f"{punti_tot} pts")
            
            st.markdown("### 📋 Dettaglio Attività")
            # Recupero lo storico dal foglio Log_Punti
            storico = df_log[(df_log['Nome'] == n_sel) & (df_log['Log_Punti' == c_sel] if 'Cognome' in df_log else df_log['Nome'] == n_sel)]
            # Nota: Filtriamo il log per nome e cognome
            storico_utente = df_log[(df_log['Nome'] == n_sel) & (df_log['Cognome'] == c_sel)]
            
            if not storico_utente.empty:
                st.dataframe(storico_utente[["Data", "Punti_Assegnati", "Attività"]], use_container_width=True, hide_index=True)
            else:
                st.info("Non ci sono ancora attività registrate a tuo nome.")
    else:
        st.warning("Nessun utente registrato nel sistema.")

# --- SEZIONE REGOLAMENTO ---
elif scelta == "Regolamento":
    st.header("🎯 Come guadagnare punti")
    st.info("Qui compariranno le tue 10 attività una volta che le avremo inserite.")
