import streamlit as st
import json
import random
import pandas as pd
import time # Importa il modulo time per un eventuale delay, se necessario

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
        st.error(f"Errore: Il file '{UTENTI_FILE}' non è un JSON valido. Potrebbe essere corrotto o vuoto.")
        return {} # Ritorna un dizionario vuoto in caso di errore di decodifica JSON

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
            st.stop() # Ferma l'esecuzione dell'app se manca l'ID
        return df.to_dict(orient="records")
    except FileNotFoundError:
        st.error(f"Errore: Il file del quiz '{QUIZ_FILE}' non è stato trovato. Assicurati che sia nella stessa directory dell'app.")
        st.stop() # Ferma l'esecuzione dell'app se il file non esiste
    except Exception as e:
        st.error(f"Errore durante il caricamento o la lettura del quiz Excel: {e}")
        st.stop() # Ferma l'esecuzione per altri errori di caricamento

# --- Login ---
def login():
    # Inizializza gli stati di sessione se non esistono
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
                st.rerun() # Rerun per mostrare subito la sidebar e le opzioni
            else:
                st.error("Username o password errati.")
    else:
        st.sidebar.write(f"Benvenuto, {st.session_state.username}!")
        # Gestione della modalità: cambia solo se la selezione è diversa
        current_modalita = st.session_state.get("modalita", "Esercizi")
        new_modalita = st.sidebar.radio("Scegli la modalità", ("Esercizi", "Simulazione Esame"), index=0 if current_modalita == "Esercizi" else 1)

        if current_modalita != new_modalita:
            st.session_state.modalita = new_modalita
            # Pulisce gli stati specifici della modalità precedente quando si cambia
            if new_modalita == "Esercizi":
                # Pulisce stati della simulazione esame
                for key in ["esame_domande", "esame_indice", "esame_punteggio",
                            "esame_ordine_risposte", "esame_risposte_date",
                            "esame_domande_errate_ids", "esame_confermato", "esame_feedback_mostrato"]:
                    st.session_state.pop(key, None)
            else: # Simulazione Esame
                # Pulisce stati degli esercizi
                for key in ["quiz", "indice", "risposte_date", "ordine_risposte",
                            "risposta_confermata", "feedback_mostrato", "domande_errate_ids"]:
                    st.session_state.pop(key, None)
            st.rerun() # Rerun per caricare la nuova modalità

        if st.sidebar.button("Logout"):
            # Qui potresti salvare eventuali progressi prima del logout se non gestito altrove
            st.session_state.clear() # Pulisce tutti gli stati di sessione
            st.rerun()

# --- Modalità Esercizi ---
def esercizi():
    st.header("Modalità Esercizi")

    # Inizializzazione degli stati per gli esercizi
    if "quiz" not in st.session_state:
        st.session_state.quiz = carica_quiz()
        random.shuffle(st.session_state.quiz) # Rimescola l'ordine delle domande una volta sola
        st.session_state.indice = 0
        st.session_state.risposte_date = {} # True/False per ogni domanda (indice)
        st.session_state.ordine_risposte = {} # Ordine rimescolato delle opzioni per ogni domanda (indice)
        st.session_state.risposta_confermata = False # True se la risposta attuale è stata confermata
        st.session_state.domande_errate_ids = [] # Lista degli ID delle domande a cui si è risposto in modo errato in questa sessione

    quiz = st.session_state.quiz
    i = st.session_state.indice

    if i < len(quiz):
        q = quiz[i]
        st.write(f"**Domanda {i+1}/{len(quiz)}:** {q['Domanda']}")

        # Rimescola e memorizza l'ordine delle opzioni solo la prima volta per questa domanda
        if i not in st.session_state.ordine_risposte:
            # Assicurati di prendere tutte le opzioni possibili (A, B, C, D, ecc.)
            opzioni_originali = [
                str(q.get("Risposta A", "")),
                str(q.get("Risposta B", "")),
                str(q.get("Risposta C", "")),
                # Aggiungi altre opzioni se presenti nel tuo Excel (es. Risposta D)
            ]
            opzioni_valide = [o for o in opzioni_originali if o.strip() != ""] # Filtra risposte vuote
            
            random.shuffle(opzioni_valide)
            st.session_state.ordine_risposte[i] = opzioni_valide

        risp_ordinate = st.session_state.ordine_risposte[i]

        # Recupera la scelta precedente se esiste per mantenere la selezione del radio button
        current_scelta = st.session_state.get(f"scelta_q{i}", None)
        # Determina l'indice pre-selezionato per il radio button
        index_selezionato = risp_ordinate.index(current_scelta) if current_scelta in risp_ordinate else 0
        
        # Mostra il radio button
        scelta = st.radio("Seleziona la risposta:", risp_ordinate, key=f"q{i}", index=index_selezionato,
                          disabled=st.session_state.risposta_confermata) # Disabilita dopo la conferma
        
        # Aggiorna la scelta nello stato di sessione immediatamente
        st.session_state[f"scelta_q{i}"] = scelta


        # Logica per mostrare il bottone "Conferma" o "Prossima domanda" e il feedback
        if not st.session_state.risposta_confermata:
            if st.button("Conferma risposta"):
                # Logica di controllo della risposta
                corretta_lettera = str(q.get("Corretta", "")).strip().upper()
                chiave_risposta_corretta = f"Risposta {corretta_lettera}"
                
                if chiave_risposta_corretta not in q:
                    st.error(f"Errore nella domanda {i+1}: La chiave '{chiave_risposta_corretta}' per la risposta corretta non è presente. Controlla il tuo file Excel.")
                    st.stop()

                corretta_text = str(q[chiave_risposta_corretta]).strip()

                st.session_state.risposte_date[i] = (scelta == corretta_text)

                if scelta == corretta_text:
                    st.success("✅ Risposta corretta!")
                else:
                    st.error(f"❌ Sbagliata. La risposta corretta era: **{corretta_text}**")
                    if 'ID' in q:
                        st.session_state.domande_errate_ids.append(q['ID'])
                    else:
                        st.warning(f"Attenzione: Domanda {i+1} sbagliata ma senza ID per il salvataggio nel profilo.")

                st.session_state.risposta_confermata = True # Imposta lo stato per mostrare "Prossima"
                st.rerun() # Rerun per aggiornare l'UI e mostrare il feedback e il nuovo bottone
        else: # Se la risposta è stata confermata, mostra il feedback e il bottone Prossima
            # Ri-mostra il feedback dopo il rerun
            corretta_lettera = str(q.get("Corretta", "")).strip().upper()
            chiave_risposta_corretta = f"Risposta {corretta_lettera}"
            corretta_text = str(q[chiave_risposta_corretta]).strip()

            if st.session_state.risposte_date[i]:
                st.success("✅ Risposta corretta!")
            else:
                st.error(f"❌ Sbagliata. La risposta corretta era: **{corretta_text}**")

            if st.button("Prossima domanda"):
                st.session_state.indice += 1
                st.session_state.risposta_confermata = False # Resetta per la prossima domanda
                st.session_state.pop(f"scelta_q{i}", None) # Rimuovi la scelta precedente per la nuova domanda
                st.rerun()

    else: # Fine degli esercizi
        corrette = sum(st.session_state.risposte_date.values())
        totale_domande = len(quiz)
        st.write("---")
        st.write(f"🎉 Hai completato tutti gli esercizi!")
        st.write(f"Risposte corrette: **{corrette}** su **{totale_domande}** domande.")
        if totale_domande > 0:
            st.write(f"Percentuale di risposte corrette: **{(corrette / totale_domande * 100):.1f}%**")
        
        # Salvataggio delle domande errate nel profilo utente
        utenti = carica_utenti()
        username = st.session_state.username

        if username not in utenti:
            utenti[username] = {} # Assicurati che l'utente esista nel dizionario

        # Aggiorna la lista delle domande errate (aggiungendo quelle di questa sessione)
        # Usiamo un set per evitare duplicati se la stessa domanda è sbagliata più volte
        current_errate_ids = set(utenti[username].get('domande_errate_ids', []))
        current_errate_ids.update(st.session_state.domande_errate_ids)
        utenti[username]['domande_errate_ids'] = list(current_errate_ids) # Converti di nuovo in lista per il JSON

        salva_utenti(utenti)
        st.info(f"Le tue domande errate sono state salvate nel tuo profilo.")

        if st.button("Ricomincia Esercizi"):
            # Resetta tutti gli stati per ricominciare gli esercizi
            for key in ["quiz", "indice", "risposte_date", "ordine_risposte",
                         "risposta_confermata", "domande_errate_ids"]: # Rimuovi anche lo stato di scelta per ogni domanda
                st.session_state.pop(key, None)
            # Rimuovi tutte le chiavi di scelta radio generate dinamicamente (es. scelta_q0, scelta_q1)
            for key in list(st.session_state.keys()):
                if key.startswith("scelta_q"):
                    st.session_state.pop(key)
            st.rerun()

# --- Modalità Simulazione Esame ---
def simulazione_esame():
    st.header("Simulazione Esame")

    # Inizializzazione degli stati per la simulazione
    if "esame_domande" not in st.session_state:
        full_quiz = carica_quiz()
        n_domande_esame = min(40, len(full_quiz)) # Limite a 40 o meno se le domande sono meno
        st.session_state.esame_domande = random.sample(full_quiz, n_domande_esame) # Seleziona un sottoinsieme casuale
        st.session_state.esame_indice = 0
        st.session_state.esame_punteggio = 0.0
        st.session_state.esame_ordine_risposte = {} # Ordine rimescolato delle opzioni per ogni domanda
        st.session_state.esame_risposte_date = {} # Registra le risposte date per l'esame (per un riepilogo futuro)
        st.session_state.esame_domande_errate_ids = [] # IDs delle domande sbagliate in questa simulazione
        st.session_state.esame_confermato = False # Stato per il feedback dell'esame
        
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
        current_es_scelta = st.session_state.get(f"es_scelta_q{j}", None)
        # Per la simulazione esame c'è anche l'opzione "lascia vuoto"
        opzioni_radio_esame = [""] + risp_ordinate # Aggiungi l'opzione vuota
        
        index_selezionato_esame = 0
        if current_es_scelta in opzioni_radio_esame:
            index_selezionato_esame = opzioni_radio_esame.index(current_es_scelta)

        scelta = st.radio("Risposta (lascia vuoto per omettere):", opzioni_radio_esame, key=f"es{j}", index=index_selezionato_esame,
                          disabled=st.session_state.esame_confermato) # Disabilita dopo la conferma
        
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
                    if 'ID' in q:
                        st.session_state.esame_domande_errate_ids.append(q['ID'])
                    else:
                        st.warning(f"Attenzione: Domanda {j+1} sbagliata ma senza ID per il salvataggio nel profilo.")

                st.session_state.esame_punteggio += pun
                # Salva la risposta data e la corretta per un possibile riepilogo finale
                st.session_state.esame_risposte_date[j] = {"scelta_data": scelta, "corretta": corretta_text, "punteggio": pun}
                
                if "⚠️" in feedback_msg:
                    st.info(feedback_msg)
                elif "✅" in feedback_msg:
                    st.success(feedback_msg)
                else:
                    st.error(feedback_msg)

                st.session_state.esame_confermato = True # Imposta lo stato per mostrare "Prossima"
                st.rerun() # Rerun per aggiornare l'UI e mostrare il feedback e il nuovo bottone

        else: # Se la risposta è stata confermata, mostra il feedback e il bottone Prossima
            # Ri-mostra il feedback dopo il rerun
            feedback_data = st.session_state.esame_risposte_date[j]
            if feedback_data["scelta_data"] == "":
                st.info("⚠️ Domanda omessa.")
            elif feedback_data["scelta_data"] == feedback_data["corretta"]:
                st.success("✅ Risposta corretta!")
            else:
                st.error(f"❌ Errata. Risposta corretta: **{feedback_data['corretta']}**")

            if st.button("Prossima domanda", key=f"btn_prossima_esame_{j}"):
                st.session_state.esame_indice += 1
                st.session_state.esame_confermato = False # Resetta per la prossima domanda
                st.session_state.pop(f"es_scelta_q{j}", None) # Rimuovi la scelta precedente
                st.rerun()

    else: # Fine della simulazione d'esame
        st.write("---")
        st.write(f"🎉 Simulazione Esame Completata!")
        
        tot_domande_esame = len(domande)
        punteggio_finale = st.session_state.esame_punteggio
        punteggio_max_possibile = tot_domande_esame * 0.75

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
                         "esame_risposte_date", "esame_domande_errate_ids", "esame_confermato"]:
                st.session_state.pop(key, None)
            # Rimuovi tutte le chiavi di scelta radio generate dinamicamente
            for key in list(st.session_state.keys()):
                if key.startswith("es_scelta_q"):
                    st.session_state.pop(key)
            st.rerun()

# --- Main ---
def main():
    login()
    if st.session_state.get("logged_in", False):
        # Mantiene la modalità selezionata dall'utente in sidebar
        m = st.session_state.get("modalita", "Esercizi")
        if m == "Esercizi":
            esercizi()
        else: # "Simulazione Esame"
            simulazione_esame()

if __name__ == "__main__":
    main()