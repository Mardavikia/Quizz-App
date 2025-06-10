import streamlit as st
import pandas as pd

# Carica file Excel
df = pd.read_excel("quiz.xlsx")

# Inizializza stato sessione
if "indice" not in st.session_state:
    st.session_state.indice = 0
    st.session_state.punteggio = 0
    st.session_state.mostra_risposta = False

st.title("🧠 Simulatore di Quiz")

# Mescola domande solo all'inizio
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

if st.session_state.indice < len(df):
    domanda = df.iloc[st.session_state.indice]
    st.subheader(f"Domanda {st.session_state.indice + 1}:")
    st.write(domanda["Domanda"])

    opzioni = {
        "A": domanda["Risposta A"],
        "B": domanda["Risposta B"],
        "C": domanda["Risposta C"]
    }

    risposta_utente = st.radio("Scegli una risposta:", list(opzioni.keys()), format_func=lambda x: f"{x}) {opzioni[x]}", key=f"risposta_{st.session_state.indice}")

    if st.button("Conferma"):
        st.session_state.mostra_risposta = True
        if risposta_utente == domanda["Corretta"]:
            st.session_state.punteggio += 1

    if st.session_state.mostra_risposta:
        risposta_corretta = domanda["Corretta"]
        if risposta_utente == risposta_corretta:
            st.success("✅ Corretto!")
        else:
            st.error(f"❌ Sbagliato. La risposta corretta era: {risposta_corretta}) {opzioni[risposta_corretta]}")

        if st.button("Prossima domanda"):
            st.session_state.indice += 1
            st.session_state.mostra_risposta = False
            st.experimental_rerun()
else:
    st.success("🎉 Hai completato il quiz!")
    st.write(f"**Punteggio finale: {st.session_state.punteggio} su {len(df)}**")

    if st.button("Ricomincia"):
        st.session_state.indice = 0
        st.session_state.punteggio = 0
        st.session_state.mostra_risposta = False
        st.experimental_rerun()
