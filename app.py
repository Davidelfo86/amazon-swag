import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Configurazione base dell'app
st.set_page_config(page_title="Amazon SWAG", page_icon="📦")

st.title("📦 Benvenuto in Amazon SWAG")
st.write("Registrati per iniziare a guadagnare punti!")

# 2. Collegamento al tuo foglio (Inserisci il tuo link qui sotto)
url = "IL_TUO_LINK_DI_GOOGLE_SHEETS_QUI"

conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Funzione di Registrazione
with st.expander("➕ Clicca qui per registrarti"):
    with st.form("registro"):
        nome = st.text_input("Il tuo Nome")
        cognome = st.text_input("Il tuo Cognome")
        email = st.text_input("La tua Email Amazon (opzionale)")
        submit = st.form_submit_button("Invia Iscrizione")
        
        if submit:
            if nome and cognome:
                # Qui diciamo all'app di aggiungere una riga al foglio
                new_data = pd.DataFrame([{"Nome": nome, "Cognome": cognome, "Email": email, "Punti": 0}])
                # Nota: Per scrivere servono i permessi "Secrets", li vedremo al prossimo step!
                st.success(f"Ciao {nome}! Ti sei registrato con successo.")
            else:
                st.error("Inserisci Nome e Cognome!")

# 4. Visualizzazione Classifica/Punti
st.divider()
st.subheader("💰 Classifica Punti Attuale")
data = conn.read(spreadsheet=url, usecols=[0,1,3]) # Legge Nome, Cognome e Punti
st.dataframe(data, use_container_width=True)
