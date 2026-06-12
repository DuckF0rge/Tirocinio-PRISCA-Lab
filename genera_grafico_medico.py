import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# Mappa degli stati in valori numerici continui
state_to_num = {
    'Basso': 1,
    'Medio-basso': 2,
    'Neutro': 3,
    'Medio-alto': 4,
    'Alto': 5
}

dati_plot = []

# Leggiamo il log dello scenario medico
try:
    with open('risultati_esperimento_medico.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
except FileNotFoundError:
    print("Errore: file 'risultati_esperimento_medico.txt' non trovato.")
    exit()

current_user = None

for line in lines:
    if line.startswith('RISULTATI PER IL PAZIENTE:'):
        current_user = line.split(':')[1].strip()
        
    # Estrazione Trust Iniziale (Round 0)
    if 'TRUST INIZIALE (Round 0):' in line:
        match = re.search(r'Round 0\): ([a-zA-Z\-]+)', line)
        if match:
            stato = match.group(1)
            dati_plot.append({'Utente': current_user, 'Round': 0, 'Trust_Value': state_to_num.get(stato, 3)})
            
    # Estrazione Trust Round 1-6
    if '==> TRUST FINALE (ROUND' in line:
        match = re.search(r'ROUND (\d+)\): \*\*([a-zA-Z\-]+)\*\*', line)
        if match:
            rnd = int(match.group(1))
            stato = match.group(2)
            dati_plot.append({'Utente': current_user, 'Round': rnd, 'Trust_Value': state_to_num.get(stato, 3)})

df = pd.DataFrame(dati_plot)

# Suddivisione nei 3 gruppi
def assegna_gruppo(utente):
    num = int(utente.replace('P', ''))
    if num <= 30: return 'Gruppo A: Ansiosi (P01-P30)'
    elif num <= 65: return 'Gruppo B: Tecno-Entusiasti (P31-P65)'
    else: return 'Gruppo C: Razionali (P66-P100)'

df['Gruppo'] = df['Utente'].apply(assegna_gruppo)

# Creazione del Plot
plt.figure(figsize=(12, 7))
sns.set_theme(style="whitegrid")

# Colori a tema medico (Rosso allarme, Verde speranza, Blu analitico)
palette = {
    'Gruppo A: Ansiosi (P01-P30)': '#d62828', 
    'Gruppo B: Tecno-Entusiasti (P31-P65)': '#2a9d8f', 
    'Gruppo C: Razionali (P66-P100)': '#0077b6'
}

# Lineplot con media per gruppo
ax = sns.lineplot(data=df, x='Round', y='Trust_Value', hue='Gruppo', 
                  marker='o', linewidth=3, markersize=9, palette=palette, errorbar=None)

plt.title('Dinamiche di Trust nell\'Interazione HRI\nScenario 2: Assistente Medico-Nutrizionale', 
          fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Round di Interazione', fontsize=12, labelpad=10)
plt.ylabel('Livello di Trust Percepito', fontsize=12, labelpad=10)

plt.yticks([1, 2, 3, 4, 5], ['Basso', 'Medio-basso', 'Neutro', 'Medio-alto', 'Alto'])
plt.ylim(0.8, 5.2)

# Linee verticali per gli eventi narrativi
plt.axvline(x=3, color='black', linestyle='--', alpha=0.6)
plt.text(3.05, 1.1, 'Errore Medico (Round 3)', color='black', fontsize=10, fontstyle='italic')

plt.axvline(x=4, color='green', linestyle='--', alpha=0.6)
plt.text(4.05, 1.1, 'Recupero e Scuse (Round 4)', color='green', fontsize=10, fontstyle='italic')

plt.legend(title='Archetipi di Pazienti', fontsize=11, title_fontsize=12, loc='lower right')
plt.tight_layout()

# Salvataggio
plt.savefig('grafico_medico.png', dpi=300)
print("Plot generato e salvato come 'plot_trust_scenario_medico.png'")