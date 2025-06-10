import streamlit as st
import json
import random
import pandas as pd
import datetime

UTENTI_FILE = "utenti.json"
QUIZ_FILE = "quiz.xlsx"

# --- Funzioni Utility ---
def carica_utenti():
    try:
        with open(UTENTI_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        st.error(f"Errore: Il file '{UTENTI_FILE}' non è un JSON valido. Potrebbe essere corrotto o vuoto.")
        return {}

def salva_utenti(utenti):
    with open(UTENTI_FILE, "w") as f:
        json.dump(utenti, f, indent=4)

@st.cache_data # <--- AGGIUNTO IL DECORATORE QUI
def carica_quiz():
    try:
        df = pd.read_excel(QUIZ_FILE)
        df.columns = df.columns.str.strip()
        if 'ID' not in df.columns:
            st.error(f"Errore: Il file '{QUIZ_FILE}' deve contenere una colonna 'ID' per identificare univocamente le domande.")
            st.stop()
        # Converti esplicitamente l'ID in stringa per consistenza con il JSON
        df['ID'] = df['ID'].astype(str) # <--- AGGIUNTO QUESTO
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
                st.rerun()
            else:
                st.error("Username o password errati.")
    else:
        st.sidebar.write(f"Benvenuto, {st.session_state.username}!")
        current_modalita = st.session_state.get("modalita", "Esercizi")
        new_modalita = st.sidebar.radio("Scegli la modalità", ("Esercizi", "Simulazione Esame"), index=0 if current_modalita == "Esercizi" else 1)

        if current_modalita != new_modalita:
            st.session_state.modalita = new_modalita
            if new_modalita == "Esercizi":
                for key in ["esame_domande", "esame_indice", "esame_punteggio",
                            "esame_ordine_risposte", "esame_risposte_dettaglio",
                            "esame_domande_errate_ids", "esame_confermato"]:
                    st.session_state.pop(key, None)
                for key in list(st.session_state.keys()):
                    if key.startswith("es_scelta_q"):
                        st.session_state.pop(key)
            else: # Simulazione Esame
                for key in ["quiz", "indice", "risposte_date", "ordine_risposte",
                            "risposta_confermata", "domande_errate_ids"]:
                    st.session_state.pop(key, None)
                for key in list(st.session_state.keys()):
                    if key.startswith("scelta_q"):
                        st.session_state.pop(key)
            st.rerun()

        # Nuova Sezione Storico Simulazioni
        visualizza_storico_simulazioni()

        if st.sidebar.button("Logout"):
            st.session_state.clear()
            st.rerun()

# --- Visualizzazione Storico Simulazioni ---
def visualizza_storico_simulazioni():
    st.sidebar.markdown("---")
    st.sidebar.subheader("Storico Simulazioni Esame")

    utenti = carica_utenti()
    username = st.session_state.username
    storico = utenti.get(username, {}).get('storico_simulazioni', [])

    if not storico:
        st.sidebar.info("Nessuna simulazione d'esame effettuata.")
    else:
        storico_ordinato = sorted(storico, key=lambda x: x.get('data', ''), reverse=True)
        # Carica il quiz completo una volta sola per recuperare i testi delle domande
        # Questo verrà servito dalla cache grazie a @st.cache_data
        quiz_completo = carica_quiz()
        domande_map = {q['ID']: q for q in quiz_completo} # Mappa ID a domanda

        for i, sim in enumerate(storico_ordinato):
            data = sim.get('data', 'N/D')
            punteggio = sim.get('punteggio_finale', 0.0)
            domande_totali = sim.get('domande_totali', 0)
            punteggio_max_possibile = sim.get('punteggio_max_possibile', 0.0)
            
            with st.sidebar.expander(f"Simulazione del {data} - Punti: {punteggio:.2f}"):
                st.write(f"**Punteggio Finale:** {punteggio:.2f} / {punteggio_max_possibile:.2f}")
                if punteggio_max_possibile > 0:
                    st.write(f"**Percentuale:** {(punteggio / punteggio_max_possibile * 100):.1f}%")
                st.write(f"**Domande Totali:** {domande_totali}")

                dettaglio_risposte = sim.get('dettaglio_risposte', [])
                if dettaglio_risposte:
                    st.write("---")
                    st.write("**Dettaglio Risposte:**")
                    
                    for k, risposta_dettaglio in enumerate(dettaglio_risposte):
                        domanda_id = risposta_dettaglio.get('id_domanda')
                        # Recupera il testo della domanda dalla mappa
                        testo_domanda = domande_map.get(domanda_id, {}).get('Domanda', f"Domanda ID {domanda_id} (non trovata)")

                        st.markdown(f"**Domanda {k+1}:** {testo_domanda}")
                        st.write(f" - **Tua scelta:** {risposta_dettaglio.get('scelta_data', 'N/D')}")
                        st.write(f" - **Corretta:** {risposta_dettaglio.get('corretta', 'N/D')}")
                        st.write(f" - **Stato:** {risposta_dettaglio.get('stato_risposta', 'N/D')}")
                        st.write(f" - **Punti assegnati:** {risposta_dettaglio.get('punteggio_assegnato', 0.0):.2f}")
                        st.markdown("---")

# --- Modalità Esercizi ---
def esercizi():
    st.header("Modalità Esercizi")

    if "quiz" not in st.session_state:
        st.session_state.quiz = carica_quiz()
        random.shuffle(st.session_state.quiz)
        st.session_state.indice = 0
        st.session_state.risposte_date = {}
        st.session_state.ordine_risposte = {}
        st.session_state.risposta_confermata = False
        st.session_state.domande_errate_ids = []

    quiz = st.session_state.quiz
    i = st.session_state.indice

    if i < len(quiz):
        q = quiz[i]
        st.write(f"**Domanda {i+1}/{len(quiz)}:** {q['Domanda']}")

        if i not in st.session_state.ordine_risposte:
            opzioni_originali = [
                str(q.get("Risposta A", "")),
                str(q.get("Risposta B", "")),
                str(q.get("Risposta C", "")),
            ]
            opzioni_valide = [o for o in opzioni_originali if o.strip() != ""]
            random.shuffle(opzioni_valide)
            st.session_state.ordine_risposte[i] = opzioni_valide

        risp_ordinate = st.session_state.ordine_risposte[i]

        current_scelta = st.session_state.get(f"scelta_q{i}", None)
        index_selezionato = risp_ordinate.index(current_scelta) if current_scelta in risp_ordinate else 0
        
        scelta = st.radio("Seleziona la risposta:", risp_ordinate, key=f"q{i}", index=index_selezionato,
                          disabled=st.session_state.risposta_confermata)
        st.session_state[f"scelta_q{i}"] = scelta


        if not st.session_state.risposta_confermata:
            if st.button("Conferma risposta"):
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

                st.session_state.risposta_confermata = True
                st.rerun()
        else:
            corretta_lettera = str(q.get("Corretta", "")).strip().upper()
            chiave_risposta_corretta = f"Risposta {corretta_lettera}"
            corretta_text = str(q[chiave_risposta_corretta]).strip()

            if st.session_state.risposte_date[i]:
                st.success("✅ Risposta corretta!")
            else:
                st.error(f"❌ Sbagliata. La risposta corretta era: **{corretta_text}**")

            if st.button("Prossima domanda"):
                st.session_state.indice += 1
                st.session_state.risposta_confermata = False
                st.session_state.pop(f"scelta_q{i}", None)
                st.rerun()

    else:
        corrette = sum(st.session_state.risposte_date.values())
        totale_domande = len(quiz)
        st.write("---")
        st.write(f"🎉 Hai completato tutti gli esercizi!")
        st.write(f"Risposte corrette: **{corrette}** su **{totale_domande}** domande.")
        if totale_domande > 0:
            st.write(f"Percentuale di risposte corrette: **{(corrette / totale_domande * 100):.1f}%**")
        
        utenti = carica_utenti()
        username = st.session_state.username

        if username not in utenti:
            utenti[username] = {}

        current_errate_ids = set(utenti[username].get('domande_errate_ids', []))
        current_errate_ids.update(st.session_state.domande_errate_ids)
        utenti[username]['domande_errate_ids'] = list(current_errate_ids)

        salva_utenti(utenti)
        st.info(f"Le tue domande errate sono state salvate nel tuo profilo.")

        if st.button("Ricomincia Esercizi"):
            for key in ["quiz", "indice", "risposte_date", "ordine_risposte",
                         "risposta_confermata", "domande_errate_ids"]:
                st.session_state.pop(key, None)
            for key in list(st.session_state.keys()):
                if key.startswith("scelta_q"):
                    st.session_state.pop(key)
            st.rerun()

# --- Modalità Simulazione Esame ---
def simulazione_esame():
    st.header("Simulazione Esame")

    if "esame_domande" not in st.session_state:
        full_quiz = carica_quiz()
        n_domande_esame = min(40, len(full_quiz))
        st.session_state.esame_domande = random.sample(full_quiz, n_domande_esame)
        st.session_state.esame_indice = 0
        st.session_state.esame_punteggio = 0.0
        st.session_state.esame_ordine_risposte = {}
        st.session_state.esame_risposte_dettaglio = []
        st.session_state.esame_domande_errate_ids = []
        st.session_state.esame_confermato = False
        
    domande = st.session_state.esame_domande
    j = st.session_state.esame_indice

    if j < len(domande):
        q = domande[j]
        st.write(f"**Domanda {j+1}/{len(domande)}:** {q['Domanda']}")

        if j not in st.session_state.esame_ordine_risposte:
            opzioni_originali = [
                str(q.get("Risposta A", "")),
                str(q.get("Risposta B", "")),
                str(q.get("Risposta C", "")),
            ]
            opzioni_valide = [o for o in opzioni_originali if o.strip() != ""]
            random.shuffle(opzioni_valide)
            st.session_state.esame_ordine_risposte[j] = opzioni_valide
        
        risp_ordinate = st.session_state.esame_ordine_risposte[j]

        current_es_scelta = st.session_state.get(f"es_scelta_q{j}", None)
        opzioni_radio_esame = [""] + risp_ordinate
        
        index_selezionato_esame = 0
        if current_es_scelta in opzioni_radio_esame:
            index_selezionato_esame = opzioni_radio_esame.index(current_es_scelta)

        scelta = st.radio("Risposta (lascia vuoto per omettere):", opzioni_radio_esame, key=f"es{j}", index=index_selezionato_esame,
                          disabled=st.session_state.esame_confermato)
        
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
                stato_risposta = ""
                
                if scelta == "":
                    pun = 0
                    stato_risposta = "omessa"
                    st.info("⚠️ Domanda omessa.")
                elif scelta == corretta_text:
                    pun = 0.75
                    stato_risposta = "corretta"
                    st.success("✅ Risposta corretta!")
                else:
                    pun = -0.25
                    stato_risposta = "sbagliata"
                    st.error(f"❌ Errata. Risposta corretta: **{corretta_text}**")
                    if 'ID' in q:
                        st.session_state.esame_domande_errate_ids.append(q['ID'])
                    else:
                        st.warning(f"Attenzione: Domanda {j+1} sbagliata ma senza ID per il salvataggio nel profilo.")

                st.session_state.esame_punteggio += pun
                
                st.session_state.esame_risposte_dettaglio.append({
                    "id_domanda": q.get('ID'),
                    "scelta_data": scelta,
                    "corretta": corretta_text,
                    "stato_risposta": stato_risposta,
                    "punteggio_assegnato": pun
                })
                
                st.session_state.esame_confermato = True
                st.rerun()

        else:
            risposta_dettaglio_corrente = next((item for item in st.session_state.esame_risposte_dettaglio if item.get('id_domanda') == q.get('ID')), None)

            if risposta_dettaglio_corrente:
                if risposta_dettaglio_corrente['stato_risposta'] == "omessa":
                    st.info("⚠️ Domanda omessa.")
                elif risposta_dettaglio_corrente['stato_risposta'] == "corretta":
                    st.success("✅ Risposta corretta!")
                else:
                    st.error(f"❌ Errata. Risposta corretta: **{risposta_dettaglio_corrente['corretta']}**")
            else:
                st.warning("Feedback non disponibile.")

            if st.button("Prossima domanda", key=f"btn_prossima_esame_{j}"):
                st.session_state.esame_indice += 1
                st.session_state.esame_confermato = False
                st.session_state.pop(f"es_scelta_q{j}", None)
                st.rerun()

    else:
        st.write("---")
        st.write(f"🎉 Simulazione Esame Completata!")
        
        tot_domande_esame = len(domande)
        punteggio_finale = st.session_state.esame_punteggio
        punteggio_max_possibile = tot_domande_esame * 0.75

        st.write(f"Punteggio finale: **{punteggio_finale:.2f}** su **{punteggio_max_possibile:.2f}**")

        if punteggio_max_possibile > 0:
            percentuale = (punteggio_finale / punteggio_max_possibile) * 100
            st.write(f"Percentuale: **{percentuale:.1f}%**")
        else:
            st.write("Nessuna domanda nel quiz per calcolare la percentuale.")

        utenti = carica_utenti()
        username = st.session_state.username

        if username not in utenti:
            utenti[username] = {}
        if 'storico_simulazioni' not in utenti[username]:
            utenti[username]['storico_simulazioni'] = []

        simulazione_record = {
            'data': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'punteggio_finale': punteggio_finale,
            'domande_totali': tot_domande_esame,
            'punteggio_max_possibile': punteggio_max_possibile,
            'dettaglio_risposte': st.session_state.esame_risposte_dettaglio
        }
        utenti[username]['storico_simulazioni'].append(simulazione_record)

        current_errate_ids_esame = set(utenti[username].get('domande_errate_esame_ids', []))
        current_errate_ids_esame.update(st.session_state.esame_domande_errate_ids)
        utenti[username]['domande_errate_esame_ids'] = list(current_errate_ids_esame)

        salva_utenti(utenti)
        st.info(f"Il tuo punteggio e lo storico dell'esame sono stati salvati nel tuo profilo.")

        if st.button("Nuova Simulazione"):
            for key in ["esame_domande", "esame_indice", "esame_punteggio", "esame_ordine_risposte",
                         "esame_risposte_dettaglio", "esame_domande_errate_ids", "esame_confermato"]:
                st.session_state.pop(key, None)
            for key in list(st.session_state.keys()):
                if key.startswith("es_scelta_q"):
                    st.session_state.pop(key)
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