import streamlit as st
import pandas as pd
import random
import json
import os

# --- CONFIG PATH FILE ---
UTENTI_FILE = "utenti.json"
QUIZ_FILE = "quiz.xlsx"

# --- UTILI PER JSON ---
def carica_utenti():
    if not os.path.exists(UTENTI_FILE):
        # file vuoto se non esiste
        with open(UTENTI_FILE, "w") as f:
            json.dump({}, f)
    with open(UTENTI_FILE, "r") as f:
        return json.load(f)

def salva_utenti(data):
    with open(UTENTI_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- LOGIN ---
def login():
    st.title("🔐 Login")
    utenti = carica_utenti()
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Accedi"):
        if username in utenti and utenti[username]["password"] == password:
            st.session_state["username"] = username
            st.session_state["utenti"] = utenti
            st.success(f"Benvenuto, {username}!")
            st.experimental_rerun()
        else:
            st.error("Username o password errati.")
    st.stop()

# --- CARICAMENTO QUIZ ---
@st.cache_data
def carica_quiz():
    df = pd.read_excel(QUIZ_FILE)
    df.columns = df.columns.str.strip()
    return df

# --- FUNZIONI AIUTO ---
def inizializza_sessione(username, df):
    if "username" not in st.session_state or st.session_state["username"] != username:
        st.session_state.clear()
        st.session_state["username"] = username
        st.session_state["domande"] = df.copy()
        st.session_state["corrette"] = 0
        st.session_state["sbagliate"] = 0
        st.session_state["indici_sbagliate"] = set()
        st.session_state["indice"] = 0
        st.session_state["mostra_risposta"] = False
        st.session_state["modalita"] = "esercitazione"  # o "esame"
        st.session_state["esame_risposte"] = []  # per punteggio esame
        st.session_state["lista_domande"] = []
        st.session_state["errori_utente"] = set()
        st.session_state["esame_terminato"] = False

def miscela_risposte(domanda):
    risposte = [
        domanda["Risposta A"].strip(),
        domanda["Risposta B"].strip(),
        domanda["Risposta C"].strip()
    ]
    random.shuffle(risposte)
    return risposte

# --- FUNZIONE PRINCIPALE APP ---
def main():
    if "username" not in st.session_state:
        login()

    utenti = st.session_state.get("utenti", {})
    username = st.session_state["username"]
    df = carica_quiz()

    # Carica dati utente da json
    dati_utente = utenti.get(username, {"password": "", "errori": [], "storico": []})

    # Scelta modalità
    st.sidebar.title(f"Benvenuto, {username}")
    modalita = st.sidebar.radio("Scegli modalità:", ["Esercitazione", "Ripassa errori", "Simulazione esame"])
    st.session_state["modalita"] = modalita.lower()

    # Inizializza quiz in base a modalità
    if "indice" not in st.session_state or st.session_state["modalita"] != modalita.lower():
        st.session_state.clear()
        st.session_state["username"] = username
        st.session_state["modalita"] = modalita.lower()
        st.session_state["corrette"] = 0
        st.session_state["sbagliate"] = 0
        st.session_state["indice"] = 0
        st.session_state["mostra_risposta"] = False
        st.session_state["esame_risposte"] = []
        st.session_state["esame_terminato"] = False

        if modalita == "Esercitazione":
            st.session_state["lista_domande"] = df.sample(frac=1).reset_index(drop=True)
        elif modalita == "Ripassa errori":
            if not dati_utente["errori"]:
                st.info("Non hai errori da ripassare, torna in Esercitazione.")
                st.stop()
            else:
                st.session_state["lista_domande"] = df.loc[dati_utente["errori"]].reset_index(drop=True)
        else:  # Simulazione esame
            if len(df) < 40:
                st.error("Il quiz non ha abbastanza domande per l'esame (minimo 40 richieste).")
                st.stop()
            st.session_state["lista_domande"] = df.sample(n=40).reset_index(drop=True)

    lista_domande = st.session_state["lista_domande"]
    indice = st.session_state["indice"]

    if indice >= len(lista_domande):
        # Fine quiz/esame
        if st.session_state["modalita"] == "simulazione esame":
            punteggio = 0
            for r in st.session_state["esame_risposte"]:
                if r == "omessa":
                    punteggio += 0
                elif r == "corretta":
                    punteggio += 0.75
                else:
                    punteggio -= 0.25
            st.header("🎉 Esame terminato!")
            st.write(f"Punteggio finale: **{punteggio:.2f}** su massimo 30 punti (40 domande * 0.75)")
            st.write(f"Risposte corrette: {st.session_state['corrette']}")
            st.write(f"Risposte errate: {st.session_state['sbagliate']}")
            st.write(f"Domande omesse: {st.session_state['indice'] - st.session_state['corrette'] - st.session_state['sbagliate']}")
            # Salva storico
            utenti[username]["storico"].append({"tipo": "esame", "punteggio": punteggio})
            salva_utenti(utenti)
            if st.button("Ricomincia"):
                st.session_state.clear()
                st.experimental_rerun()
            return
        else:
            st.header("🎉 Hai completato il quiz!")
            st.write(f"Punteggio: {st.session_state['corrette']} corrette su {len(lista_domande)} domande")
            st.write(f"Errori totali: {st.session_state['sbagliate']}")
            if st.button("Ricomincia"):
                st.session_state.clear()
                st.experimental_rerun()
            return

    domanda = lista_domande.iloc[indice]
    st.subheader(f"Domanda {indice+1} / {len(lista_domande)}")
    st.write(domanda["Domanda"])

    risposte_mischiate = miscela_risposte(domanda)

    corretta_lettera = domanda["Corretta"].strip().upper()
    corretta_testo = domanda[f"Risposta {corretta_lettera}"].strip()

    risposta_utente = st.radio("Scegli una risposta:", options=risposte_mischiate + ["Omessa"], index=len(risposte_mischiate), key=f"risposta_{indice}")

    if not st.session_state["mostra_risposta"]:
        if st.button("Conferma risposta"):
            st.session_state["mostra_risposta"] = True

            if risposta_utente == "Omessa":
                st.session_state["esame_risposte"].append("omessa")
            elif risposta_utente == corretta_testo:
                st.session_state["corrette"] += 1
                st.session_state["esame_risposte"].append("corretta")
            else:
                st.session_state["sbagliate"] += 1
                st.session_state["esame_risposte"].append("errata")
                # Salva errore in json (indice reale)
                pos_domanda = domanda.name
                if pos_domanda not in dati_utente["errori"]:
                    dati_utente["errori"].append(pos_domanda)
                    utenti[username]["errori"] = dati_utente["errori"]
                    salva_utenti(utenti)
    else:
        if risposta_utente == "Omessa":
            st.info("Hai omesso questa domanda.")
        elif risposta_utente == corretta_testo:
            st.success("✅ Risposta corretta!")
        else:
            st.error(f"❌ Risposta errata! La risposta corretta era: **{corretta_testo}**")

        if st.button("Domanda successiva"):
            st.session_state["indice"] += 1
            st.session_state["mostra_risposta"] = False
            st.experimental_rerun()

    # Barra progresso e info utente
    st.sidebar.markdown(f"**Utente:** {username}")
    st.sidebar.markdown(f"**Modalità:** {modalita}")
    st.sidebar.markdown(f"**Domanda:** {indice + 1} / {len(lista_domande)}")
    st.sidebar.markdown(f"✅ Corrette: {st.session_state['corrette']}")
    st.sidebar.markdown(f"❌ Sbagliate: {st.session_state['sbagliate']}")
    st.sidebar.markdown(f"📌 Errori da ripassare: {len(dati_utente['errori'])}")

if __name__ == "__main__":
    main()
