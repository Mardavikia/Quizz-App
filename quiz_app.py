import streamlit as st
import pandas as pd
import random

# Carica file Excel
df = pd.read_excel("quiz.xlsx")
df.columns = df.columns.str.strip()  # pulisce eventuali spazi bianchi

st.title("🧠 Simulatore di Quiz")

# Inizializza domande mischiando ordine delle domande e delle risposte (una volta sola)
if "domande" not in st.session_state:
    st.session_state.domande = df.sample(frac=1).reset_index(drop=True)
    st.session_state.indice = 0
    st.session_state.punteggio = 0
    st.session_state.mostra_risposta = False
    st.session_state.ordini_risposte = []  # salveremo qui l'ordine random di risposte per ogni domanda

    # Prepara ordine delle risposte per ogni domanda
    for i in range(len(st.session_state.domande)):
        risposte = [
            ("A", st.session_state.domande.iloc[i]["Risposta A"]),
            ("B", st.session_state.domande.iloc[i]["Risposta B"]),
            ("C", st.session_state.domande.iloc[i]["Risposta C"]),
        ]
        random.shuffle(risposte)
        st.session_state.ordini_risposte.append(risposte)

if st.session_state.indice < len(st.session_state.domande):
    domanda = st.session_state.domande.iloc[st.session_state.indice]
    st.subheader(f"Domanda {st.session_state.indice + 1}:")
    st.write(domanda["Domanda"])

    risposte_mischiate = st.session_state.ordini_risposte[st.session_state.indice]
    lettere_opzioni = ["A", "B", "C"]

    # Dizionario opzioni per radio
    opzioni = {lettere_opzioni[i]: risposte_mischiate[i][1] for i in range(3)}

    # Trova quale lettera (A/B/C) nelle risposte mischiate corrisponde alla risposta corretta originale
    risposta_corretta_originale = domanda["Corretta"]
    testo_risposta_corretta = domanda[f"Risposta {risposta_corretta_originale}"]

    risposta_corretta_mischiata = None
    for k, v in opzioni.items():
        if v == testo_risposta_corretta:
            risposta_corretta_mischiata = k
            break

    # Chiave unica per il widget radio per farlo aggiornare correttamente
    key_radio = f"risposta_{st.session_state.indice}"

    risposta_utente = st.radio(
        "Scegli una risposta:", 
        lettere_opzioni, 
        format_func=lambda x: f"{x}) {opzioni[x]}",
        key=key_radio
    )

    if st.button("Conferma"):
        st.session_state.mostra_risposta = True

        if risposta_utente == risposta_corretta_mischiata:
            st.session_state.punteggio += 1

    if st.session_state.mostra_risposta:
        if risposta_utente == risposta_corretta_mischiata:
            st.success("✅ Corretto!")
        else:
            st.error(f"❌ Sbagliato. La risposta corretta era: {risposta_corretta_mischiata}) {opzioni[risposta_corretta_mischiata]}")

        if st.button("Prossima domanda"):
            st.session_state.indice += 1
            st.session_state.mostra_risposta = False
            st.experimental_rerun()
else:
    st.success("🎉 Hai completato il quiz!")
    st.write(f"**Punteggio finale: {st.session_state.punteggio} su {len(st.session_state.domande)}**")

    if st.button("Ricomincia"):
        st.session_state.indice = 0
        st.session_state.punteggio = 0
        st.session_state.mostra_risposta = False
        st.experimental_rerun()
