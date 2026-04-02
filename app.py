import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Amazon SWAG", page_icon="📦", layout="centered")

st.title("📦 Amazon SWAG Program")
st.write("Gestione punti e iscrizioni dipendenti")
st.markdown("---")

conn = st.connection("gsheets", type=GSheetsConnection)

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
                    # 1. Leggiamo i dati aggirando la cache (ttl=0)
                    df_anagrafica = conn.read(worksheet="Anagrafica", ttl=0)
                    
                    # 2. IL TRUCCO: Puliamo le celle vuote che fanno arrabbiare Google!
                    df_anagrafica = df_anagrafica.dropna(how="all")
                    df_anagrafica = df_anagrafica.fillna("")
                    
                    # 3. Creiamo la nuova riga
                    nuovo_utente = pd.DataFrame([{
                        "Nome": nome, 
                        "Cognome": cognome, 
                        "Email": email if email else "", 
                        "Punti_Totali": 0
                    }])
                    
                    # 4. Uniamo e carichiamo
                    updated_df = pd.concat([df_anagrafica, nuovo_utente], ignore_index=True)
                    conn.update(worksheet="Anagrafica", data=updated_df)
                    
                    st.success(f"Benvenuto {nome}! Registrazione completata con successo.")
                    st.balloons()
                except Exception as e:
                    st.error(f"ERRORE TECNICO: {e}")
            else:
                st.warning("Nome e Cognome sono obbligatori!")

# --- SEZIONE 2: I MIEI PUNTI ---
elif scelta == "I miei Punti":
    st.header("💰 Il tuo Saldo Punti")
    
    try:
        df_totali = conn.read(worksheet="Anagrafica", ttl=0)
        df_log = conn.read(worksheet="Log_Punti", ttl=0)

        # Pulizia base per evitare problemi di lettura
        df_totali = df_totali.dropna(how="all")
        df_log = df_log.dropna(how="all")

        if not df_totali.empty:
            lista_nomi = (df_totali['Nome'].astype(str) + " " + df_totali['Cognome'].astype(str)).tolist()
            utente_sel = st.selectbox("Seleziona il tuo nome:", lista_nomi)
            
            if utente_sel:
                n_sel, c_sel = utente_sel.split(" ", 1)
                
                punti_row = df_totali.loc[(df_totali['Nome'] == n_sel) & (df_totali['Cognome'] == c_sel)]
                if not punti_row.empty:
                    punti_tot = punti_row['Punti_Totali'].values[0]
                    st.metric("Saldo Attuale", f"{punti_tot} SWAG Points")
                
                st.markdown("### 📋 Cronologia Attività")
                storico_utente = df_log[(df_log['Nome'] == n_sel) & (df_log['Cognome'] == c_sel)]
                
                if not storico_utente.empty:
                    st.dataframe(storico_utente[["Data", "Punti_Assegnati", "Attività"]], use_container_width=True, hide_index=True)
                else:
                    st.info("Nessuna attività registrata ancora. Continua così!")
        else:
            st.info("Nessun utente registrato.")
    except Exception as e:
        st.error(f"ERRORE TECNICO LETTURA: {e}")

# --- SEZIONE 3: REGOLAMENTO ---
elif scelta == "Regolamento":
    st.header("📜 Come guadagnare punti")
    st.write("Segui queste attività per accumulare punti SWAG:")
    st.info("Qui potrai elencare le tue 10 attività specifiche.")
