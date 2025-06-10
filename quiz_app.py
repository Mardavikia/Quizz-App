import streamlit as st
import pandas as pd
import random

# Carica file Excel
df = pd.read_excel("quiz.xlsx")
df.columns = df.columns.str.strip()  # pulisce eventuali spazi bianchi

st.title("🧠 Simulatore di Quiz")

# Mescola domande una volta (usa random_state per riproducibilità se vuoi)
if "domande" not in st.session_state:
    st.session_state.domande = df.sample(frac=1).reset_index(drop=True)
    st.session_state.indice = 0
    st.session_state.punteggio = 0
    st.session_state.mostra_risposta = False

if st.session_state.indice < len(st.session_state.domande):
    domanda = st.session_state.domande.iloc[st.session_state.indice]
    st.subheader(f"Domanda {st.session_state.indice + 1}:")
    st.write(domanda["Domanda"])

    # Prepara le risposte in lista (tupla: codice, testo)
    risposte_originali = [
        ("A", domanda["Risposta A"]),
        ("B", domanda["Risposta B"]),
        ("C", domanda["Risposta C"])
    ]

    # Mischia le risposte
    random.shuffle(risposte_originali)

    # Crea un dizionario per mappare la risposta scelta al codice originale
    # es. {'A': 'Risposta B', ...} -> dobbiamo tenere traccia di quale risposta è corretta
    risposta_corretta_originale = domanda["Corretta"]

    # Trova la lettera (A/B/C) della risposta corretta nell'ordine originale
    testo_risposta_corretta = domanda[f"Risposta {risposta_corretta_originale}"]

    # Ora associare a ciascuna opzione (posizione) il codice "fittizio" A, B, C per l'utente
    lettere_opzioni = ["A", "B", "C"]
    opzioni_mischiate = {lettere_opzioni[i]: risposte_originali[i][1] for i in range(3)}

    # Trova quale lettera (A/B/C) corrisponde alla risposta corretta nelle risposte miste
    risposta_corretta_mischiata = None
    for k, v in opzioni_mischiate.items():
        if v == testo_risposta_corretta:
            risposta_corretta_mischiata = k
            break
