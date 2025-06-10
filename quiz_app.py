import streamlit as st
import json
import random
import pandas as pd

UTENTI_FILE = "utenti.json"
QUIZ_FILE = "quiz.xlsx"

# --- Funzioni Utility ---
def carica_utenti():
    try:
        with open(UTENTI_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def salva_utenti(utenti):
    with open(UTENTI_FILE, "w") as f:
        json.dump(utenti, f, indent=4)

def carica_quiz():
    df = pd.read_excel(QUIZ_FILE)
    df.columns = df.columns.str.strip()
    return df.to_dict(orient="records")

# --- Login ---
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
                st.session_state.login_rerun = True
            else:
                st.error("Username o password errati")
        if st.session_state.get("login_rerun", False):
            st.session_state.login_rerun = False
            st.rerun()
    else:
        st.sidebar.write(f"Benvenuto, {st.session_state.username}!")
        modalita = st.sidebar.radio("Scegli la modalità", ("Esercizi", "Simulazione Esame"))
        st.session_state.modalita = modalita
        if st.sidebar.button("Logout"):
            st.session_state.clear()
            st.rerun()

# --- Modalità Esercizi ---
def esercizi():
    st.header("Modalità Esercizi")

    if "quiz" not in st.session_state:
        st.session_state.quiz = carica_quiz()
        st.session_state.indice = 0
        st.session_state.risposte_date = {}

    quiz = st.session_state.quiz
    i = st.session_state.indice

    if i < len(quiz):
        q = quiz[i]
        st.write(f"**Domanda {i+1}:** {q['Domanda']}")

        risp = [q["Risposta A"], q["Risposta B"], q["Risposta C"]]
        random.shuffle(risp)
        scelta = st.radio("Seleziona la risposta:", risp, key=f"q{i}")

        if st.button("Conferma risposta"):
            corretta = str(q.get("Corretta", "")).strip().upper()
            chiave = f"Risposta {corretta}"
            if chiave not in q:
                st.error(f"Errore interno: '{chiave}' non presente.")
                st.stop()
            corretta_text = str(q[chiave]).strip()
            st.session_state.risposte_date[i] = (scelta == corretta_text)
            if scelta == corretta_text:
                st.success("✅ Risposta corretta!")
            else:
                st.error(f"❌ Sbagliata. La risposta corretta è: {corretta_text}")
            st.session_state.indice += 1
            st.rerun()
    else:
        corrette = sum(st.session_state.risposte_date.values())
        st.write(f"Risposte corrette: **{corrette}** su **{len(quiz)}** domande")

# --- Modalità Simulazione Esame ---
def simulazione_esame():
    st.header("Simulazione Esame")

    if "esame_domande" not in st.session_state:
        full = carica_quiz()
        n = min(40, len(full))
        st.session_state.esame_domande = random.sample(full, n)
        st.session_state.esame_indice = 0
        st.session_state.esame_punteggio = 0.0

    domande = st.session_state.esame_domande
    j = st.session_state.esame_indice

    if j < len(domande):
        q = domande[j]
        st.write(f"**Domanda {j+1}/{len(domande)}:** {q['Domanda']}")
        risp = [q["Risposta A"], q["Risposta B"], q["Risposta C"]]
        random.shuffle(risp)
        scelta = st.radio("Risposta (lascia vuoto per omettere):", [""] + risp, key=f"es{j}")

        if st.button("Conferma risposta", key=f"btn{j}"):
            corretta = str(q.get("Corretta", "")).strip().upper()
            chiave = f"Risposta {corretta}"
            if chiave not in q:
                st.error(f"Errore interno: '{chiave}' non presente.")
                st.stop()
            corretta_text = str(q[chiave]).strip()
            if scelta == "":
                pun = 0
                st.info("⚠️ Domanda omessa.")
            elif scelta == corretta_text:
                pun = 0.75
                st.success("✅ Risposta corretta!")
            else:
                pun = -0.25
                st.error(f"❌ Errata. Risposta corretta: {corretta_text}")
            st.session_state.esame_punteggio += pun
            st.session_state.esame_indice += 1
            st.rerun()
    else:
        tot = len(domande)
        punteggio = st.session_state.esame_punteggio
        st.write(f"Punteggio finale: **{punteggio:.2f}** su **{tot * 0.75:.2f}**")
        st.write(f"Percentuale: **{(punteggio / (tot * 0.75) * 100):.1f}%**")

# --- Main ---
def main():
    login()
    if st.session_state.get("logged_in", False):
        m = st.session_state.get("modalita", "Esercizi")
        if m == "Esercizi":
            esercizi()
        else:
            simulazione_esame()

if __name__ == "__main__":
    main()
