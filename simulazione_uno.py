import numpy as np
import json
import datetime
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
from google_sheets_extractor import scarica_database_T0, scarica_database_MID

# ====================================
# IMPOSTAZIONI E COSTANTI
# ====================================
stati = ['Basso', 'Medio-basso', 'Neutro', 'Medio-alto', 'Alto']
card = len(stati)
CRITICALITY_TASK = 4 
FILE_OUTPUT = "risultati_esperimento_finanziario.txt"

# Lista degli ID da testare (da P01 a P100)
lista_utenti = [f"P{str(i).zfill(2)}" for i in range(1, 101)]

# Nodi di cui vogliamo stampare le dinamiche interne ad ogni step
nodi_da_monitorare = ['Ability', 'Benevolence', 'Integrity', 'Transparency', 'Trustworthiness', 'Perceived_Risk', 'Risk_Taking']

# ====================================
# FUNZIONI CPT DELLA RETE
# ====================================
def crea_cpt_da_voto(nome_nodo, voto_1_a_5):
    indice_stato = voto_1_a_5 - 1
    probabilita = [0.0] * card
    probabilita[indice_stato] = 1.0
    valori_per_pgmpy = [[p] for p in probabilita]
    return TabularCPD(variable=nome_nodo, variable_card=card, values=valori_per_pgmpy, state_names={nome_nodo: stati})

def genera_cpt_un_genitore(nome_nodo, nome_genitore):
    matrice_logica = [
        [0.70, 0.20, 0.05, 0.00, 0.00], [0.20, 0.60, 0.15, 0.05, 0.00], [0.10, 0.15, 0.60, 0.15, 0.10], 
        [0.00, 0.05, 0.15, 0.60, 0.20], [0.00, 0.00, 0.05, 0.20, 0.70]  
    ]
    return TabularCPD(variable=nome_nodo, variable_card=card, values=matrice_logica, evidence=[nome_genitore], evidence_card=[card], state_names={nome_nodo: stati, nome_genitore: stati})

def genera_cpt_multi(nome_nodo, nomi_genitori, pesi=None, direzioni=None):
    import itertools
    num_genitori = len(nomi_genitori)
    if pesi is None: pesi = [1.0] * num_genitori
    if direzioni is None: direzioni = [1] * num_genitori 
    pesi_norm = [p / sum(pesi) for p in pesi]
    matrice = [[] for _ in range(card)]
    combinazioni = list(itertools.product(range(card), repeat=num_genitori))
    
    for combo in combinazioni:
        punteggio_totale = sum((((card - 1) - combo[i]) if direzioni[i] == -1 else combo[i]) * pesi_norm[i] for i in range(num_genitori))
        prob_colonna = [np.exp(-(abs(stato_figlio - punteggio_totale)**2) / 0.15) for stato_figlio in range(card)]
        somma_prob = sum(prob_colonna)
        for riga in range(card): matrice[riga].append(prob_colonna[riga] / somma_prob)
            
    return TabularCPD(variable=nome_nodo, variable_card=card, values=matrice, evidence=nomi_genitori, evidence_card=[card]*num_genitori, state_names={nome_nodo: stati, **{g: stati for g in nomi_genitori}})

# ==========================================
# ESECUZIONE MAIN BATCH
# ==========================================
if __name__ == "__main__":
    print("Scaricamento globale del database T0 in corso...")
    DB_T0 = scarica_database_T0()
    print("Scaricamento globale del database MID in corso...")
    DB_MID = scarica_database_MID()
    print(f"Dati scaricati con successo. Avvio simulazione automatizzata per {len(lista_utenti)} utenti...\n")
    
    try:
        with open('scenario_uno.json', 'r', encoding='utf-8') as f:
            database_scenari = json.load(f)
            interazioni_robot = database_scenari["scenario_finanziario"]
    except Exception as e:
        print(f"Errore caricamento scenario JSON: {e}")
        exit()

    with open(FILE_OUTPUT, 'w', encoding='utf-8') as log_file:
        log_file.write(f"=== REPORT SIMULAZIONE HRI (DATA: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}) ===\n")
        log_file.write(f"Utenti Testati: {len(lista_utenti)} | Scenario: Finanziario (Criticality: {CRITICALITY_TASK})\n")
        log_file.write("=================================================================================\n\n")

        for utente_id in lista_utenti:
            
            # Verifichiamo se l'utente esiste nel database locale
            if utente_id not in DB_T0 or utente_id not in DB_MID:
                print(f"!!! Salto {utente_id}: Dati mancanti su Google Sheets.")
                continue

            print(f"-> Elaborazione {utente_id} in corso...")
            log_file.write(f"\n{'='*60}\n")
            log_file.write(f"RISULTATI PER L'UTENTE: {utente_id}\n")
            log_file.write(f"{'='*60}\n")
            
            try:
                # 1. RECUPERO DATI DAL DIZIONARIO LOCALE
                dati_t0 = DB_T0[utente_id]
                log_file.write(f"[FASE PRE-INTERAZIONE] Propensity: {dati_t0['Propensity_to_Trust']}, Integrity_Prior: {dati_t0['Integrity_Prior']}, Initial_Risk: {dati_t0['InitialPropensityRisk']}\n")

                # 2. CREAZIONE DELLA RETE DA ZERO PER L'UTENTE
                model = DiscreteBayesianNetwork([
                    ('TaskSuccess', 'Ability'), ('Helpfulness', 'Benevolence'), ('Ability', 'Trustworthiness'),
                    ('Benevolence', 'Trustworthiness'), ('Integrity', 'Trustworthiness'), ('Criticality', 'Perceived_Risk'),
                    ('Trustworthiness', 'Risk_Taking'), ('Perceived_Risk', 'Risk_Taking'), ('InitialPropensityRisk', 'Risk_Taking'),
                    ('Transparency', 'Trust'), ('Risk_Taking', 'Trust'), ('Propensity_to_Trust', 'Trust'), ('Trustworthiness', 'Trust')
                ])
                
                cpd_ts = TabularCPD('TaskSuccess', card, values=[[0.2], [0.2], [0.2], [0.2], [0.2]], state_names={'TaskSuccess': stati})
                cpd_hp = TabularCPD('Helpfulness', card, values=[[0.2], [0.2], [0.2], [0.2], [0.2]], state_names={'Helpfulness': stati})
                cpd_tr = TabularCPD('Transparency', card, values=[[0.2], [0.2], [0.2], [0.2], [0.2]], state_names={'Transparency': stati})
                cpd_cr = crea_cpt_da_voto('Criticality', CRITICALITY_TASK)
                cpd_in = crea_cpt_da_voto('Integrity', dati_t0['Integrity_Prior'])
                cpd_pr = crea_cpt_da_voto('Propensity_to_Trust', dati_t0['Propensity_to_Trust'])
                cpd_ir = crea_cpt_da_voto('InitialPropensityRisk', dati_t0['InitialPropensityRisk'])

                cpd_ab = genera_cpt_un_genitore('Ability', 'TaskSuccess')
                cpd_be = genera_cpt_un_genitore('Benevolence', 'Helpfulness')
                cpd_per_r = genera_cpt_un_genitore('Perceived_Risk', 'Criticality')
                cpd_tw = genera_cpt_multi('Trustworthiness', ['Ability', 'Benevolence', 'Integrity'], direzioni=[1, 1, 1], pesi=[3.0, 3.0, 1.0])
                cpd_rt = genera_cpt_multi('Risk_Taking', ['Trustworthiness', 'Perceived_Risk', 'InitialPropensityRisk'], direzioni=[1, -1, 1], pesi=[4.0, 1.5, 1.0])
                cpd_trust = genera_cpt_multi('Trust', ['Risk_Taking', 'Propensity_to_Trust', 'Trustworthiness', 'Transparency'], direzioni=[1, 1, 1, 1], pesi=[1.0, 3.0, 2.0, 1.0]) # Pesi modificati

                model.add_cpds(cpd_ts, cpd_hp, cpd_tr, cpd_cr, cpd_in, cpd_pr, cpd_ir, cpd_ab, cpd_be, cpd_per_r, cpd_tw, cpd_rt, cpd_trust)
                
                if not model.check_model():
                    log_file.write("[ERRORE] Rete non valida per questo utente.\n")
                    continue

                infer = VariableElimination(model)

                risultato_t0 = infer.query(variables=['Trust'])
                fiducia_iniziale = stati[np.argmax(risultato_t0.values)]
                log_file.write(f"-> TRUST INIZIALE (Round 0): {fiducia_iniziale} ({(np.max(risultato_t0.values)*100):.1f}%)\n")
                log_file.write("-" * 50 + "\n")

                # 3. CICLO DEI ROUND (1-6)
                for step in interazioni_robot:
                    t = step['Time']
                    log_file.write(f"\n[ROUND {t}] Evidenze Iniettate: {step['Evidenze']}\n")
                    
                    log_file.write("  Dinamiche Interne:\n")
                    for nodo in nodi_da_monitorare:
                        if nodo in step['Evidenze']:
                            stato_conosciuto = step['Evidenze'][nodo]
                            log_file.write(f"    - {nodo}: {stato_conosciuto} (100.0% - Evidenza Diretta)\n")
                        else:
                            res_nodo = infer.query(variables=[nodo], evidence=step['Evidenze'])
                            log_file.write(f"    - {nodo}: {stati[np.argmax(res_nodo.values)]} ({(np.max(res_nodo.values)*100):.1f}%)\n")
                    
                    risultato_trust = infer.query(variables=['Trust'], evidence=step['Evidenze'])
                    log_file.write(f"  --------------------------------------------------\n")
                    log_file.write(f"  ==> TRUST FINALE (ROUND {t}): **{stati[np.argmax(risultato_trust.values)]}** ({(np.max(risultato_trust.values)*100):.1f}%)\n")
                    log_file.write(f"  --------------------------------------------------\n")

                    if t == 3:
                        log_file.write("\n" + "*"*40 + "\n")
                        log_file.write("*** INIEZIONE DATI QUESTIONARIO MID ***\n")
                        log_file.write("*"*40 + "\n")
                        
                        dati_mid = DB_MID[utente_id]
                        log_file.write(f"  Voti estratti -> Transparency: {dati_mid['Transparency_Mid']}, Integrity: {dati_mid['Integrity_Mid']}, Benevolence: {dati_mid['Benevolence_Mid']}, Ability: {dati_mid['Ability_Mid']}, Risk: {dati_mid['Perceived_Risk_Mid']}\n")
                        
                        nuova_cpt_transparency = crea_cpt_da_voto('Transparency', dati_mid['Transparency_Mid'])
                        nuova_cpt_integrity = crea_cpt_da_voto('Integrity', dati_mid['Integrity_Mid'])
                        model.remove_cpds('Transparency', 'Integrity')
                        model.add_cpds(nuova_cpt_transparency, nuova_cpt_integrity)
                        infer = VariableElimination(model)
                        log_file.write("  [Rete aggiornata con le nuove percezioni post-disastro]\n")

            except Exception as e:
                log_file.write(f"[ERRORE DURANTE L'ELABORAZIONE]: {e}\n")
                print(f"!!! Errore su {utente_id}: {e}")

    print(f"\nSimulazione completata con successo! Apri il file '{FILE_OUTPUT}' per leggere tutti i risultati.")