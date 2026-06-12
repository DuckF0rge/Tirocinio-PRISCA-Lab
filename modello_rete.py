import numpy as np
import itertools
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
from google_sheets_extractor import ottieni_risposte_T0, ottieni_risposte_T3_MID

# ====================================
# DEFINIZIONE STATI E FUNZIONI CPT
# ====================================

stati = ['Basso', 'Medio-basso', 'Neutro', 'Medio-alto', 'Alto']
card = len(stati)

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

# ==========================
# CREAZIONE DELLA RETE
# ==========================

model = DiscreteBayesianNetwork([
    ('TaskSuccess', 'Ability'),
    ('Helpfulness', 'Benevolence'),
    ('Ability', 'Trustworthiness'),
    ('Benevolence', 'Trustworthiness'),
    ('Integrity', 'Trustworthiness'),
    ('Criticality', 'Perceived_Risk'),
    ('Trustworthiness', 'Risk_Taking'),
    ('Perceived_Risk', 'Risk_Taking'),
    ('InitialPropensityRisk', 'Risk_Taking'),
    ('Transparency', 'Trust'), 
    ('Risk_Taking', 'Trust'),
    ('Propensity_to_Trust', 'Trust'),
    ('Trustworthiness', 'Trust')
])

# ==========================================
# SETUP E INIZIALIZZAZIONE (MAIN)
# ==========================================
if __name__ == "__main__":
    print("\n" + "="*50)
    print("INIZIALIZZAZIONE RETE BAYESIANA - HRI")
    print("="*50)
    
    ID_UTENTE = input("Inserire l'ID del partecipante (es. P01): ").strip()
    CRITICALITY_TASK = 4 

    print(f"\n[Attendere...] Connessione a Google Sheets per l'utente {ID_UTENTE}...")
    try:
        dati_utente = ottieni_risposte_T0(ID_UTENTE)
        print("   -> Dati T0 scaricati con successo.")
    except Exception as e:
        print(f"   -> [ERRORE CRITICO] Impossibile procedere: {e}")
        exit()

    print("\nCreazione delle Tabelle di Probabilità Condizionata (CPT)...")

    cpd_task_success = TabularCPD('TaskSuccess', card, values=[[0.2], [0.2], [0.2], [0.2], [0.2]], state_names={'TaskSuccess': stati})
    cpd_helpfulness = TabularCPD('Helpfulness', card, values=[[0.2], [0.2], [0.2], [0.2], [0.2]], state_names={'Helpfulness': stati})
    cpd_transparency = TabularCPD('Transparency', card, values=[[0.2], [0.2], [0.2], [0.2], [0.2]], state_names={'Transparency': stati})

    cpd_criticality = crea_cpt_da_voto('Criticality', CRITICALITY_TASK)
    cpd_integrity = crea_cpt_da_voto('Integrity', dati_utente['Integrity_Prior'])
    cpd_prop_trust = crea_cpt_da_voto('Propensity_to_Trust', dati_utente['Propensity_to_Trust'])
    cpd_initial_risk = crea_cpt_da_voto('InitialPropensityRisk', dati_utente['InitialPropensityRisk'])

    cpd_ability = genera_cpt_un_genitore('Ability', 'TaskSuccess')
    cpd_benevolence = genera_cpt_un_genitore('Benevolence', 'Helpfulness')
    cpd_perceived_risk = genera_cpt_un_genitore('Perceived_Risk', 'Criticality')

    cpd_trustworthiness = genera_cpt_multi('Trustworthiness', ['Ability', 'Benevolence', 'Integrity'], direzioni=[1, 1, 1], pesi=[3.0, 3.0, 1.0])
    cpd_risk_taking = genera_cpt_multi('Risk_Taking', ['Trustworthiness', 'Perceived_Risk', 'InitialPropensityRisk'], direzioni=[1, -1, 1], pesi=[4.0, 1.5, 1.0])
    cpd_trust = genera_cpt_multi('Trust', ['Risk_Taking', 'Propensity_to_Trust', 'Trustworthiness', 'Transparency'], direzioni=[1, 1, 1, 1], pesi=[1.0, 0.5, 4.0, 1.5]) # DA MODIFICARE

    model.add_cpds(cpd_task_success, cpd_helpfulness, cpd_transparency, cpd_criticality, cpd_initial_risk, cpd_prop_trust, cpd_integrity, 
                   cpd_ability, cpd_benevolence, cpd_perceived_risk, cpd_trustworthiness, cpd_risk_taking, cpd_trust)

    print("Verifica della coerenza strutturale della Rete Bayesiana...")
    if model.check_model():
        print("\n   [SUCCESSO] La rete è matematicamente valida e pronta per le inferenze!")
    
    infer = VariableElimination(model)
    risultato_t0 = infer.query(variables=['Trust'])
    print(f"\n-> Livello di TRUST iniziale (T0): {stati[np.argmax(risultato_t0.values)]} ({(np.max(risultato_t0.values)*100):.1f}%)")
    
    print("\n" + "="*50)
    print("SISTEMA PRONTO PER IL NUOVO SETTING DI TEST.")
    print("="*50 + "\n")