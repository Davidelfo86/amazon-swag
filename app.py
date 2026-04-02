import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Configurazione della pagina (Titolo che appare sulla scheda del browser)
st.set_page_config(page_title="Amazon SWAG App", page_icon="📦", layout="centered")

# Stile grafico minimo per renderlo più "Amazon"
st.title("📦 Amazon SWAG Program")
st.markdown("---")
st.write("Benvenuto! Registrati qui sotto per iniziare ad accumulare punti SWAG.")

# 2. Collegamento al tuo foglio Google
# Ho inserito il link che mi hai fornito
url = "https://docs.google.com/spreadsheets/d/1zcW2RmucH-zrPNphehPjYmohf8cj-_-TQST2iwvNmfU/edit?usp=sharing"

# Creiamo la connessione
conn = st.connection("gsheets", type=GSheetsConnection)

# Leggiamo i dati attuali (per poterli aggiornare dopo)
df = conn.read(spreadsheet=url)

# --- SEZIONE 1: MODULO DI REGISTRAZIONE ---
with st.expander("➕ CLICCA QUI PER ISCRIVERTI AL PROGRAMMA"):
    with st.form("form_registro", clear_on_submit=True):
        nome = st.text_input("Il tuo Nome")
        cognome = st.text_input("Il tuo Cognome")
        email = st.text_input("La tua Email (opzionale)")
        
        submit = st.form_submit_button("Invia Iscrizione")
        
        if submit:
            if nome and cognome:
                # Creiamo la nuova riga con i dati inseriti
                # Nota: assegniamo 0 punti di default ai nuovi iscritti
                nuovo_utente = pd.DataFrame([{"Nome": nome, "Cognome": cognome, "Email": email, "Punti": 0}])
                
                # Uniamo i vecchi dati con il nuovo utente
                updated_df = pd.concat([df, nuovo_utente], ignore_index=True)
                
                # Aggiorniamo il foglio Google
                conn.update(spreadsheet=url, data=updated_df)
                
                st.success(f"Ottimo {nome}! Ti sei registrato correttamente. Vedrai il tuo nome nella lista tra pochi istanti.")
                st.balloons()
            else:
                st.error("Per favore, inserisci almeno Nome e Cognome per procedere.")

# --- SEZIONE 2: VISUALIZZAZIONE PUNTI ---
st.markdown("---")
st.subheader("💰 La tua situazione Punti")

# Rileggiamo i dati aggiornati per mostrarli nella tabella
data_display = conn.read(spreadsheet=url)

# Mostriamo solo le colonne che servono ai dipendenti (Nome, Cognome e Punti)
if not data_display.empty:
    st.dataframe(data_display[["Nome", "Cognome", "Punti"]], use_container_width=True, hide_index=True)
else:
    st.info("Al momento non ci sono iscritti. Sii il primo!")

# --- SEZIONE 3: LE 10 REGOLE (Promemoria) ---
st.sidebar.header("🎯 Come guadagnare")
st.sidebar.info("""
Ecco alcune attività:
1. Zero errori nel turno
2. Straordinario programmato
3. Segnalazione sicurezza
4. (Aggiungi qui le altre tue 7 attività...)
""")
