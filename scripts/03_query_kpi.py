"""
Qui ci sono le query SQL per i 4 indicatori principali chiesti dalla
traccia: numero richieste, incassi, tempo medio di erogazione e
percentuale di clienti che tornano (retention).
Una cosa a cui ho fatto attenzione: le stesse identiche definizioni
devono valere anche nella dashboard (04_dashboard.py).
"""

import sqlite3

DB_PATH = "db/homecare.db"


def numero_richieste(conn: sqlite3.Connection) -> dict:
    """Conta le richieste totali e anche il dettaglio per stato, così si
    vede subito quante sono andate a buon fine e quante no."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Fatti_Richieste")
    totale = cur.fetchone()[0]

    cur.execute("""
        SELECT stato, COUNT(*) 
        FROM Fatti_Richieste 
        GROUP BY stato
        ORDER BY COUNT(*) DESC
    """)
    per_stato = dict(cur.fetchall())

    return {"totale": totale, "per_stato": per_stato}


def incassi(conn: sqlite3.Connection) -> dict:
    """Calcolo due numeri diversi per "incassi", perché dire solo
    "incassi totali" è ambiguo:
    - realizzati: solo richieste completate o in ritardo, cioè dove il
      servizio è stato davvero erogato e quindi i soldi sono incassati
      per davvero
    - previsti: somma di tutto, comprese le richieste ancora in corso
      (il cui importo è previsto ma non ancora incassato). Le annullate
      valgono 0 quindi non cambiano il conto.
    Aggiungo anche il dettaglio realizzati per città."""
    cur = conn.cursor()

    cur.execute("""
        SELECT ROUND(SUM(importo), 2) FROM Fatti_Richieste
        WHERE stato IN ('completata', 'in_ritardo')
    """)
    realizzati = cur.fetchone()[0]

    cur.execute("SELECT ROUND(SUM(importo), 2) FROM Fatti_Richieste")
    previsti = cur.fetchone()[0]

    cur.execute("""
        SELECT zona, ROUND(SUM(importo), 2) AS incasso
        FROM Fatti_Richieste
        WHERE stato IN ('completata', 'in_ritardo')
        GROUP BY zona
        ORDER BY incasso DESC
    """)
    realizzati_per_zona = dict(cur.fetchall())

    return {"realizzati": realizzati, "previsti": previsti,
            "realizzati_per_zona": realizzati_per_zona}


def tempo_medio_erogazione(conn: sqlite3.Connection) -> dict:
    """Media dei minuti di erogazione. Uso semplicemente AVG(), che in
    SQL ignora automaticamente i valori NULL - e le richieste annullate
    o ancora in corso hanno proprio tempo_erogazione_min NULL, quindi
    vengono escluse dal calcolo senza dover scrivere un WHERE apposta."""
    cur = conn.cursor()
    cur.execute("""
        SELECT ROUND(AVG(tempo_erogazione_min), 1)
        FROM Fatti_Richieste
        WHERE tempo_erogazione_min IS NOT NULL
    """)
    media_generale = cur.fetchone()[0]

    cur.execute("""
        SELECT categoria_servizio, ROUND(AVG(tempo_erogazione_min), 1) AS media
        FROM Fatti_Richieste
        WHERE tempo_erogazione_min IS NOT NULL
        GROUP BY categoria_servizio
        ORDER BY media DESC
    """)
    per_categoria = dict(cur.fetchall())

    return {"media_generale_minuti": media_generale,
            "per_categoria": per_categoria}


def percentuale_clienti_ricorrenti(conn: sqlite3.Connection) -> dict:
    """Un cliente "attivo" per me è uno che ha almeno una richiesta che
    ha comportato un servizio vero (quindi escludo le annullate: un
    cliente che prova a prenotare e poi annulla non ha davvero usato il
    servizio). Un cliente "ricorrente" è uno con più di una di queste
    richieste.
    La percentuale è: ricorrenti / attivi. """
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(DISTINCT cliente_id) FROM Fatti_Richieste
        WHERE stato != 'annullata'
    """)
    clienti_attivi = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT cliente_id
            FROM Fatti_Richieste
            WHERE stato != 'annullata'
            GROUP BY cliente_id
            HAVING COUNT(*) > 1
        )
    """)
    clienti_ricorrenti = cur.fetchone()[0]

    percentuale = (round(100 * clienti_ricorrenti / clienti_attivi, 1)
                   if clienti_attivi > 0 else 0)

    return {
        "clienti_attivi": clienti_attivi,
        "clienti_ricorrenti": clienti_ricorrenti,
        "percentuale_ricorrenti": percentuale,
    }


def stampa_report_kpi(conn: sqlite3.Connection) -> None:
    print("=" * 60)
    print("REPORT INDICATORI PRINCIPALI - HomeCare")
    print("=" * 60)

    nr = numero_richieste(conn)
    print(f"\n1) NUMERO DI RICHIESTE")
    print(f"   Totale: {nr['totale']}")
    for stato, count in nr["per_stato"].items():
        print(f"   - {stato}: {count}")

    inc = incassi(conn)
    print(f"\n2) INCASSI")
    print(f"   Realizzati (completata + in_ritardo): {inc['realizzati']} EUR")
    print(f"   Previsti (tutte le richieste): {inc['previsti']} EUR")
    print("   Realizzati per città:")
    for zona, val in inc["realizzati_per_zona"].items():
        print(f"   - {zona}: {val} EUR")

    tempo = tempo_medio_erogazione(conn)
    print(f"\n3) TEMPO MEDIO DI EROGAZIONE")
    print(f"   Media generale: {tempo['media_generale_minuti']} minuti")
    print("   Per categoria:")
    for cat, val in tempo["per_categoria"].items():
        print(f"   - {cat}: {val} minuti")

    ret = percentuale_clienti_ricorrenti(conn)
    print(f"\n4) PERCENTUALE CLIENTI RICORRENTI (RETENTION)")
    print(f"   Clienti attivi (>=1 richiesta): {ret['clienti_attivi']}")
    print(f"   Clienti ricorrenti (>1 richiesta): {ret['clienti_ricorrenti']}")
    print(f"   Percentuale ricorrenti: {ret['percentuale_ricorrenti']}%")

    print("\n" + "=" * 60)


def main():
    conn = sqlite3.connect(DB_PATH)
    stampa_report_kpi(conn)
    conn.close()


if __name__ == "__main__":
    main()
