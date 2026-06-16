import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Nome del file generato in precedenza
FILE_INPUT = "risultati_esperimento_finanziario.txt"

# Funzione per assegnare l'archetipo in base all'ID (da P01 a P100)
def assegna_gruppo(user_id):
    num = int(user_id.replace("P", ""))
    if num <= 30:
        return "Gruppo A: Conservatori (P01-P30)"
    elif num <= 65:
        return "Gruppo B: Tecno-Entusiasti (P31-P65)"
    else:
        return "Gruppo C: Razionali/Analitici (P66-P100)"

# Mappa degli stati in valori numerici continui per poterli plottare
state_to_num = {
    'Basso': 1,
    'Medio-basso': 2,
    'Neutro': 3,
    'Medio-alto': 4,
    'Alto': 5
}

# Parse del file di testo
dati_grafico = []
utente_corrente = None

try:
    with open(FILE_INPUT, 'r', encoding='utf-8') as f:
        for linea in f:
            # Trova l'ID utente
            match_user = re.search(r"RISULTATI PER L'UTENTE: (P\d+)", linea)
            if match_user:
                utente_corrente = match_user.group(1)
                gruppo = assegna_gruppo(utente_corrente)
                continue
            
            if not utente_corrente:
                continue

            # Estrai il Trust Iniziale (Round 0) - Estraiamo l'etichetta testuale
            match_t0 = re.search(r"TRUST INIZIALE \(Round 0\): \**([a-zA-Z\-]+)\**", linea)
            if match_t0:
                stato = match_t0.group(1)
                dati_grafico.append({"Utente": utente_corrente, "Gruppo": gruppo, "Round": 0, "Trust_Value": state_to_num.get(stato, 3)})
            
            # Estrai il Trust dei Round 1-6 - Estraiamo l'etichetta testuale
            match_round = re.search(r"(?:TRUST CALCOLATO A FINE ROUND|TRUST FINALE \(ROUND) (\d)\)?: \**([a-zA-Z\-]+)\**", linea)
            if match_round:
                round_num = int(match_round.group(1))
                stato = match_round.group(2)
                dati_grafico.append({"Utente": utente_corrente, "Gruppo": gruppo, "Round": round_num, "Trust_Value": state_to_num.get(stato, 3)})

except FileNotFoundError:
    print(f"Errore: Il file {FILE_INPUT} non è stato trovato nella cartella.")
    exit()

# Creazione del DataFrame Pandas
df = pd.DataFrame(dati_grafico)

# ==========================================
# CREAZIONE DEL GRAFICO A LIVELLI (1-5)
# ==========================================
sns.set_theme(style="whitegrid")
plt.figure(figsize=(12, 7))

# Colori per rispettare il design dell'immagine
palette = ["#d62828", "#2a9d8f", "#0077b6"] 

ax = sns.lineplot(
    data=df, 
    x="Round", 
    y="Trust_Value",
    hue="Gruppo", 
    palette=palette,
    marker="o", 
    linewidth=3,
    markersize=9,
    errorbar='ci' # Mostra le bande di confidenza per validità statistica
)

# Sostituiamo i numeri sull'asse Y con le etichette di testo (Da Basso ad Alto)
plt.yticks([1, 2, 3, 4, 5], ['Basso', 'Medio-basso', 'Neutro', 'Medio-alto', 'Alto'])
plt.ylim(0.8, 5.2)

# Linea del disastro e del recupero
plt.axvline(x=3, color='black', linestyle='--', alpha=0.5)
plt.text(3.05, 1.1, 'Violazione Fiducia (Round 3)', color='black', fontsize=10, fontstyle='italic')

plt.axvline(x=4, color='green', linestyle='--', alpha=0.5)
plt.text(4.05, 1.1, 'Recupero (Round 4)', color='green', fontsize=10, fontstyle='italic')

plt.title("Dinamiche di Trust nell'Interazione HRI\nScenario 1: Consulente Finanziario", fontsize=16, fontweight='bold', pad=20)
plt.xlabel("Round di Interazione", fontsize=12)
plt.ylabel("Livello di Trust Percepito", fontsize=12)
plt.xticks(range(0, 7))

# Posizioniamo la legenda fuori per non coprire le linee
plt.legend(title="Archetipi di Pazienti", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)

plt.tight_layout()
plt.savefig("grafico_finanziario.png", dpi=300)
plt.show()