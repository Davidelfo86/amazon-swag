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
                    # Manteniamo solo le colonne necessarie
                    cols = ["Nome", "Cognome", "Email", "Punti_Totali"]
                    df_anagrafica = df_anagrafica[[c for c in cols if c in df_anagrafica.columns]]
                    
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
        # Rimuoviamo eventuali colonne fantasma in lettura
        df_totali = df_totali.loc[:, ~df_totali.columns.astype(str).str.contains('^Unnamed')]
        
        if not df_totali.empty:
            lista_nomi = (df_totali['Nome'].astype(str) + " " + df_totali['Cognome'].astype(str)).tolist()
            utente_sel = st.selectbox("Seleziona il tuo nome:", lista_nomi)
            
            if utente_sel:
                n_sel, c_sel = utente_sel.split(" ", 1)
                
                try:
                    df_log = conn.read(worksheet="Log_Punti", ttl=0).dropna(how="all")
                    df_log = df_log.loc[:, ~df_log.columns.astype(str).str.contains('^Unnamed')]
                    
                    storico_utente = df_log[(df_log['Nome'] == n_sel) & (df_log['Cognome'] == c_sel)]
                    
                    if not storico_utente.empty:
                        punti_numerici = pd.to_numeric(storico_utente['Punti_Assegnati'], errors='coerce').fillna(0)
                        totale_reale = int(punti_numerici.sum())
                    else:
                        totale_reale = 0
                    
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

# --- SEZIONE 3: REGOLAMENTO ---
elif scelta == "Regolamento":
    st.header("📜 Regolamento e Attività SWAG")
    st.write("Scopri come guadagnare i tuoi SWAG Points. Ecco tutte le attività valide divise per categoria:")
    
    with st.expander("🤝 HR & Personal Development", expanded=True):
        st.markdown("""
        * **Peak Hero:** For those who participated in Peak ➔ **+5 Swaggies**
        * **Prime Day Hero:** For those who participated in Prime Day ➔ **+3 Swaggies**
        * **GB/BB Conversion:** SAs going from GB to BB ➔ **+6 Swaggies**
        * **Active Ambassador:** Participates as an active ambassador at least once in the month ➔ **+3 Swaggies**
        * **Night activities/Gemba Walk:** SAs who participate in the monthly walk ➔ **+3 Swaggies**
        * **Fun Events:** Active participation in Fun Events ➔ **+3 Swaggies**
        * **Away Team member:** Members of the Away team for the launch of a new DS ➔ **+15 Swaggies**
        * **Voice of Associates best idea:** SA who proposed the best improvement idea via the board ➔ **+10 Swaggies**
        """)

    with st.expander("⭐ Quality", expanded=False):
        st.markdown("""
        * **Gold NOV:** Monthly DS NOV result below 15 DPMO (for everyone) ➔ **+2 Swaggies**
        * **Silver NOV:** Monthly DS NOV result below 30 DPMO (for everyone) ➔ **+1 Swaggie**
        """)

    with st.expander("🦺 Safety", expanded=False):
        st.markdown("""
        * **Kaizen Idea Implementation:** Concrete implementation of a Kaizen idea ➔ **+10 Swaggies**
        * **Safety Hero:** The well-deserved award for the “Safety” hero of the month ➔ **+10 Swaggies**
        """)

    with st.expander("🏢 Delivery Station Development", expanded=False):
        st.markdown("""
        * **Happy Birthday:** Best wishes from the SWAG team on your birthday ➔ **+5 Swaggies**
        * **Delivery Station Birthday:** Everyone in DS on the anniversary of the opening ➔ **+3 Swaggies**
        * **WW Scorecard Top 10:** For contributing to reaching a TOP 10 WW ranking ➔ **+7 Swaggies**
        * **Buddy DS:** Helping train intended new hires launching a new site ➔ **+5 Swaggies**
        """)

    with st.expander("🌱 Sustainability", expanded=False):
        st.markdown("""
        * **Kaizen Sustainability Idea:** SAs who propose ideas evaluated by the OPS team ➔ **+1 Swaggie**
        * **Kaizen Sustainability Implementation:** Concrete implementation of the idea ➔ **+3 Swaggies**
        """)
        
    st.info("💡 **Ricorda:** I punti verranno accreditati direttamente dai Manager nel tuo storico personale!")
