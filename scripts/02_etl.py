"""
Questo è lo script ETL (Estrazione, Trasformazione, Caricamento): prende
i CSV generati da 01_genera_dati.py e li carica dentro il database
SQLite, seguendo lo schema a stella definito in db/schema.sql.

Le tre fasi sono divise abbastanza chiaramente nel codice:
- estrazione: leggo i CSV così come sono
- trasformazione: sistemo i tipi (stringhe -> int/float), gestisco i
  valori mancanti e costruisco la dimensione Tempo
- caricamento: creo le tabelle e ci scrivo dentro i dati
"""

import csv
import sqlite3
from datetime import datetime

DB_PATH = "db/homecare.db"
SCHEMA_PATH = "db/schema.sql"

GIORNI_SETTIMANA = ["lunedì", "martedì", "mercoledì", "giovedì",
                     "venerdì", "sabato", "domenica"]
NOMI_MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
             "luglio", "agosto", "settembre", "ottobre", "novembre",
             "dicembre"]


# ESTRAZIONE

def leggi_csv(percorso: str) -> list[dict]:
    with open(percorso, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# TRASFORMAZIONE

def pulisci_clienti(righe: list[dict]) -> list[tuple]:
    out = []
    for r in righe:
        out.append((
            int(r["cliente_id"]),
            r["nome"].strip(),
            r["cognome"].strip(),
            r["zona"].strip(),
            r["data_iscrizione"].strip(),
        ))
    return out


def pulisci_fornitori(righe: list[dict]) -> list[tuple]:
    out = []
    for r in righe:
        out.append((
            int(r["fornitore_id"]),
            r["nome"].strip(),
            r["categoria_servizio"].strip(),
            r["zona"].strip(),
        ))
    return out


def pulisci_operatori(righe: list[dict]) -> list[tuple]:
    out = []
    for r in righe:
        out.append((
            int(r["operatore_id"]),
            r["nome"].strip(),
            r["cognome"].strip(),
            r["zona"].strip(),
            r["tipo_attivita"].strip(),
        ))
    return out




def costruisci_dim_tempo(righe_richieste: list[dict]) -> list[tuple]:
    """La Dim_Tempo non è un calendario completo, ma solo i giorni che
    compaiono davvero nelle richieste (con 9 mesi di dati non tutti i
    giorni sono per forza rappresentati). Prendo le date uniche e per
    ognuna calcolo mese, trimestre, giorno della settimana ecc."""
    
    date_uniche = set()
    for r in righe_richieste:
        data_str = r["data_ora"].split(" ")[0]  # solo la parte data
        date_uniche.add(data_str)

    out = []
    for data_str in sorted(date_uniche):
        dt = datetime.strptime(data_str, "%Y-%m-%d")
        data_id = int(dt.strftime("%Y%m%d"))
        trimestre = (dt.month - 1) // 3 + 1
        is_weekend = 1 if dt.weekday() >= 5 else 0
        out.append((
            data_id,
            data_str,
            dt.year,
            dt.month,
            NOMI_MESI[dt.month - 1],
            trimestre,
            GIORNI_SETTIMANA[dt.weekday()],
            is_weekend,
        ))
    return out




def pulisci_richieste(righe: list[dict]) -> list[tuple]:
    """Qui oltre a pulire i campi devo anche collegare ogni richiesta
    alla Dim_Tempo, quindi trasformo la data in un data_id (YYYYMMDD)
    che corrisponde alla chiave primaria della dimensione."""

    out = []
    for r in righe:
        data_str, ora_str = r["data_ora"].split(" ")
        dt = datetime.strptime(data_str, "%Y-%m-%d")
        data_id = int(dt.strftime("%Y%m%d"))
        ora = ora_str[:5]  # HH:MM

        # tempo_erogazione_min può essere una stringa vuota (richieste
        # annullate o ancora in corso non hanno un tempo di erogazione),
        # quindi la trasformo in None così SQLite la salva come NULL
        tempo_erog = r["tempo_erogazione_min"].strip()
        tempo_erog = int(tempo_erog) if tempo_erog != "" else None

        out.append((
            int(r["richiesta_id"]),
            int(r["cliente_id"]),
            int(r["fornitore_id"]),
            int(r["operatore_id"]),
            data_id,
            ora,
            r["categoria_servizio"].strip(),
            r["zona"].strip(),
            round(float(r["importo"]), 2),
            tempo_erog,
            r["stato"].strip(),
        ))
    return out


# CARICAMENTO

def crea_schema(conn: sqlite3.Connection) -> None:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())


def carica_dati(conn: sqlite3.Connection,
                 clienti, fornitori, operatori, dim_tempo, richieste) -> None:
    cur = conn.cursor()

    cur.executemany(
        "INSERT INTO Dim_Cliente VALUES (?, ?, ?, ?, ?)", clienti)
    cur.executemany(
        "INSERT INTO Dim_Fornitore VALUES (?, ?, ?, ?)", fornitori)
    cur.executemany(
        "INSERT INTO Dim_Operatore VALUES (?, ?, ?, ?, ?)", operatori)
    cur.executemany(
        "INSERT INTO Dim_Tempo VALUES (?, ?, ?, ?, ?, ?, ?, ?)", dim_tempo)
    cur.executemany(
        "INSERT INTO Fatti_Richieste VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        richieste)

    conn.commit()


def verifica_caricamento(conn: sqlite3.Connection) -> None:   
    """Piccolo controllo finale: conto le righe direttamente dal database
    (non dalle liste Python che ho già in memoria) per essere sicuro che
    il caricamento sia andato a buon fine davvero, e non solo "sulla carta"."""

    tabelle = ["Dim_Cliente", "Dim_Fornitore", "Dim_Operatore",
               "Dim_Tempo", "Fatti_Richieste"]
    print("\nVerifica caricamento (conteggio righe nel database):")
    for tabella in tabelle:
        n = conn.execute(f"SELECT COUNT(*) FROM {tabella}").fetchone()[0]
        print(f"- {tabella}: {n} righe")


def main():
    # ESTRAZIONE
    clienti_raw = leggi_csv("data/clienti.csv")
    fornitori_raw = leggi_csv("data/fornitori.csv")
    operatori_raw = leggi_csv("data/operatori.csv")
    richieste_raw = leggi_csv("data/richieste.csv")

    # TRASFORMAZIONE
    clienti = pulisci_clienti(clienti_raw)
    fornitori = pulisci_fornitori(fornitori_raw)
    operatori = pulisci_operatori(operatori_raw)
    dim_tempo = costruisci_dim_tempo(richieste_raw)
    richieste = pulisci_richieste(richieste_raw)

    # CARICAMENTO
    conn = sqlite3.connect(DB_PATH)
    crea_schema(conn)
    carica_dati(conn, clienti, fornitori, operatori, dim_tempo, richieste)
    verifica_caricamento(conn)
    conn.close()

    print(f"\nETL completato. Database creato in: {DB_PATH}")
    print(f"- Clienti: {len(clienti)}")
    print(f"- Fornitori: {len(fornitori)}")
    print(f"- Operatori: {len(operatori)}")
    print(f"- Righe Dim_Tempo: {len(dim_tempo)}")
    print(f"- Richieste: {len(richieste)}")


if __name__ == "__main__":
    main()
