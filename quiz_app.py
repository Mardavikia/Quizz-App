import streamlit as st
import json
import random

# Funzione per caricare utenti da json (file "utenti.json" deve esistere)
def carica_utenti():
    try:
        with open("utenti.json", "r") as f:
            return json.load(f)
    except:
        # se file non esiste o è vuoto
        return {}

# Funzione di login
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
        # Sidebar: scelta modalità + logout
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
            st.experimental_rerun()

# Funzione per la modalità Esercizi (placeholder semplice)
def esercizi():
    st.header("Modalità Esercizi")
    st.write("Qui mostreresti le domande per esercitarti.")

# Funzione per la modalità Simulazione Esame (placeholder semplice)
def simulazione_esame():
    st.header("Modalità Simulazione Esame")
    st.write("Qui mostreresti la simulazione dell'esame.")

# Funzione main
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
