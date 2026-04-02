import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Impostazioni della Pagina
st.set_page_config(page_title="Amazon SWAG", page_icon="📦", layout="centered")

st.title("📦 Amazon SWAG Program")
st.write("Gestione punti e iscrizioni dipendenti")
st.markdown("---")

# 2. Link pulito al tuo Google Sheet
# Ho rimosso la parte finale del link per stabilità
url = "https://docs.google.com/spreadsheets/d/1zcW2RmucH-zrPNphehPjYmohf8cj-_-TQST2iwvNmfU/"

# Creiamo la connessione
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Menu laterale
scelta = st.sidebar.radio("Scegli operazione:", ["Registrazione", "I miei Punti", "Regolamento"])

# --- SEZIONE 1: REGISTRAZIONE ---
if scelta == "Registrazione":
    st.header("📝 Modulo d'Iscrizione")
    with st.form("form_iscrizione", clear_on_submit=True):
        nome = st.text_input("Il tuo Nome")
        cognome = st.text_input("Il tuo Cognome")
        email = st.text_input("Email (facoltativa)")
        submit = st.form_submit_button("Invia Iscrizione")
        
        if submit:
            if nome and cognome:
                try:
                    # Leggiamo i dati attuali
                    df_anagrafica = conn.read(spreadsheet=url, worksheet="Anagrafica")
                    
                    # Creiamo la nuova riga
                    nuovo_utente = pd.DataFrame([{
                        "Nome": nome, 
                        "Cognome": cognome, 
                        "Email": email, 
                        "Punti_Totali": 0
                    }])
                    
                    # Uniamo i dati e carichiamo
                    updated_df = pd.concat([df_anagrafica, nuovo_utente], ignore_index=True)
                    conn.update(spreadsheet=url, data=updated_df, worksheet="Anagrafica")
                    
                    st.success(f"Benvenuto {nome}! Registrazione completata con successo.")
                    st.balloons()
                except Exception as e:
                    st.error("Errore nella scrittura. Assicurati che l'accesso al foglio sia 'Editor' nelle impostazioni di condivisione di Google.")
            else:
                st.warning("Nome e Cognome sono obbligatori!")

# --- SEZIONE 2: I MIEI PUNTI ---
elif scelta == "I miei Punti":
    st.header("💰 Il tuo Saldo Punti")
    
    try:
        # Leggiamo entrambi i fogli
        df_totali = conn.read(spreadsheet=url, worksheet="Anagrafica")
        df_log = conn.read(spreadsheet=url, worksheet="Log_Punti")

        if not df_totali.empty:
            # Creiamo la lista per la ricerca
            lista_nomi = (df_totali['Nome'] + " " + df_totali['Cognome']).tolist()
            utente_sel = st.selectbox("Seleziona il tuo nome:", lista_nomi)
            
            if utente_sel:
                # Recuperiamo i dati dell'utente selezionato
                n_sel, c_sel = utente_sel.split(" ", 1)
                
                # Mostra Totale
                punti_row = df_totali.loc[(df_totali['Nome'] == n_sel) & (df_totali['Cognome'] == c_sel)]
                if not punti_row.empty:
                    punti_tot = punti_row['Punti_Totali'].values[0]
                    st.metric("Saldo Attuale", f"{punti_tot} SWAG Points")
                
                st.markdown("### 📋 Cronologia Attività")
                # Filtra lo storico dal foglio Log_Punti
                storico_utente = df_log[(df_log['Nome'] == n_sel) & (df_log['Cognome'] == c_sel)]
                
                if not storico_utente.empty:
                    # Mostra solo Data, Punti Assegnati e Attività
                    st.dataframe(storico_utente[["Data", "Punti_Assegnati", "Attività"]], use_container_width=True, hide_index=True)
                else:
                    st.info("Nessuna attività registrata ancora. Continua così!")
        else:
            st.info("Nessun utente registrato.")
    except Exception as e:
        st.error("Non riesco a leggere i dati. Controlla che i nomi delle schede siano 'Anagrafica' e 'Log_Punti'.")

# --- SEZIONE 3: REGOLAMENTO ---
elif scelta == "Regolamento":
    st.header("📜 Come guadagnare punti")
    st.write("Segui queste attività per accumulare punti SWAG:")
    st.info("Qui potrai elencare le tue 10 attività specifiche.")
