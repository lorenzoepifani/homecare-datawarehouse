"""
Genera i dati finti per HomeCare, la startup di manutenzione casa
che uso come caso di studio per il project work.

Alla fine avremo 4 CSV dentro data/: clienti, fornitori, operatori e
richieste (quest'ultima è la tabella dei fatti che poi andrà nel data
warehouse).

Nessun dato è reale, è tutto generato a caso (ma con un minimo di logica
dietro, vedi sotto).
"""

import csv
import random
from datetime import datetime, timedelta
from faker import Faker

# Seed fisso così ogni volta che rilancio lo script ottengo sempre
# gli stessi dati. Comodo per il debug e per non dover rifare gli
# screenshot ogni volta che tocco qualcosa.
random.seed(42)
Faker.seed(42)
fake = Faker("it_IT")  # per avere nomi e cognomi italiani plausibili


# PARAMETRI
# La traccia chiede 300-600 record per tipologia. Ho tenuto i valori
# abbastanza alti (vicino al massimo) perché il periodo storico è di 9
# mesi e con numeri troppo bassi i grafici della dashboard risultano spogli

N_CLIENTI = 600
N_FORNITORI = 480
N_OPERATORI = 520
N_RICHIESTE = 600

ZONE = ["Milano", "Torino", "Bologna", "Roma", "Napoli"]

CATEGORIE_SERVIZIO = [
    "Idraulica",
    "Elettricista",
    "Imbianchino",
    "Falegnameria",
    "Climatizzazione",
    "Giardinaggio e Irrigazione",
    "Caldaie",
]

# circa 9 mesi di storico (periodo scelto da me). Serve per avere abbastanza dati da
# far vedere un andamento nel tempo e la stagionalità dei servizi.
DATA_FINE = datetime(2026, 8, 31)
DATA_INIZIO = DATA_FINE - timedelta(days=273)

# Stato di una richiesta. "Completata" compare più volte nella lista
# così che random.choice() la selezioni più spesso delle altre, dando
# un peso maggiore senza dover ricorrere a random.choices().
STATI_RICHIESTA = ["completata", "completata", "completata", "completata",
                    "annullata", "in_ritardo", "in_corso"]

# Prefissi per i nomi dei fornitori, divisi per categoria, così un
# fornitore di Idraulica ha un nome come "IdroCasa" e non "PitturaProCasa"
NOMI_AZIENDA_FORNITORE = {
    "Idraulica": ["Idro", "AcquaPro", "TuboService", "IdroCasa", "RubinettoExpress"],
    "Elettricista": ["Elettro", "VoltService", "LucePro", "ElettroCasa", "AmpereTeam"],
    "Imbianchino": ["ColorCasa", "PitturaPro", "TintaService", "ColorExpress", "MuroNuovo"],
    "Falegnameria": ["LegnoService", "FalegnamPro", "WoodCasa", "TavolaExpress", "ArteLegno"],
    "Climatizzazione": ["ClimaService", "FreddoPro", "ClimaCasa", "AirExpress", "TermoTeam"],
    "Giardinaggio e Irrigazione": ["GreenService", "GiardinoPro", "VerdeCasa",
                                    "IrrigaExpress", "PratoTeam"],
    "Caldaie": ["CaldaiaService", "TermoCaldaie", "CalorPro", "CaldaieCasa",
                "HeatExpress"],
}
SUFFISSI_AZIENDA = ["Service", "Solutions", "Group", "Team", "Point", "Pro",
                    "Casa", "Express"]

# Range di prezzo per categoria (min, max in euro)
FASCE_PREZZO = {
    "Idraulica": (40, 250),
    "Elettricista": (35, 220),
    "Imbianchino": (80, 500),
    "Falegnameria": (50, 400),
    "Climatizzazione": (60, 450),
    "Giardinaggio e Irrigazione": (30, 200),
    "Caldaie": (80, 600),
}


# STAGIONALITÀ
# Idea: non tutte le categorie hanno la stessa probabilità in ogni mese.
# Le caldaie si rompono/servono più d'inverno, il giardino e l'aria
# condizionata più d'estate. Ho messo dei pesi diversi per stagione così
# nei grafici si vede questo cambiamento invece di avere delle linee più piatte.


def pesi_categoria_per_mese(mese: int) -> list[float]:
    """Dato un mese (1-12) restituisce i pesi da dare a ciascuna
    categoria per la scelta random (stesso ordine di CATEGORIE_SERVIZIO).
    Più alto il peso, più probabile che venga scelta quella categoria."""

    # pesi standard, validi più o meno tutto l'anno
    pesi = {
        "Idraulica": 18,
        "Elettricista": 16,
        "Imbianchino": 12,
        "Falegnameria": 10,
        "Climatizzazione": 10,
        "Giardinaggio e Irrigazione": 10,
        "Caldaie": 12,
    }

    # poi li modifico in base alla stagione
    if mese in (12, 1, 2):  # inverno
        pesi["Caldaie"] = 32
        pesi["Climatizzazione"] = 4
        pesi["Giardinaggio e Irrigazione"] = 3
    elif mese in (3, 4, 5):  # primavera
        pesi["Giardinaggio e Irrigazione"] = 24
        pesi["Imbianchino"] = 18  # tinteggiature in primavera
        pesi["Caldaie"] = 8
    elif mese in (6, 7, 8):  # estate
        pesi["Climatizzazione"] = 30
        pesi["Giardinaggio e Irrigazione"] = 20
        pesi["Caldaie"] = 3
    else:  # autunno
        pesi["Caldaie"] = 20  # revisione caldaia prima dell'inverno
        pesi["Giardinaggio e Irrigazione"] = 6

    return [pesi[c] for c in CATEGORIE_SERVIZIO]


# FUNZIONI DI GENERAZIONE

def data_casuale(inizio: datetime, fine: datetime) -> datetime:
    """Genera una data/ora a caso tra inizio e fine. Non è del tutto
    uniforme: ho fatto in modo che escano più spesso giorni feriali e
    orari diurni, perché è più realistico per un servizio di manutenzione
    (raramente ci sono chiamate durante la notte, se non in emergenza)."""
    delta_giorni = (fine - inizio).days
    giorno = inizio + timedelta(days=random.randint(0, delta_giorni))

    # se è capitato un weekend, il 60% delle volte lo "sposto" al
    # venerdì più vicino per avere più richieste nei giorni feriali
    if giorno.weekday() >= 5 and random.random() < 0.6:
        giorno = giorno - timedelta(days=giorno.weekday() - 4)

    # orario: soprattutto 9-12 e 15-18 (fasce tipiche di lavoro),
    # il resto del tempo un orario qualsiasi tra le 8 e le 20
    if random.random() < 0.7:
        ora = random.choice(list(range(9, 12)) + list(range(15, 18)))
    else:
        ora = random.randint(8, 20)
    minuto = random.randint(0, 59)

    return giorno.replace(hour=ora, minute=minuto, second=0, microsecond=0)


def genera_nome_cognome_unici(usati: set) -> tuple[str, str]:
    """Genera nome e cognome con Faker, controllando che la coppia non
    sia già uscita prima: con 500-600 persone generate a caso, senza
    questo controllo è concreto il rischio che capitino due omonimi
    identici. Uso first_name()/last_name() separati invece di
    fake.name() perché quest'ultimo a volte ci mette davanti "Dott."
    o "Sig." e non serviva."""
    while True:
        nome = fake.first_name()
        cognome = fake.last_name()
        chiave = (nome, cognome)
        if chiave not in usati:
            usati.add(chiave)
            return nome, cognome


def genera_clienti(n: int) -> list[dict]:
    clienti = []
    combinazioni_usate = set()
    for i in range(1, n + 1):
        nome, cognome = genera_nome_cognome_unici(combinazioni_usate)
        data_iscrizione = data_casuale(DATA_INIZIO, DATA_FINE)
        clienti.append({
            "cliente_id": i,
            "nome": nome,
            "cognome": cognome,
            "zona": random.choice(ZONE),
            "data_iscrizione": data_iscrizione.strftime("%Y-%m-%d"),
        })
    return clienti


def genera_fornitori(n: int) -> list[dict]:
    """Il nome del fornitore dipende dalla categoria: prendo un prefisso
    dalla lista giusta (solo prefissi "idraulici" per un fornitore di
    Idraulica), per evitare abbinamenti incoerenti come un imbianchino
    chiamato "IdroSolutions"."""
    fornitori = []
    for i in range(1, n + 1):
        categoria = random.choice(CATEGORIE_SERVIZIO)
        prefisso = random.choice(NOMI_AZIENDA_FORNITORE[categoria])
        # tolgo dai suffissi possibili quelli già contenuti nel prefisso,
        # altrimenti si generavano nomi ripetuti come "RubinettoExpressExpress"
        suffissi_validi = [s for s in SUFFISSI_AZIENDA if s not in prefisso]
        suffisso = random.choice(suffissi_validi)
        fornitori.append({
            "fornitore_id": i,
            "nome": f"{prefisso}{suffisso}",
            "categoria_servizio": categoria,
            "zona": random.choice(ZONE),
        })
    return fornitori


def genera_operatori(n: int) -> list[dict]:
    operatori = []
    combinazioni_usate = set()
    for i in range(1, n + 1):
        nome, cognome = genera_nome_cognome_unici(combinazioni_usate)
        operatori.append({
            "operatore_id": i,
            "nome": nome,
            "cognome": cognome,
            "zona": random.choice(ZONE),
            "tipo_attivita": random.choice(CATEGORIE_SERVIZIO),
        })
    return operatori


def genera_richieste(n: int, clienti: list[dict], fornitori: list[dict],
                      operatori: list[dict]) -> list[dict]:
    """Questa è la funzione principale, genera la tabella dei fatti.
    Per ogni richiesta: prendo un cliente a caso, scelgo la categoria di
    servizio pesata sul mese (stagionalità), poi cerco un fornitore e un
    operatore che abbiano senso rispetto a zona e categoria."""
    richieste = []

    # indici per trovare velocemente fornitori/operatori compatibili
    # con zona e categoria, invece di scorrere tutta la lista ogni volta
    fornitori_per_zona_categoria = {}
    for f in fornitori:
        chiave = (f["zona"], f["categoria_servizio"])
        fornitori_per_zona_categoria.setdefault(chiave, []).append(f)

    operatori_per_zona_tipo = {}
    for o in operatori:
        chiave = (o["zona"], o["tipo_attivita"])
        operatori_per_zona_tipo.setdefault(chiave, []).append(o)

    operatori_per_zona = {}
    for o in operatori:
        operatori_per_zona.setdefault(o["zona"], []).append(o)

    for i in range(1, n + 1):
        cliente = random.choice(clienti)
        zona = cliente["zona"]

        data_richiesta = data_casuale(DATA_INIZIO, DATA_FINE)
        pesi = pesi_categoria_per_mese(data_richiesta.month)
        categoria = random.choices(CATEGORIE_SERVIZIO, weights=pesi, k=1)[0]

        # provo prima a prendere un fornitore della stessa zona e
        # categoria; se non c'è (può capitare, sono dati random) allora
        # prendo uno qualsiasi di quella categoria
        pool_fornitori = fornitori_per_zona_categoria.get((zona, categoria))
        if not pool_fornitori:
            pool_fornitori = [f for f in fornitori
                               if f["categoria_servizio"] == categoria]
        fornitore = random.choice(pool_fornitori)

        # stessa logica per l'operatore
        pool_operatori = operatori_per_zona_tipo.get((zona, categoria))
        if not pool_operatori:
            pool_operatori = operatori_per_zona.get(zona, operatori)
        operatore = random.choice(pool_operatori)

        min_p, max_p = FASCE_PREZZO.get(categoria, (30, 200))
        importo = round(random.uniform(min_p, max_p), 2)

        stato = random.choice(STATI_RICHIESTA)

        # il tempo di erogazione dipende dallo stato: se è annullata o
        # ancora in corso non ha senso avere un tempo (non si è ancora
        # concluso niente), se è in ritardo il tempo è più alto del
        # normale
        if stato == "annullata":
            tempo_erogazione = None
            importo = 0.0  # una richiesta annullata non porta incasso
        elif stato == "in_corso":
            tempo_erogazione = None
        elif stato == "in_ritardo":
            tempo_erogazione = random.randint(90, 300)
        else:
            tempo_erogazione = random.randint(30, 150)

        richieste.append({
            "richiesta_id": i,
            "cliente_id": cliente["cliente_id"],
            "fornitore_id": fornitore["fornitore_id"],
            "operatore_id": operatore["operatore_id"],
            "data_ora": data_richiesta.strftime("%Y-%m-%d %H:%M:%S"),
            "categoria_servizio": categoria,
            "zona": zona,
            "importo": importo,
            "tempo_erogazione_min": tempo_erogazione
            if tempo_erogazione is not None else "",
            "stato": stato,
        })

    return richieste


def salva_csv(righe: list[dict], percorso: str) -> None:
    if not righe:
        return
    campi = list(righe[0].keys())
    with open(percorso, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campi)
        writer.writeheader()
        writer.writerows(righe)


def main():
    clienti = genera_clienti(N_CLIENTI)
    fornitori = genera_fornitori(N_FORNITORI)
    operatori = genera_operatori(N_OPERATORI)
    richieste = genera_richieste(N_RICHIESTE, clienti, fornitori, operatori)

    salva_csv(clienti, "data/clienti.csv")
    salva_csv(fornitori, "data/fornitori.csv")
    salva_csv(operatori, "data/operatori.csv")
    salva_csv(richieste, "data/richieste.csv")

    print(f"Generati: {len(clienti)} clienti, {len(fornitori)} fornitori, "
          f"{len(operatori)} operatori, {len(richieste)} richieste.")
    print("File salvati nella cartella data/")


if __name__ == "__main__":
    main()
