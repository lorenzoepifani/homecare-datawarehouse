
-- Schema del data warehouse a stella per HomeCare.

-- Al centro c'è Fatti_Richieste, collegata a 4 dimensioni: Dim_Cliente, Dim_Fornitore, Dim_Operatore, Dim_Tempo.
-- Tutto lo schema viene ricreato da zero ogni volta che gira 02_etl.py (da qui i DROP TABLE sotto).


DROP TABLE IF EXISTS Fatti_Richieste;
DROP TABLE IF EXISTS Dim_Cliente;
DROP TABLE IF EXISTS Dim_Fornitore;
DROP TABLE IF EXISTS Dim_Operatore;
DROP TABLE IF EXISTS Dim_Tempo;


-- DIMENSIONE CLIENTE

CREATE TABLE Dim_Cliente (
    cliente_id      INTEGER PRIMARY KEY,
    nome            TEXT NOT NULL,
    cognome         TEXT NOT NULL,
    zona            TEXT NOT NULL,
    data_iscrizione DATE NOT NULL
);


-- DIMENSIONE FORNITORE

CREATE TABLE Dim_Fornitore (
    fornitore_id        INTEGER PRIMARY KEY,
    nome                TEXT NOT NULL,
    categoria_servizio  TEXT NOT NULL,
    zona                TEXT NOT NULL
);


-- DIMENSIONE OPERATORE

CREATE TABLE Dim_Operatore (
    operatore_id    INTEGER PRIMARY KEY,
    nome            TEXT NOT NULL,
    cognome         TEXT NOT NULL,
    zona            TEXT NOT NULL,
    tipo_attivita   TEXT NOT NULL
);


-- DIMENSIONE TEMPO
-- Una riga per ogni data presente tra le richieste, con attributi utili per filtrare/aggregare (giorno settimana, mese, trimestre, weekend).

CREATE TABLE Dim_Tempo (
    data_id         INTEGER PRIMARY KEY,  -- formato YYYYMMDD
    data_completa   DATE NOT NULL,
    anno            INTEGER NOT NULL,
    mese            INTEGER NOT NULL,
    nome_mese       TEXT NOT NULL,
    trimestre       INTEGER NOT NULL,
    giorno_settimana TEXT NOT NULL,
    is_weekend      INTEGER NOT NULL      -- 0 = feriale, 1 = weekend
);


-- TABELLA DEI FATTI: Fatti_Richieste
-- Una riga = una richiesta di servizio. Le foreign key puntano alle 4 dimensioni;
-- le misure numeriche sono importo e tempo_erogazione_min.

CREATE TABLE Fatti_Richieste (
    richiesta_id        INTEGER PRIMARY KEY,
    cliente_id          INTEGER NOT NULL,
    fornitore_id          INTEGER NOT NULL,
    operatore_id          INTEGER NOT NULL,
    data_id               INTEGER NOT NULL,
    ora                  TEXT NOT NULL,       -- HH:MM, per analisi su fasce orarie
    categoria_servizio   TEXT NOT NULL,       -- ridondanza controllata: utile per query rapide senza JOIN
    zona                 TEXT NOT NULL,       -- idem, ridondanza controllata
    importo              REAL NOT NULL,
    tempo_erogazione_min INTEGER,             -- NULL se annullata/in_corso
    stato                TEXT NOT NULL,

    FOREIGN KEY (cliente_id)   REFERENCES Dim_Cliente(cliente_id),
    FOREIGN KEY (fornitore_id) REFERENCES Dim_Fornitore(fornitore_id),
    FOREIGN KEY (operatore_id) REFERENCES Dim_Operatore(operatore_id),
    FOREIGN KEY (data_id)      REFERENCES Dim_Tempo(data_id)
);


-- Indici sulle foreign key e sui campi che uso spesso nei filtri (zona, categoria, stato)
-- per non far diventare lente le query man mano che crescono i dati

CREATE INDEX idx_fatti_cliente   ON Fatti_Richieste(cliente_id);
CREATE INDEX idx_fatti_fornitore ON Fatti_Richieste(fornitore_id);
CREATE INDEX idx_fatti_operatore ON Fatti_Richieste(operatore_id);
CREATE INDEX idx_fatti_data      ON Fatti_Richieste(data_id);
CREATE INDEX idx_fatti_zona      ON Fatti_Richieste(zona);
CREATE INDEX idx_fatti_categoria ON Fatti_Richieste(categoria_servizio);
CREATE INDEX idx_fatti_stato     ON Fatti_Richieste(stato);
