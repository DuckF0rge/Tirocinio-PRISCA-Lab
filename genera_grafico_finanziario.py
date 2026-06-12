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
        return "Gruppo A: Conservatori"
    elif num <= 65:
        return "Gruppo B: Tecno-Entusiasti"
    else:
        return "Gruppo C: Razionali/Analitici"

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
            
            if  not utente_corrente:
                continue

            # Estrai il Trust Iniziale (Round 0)
            match_t0 = re.search(r"TRUST INIZIALE \(Round 0\): .* \(([\d\.]+)%\)", linea)
            if match_t0:
                dati_grafico.append({"Utente": utente_corrente, "Gruppo": gruppo, "Round": 0, "Trust (%)": float(match_t0.group(1))})
            
            # Estrai il Trust dei Round 1-6 
            # (Supporta sia la vecchia dicitura che la nuova dicitura "TRUST FINALE")
            match_round = re.search(r"(?:TRUST CALCOLATO A FINE ROUND|TRUST FINALE \(ROUND) (\d)\)?: .* \(([\d\.]+)%\)", linea)
            if match_round:
                round_num = int(match_round.group(1))
                trust_val = float(match_round.group(2))
                dati_grafico.append({"Utente": utente_corrente, "Gruppo": gruppo, "Round": round_num, "Trust (%)": trust_val})

except FileNotFoundError:
    print(f"Errore: Il file {FILE_INPUT} non è stato trovato nella cartella.")
    exit()

# Creazione del DataFrame Pandas
df = pd.DataFrame(dati_grafico)

# CALCOLO DEL DELTA TRUST
# Calcoliamo il Trust_0 per ogni utente e sottraiamolo a ogni riga
df['Trust_0'] = df.groupby('Utente')['Trust (%)'].transform(lambda x: x[x.index == 0].iloc[0] if len(x[x.index == 0]) > 0 else 0)
df['Delta Trust (%)'] = df['Trust (%)'] - df['Trust_0']

# ==========================================
# CREAZIONE DEL GRAFICO (DELTA TRUST)
# ==========================================
sns.set_theme(style="whitegrid")
plt.figure(figsize=(12, 7))

ax = sns.lineplot(
    data=df, 
    x="Round", 
    y="Delta Trust (%)",
    hue="Gruppo", 
    palette=["#e74c3c", "#2ecc71", "#3498db"],
    marker="o", 
    linewidth=2.5,
    errorbar='ci'
)

# Linea dello zero (il punto di partenza comune)
plt.axhline(0, color='gray', linestyle='-', alpha=0.3)
# Linea del disastro
plt.axvline(x=3, color='black', linestyle='--', alpha=0.5)

plt.title("Evoluzione del Delta Trust (Reazione agli Stimoli)", fontsize=16, fontweight='bold', pad=20)
plt.xlabel("Round di Interazione", fontsize=12)
plt.ylabel("Variazione del Trust rispetto alla Baseline (%)", fontsize=12)
plt.xticks(range(0, 7))
plt.legend(title="Archetipo Psicologico", bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.savefig("grafico_finanziario.png", dpi=300)
plt.show()