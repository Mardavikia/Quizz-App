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
    except FileNotFoundError:
        return {} # Ritorna un dizionario vuoto se il file non esiste
    except json.JSONDecodeError:
        st.error(f"Errore: Il file '{UTENTI_FILE}' non è un JSON valido.")
        return {}

def salva_utenti(utenti):
    with open(UTENTI_FILE, "w") as f:
        json.dump(utenti, f, indent=4)

def carica_quiz():
    try:
        df = pd.read_excel(QUIZ_FILE)
        df.columns = df.columns.str.strip()
        # Assicurati che ogni domanda abbia un ID univoco
        if 'ID' not in df.columns:
            st.error(f"Errore: Il file '{QUIZ_FILE}' deve contenere una colonna 'ID' per identificare univocamente le domande.")
            st.stop()
        return df.to_dict(orient="records")
    except FileNotFoundError:
        st.error(f"Errore: Il file del quiz '{QUIZ_FILE}' non è stato trovato. Assicurati che sia nella stessa directory dell'app.")
        st.stop()
    except Exception as e:
        st.error(f"Errore durante il caricamento o la lettura del quiz Excel: {e}")
        st.stop()

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
            if username in utenti and utenti[username].get("password") == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Benvenuto, {username}!")
                st.rerun() # Rerun per mostrare subito la sidebar
            else:
                st.error("Username o password errati.")
    else:
        st.sidebar.write(f"Benvenuto, {st.session_state.username}!")
        modalita = st.sidebar.radio("Scegli la modalità", ("Esercizi", "Simulazione Esame"))
        # Solo aggiorna la modalità se è cambiata per evitare rerun inutili
        if st.session_state.get("modalita") != modalita:
            st.session_state.modalita = modalita
            # Puliamo gli stati delle modalità quando si cambia
            if modalita == "Esercizi":
                st.session_state.pop("esame_domande", None)
            else: # Simulazione Esame
                st.session_state.pop("quiz", None)
            st.rerun()

        if st.sidebar.button("Logout"):
            # Salva i dati utente prima del logout se necessario
            # Esempio: salva_progressi_utente(st.session_state.username)
            st.session_state.clear()
            st.rerun()

# --- Modalità Esercizi ---
def esercizi():
    st.header("Modalità Esercizi")

    # Inizializzazione degli stati per gli esercizi
    if "quiz" not in st.session_state:
        st.session_state.quiz = carica_quiz()
        random.shuffle(st.session_state.quiz) # Rimescola le domande una volta sola
        st.session_state.indice = 0
        st.session_state.risposte_date = {} # True/False per ogni domanda (indice)
        st.session_state.ordine_risposte = {} # Ordine rimescolato delle opzioni per ogni domanda (indice)
        st.session_state.risposta_confermata = False # Controlla se una risposta è stata appena confermata
        st.session_state.feedback_mostrato = False # Controlla se il feedback è stato già visualizzato
        st.session_state.domande_errate_ids = [] # Lista degli ID delle domande errate

    quiz = st.session_state.quiz
    i = st.session_state.indice

    if i < len(quiz):
        q = quiz[i]
        st.write(f"**Domanda {i+1}/{len(quiz)}:** {q['Domanda']}")

        # Rimescola e memorizza l'ordine delle risposte solo la prima volta
        if i not in st.session_state.ordine_risposte:
            # Assicurati che ci siano almeno 3 risposte valide
            opzioni_originali = [
                str(q.get("Risposta A", "")),
                str(q.get("Risposta B", "")),
                str(q.get("Risposta C", "")),
                # Aggiungi altre opzioni se presenti nel tuo Excel (es. Risposta D)
            ]
            # Filtra le risposte vuote e le rimuovi
            opzioni_valide = [o for o in opzioni_originali if o.strip() != ""]
            
            random.shuffle(opzioni_valide)
            st.session_state.ordine_risposte[i] = opzioni_valide

        risp_ordinate = st.session_state.ordine_risposte[i]

        # La scelta dell'utente è persistente se il feedback non è ancora mostrato
        scelta_precedente = st.session_state.get(f"scelta_q{i}", None)
        scelta = st.radio("Seleziona la risposta:", risp_ordinate, key=f"q{i}", index=risp_ordinate.index(scelta_precedente) if scelta_precedente in risp_ordinate else 0)

        # Memorizza la scelta dell'utente non appena viene fatta (Streamlit lo fa automaticamente con key)
        st.session_state[f"scelta_q{i}"] = scelta


        # Mostra il bottone "Conferma" o "Prossima Domanda" in base allo stato
        if not st.session_state.risposta_confermata:
            if st.button("Conferma risposta"):
                corretta_lettera = str(q.get("Corretta", "")).strip().upper()
                chiave_risposta_corretta = f"Risposta {corretta_lettera}"
                
                # Controllo robusto per la presenza della chiave della risposta corretta
                if chiave_risposta_corretta not in q:
                    st.error(f"Errore nella domanda {i+1}: La chiave '{chiave_risposta_corretta}' per la risposta corretta non è presente. Controlla il tuo file Excel.")
                    st.stop() # Ferma l'esecuzione per evitare ulteriori errori

                corretta_text = str(q[chiave_risposta_corretta]).strip()

                st.session_state.risposte_date[i] = (scelta == corretta_text)

                if scelta == corretta_text:
                    st.success("✅ Risposta corretta!")
                else:
                    st.error(f"❌ Sbagliata. La risposta corretta era: **{corretta_text}**")
                    # Salva l'ID della domanda sbagliata
                    if 'ID' in q: # Assicurati che l'ID esista
                        st.session_state.domande_errate_ids.append(q['ID'])
                    else:
                        st.warning(f"Attenzione: Domanda {i+1} sbagliata ma senza ID per il salvataggio.")

                st.session_state.risposta_confermata = True
                st.session_state.feedback_mostrato = True # Per indicare che il feedback è stato dato
                # Non fare rerun qui subito, lo faremo col bottone "Prossima domanda"
                st.rerun() # Un rerun per mostrare il feedback e il bottone "Prossima domanda"

        elif st.session_state.feedback_mostrato: # Se il feedback è stato mostrato, ora mostra il bottone "Prossima"
            if st.button("Prossima domanda"):
                st.session_state.indice += 1
                # Resetta gli stati per la prossima domanda
                st.session_state.risposta_confermata = False
                st.session_state.feedback_mostrato = False
                st.session_state.pop(f"scelta_q{i}", None) # Rimuovi la scelta precedente
                st.rerun()

    else: # Fine degli esercizi
        corrette = sum(st.session_state.risposte_date.values())
        totale_domande = len(quiz)
        st.write(f"🎉 Hai completato gli esercizi!")
        st.write(f"Risposte corrette: **{corrette}** su **{totale_domande}** domande.")
        st.write(f"Percentuale di risposte corrette: **{(corrette / totale_domande * 100):.1f}%**")

        # Salvataggio delle domande errate nel profilo utente
        utenti = carica_utenti()
        username = st.session_state.username

        if username not in utenti:
            utenti[username] = {} # Assicurati che l'utente esista nel dizionario

        # Aggiorna la lista delle domande errate (evita duplicati se l'ID è lo stesso)
        # Potresti voler gestire la storia delle domande errate (es. data, sessione)
        # Per ora, semplicemente aggiungiamo e rimuoviamo duplicati
        current_errate_ids = set(utenti[username].get('domande_errate_ids', []))
        current_errate_ids.update(st.session_state.domande_errate_ids)
        utenti[username]['domande_errate_ids'] = list(current_errate_ids) # Converti di nuovo in lista per il JSON

        salva_utenti(utenti)
        st.info(f"Le tue domande errate sono state salvate nel tuo profilo.")

        if st.button("Ricomincia Esercizi"):
            # Resetta tutti gli stati per ricominciare
            for key in ["quiz", "indice", "risposte_date", "ordine_risposte",
                         "risposta_confermata", "feedback_mostrato", "domande_errate_ids"]:
                st.session_state.pop(key, None)
            st.rerun()

        # Opzionale: Mostra un link per rivedere le domande errate
        # if len(utenti[username].get('domande_errate_ids', [])) > 0:
        #     st.write("---")
        #     st.subheader("Le tue domande errate in passato:")
        #     # Qui dovresti caricare le domande basandoti sugli ID salvati
        #     # e mostrarle all'utente per ripasso.


# --- Modalità Simulazione Esame ---
def simulazione_esame():
    st.header("Simulazione Esame")

    # Inizializzazione degli stati per la simulazione
    if "esame_domande" not in st.session_state:
        full_quiz = carica_quiz()
        n_domande_esame = min(40, len(full_quiz)) # Limite a 40 o meno se le domande sono meno
        st.session_state.esame_domande = random.sample(full_quiz, n_domande_esame)
        st.session_state.esame_indice = 0
        st.session_state.esame_punteggio = 0.0
        st.session_state.esame_ordine_risposte = {} # Ordine rimescolato delle opzioni per ogni domanda
        st.session_state.esame_risposte_date = {} # Registra le risposte date per l'esame
        st.session_state.esame_domande_errate_ids = [] # IDs delle domande sbagliate nell'esame
        st.session_state.esame_confermato = False # Stato per il feedback dell'esame
        st.session_state.esame_feedback_mostrato = False # Stato per il feedback dell'esame

    domande = st.session_state.esame_domande
    j = st.session_state.esame_indice

    if j < len(domande):
        q = domande[j]
        st.write(f"**Domanda {j+1}/{len(domande)}:** {q['Domanda']}")

        # Rimescola e memorizza l'ordine delle risposte solo la prima volta per l'esame
        if j not in st.session_state.esame_ordine_risposte:
            opzioni_originali = [
                str(q.get("Risposta A", "")),
                str(q.get("Risposta B", "")),
                str(q.get("Risposta C", "")),
                # Aggiungi altre opzioni se presenti
            ]
            opzioni_valide = [o for o in opzioni_originali if o.strip() != ""]
            random.shuffle(opzioni_valide)
            st.session_state.esame_ordine_risposte[j] = opzioni_valide
        
        risp_ordinate = st.session_state.esame_ordine_risposte[j]

        # La scelta dell'utente è persistente se il feedback non è ancora mostrato
        scelta_precedente = st.session_state.get(f"es_scelta_q{j}", None)
        # In simulazione esame c'è anche l'opzione "lascia vuoto"
        opzioni_radio = [""] + risp_ordinate
        index_selezionato = 0
        if scelta_precedente in opzioni_radio:
            index_selezionato = opzioni_radio.index(scelta_precedente)

        scelta = st.radio("Risposta (lascia vuoto per omettere):", opzioni_radio, key=f"es{j}", index=index_selezionato)
        st.session_state[f"es_scelta_q{j}"] = scelta


        if not st.session_state.esame_confermato:
            if st.button("Conferma risposta", key=f"btn_esame_{j}"):
                corretta_lettera = str(q.get("Corretta", "")).strip().upper()
                chiave_risposta_corretta = f"Risposta {corretta_lettera}"
                
                if chiave_risposta_corretta not in q:
                    st.error(f"Errore nella domanda {j+1}: La chiave '{chiave_risposta_corretta}' per la risposta corretta non è presente. Controlla il tuo file Excel.")
                    st.stop()

                corretta_text = str(q[chiave_risposta_corretta]).strip()
                
                pun = 0
                feedback_msg = ""
                
                if scelta == "":
                    pun = 0
                    feedback_msg = "⚠️ Domanda omessa."
                elif scelta == corretta_text:
                    pun = 0.75
                    feedback_msg = "✅ Risposta corretta!"
                else:
                    pun = -0.25
                    feedback_msg = f"❌ Errata. Risposta corretta: **{corretta_text}**"
                    if 'ID' in q: # Assicurati che l'ID esista
                        st.session_state.esame_domande_errate_ids.append(q['ID'])
                    else:
                        st.warning(f"Attenzione: Domanda {j+1} sbagliata ma senza ID per il salvataggio.")

                st.session_state.esame_punteggio += pun
                st.session_state.esame_risposte_date[j] = {"scelta": scelta, "corretta": corretta_text, "punteggio": pun}
                
                if "⚠️" in feedback_msg:
                    st.info(feedback_msg)
                elif "✅" in feedback_msg:
                    st.success(feedback_msg)
                else:
                    st.error(feedback_msg)

                st.session_state.esame_confermato = True
                st.session_state.esame_feedback_mostrato = True
                st.rerun() # Rerun per mostrare il feedback e il bottone "Prossima"

        elif st.session_state.esame_feedback_mostrato:
            if st.button("Prossima domanda", key=f"btn_prossima_esame_{j}"):
                st.session_state.esame_indice += 1
                # Resetta gli stati per la prossima domanda dell'esame
                st.session_state.esame_confermato = False
                st.session_state.esame_feedback_mostrato = False
                st.session_state.pop(f"es_scelta_q{j}", None) # Rimuovi la scelta precedente
                st.rerun()

    else: # Fine della simulazione d'esame
        tot_domande_esame = len(domande)
        punteggio_finale = st.session_state.esame_punteggio
        punteggio_max_possibile = tot_domande_esame * 0.75

        st.write(f"🎉 Simulazione Esame Completata!")
        st.write(f"Punteggio finale: **{punteggio_finale:.2f}** su **{punteggio_max_possibile:.2f}**")

        if punteggio_max_possibile > 0: # Evita divisione per zero
            percentuale = (punteggio_finale / punteggio_max_possibile) * 100
            st.write(f"Percentuale: **{percentuale:.1f}%**")
        else:
            st.write("Nessuna domanda nel quiz per calcolare la percentuale.")


        # Salvataggio delle domande errate e del punteggio finale nel profilo utente
        utenti = carica_utenti()
        username = st.session_state.username

        if username not in utenti:
            utenti[username] = {}

        # Salva il punteggio dell'ultima simulazione
        utenti[username]['ultimo_punteggio_esame'] = punteggio_finale
        utenti[username]['data_ultimo_esame'] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

        # Aggiorna la lista delle domande errate dell'esame
        current_errate_ids_esame = set(utenti[username].get('domande_errate_esame_ids', []))
        current_errate_ids_esame.update(st.session_state.esame_domande_errate_ids)
        utenti[username]['domande_errate_esame_ids'] = list(current_errate_ids_esame)

        salva_utenti(utenti)
        st.info(f"Il tuo punteggio e le domande errate sono stati salvati nel tuo profilo.")

        if st.button("Nuova Simulazione"):
            # Resetta tutti gli stati per ricominciare una simulazione
            for key in ["esame_domande", "esame_indice", "esame_punteggio", "esame_ordine_risposte",
                         "esame_risposte_date", "esame_domande_errate_ids", "esame_confermato", "esame_feedback_mostrato"]:
                st.session_state.pop(key, None)
            st.rerun()

# --- Main ---
def main():
    login()
    if st.session_state.get("logged_in", False):
        m = st.session_state.get("modalita", "Esercizi")
        if m == "Esercizi":
            esercizi()
        else: # "Simulazione Esame"
            simulazione_esame()

if __name__ == "__main__":
    main()