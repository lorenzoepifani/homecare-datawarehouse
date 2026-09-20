"""
Dashboard Streamlit per il data warehouse HomeCare.

Si avvia con: streamlit run scripts/04_dashboard.py

Cosa contiene:
- 4 KPI in alto: numero richieste, tempo medio di erogazione, clienti
  attivi, percentuale di clienti ricorrenti
- un blocco con distribuzione delle richieste (si può switchare tra
  vista per stato, per categoria o per zona) + incassi realizzati/previsti
- andamento nel tempo (totale o per categoria, con selettore)
- top 5 fornitori per incassi e incassi per città
- filtri in sidebar: periodo, città, categoria di servizio

"""

import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = "db/homecare.db"


# PALETTE COLORI

BLU_SCURO = "#0B3D5C"
BLU = "#1F7A8C"
VERDE_SCURO = "#2E8B57"
VERDE = "#3CB371"
VERDE_CHIARO = "#66CDAA"
BLU_CHIARO = "#4FA8D8"

PALETTE_CATEGORIE = [BLU_SCURO, BLU, VERDE_SCURO, VERDE, VERDE_CHIARO,
                     BLU_CHIARO, "#0A9396"]

# Colori per stato richiesta (verde = ok, giallo = attenzione, rosso = problema)
COLORI_STATO = {
    "completata": VERDE_SCURO,
    "in_ritardo": "#E8A33D",
    "in_corso": BLU_CHIARO,
    "annullata": "#C0392B",
}


# CARICAMENTO DATI (uso la cache di streamlit, altrimenti rilegge il DB ogni volta che cambio un filtro)

@st.cache_data
def carica_dati() -> pd.DataFrame:
    """Faccio un unico JOIN tra fatti e dimensioni e tengo tutto in un
    DataFrame pandas: mi semplifica la vita dopo con i filtri e i grafici,
    invece di fare tante query SQL separate ogni volta."""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            f.richiesta_id,
            f.importo,
            f.tempo_erogazione_min,
            f.stato,
            f.zona,
            f.categoria_servizio,
            f.cliente_id,
            fo.nome AS fornitore_nome,
            t.data_completa,
            t.mese,
            t.nome_mese,
            t.anno
        FROM Fatti_Richieste f
        JOIN Dim_Fornitore fo ON f.fornitore_id = fo.fornitore_id
        JOIN Dim_Tempo t ON f.data_id = t.data_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["data_completa"] = pd.to_datetime(df["data_completa"])
    return df


# CONFIGURAZIONE PAGINA E STILE

st.set_page_config(
    page_title="HomeCare - Dashboard Analytics",
    page_icon="🛠️",
    layout="wide",
)

st.markdown(f"""
<style>
    .stApp {{
        background-color: #F4FAF8;
    }}
    [data-testid="stMetric"] {{
        background: linear-gradient(135deg, {BLU_SCURO} 0%, {VERDE_SCURO} 100%);
        padding: 18px 16px;
        border-radius: 12px;
        color: white;
        height: 120px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: center;
        overflow: hidden;
    }}
    [data-testid="stMetricLabel"] {{
        color: #E8F5F0 !important;
    }}
    [data-testid="stMetricValue"] {{
        color: white !important;
    }}
    [data-testid="stMetricDelta"] {{
        color: #C9F2E0 !important;
    }}
    .header-banner {{
        background: linear-gradient(90deg, {BLU_SCURO} 0%, {VERDE_SCURO} 100%);
        padding: 24px 28px;
        border-radius: 12px;
        margin-bottom: 24px;
    }}
    .header-banner h1 {{
        color: white;
        margin: 0;
    }}
    .header-banner p {{
        color: #E8F5F0;
        margin: 6px 0 0 0;
        font-size: 16px;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {BLU_SCURO};
    }}
    /* Testo di label/titoli nella sidebar: bianco */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p {{
        color: white !important;
    }}
    /* Campo del selettore periodo (date input): sfondo chiaro, testo
       scuro, così resta leggibile sopra la sidebar blu scura */
    section[data-testid="stSidebar"] [data-testid="stDateInput"] input {{
        color: #1A1A1A !important;
        background-color: white !important;
    }}
    /* Casella di ricerca dentro le multiselect: stesso trattamento */
    section[data-testid="stSidebar"] [data-baseweb="select"] input {{
        color: #1A1A1A !important;
    }}
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background-color: white !important;
    }}
    /* Tag delle opzioni selezionate nelle multiselect: verde invece
       dell'arancione di default, coerente con la palette del brand */
    section[data-testid="stSidebar"] span[data-baseweb="tag"] {{
        background-color: {VERDE_SCURO} !important;
    }}
    section[data-testid="stSidebar"] span[data-baseweb="tag"] * {{
        color: white !important;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-banner">
    <h1>HomeCare — Dashboard Analytics</h1>
    <p>Servizi di manutenzione per la casa</p>
</div>
""", unsafe_allow_html=True)

df = carica_dati()

# FILTRI INTERATTIVI (sidebar): periodo, zona, categoria di servizio

st.sidebar.header("🔎 Filtri")

data_min = df["data_completa"].min().date()
data_max = df["data_completa"].max().date()

periodo = st.sidebar.date_input(
    "📅 Periodo",
    value=(data_min, data_max),
    min_value=data_min,
    max_value=data_max,
)

zone_disponibili = sorted(df["zona"].unique())
zone_selezionate = st.sidebar.multiselect(
    "📍 Città", options=zone_disponibili, default=zone_disponibili
)

categorie_disponibili = sorted(df["categoria_servizio"].unique())
categorie_selezionate = st.sidebar.multiselect(
    "🔧 Categoria di servizio", options=categorie_disponibili,
    default=categorie_disponibili
)

# Applicazione dei filtri al DataFrame
if len(periodo) == 2:
    data_inizio_f, data_fine_f = periodo
else:
    data_inizio_f, data_fine_f = data_min, data_max

df_filtrato = df[
    (df["data_completa"].dt.date >= data_inizio_f)
    & (df["data_completa"].dt.date <= data_fine_f)
    & (df["zona"].isin(zone_selezionate))
    & (df["categoria_servizio"].isin(categorie_selezionate))
]

if df_filtrato.empty:
    st.warning("Nessun dato disponibile per i filtri selezionati.")
    st.stop()

# I 4 KPI principali. 
# Per dare un'idea di trend, confronto la prima metà del periodo selezionato con la seconda metà 
# (non è statisticamente rigoroso ma dà un'idea al colpo d'occhio se le cose stanno migliorando)

numero_richieste = len(df_filtrato)
tempo_medio = df_filtrato["tempo_erogazione_min"].dropna().mean()

# "attivo"/"ricorrente" li calcolo solo sulle richieste che hanno comportato un servizio vero (escludo le annullate: un cliente che
# prova a prenotare e poi annulla non ha davvero usato il servizio, quindi non lo conto come attivo - stessa logica già usata per gli
# incassi realizzati/previsti)

df_servizio_reale = df_filtrato[df_filtrato["stato"] != "annullata"]
richieste_per_cliente = df_servizio_reale.groupby("cliente_id").size()
clienti_attivi = len(richieste_per_cliente)
clienti_ricorrenti = (richieste_per_cliente > 1).sum()
pct_ricorrenti = (100 * clienti_ricorrenti / clienti_attivi
                   if clienti_attivi > 0 else 0)


punto_medio = data_inizio_f + (data_fine_f - data_inizio_f) / 2
prima_meta = df_filtrato[df_filtrato["data_completa"].dt.date <= punto_medio]
seconda_meta = df_filtrato[df_filtrato["data_completa"].dt.date > punto_medio]

def variazione_pct(nuovo: float, vecchio: float) -> str | None:
    if vecchio in (0, None) or pd.isna(vecchio):
        return None
    delta = 100 * (nuovo - vecchio) / vecchio
    return f"{delta:+.0f}%"

delta_richieste = variazione_pct(len(seconda_meta), len(prima_meta))

col1, col2, col3, col4 = st.columns(4)
col1.metric("📋 Numero richieste", f"{numero_richieste:,}", delta_richieste)
col2.metric(
    "⏱️ Tempo medio erogazione",
    f"{tempo_medio:.0f} min" if pd.notna(tempo_medio) else "N/D",
)
col3.metric("👤 Clienti attivi", f"{clienti_attivi:,}",
            help="Clienti che hanno effettuato almeno una richiesta "
                 "non annullata nel periodo selezionato")
col4.metric("👥 Clienti ricorrenti", f"{pct_ricorrenti:.0f}%",
            help=f"{clienti_ricorrenti} clienti su {clienti_attivi} attivi "
                 f"hanno fatto più di una richiesta")

st.divider()

# Qui si può scegliere se vedere la distribuzione delle richieste per stato, categoria o zona;
# un solo grafico alla volta invece di tre messi in fila, così la pagina resta più pulita e leggibile


vista_distribuzione = st.radio(
    "Distribuzione richieste",
    options=["Per stato", "Per categoria", "Per zona"],
    horizontal=True,
    label_visibility="visible",
)

if vista_distribuzione == "Per stato":
    st.subheader("📊 Distribuzione richieste per stato")
    ordine_stati = ["completata", "in_ritardo", "in_corso", "annullata"]
    etichette_stati = {
        "completata": "Completata", "in_ritardo": "In ritardo",
        "in_corso": "In corso", "annullata": "Annullata",
    }
    per_stato = (
        df_filtrato["stato"].value_counts()
        .reindex(ordine_stati, fill_value=0)
        .reset_index()
    )
    per_stato.columns = ["stato", "numero_richieste"]
    per_stato["stato_label"] = per_stato["stato"].map(etichette_stati)

    fig_stato = px.bar(
        per_stato, x="stato_label", y="numero_richieste",
        labels={"stato_label": "Stato", "numero_richieste": "Richieste"},
        color="stato", color_discrete_map=COLORI_STATO,
    )
    fig_stato.update_layout(
        showlegend=False, plot_bgcolor="white", paper_bgcolor="white"
    )
    st.plotly_chart(fig_stato, use_container_width=True)

elif vista_distribuzione == "Per categoria":
    st.subheader("🔧 Distribuzione richieste per categoria di servizio")
    per_categoria = (
        df_filtrato["categoria_servizio"].value_counts().reset_index()
    )
    per_categoria.columns = ["categoria", "numero_richieste"]
    fig_categoria = px.bar(
        per_categoria, x="categoria", y="numero_richieste",
        labels={"categoria": "Categoria", "numero_richieste": "Richieste"},
        color="categoria", color_discrete_sequence=PALETTE_CATEGORIE,
    )
    fig_categoria.update_layout(
        showlegend=False, plot_bgcolor="white", paper_bgcolor="white"
    )
    st.plotly_chart(fig_categoria, use_container_width=True)

else:  # Per zona
    st.subheader("📍 Distribuzione richieste per zona")
    per_zona_count = df_filtrato["zona"].value_counts().reset_index()
    per_zona_count.columns = ["zona", "numero_richieste"]
    fig_zona_count = px.bar(
        per_zona_count, x="zona", y="numero_richieste",
        labels={"zona": "Città", "numero_richieste": "Richieste"},
        color="zona", color_discrete_sequence=PALETTE_CATEGORIE,
    )
    fig_zona_count.update_layout(
        showlegend=False, plot_bgcolor="white", paper_bgcolor="white"
    )
    st.plotly_chart(fig_zona_count, use_container_width=True)

# stessa distinzione fatta in 03_query_kpi.py: realizzati = solo completata/in_ritardo, previsti = tutto
# (le annullate contano 0 quindi non cambiano il risultato)

incassi_realizzati = df_filtrato.loc[
    df_filtrato["stato"].isin(["completata", "in_ritardo"]), "importo"
].sum()
incassi_previsti = df_filtrato["importo"].sum()

col_r, col_p = st.columns(2)
col_r.metric("💶 Incassi realizzati", f"€ {incassi_realizzati:,.2f}",
             help="Somma degli importi delle richieste completate o "
                  "in ritardo (servizio comunque erogato)")
col_p.metric("💰 Incassi previsti", f"€ {incassi_previsti:,.2f}",
             help="Somma degli importi di tutte le richieste nel periodo "
                  "selezionato (incluse in corso; le annullate valgono 0)")

st.divider()

# GRAFICI


# anche qui uso un selettore invece di mettere due grafici uno sotto l'altro per pulizia e leggibilità

vista_andamento = st.radio(
    "Andamento richieste nel tempo",
    options=["Totale", "Per categoria"],
    horizontal=True,
    label_visibility="visible",
)

if vista_andamento == "Totale":
    andamento = (
        df_filtrato.groupby(df_filtrato["data_completa"].dt.to_period("M"))
        .size()
        .reset_index(name="numero_richieste")
    )
    andamento["data_completa"] = andamento["data_completa"].astype(str)
    fig_andamento = px.area(
        andamento, x="data_completa", y="numero_richieste", markers=True,
        labels={"data_completa": "Mese", "numero_richieste": "Richieste"},
    )
    fig_andamento.update_traces(line_color=BLU_SCURO,
                                 fillcolor="rgba(46,139,87,0.25)")
    fig_andamento.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig_andamento, use_container_width=True)
else:
    andamento_categoria = (
        df_filtrato.groupby(
            [df_filtrato["data_completa"].dt.to_period("M"),
             "categoria_servizio"]
        )
        .size()
        .reset_index(name="numero_richieste")
    )
    andamento_categoria["data_completa"] = (
        andamento_categoria["data_completa"].astype(str)
    )
    fig_andamento_categoria = px.line(
        andamento_categoria, x="data_completa", y="numero_richieste",
        color="categoria_servizio", markers=True,
        labels={"data_completa": "Mese", "numero_richieste": "Richieste",
                "categoria_servizio": "Categoria"},
        color_discrete_sequence=PALETTE_CATEGORIE,
    )
    fig_andamento_categoria.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
    )
    st.plotly_chart(fig_andamento_categoria, use_container_width=True)

col_sx, col_dx = st.columns(2)

# 2) Top 5 fornitori per incassi - uso solo gli incassi realizzati
df_incassate = df_filtrato[df_filtrato["stato"].isin(["completata", "in_ritardo"])]

with col_sx:
    st.subheader("🏆 Top 5 fornitori per incassi")
    top_fornitori = (
        df_incassate.groupby("fornitore_nome")["importo"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )
    fig_top_fornitori = px.bar(
        top_fornitori, x="importo", y="fornitore_nome", orientation="h",
        labels={"importo": "Incassi (€)", "fornitore_nome": "Fornitore"},
        color="importo", color_continuous_scale=[VERDE_CHIARO, BLU_SCURO],
    )
    fig_top_fornitori.update_layout(
        yaxis={"categoryorder": "total ascending"},
        plot_bgcolor="white", paper_bgcolor="white",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_top_fornitori, use_container_width=True)

# 3) Incassi per città - stesso discorso di sopra, solo realizzati.
#    Mostro sia l'importo in euro sia la percentuale sul totale
with col_dx:
    st.subheader("📍 Incassi per città")
    incassi_zona = (
        df_incassate.groupby("zona")["importo"]
        .sum()
        .reset_index()
        .sort_values("importo", ascending=False)
    )
    fig_zona = px.pie(
        incassi_zona, names="zona", values="importo", hole=0.45,
        color_discrete_sequence=PALETTE_CATEGORIE,
    )
    fig_zona.update_traces(
        texttemplate="%{label}<br>€ %{value:,.0f} (%{percent})"
    )
    fig_zona.update_layout(paper_bgcolor="white")
    st.plotly_chart(fig_zona, use_container_width=True)


st.divider()
st.caption(
    f"Dati aggiornati al {data_max.strftime('%d/%m/%Y')} — "
    f"Dashboard sviluppata per il project work HomeCare"
)
