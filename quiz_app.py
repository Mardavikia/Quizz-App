import streamlit as st
import json
import random
import pandas as pd

# Carica utenti da JSON
def carica_utenti():
    try:
        with open("utenti.json", "r") as f:
            return json.load(f)
    except:
        return {}

# Carica quiz da Excel
def carica_quiz():
    df = pd.read_excel("quiz.xlsx")
    return df.to_dict(orient="records")

# Login
def login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""

    if not st.session_state.logged_in:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_premuto = st.button("Login")

        if login_premuto:
            utenti = carica_utenti()
            if username in utenti and utenti[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.login_rerun = True
            else:
                st.error("Username o password errati")

        if st.session_state.get("login_rerun", False):
            st.session_state.login_rerun = False
            st.experimental_rerun()

    else:
        st.sidebar.write(f"Benvenuto, {st.session_state.username}!")
        modalita = st.sidebar.radio(
            "Scegli la modalità",
            ("Esercizi", "Simulazione Esame"),
            index=0
        )
        st.session_state.modalita = modalita

        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            # Pulizia stato quiz/esame
            for key in ["quiz", "indice", "risposte_date", "esame_domande", "esame_indice", "esame_punteggio"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.experimental_rerun()

# Modalità esercizi (quiz semplice)
def esercizi():
    st.header("Modalità Esercizi")

    if "quiz" not in st.session_state:
        st.session_state.quiz = carica_quiz()
        st.session_state.indice = 0
        st.session_state.risposte_date = {}

    quiz = st.session_state.quiz
    indice = st.session_state.indice

    if indice < len(quiz):
        domanda = quiz[indice]
        st.write(f"**Domanda {indice+1}:** {domanda['Domanda']}")

        risposte = [domanda["Risposta A"], domanda["Risposta B"], domanda["Risposta C"]]
        random.shuffle(risposte)

        scelta = st.radio("Seleziona la risposta:", risposte, key=f"q{indice}")

        if st.button("Conferma risposta"):
            corretta = domanda["Corretta"].strip()
            risposta_corretta = domanda[f"Risposta {corretta}"].strip()

            st.session_state.risposte_date[indice] = (scelta == risposta_corretta)
            if scelta == risposta_corretta:
                st.success("✅ Risposta corretta!")
            else:
                st.error(f"❌ Risposta sbagliata. La risposta corretta è: {risposta_corretta}")

            st.session_state.indice += 1
            st.experimental_rerun()

    else:
        corrette = sum(v for v in st.session_state.risposte_date.values())
        totale = len(st.session_state.quiz)
        st.write(f"**Hai completato il quiz!**")
        st.write(f"Risposte corrette: {corrette} su {totale}")

# Modalità simulazione esame
def simulazione_esame():
    st.header("Modalità Simulazione Esame")

    if "esame_domande" not in st.session_state:
        quiz = carica_quiz()
        # Prendi 40 domande casuali (se meno di 40 usa tutte)
        n = min(40, len(quiz))
        st.session_state.esame_domande = random.sample(quiz, n)
        st.session_state.esame_indice = 0
        st.session_state.esame_punteggio = 0.0
        st.session_state.esame_risposte = {}

    domande = st.session_state.esame_domande
    indice = st.session_state.esame_indice

    if indice < len(domande):
        domanda = domande[indice]
        st.write(f"**Domanda {indice+1} di {len(domande)}:** {domanda['Domanda']}")

        risposte = [domanda["Risposta A"], domanda["Risposta B"], domanda["Risposta C"]]
        random.shuffle(risposte)

        scelta = st.radio("Seleziona la risposta (o lascia vuoto per saltare):", 
                          options=[""] + risposte, key=f"esame_q{indice}")

        if st.button("Conferma risposta"):
            corretta = domanda["Corretta"].strip()
            risposta_corretta = domanda[f"Risposta {corretta}"].strip()

            if scelta == "":
                # risposta omessa
                punteggio = 0
            elif scelta == risposta_corretta:
                punteggio = 0.75
            else:
                punteggio = -0.25

            st.session_state.esame_punteggio += punteggio
            st.session_state.esame_risposte[indice] = punteggio

            if punteggio == 0.75:
                st.success("✅ Risposta corretta!")
            elif punteggio == -0.25:
                st.error(f"❌ Risposta errata. La risposta corretta è: {risposta_corretta}")
            else:
                st.info("⚠️ Risposta omessa.")

            st.session_state.esame_indice += 1
            st.experimental_rerun()
    else:
        punteggio = st.session_state.esame_punteggio
        st.write("**Esame completato!**")
        st.write(f"Punteggio finale: {punteggio:.2f} su {len(st.session_state.esame_domande) * 0.75}")
        # Opzionale: visualizza statistiche dettagliate

# Main
def main():
    login()
    if st.session_state.get("logged_in", False):
        modalita = st.session_state.get("modalita", "Esercizi")
        if modalita == "Esercizi":
            esercizi()
        elif modalita == "Simulazione Esame":
            simulazione_esame()

if __name__ == "__main__":
    main()
