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
                    df_anagrafica = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all").fillna("")
                    nuovo_utente = pd.DataFrame([{
                        "Nome": nome, "Cognome": cognome, 
                        "Email": email if email else "", "Punti_Totali": 0
                    }])
                    updated_df = pd.concat([df_anagrafica, nuovo_utente], ignore_index=True)
                    conn.update(worksheet="Anagrafica", data=updated_df)
                    st.success(f"Benvenuto {nome}! Registrazione completata.")
                    st.balloons()
                except Exception as e:
                    st.error(f"ERRORE: {e}")
            else:
                st.warning("Nome e Cognome obbligatori!")

# --- SEZIONE 2: I MIEI PUNTI ---
elif scelta == "I miei Punti":
    st.header("💰 Il tuo Saldo Punti")
    
    try:
        df_totali = conn.read(worksheet="Anagrafica", ttl=0).dropna(how="all")
        
        if not df_totali.empty:
            lista_nomi = (df_totali['Nome'].astype(str) + " " + df_totali['Cognome'].astype(str)).tolist()
            utente_sel = st.selectbox("Seleziona il tuo nome:", lista_nomi)
            
            if utente_sel:
                n_sel, c_sel = utente_sel.split(" ", 1)
                
                # Leggiamo il registro attività
                try:
                    df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all")
                    
                    # FILTRO: prendiamo solo le righe di questo utente
                    storico_utente = df_log[(df_log['Nome'] == n_sel) & (df_log['Cognome'] == c_sel)]
                    
                    # CALCOLO MAGICO: Sommiamo i punti della colonna Punti_Assegnati
                    if not storico_utente.empty:
                        # Convertiamo in numeri per sicurezza
                        punti_numerici = pd.to_numeric(storico_utente['Punti_Assegnati'], errors='coerce').fillna(0)
                        totale_reale = int(punti_numerici.sum())
                    else:
                        totale_reale = 0
                    
                    # Mostriamo il totale calcolato
                    st.metric("Saldo Attuale", f"{totale_reale} SWAG Points")
                    
                    st.markdown("### 📋 Cronologia Attività")
                    if not storico_utente.empty:
                        st.dataframe(storico_utente[["Data", "Punti_Assegnati", "Attività"]], use_container_width=True, hide_index=True)
                    else:
                        st.info("Nessuna attività registrata ancora.")
                except Exception as e:
                    st.metric("Saldo Attuale", "0 SWAG Points")
                    st.info("Inizia a guadagnare i tuoi primi punti!")
        else:
            st.info("Nessun utente registrato.")
    except Exception as e:
        st.error(f"ERRORE LETTURA: {e}")

elif scelta == "Regolamento":
    st.header("📜 Regolamento")
    st.write("Le attività verranno caricate a breve.")
