import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connetti_google_sheets(url_foglio):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credenziali.json', scope)
    client = gspread.authorize(creds)
    return client.open_by_url(url_foglio).sheet1

def scarica_database_T0():
    # url_t0 = "https://docs.google.com/spreadsheets/d/19FiqEfbQGqWZTRgBYmevrhzcSBdt1jh6oquyz8sIMhc/edit?usp=sharing"
    url_t0 = "https://docs.google.com/spreadsheets/d/1IWyk24hZQsDJtduFZgFgYAv8L2mUT1vg_0mG_1CyI1I/edit?usp=sharing" # Estrazione per scenario medico
    sheet = connetti_google_sheets(url_t0)
    tutti_i_record = sheet.get_all_records()
    
    database_t0 = {}
    for utente in tutti_i_record:
        # Estraiamo l'ID e saltiamo le righe vuote
        id_p = str(utente.get("ID Partecipante", "")).strip()
        if not id_p: 
            continue
        
        try:
            ben_1 = int(utente["In generale le persone tengono davvero al benessere degli altri"])
            ben_2 = int(utente["La persona tipica è sinceramente preoccupata per i problemi altrui"])
            ben_3 = int(utente["La maggior parte delle volte, le persone si preoccupano abbastanza da cercare di essere d'aiuto, piuttosto che pensare solo a sé stesse"])
            media_benevolence = (ben_1 + ben_2 + ben_3) / 3

            int_1 = int(utente["In generale, la maggior parte delle persone mantiene le proprie promesse"])
            int_2 = int(utente["Penso che le persone in genere cerchino di sostenere le proprie parole con i fatti"])
            int_3 = int(utente["La maggior parte delle persone è onesta nei rapporti con gli altri"])
            media_integrity = (int_1 + int_2 + int_3) / 3

            abi_1 = int(utente["Credo che la maggior parte dei professionisti svolga un ottimo lavoro nel proprio campo"])
            abi_2 = int(utente["La maggior parte dei professionisti è molto competente nel settore che ha scelto"])
            abi_3 = int(utente["Una grande maggioranza di professionisti è competente nella propria area di specializzazione"])
            media_ability = (abi_1 + abi_2 + abi_3) / 3

            prop_1 = int(utente["Di solito mi fido delle persone finché non mi danno un motivo per non farlo"])
            prop_2 = int(utente["In genere do alle persone il beneficio del dubbio quando le incontro per la prima volta"])
            prop_3 = int(utente["Il mio approccio tipico è quello di fidarmi dei nuovi conoscenti finché non dimostrano che non dovrei farlo"])
            media_stance = (prop_1 + prop_2 + prop_3) / 3

            propensity_globale = int(round((media_benevolence + media_integrity + media_ability + media_stance) / 4))
            integrity_iniziale = int(round(media_integrity))

            database_t0[id_p] = {
                'Propensity_to_Trust': propensity_globale,
                'Integrity_Prior': integrity_iniziale, 
                'InitialPropensityRisk': int(utente["In generale, quanto sei propenso ad accettare un rischio durante l'utilizzo di una nuova tecnologia"])
            }
        except Exception as e:
            continue
            
    return database_t0

def scarica_database_MID():
    # url_mid = "https://docs.google.com/spreadsheets/d/18qulPTiSaEpmDKAPZFW7hi6s1Ev0kUINDvuKSiHrTfk/edit?usp=sharing"
    url_mid = "https://docs.google.com/spreadsheets/d/1ko6eqUSZnfZLH-U70o2tK3Rd9YjMcYznv2VXxCZsFlA/edit?usp=sharing" #url per estrazione scenario medico
    sheet = connetti_google_sheets(url_mid)
    tutti_i_record = sheet.get_all_records()
    
    database_mid = {}
    for utente in tutti_i_record:
        id_p = str(utente.get("ID Partecipante", "")).strip()
        if not id_p: 
            continue
        
        try:
            ill_1 = 6 - int(utente["Il funzionamento generale del robot è un mistero per me"])
            ill_2 = 6 - int(utente["E’ difficile capire il generale funzionamento del robot"])
            ill_3 = 6 - int(utente["E’ difficile avere una chiara visione delle operazioni generali del robot"])
            ill_4 = 6 - int(utente["Sono confuso sul obiettivo generale del robot"])
            ill_5 = 6 - int(utente["Non sono sicuro di cosa faccia il robot"])
            ill_6 = 6 - int(utente["Non capisco quali siano i processi interni del robot"])
            ill_7 = 6 - int(utente["Non so spiegare il comportamento del robot"])
            ill_8 = 6 - int(utente["E’ impossibile sapere cosa il robot faccia"]) 
            ill_9 = int(utente["Mi è chiaro cosa il robot faccia"])
            ill_10 = int(utente["Ho una chiara comprensione sul come il robot operi in generale"])
            ill_11 = int(utente["Ho l’impressione che le spiegazioni del robot siano utili"])
            media_illegibilita = sum([ill_1, ill_2, ill_3, ill_4, ill_5, ill_6, ill_7, ill_8, ill_9, ill_10, ill_11]) / 11

            spi_1 = int(utente["Il robot spiega task complessi in un modo semplice da capire"])
            spi_2 = int(utente["Il robot da spiegazioni dettagliate delle sue azioni"])
            spi_3 = int(utente["Il robot da chiare spiegazioni delle sue azioni"])
            spi_4 = int(utente["Le spiegazioni date dal robot sulle sue azioni sono dirette"])
            spi_5 = int(utente["Mi sento informato riguardo le attività del robot"])
            spi_6 = int(utente["Il robot comunica il suo stato generale in maniera effettiva"])
            spi_7 = int(utente["E’ facile per me prevedere le future azioni del robot"])
            media_spiegabilita = sum([spi_1, spi_2, spi_3, spi_4, spi_5, spi_6, spi_7]) / 7

            pre_1 = int(utente["Il comportamento del robot è prevedibile"])
            pre_2 = int(utente["Mi sento sicuro nel predire i movimenti successivi del robot"])
            pre_3 = int(utente["E’ facile anticipare cosa avverrà dal comportamento del robot"])
            pre_4 = 6 - int(utente["E’ difficile per me dire cosa il robot farà successivamente"])
            pre_5 = int(utente["Le prossime azioni del robot sono chiare per me"])
            pre_6 = int(utente["Le azioni del robot sono scontate"])
            pre_7 = int(utente["Il robot da indizi che aiutano a predire le sue successive azioni"])
            pre_8 = 6 - int(utente["Il comportamento del robot non aiuta a predire cosa farà successivamente"])
            media_prevedibilita = sum([pre_1, pre_2, pre_3, pre_4, pre_5, pre_6, pre_7, pre_8]) / 8

            int_1 = int(utente["In generale, il robot ha mantenuto le proprie promesse"])
            int_2 = int(utente["Penso che il robot in genere abbia sostenuto le sue parole con i fatti"])
            int_3 = int(utente["Il robot è stato onesto nei rapporti"])
            media_integrity_mid = (int_1 + int_2 + int_3) / 3

            ben_mid_1 = int(utente["Il robot è molto attento al mio benessere durante il compito"])
            ben_mid_2 = int(utente["I miei bisogni e desideri sono molto importanti per il robot"])
            ben_mid_3 = int(utente["Il robot non ha fatto consapevolmente nulla per influenzare negativamente la mia performance durante il compito"])
            ben_mid_4 = int(utente["Il robot si preoccupa realmente di ciò che è importante per me"])
            ben_mid_5 = int(utente["Il robot non farà di tutto per aiutarmi"])
            media_benevolence_mid = (ben_mid_1 + ben_mid_2 + ben_mid_3 + ben_mid_4 + ben_mid_5) / 5

            abi_mid = int(utente["Il robot è stato abile nel guidarmi al completamento del task"])
            per_risk = int(utente["Quanto è stato critico o pericoloso il compito che il robot ti ha guidato a svolgere in questo studio"])

            media_transparency = int(round((media_illegibilita + media_spiegabilita + media_prevedibilita) / 3))
            media_integrity_mid = int(round(media_integrity_mid))
            media_benevolence_mid = int(round(media_benevolence_mid))

            database_mid[id_p] = {
                'Transparency_Mid': media_transparency,
                'Integrity_Mid': media_integrity_mid,
                'Benevolence_Mid': media_benevolence_mid,
                'Ability_Mid': abi_mid,
                'Perceived_Risk_Mid': per_risk
            }
        except Exception as e:
            continue
            
    return database_mid