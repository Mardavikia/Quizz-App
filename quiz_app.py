import streamlit as st
import pandas as pd
import json
import os
import random

UTENTI_FILE = "utenti.json"
QUIZ_FILE = "quiz.xlsx"

# Funzioni per gestire utenti
def carica_utenti():
    if not os.path.exists(UTENTI_FILE):
        with open(UTENTI_FILE, "w") as f:
            json.dump({}, f)
    try:
        with open(UTENTI_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        with open(UTENTI_FILE, "w") as f:
            json.dump({}, f)
        return {}

def salva_utenti(utenti):
    with open(UTENTI_FILE, "w") as f:
        json.dump(utenti, f, indent=4)

# Login semplice
def login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""

    if not st.session_state.logged_in:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            utenti = carica_utenti()
            if username in utenti and utenti[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.experimental_rerun()
            else:
                st.error("Username o password errati")
    else:
        st.sidebar.write(f"Benvenuto, {st.session_state.username}!")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.experimental_rerun()

# Carica quiz da Excel
@st.cache_data
def carica_quiz():
    df = pd.read_excel(QUIZ_FILE)
    return df.to_dict(orient="records")

# Funzione per mischiare risposte e mantenerle associate alle lettere
def mischia_risposte(domanda):
    opzioni = {
        "A": domanda["Risposta A"],
        "B": domanda["Risposta B"],
        "C": domanda["Risposta C"],
    }
    lista = list(opzioni.items())
    random.shuffle(lista)
    return lista  # ritorna lista di tuple (lettera, testo)

# Pagina principale quiz
def quiz_app():
    st.title("Quiz")

    quiz = carica_quiz()
    utenti = carica_utenti()
    username = st.session_state.username

    if username not in utenti:
        utenti[username] = {"password": "", "errori": [], "storico": []}

    modalità = st.radio("Modalità", ["Tutte le domande", "Solo domande sbagliate", "Simula esame"])

    # Se modalità "Solo domande sbagliate" e non ce ne sono, avvisa e esci
    if modalità == "Solo domande sbagliate" and not utenti[username]["errori"]:
        st.warning("Non hai ancora domande sbagliate. Prova con tutte le domande.")
        return

    if modalità == "Simula esame":
        domande = random.sample(quiz, min(40, len(quiz)))
        punteggio = 0.0
        domanda_idx = st.session_state.get("domanda_idx", 0)
        risposte_date = st.session_state.get("risposte_date", [])

        if domanda_idx >= len(domande):
            st.write(f"**Esame terminato! Punteggio finale: {punteggio:.2f}**")
            if st.button("Ricomincia"):
                st.session_state.domanda_idx = 0
                st.session_state.risposte_date = []
                st.experimental_rerun()
            return

        domanda = domande[domanda_idx]
        st.write(f"Domanda {domanda_idx + 1} di {len(domande)}:")
        st.write(domanda["Domanda"])

        opzioni = mischia_risposte(domanda)
        scelta = st.radio("Scegli la risposta:", [t[1] for t in opzioni], key=f"q{domanda_idx}")

        if st.button("Conferma risposta"):
            # trova la lettera scelta
            scelta_lettera = None
            for lettera, testo in opzioni:
                if testo == scelta:
                    scelta_lettera = lettera
                    break

            corretta = domanda["Risposta Corretta"].strip().upper()
            # Calcola punteggio
            if scelta_lettera == corretta:
                punteggio += 0.75
            elif scelta_lettera is None:
                # risposta omessa
                punteggio += 0
            else:
                punteggio -= 0.25

            st.session_state.risposte_date.append((domanda_idx, scelta_lettera))
            st.session_state.domanda_idx = domanda_idx + 1
            st.experimental_rerun()

    else:
        if modalità == "Solo domande sbagliate":
            # Filtro solo domande sbagliate
            domande = [q for i, q in enumerate(quiz) if i in utenti[username]["errori"]]
        else:
            domande = quiz

        # Scegli domanda a caso
        domanda = random.choice(domande)
        st.write(domanda["Domanda"])

        opzioni = mischia_risposte(domanda)
        scelta = st.radio("Scegli la risposta:", [t[1] for t in opzioni], key="quiz_radio")

        if st.button("Conferma risposta"):
            scelta_lettera = None
            for lettera, testo in opzioni:
                if testo == scelta:
                    scelta_lettera = lettera
                    break
            corretta = domanda["Risposta Corretta"].strip().upper()

            if scelta_lettera == corretta:
                st.success("✅ Risposta corretta!")
                # rimuovi la domanda dagli errori se c'era
                try:
                    index_domanda = quiz.index(domanda)
                except:
                    index_domanda = None
                if index_domanda is not None and index_domanda in utenti[username]["errori"]:
                    utenti[username]["errori"].remove(index_domanda)
            else:
                st.error(f"❌ Risposta sbagliata. La risposta corretta era: {domanda[f'Risposta {corretta}']}")
                # salva errore
                try:
                    index_domanda = quiz.index(domanda)
                except:
                    index_domanda = None
                if index_domanda is not None and index_domanda not in utenti[username]["errori"]:
                    utenti[username]["errori"].append(index_domanda)

            # Salva utenti aggiornati
            salva_utenti(utenti)

            st.experimental_rerun()

def main():
    login()
    if st.session_state.get("logged_in", False):
        quiz_app()

if __name__ == "__main__":
    main()
