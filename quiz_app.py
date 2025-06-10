import streamlit as st
import pandas as pd
import random

# Carica il file Excel
df = pd.read_excel("quiz.xlsx")
df.columns = df.columns.str.strip()  # rimuove eventuali spazi nelle intestazioni

# Titolo app
st.title("🧠 Simulatore di Quiz")

# Inizializzazione dello stato
if "indice" not in st.session_state:
    st.session_state.indice = 0
    st.session_state.punteggio = 0
    st.session_state.mostra_risposta = False
    st.session_state.domande = df.sample(frac=1).reset_index(drop=True)  # mischia domande
    st.session_state.ordini_risposte = []
    for i in range(len(st.session_state.domande)):
        risposte = [
            ("A", st.session_state.domande.iloc[i]["Risposta A"]),
            ("B", st.session_state.domande.iloc[i]["Risposta B"]),
            ("C", st.session_state.domande.iloc[i]["Risposta C"]),
        ]
        random.shuffle(risposte)
        st.session_state.ordini_risposte.append(risposte)

# Controlla se ci sono ancora domande
if st.session_state.indice < len(st.session_state.domande):
    domanda = st.session_state.domande.iloc[st.session_state.indice]
    st.subheader(f"Domanda {st.session_state.indice + 1}:")
    st.write(domanda["Domanda"])

    # Opzioni mescolate
    risposte_mischiate = st.session_state.ordini_risposte[st.session_state.indice]
    opzioni = {lettera: testo for lettera, testo in risposte_mischiate}

    # Trova risposta corretta mescolata
    corretta_lettera = domanda["Corretta"].strip()
    corretta_testo = domanda[f"Risposta {corretta_lettera}"].strip()
    lettera_corretta_mischiata = next(
        (lettera for lettera, testo in risposte_mischiate if testo == corretta_testo), None
    )

    risposta_utente = st.radio(
        "Scegli una risposta:",
        list(opzioni.keys()),
        format_func=lambda x: f"{x}) {opzioni[x]}",
        key=f"risposta_{st.session_state.indice}"
    )

    if not st.session_state.mostra_risposta:
        if st.button("Conferma"):
            st.session_state.mostra_risposta = True
            if risposta_utente == lettera_corretta_mischiata:
                st.session_state.punteggio += 1

    if st.session_state.mostra_risposta:
        if risposta_utente == lettera_corretta_mischiata:
            st.success("✅ Corretto!")
        else:
            st.error(f"❌ Sbagliato. La risposta corretta era: {lettera_corretta_mischiata}) {opzioni[lettera_corretta_mischiata]}")

        if st.button("Prossima domanda"):
            st.session_state.indice += 1
            st.session_state.mostra_risposta = False
            st.rerun()

else:
    # Fine del quiz
    st.success("🎉 Hai completato il quiz!")
    st.write(f"**Punteggio finale: {st.session_state.punteggio} su {len(st.session_state.domande)}**")

    if st.button("Ricomincia"):
        st.session_state.clear()
        st.rerun()
