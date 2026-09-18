# HomeCare — Data Warehouse e Dashboard (Project Work)

## Panoramica

Questo progetto è un prototipo di **data warehouse** organizzato "a stella"
e di una **dashboard interattiva**, sviluppato per HomeCare: un'ipotetica
startup digitale di servizi di manutenzione casa on-demand (idraulica,
elettricista, imbianchino, falegnameria, climatizzazione, giardinaggio e
irrigazione, caldaie).

Il progetto è composto da quattro script Python, da eseguire **in ordine**:

1. genera i dati sintetici (clienti, fornitori, operatori, richieste);
2. li carica in un database SQLite organizzato a stella;
3. calcola a terminale i quattro indicatori (KPI) richiesti;
4. mostra i dati in una dashboard web interattiva.

## Struttura del progetto

```
pw21/
├── data/                  CSV generati dallo script 1 (clienti, fornitori, operatori, richieste)
├── db/
│   ├── schema.sql         schema SQL del data warehouse a stella
│   └── homecare.db        database SQLite creato dallo script 2
├── scripts/
│   ├── 01_genera_dati.py  genera i 4 CSV con dati sintetici
│   ├── 02_etl.py          carica i CSV nel data warehouse SQLite
│   ├── 03_query_kpi.py    stampa a terminale i 4 indicatori principali
│   └── 04_dashboard.py    dashboard interattiva (Streamlit)
├── .streamlit/
│   └── config.toml        tema grafico della dashboard (colori)
├── requirements.txt       librerie Python necessarie
└── README.md              questo file
```

## 1. Requisiti

- Python 3.10 o superiore
- (opzionale) un ambiente virtuale, per non installare le
  librerie del progetto insieme a quelle già presenti sul sistema

## 2. Installazione

Aprire un terminale nella cartella `pw21/` ed eseguire:

```bash
# opzionale: crea e attiva un ambiente virtuale
python3 -m venv venv
source venv/bin/activate        # su Windows: venv\Scripts\activate

# installa le librerie richieste
pip install -r requirements.txt
```

## 3. Esecuzione

Gli script vanno eseguiti **in ordine numerico**, sempre dalla cartella
`pw21/`. Ogni passo dipende dall'esito del precedente.

I comandi seguenti usano `python3`, il nome standard su macOS e Linux
(dove convivono spesso più versioni di Python). Su Windows il comando
è di solito `python` (senza il 3): se uno dei due non viene riconosciuto
dal terminale, provare l'altro.

### Passo 1 — Generazione dei dati sintetici

```bash
python3 scripts/01_genera_dati.py
```

Al termine, nella cartella `data/` compaiono quattro file: `clienti.csv`,
`fornitori.csv`, `operatori.csv`, `richieste.csv`. Si possono aprire con
Excel, LibreOffice Calc o un editor di testo per ispezionare i dati
generati.

### Passo 2 — Caricamento nel data warehouse (ETL)

```bash
python3 scripts/02_etl.py
```

Lo script legge i quattro CSV, li pulisce e li carica in un nuovo
database SQLite, `db/homecare.db`. Al termine stampa a schermo il numero
di righe caricate in ciascuna tabella, come controllo che il caricamento
sia andato a buon fine.

Per esplorare il contenuto del database in modo visuale è utile **DB
Browser for SQLite**: https://sqlitebrowser.org/. Aprendo
`homecare.db` con questo programma si possono consultare le tabelle
`Fatti_Richieste`, `Dim_Cliente`, `Dim_Fornitore`, `Dim_Operatore` e
`Dim_Tempo` riga per riga.

### Passo 3 — Calcolo degli indicatori (KPI)

```bash
python3 scripts/03_query_kpi.py
```

Stampa a terminale i quattro indicatori richiesti: numero di richieste,
incassi, tempo medio di erogazione e percentuale di clienti ricorrenti.
Per gli incassi vengono mostrati due valori distinti:

- **realizzati**: solo le richieste completate o in ritardo, per cui il
  servizio è stato effettivamente erogato;
- **previsti**: tutte le richieste, comprese quelle ancora in corso, il
  cui importo è preventivato ma non ancora incassato.

### Passo 4 — Dashboard interattiva

```bash
streamlit run scripts/04_dashboard.py
```

Il comando avvia un server locale e apre automaticamente il browser su
`http://localhost:8501` (se non si apre da solo, copiare l'indirizzo
mostrato nel terminale). La pagina è organizzata, dall'alto in basso, in
questo modo:

| Blocco | Contenuto |
|---|---|
| Indicatori principali | numero richieste, tempo medio di erogazione, clienti attivi, percentuale di clienti ricorrenti |
| Distribuzione richieste | un selettore alterna la vista per stato, per categoria o per zona |
| Incassi | due indicatori: realizzati e previsti |
| Andamento nel tempo | un selettore alterna la vista totale o suddivisa per categoria |
| Fornitori e città | classifica dei primi 5 fornitori per incassi, e incassi per città |
| Filtri (barra laterale) | periodo, città, categoria di servizio |

Cambiando un filtro, tutti gli indicatori e i grafici si aggiornano di
conseguenza. Per chiudere la dashboard, tornare al terminale e premere
`CTRL+C`.

Una precisazione sulla definizione di "clienti attivi" e "clienti
ricorrenti": sono calcolati escludendo le richieste annullate. Un
cliente che ha soltanto una richiesta poi annullata non viene quindi
considerato attivo, perché non ha effettivamente usufruito del
servizio.

## 4. Note sull'ordine di esecuzione

Se si rigenerano i dati (Passo 1), è necessario rilanciare anche l'ETL
(Passo 2): senza questo passaggio, il database resterebbe quello vecchio
e la dashboard mostrerebbe dati non aggiornati.

## 5. Caratteristiche dei dati generati

- I dati sono interamente sintetici (nessuna informazione reale o
  personale) e vengono generati con un seed fisso: rieseguendo lo script
  1 si ottengono sempre gli stessi dati.
- Il periodo storico coperto è di 9 mesi (dicembre 2025 – agosto 2026).
- Le sette categorie di servizio (Idraulica, Elettricista, Imbianchino,
  Falegnameria, Climatizzazione, Giardinaggio e Irrigazione, Caldaie)
  seguono una stagionalità simulata: ad esempio le Caldaie sono più
  richieste in inverno, la Climatizzazione e il Giardinaggio/Irrigazione
  in estate.

## 6. Scelte che vanno oltre il minimo richiesto dalla traccia

Le seguenti scelte ampliano quanto richiesto dalla traccia, senza
esservi in contrasto:

- le richieste possono avere anche lo stato "in corso" (oltre a
  completata, annullata e in ritardo, esplicitamente richiesti dalla
  traccia), per rappresentare richieste ancora in lavorazione;
- i campi nome e cognome per clienti e operatori (la traccia richiede
  solo identificativo, zona e simili, senza il nome);
- la stagionalità nella scelta della categoria di servizio;
- la distinzione tra incassi "realizzati" e "previsti", più precisa
  della sola dicitura "incassi totali" presente nella traccia.

## 7. Problemi comuni in fase di installazione ed esecuzione

Durante l'installazione o il primo avvio possono comparire alcuni
messaggi che sembrano errori ma non lo sono:

**Durante `pip install -r requirements.txt` compaiono avvisi tipo
"WARNING: The script ... is installed in ... which is not on PATH"**
Non è un errore, è solo un avviso: `pip` segnala che alcuni comandi
(come `streamlit`) non sono richiamabili digitando direttamente il loro
nome da terminale. Se l'installazione si conclude con "Successfully
installed ...", è andata a buon fine ed è possibile procedere.

**Il comando `streamlit run scripts/04_dashboard.py` non viene
riconosciuto dal terminale**
È una conseguenza dell'avviso sopra. In questo caso è sufficiente
eseguire lo stesso comando passando da Python direttamente:
```bash
python -m streamlit run scripts/04_dashboard.py
```
(su alcuni sistemi il comando è `python3` invece di `python`).
