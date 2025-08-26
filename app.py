import io
import re
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dash Circos", page_icon="🎪", layout="wide")

st.title("🎪 Dashboards de Eventos • Estilo Power BI")

with st.sidebar:
    st.markdown("## 📁 Upload do arquivo")
    up = st.file_uploader("Envie seu Excel (.xlsx) ou CSV", type=["xlsx", "csv"])
    st.caption("O app detecta automaticamente as colunas padrão do relatório.")

@st.cache_data(show_spinner=False)
def load_df(file):
    if file is None:
        return None
    name = file.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(file, sep=None, engine="python")
    else:
        # tenta primeira planilha por padrão
        try:
            df = pd.read_excel(file, sheet_name=0, engine="openpyxl")
        except Exception:
            # fallback
            df = pd.read_excel(file, engine="openpyxl")
    # normaliza nomes
    df.columns = [str(c).strip() for c in df.columns]
    return df

def try_parse_dates(df):
    # tenta encontrar a coluna de data do evento
    date_col_candidates = [c for c in df.columns if c.lower() in ["data evento", "data", "data do evento"]]
    if not date_col_candidates:
        # tentativa heurística: qualquer coluna com "data"
        date_col_candidates = [c for c in df.columns if "data" in c.lower()]
    date_col = date_col_candidates[0] if date_col_candidates else None
    if date_col:
        # converte com dia primeiro (pt-br)
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
    return df, date_col

def derive_circo(df):
    # Gera coluna "Circo" a partir de "Evento" (texto antes do pipe " | ")
    circo_col = None
    evento_col_candidates = [c for c in df.columns if c.lower() in ["evento", "nome do evento", "titulo"]]
    if evento_col_candidates:
        ev = evento_col_candidates[0]
        def extract_circo(x):
            if pd.isna(x):
                return np.nan
            s = str(x)
            if "|" in s:
                return s.split("|")[0].strip()
            # tenta achar "Circo ..." no começo
            m = re.search(r"(Circo[^|\\-]*)", s, flags=re.IGNORECASE)
            return m.group(1).strip() if m else s[:60].strip()
        df["Circo"] = df[ev].apply(extract_circo)
        circo_col = "Circo"
    return df, circo_col

def ensure_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

df = load_df(up)
if df is None:
    st.info("Envie o arquivo para começar.")
    st.stop()

orig_cols = df.columns.tolist()

# Parse data e circo
df, date_col = try_parse_dates(df)
df, circo_col = derive_circo(df)

# Colunas financeiras que o relatório costuma ter
money_cols = [
    "Faturamento Total",
    "Faturamento Gestão Produtor",
    "Faturamento Gestão Empresa",
    "Faturamento Pdv",
    "Faturamento Web",
    "Total Repasses",
    "Total Descontos",
    "Taxa Antecipação",
    "Taxa Transferencia",
    "I:Comissão Bilheteria e PDVS",
    "I:Insumo - Ingresso Cancelado",
    "I:Insumo - Ingresso Cortesia",
    "I:Taxas Cartões - Debito",
    "I:Taxas Cartões - Credito à Vista",
    "I:Taxa Pix",
    "I:Despesas Jurídicas",
]

df = ensure_numeric(df, money_cols)

# Filtros na sidebar
with st.sidebar:
    st.markdown("## 🔎 Filtros")
    # filtro de data
    if date_col and df[date_col].notna().any():
        min_d = pd.to_datetime(df[date_col]).min()
        max_d = pd.to_datetime(df[date_col]).max()
        start, end = st.date_input(
            "Período (Data Evento)",
            value=(min_d.date(), max_d.date()),
            min_value=min_d.date(),
            max_value=max_d.date(),
        )
    else:
        start = end = None
    # filtro de circo
    if circo_col and df[circo_col].notna().any():
        unique_circos = sorted([x for x in df[circo_col].dropna().unique().tolist()])
        selected_circos = st.multiselect("Circo", unique_circos, default=unique_circos[:10])
    else:
        selected_circos = []

# aplica filtros
mask = pd.Series([True] * len(df))
if date_col and start and end:
    mask &= (df[date_col] >= pd.to_datetime(start)) & (df[date_col] <= pd.to_datetime(end))
if circo_col and selected_circos:
    mask &= df[circo_col].isin(selected_circos)

fdf = df[mask].copy()

# KPIs
def fmt_money(x):
    if pd.isna(x):
        return "R$ 0"
    return f"R$ {x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

kpi_cols = st.columns(4)
total_fat = fdf["Faturamento Total"].sum() if "Faturamento Total" in fdf.columns else np.nan
total_pdv = fdf["Faturamento Pdv"].sum() if "Faturamento Pdv" in fdf.columns else np.nan
total_web = fdf["Faturamento Web"].sum() if "Faturamento Web" in fdf.columns else np.nan
qtd_eventos = int(fdf.shape[0])

with kpi_cols[0]:
    st.metric("Faturamento Total", fmt_money(total_fat))
with kpi_cols[1]:
    st.metric("PDV (soma)", fmt_money(total_pdv))
with kpi_cols[2]:
    st.metric("Web (soma)", fmt_money(total_web))
with kpi_cols[3]:
    st.metric("Qtd. de Eventos", f"{qtd_eventos}")

st.markdown("---")

# Gráficos
if date_col and fdf[date_col].notna().any():
    gdf = fdf.groupby(date_col, as_index=False).agg({
        c: "sum" for c in ["Faturamento Total", "Faturamento Pdv", "Faturamento Web"] if c in fdf.columns
    })
    if "Faturamento Total" in gdf.columns:
        fig1 = px.line(gdf, x=date_col, y="Faturamento Total", title="Faturamento Total por Data")
        st.plotly_chart(fig1, use_container_width=True)
    if all(c in gdf.columns for c in ["Faturamento Pdv", "Faturamento Web"]):
        fig2 = px.bar(
            gdf.melt(id_vars=[date_col], value_vars=["Faturamento Pdv", "Faturamento Web"], var_name="Canal", value_name="Faturamento"),
            x=date_col, y="Faturamento", color="Canal", barmode="stack", title="Faturamento por Canal ao Longo do Tempo"
        )
        st.plotly_chart(fig2, use_container_width=True)

# Top eventos
evento_col = [c for c in fdf.columns if c.lower() == "evento"]
evento_col = evento_col[0] if evento_col else None
if evento_col and "Faturamento Total" in fdf.columns:
    top = (
        fdf.groupby(evento_col, as_index=False)["Faturamento Total"]
        .sum()
        .sort_values("Faturamento Total", ascending=False)
        .head(15)
    )
    fig3 = px.bar(top, x="Faturamento Total", y=evento_col, orientation="h", title="Top 15 Eventos por Faturamento")
    st.plotly_chart(fig3, use_container_width=True)

# Participação PDV x Web
if all(c in fdf.columns for c in ["Faturamento Pdv", "Faturamento Web"]):
    total_pdv_web = (
        fdf[["Faturamento Pdv", "Faturamento Web"]]
        .sum()
        .rename({"Faturamento Pdv": "PDV", "Faturamento Web": "Web"})
    )
    part_df = total_pdv_web.reset_index()
    part_df.columns = ["Canal", "Faturamento"]
    fig4 = px.pie(part_df, names="Canal", values="Faturamento", title="Participação por Canal")
    st.plotly_chart(fig4, use_container_width=True)

# Tabela breve
st.subheader("📊 Dados (filtrados)")
st.dataframe(fdf, use_container_width=True)

# Insights automáticos
insights = []
if "Faturamento Total" in fdf.columns and date_col:
    # melhor dia
    by_day = fdf.groupby(date_col)["Faturamento Total"].sum().sort_values(ascending=False)
    if not by_day.empty:
        best_day = by_day.index[0]
        best_val = by_day.iloc[0]
        insights.append(f"Melhor dia de faturamento: **{best_day.date()}** com **{fmt_money(best_val)}**.")
    # ticket médio (se houver total de ingressos, mas caso não exista, usa por evento)
    avg_per_event = fdf["Faturamento Total"].mean()
    insights.append(f"Faturamento médio por evento: **{fmt_money(avg_per_event)}**.")
if all(c in fdf.columns for c in ["Faturamento Pdv", "Faturamento Web"]):
    s = fdf[["Faturamento Pdv", "Faturamento Web"]].sum()
    total = s.sum() if s.sum() else 0
    if total > 0:
        web_pct = s["Faturamento Web"] / total * 100
        insights.append(f"Participação Web: **{web_pct:.1f}%** do faturamento (restante PDV).")
if "Taxa Antecipação" in fdf.columns:
    ta = fdf["Taxa Antecipação"].replace(0, np.nan).dropna()
    if not ta.empty:
        insights.append(f"Taxa de antecipação média (onde aplicada): **{ta.mean():.2f}**.")
if "Total Descontos" in fdf.columns:
    descontos = fdf["Total Descontos"].sum()
    if descontos > 0:
        insights.append(f"Descontos totais no período filtrado: **{fmt_money(descontos)}**.")

st.subheader("💡 Insights")
if insights:
    for t in insights:
        st.markdown(f"- {t}")
else:
    st.write("Sem insights calculáveis para as colunas disponíveis.")

# Download dos dados filtrados
csv = fdf.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Baixar dados filtrados (CSV)", csv, file_name="dados_filtrados.csv", mime="text/csv")

# Rodapé
st.caption("Feito com ❤️ em Streamlit. Dica: publique no Streamlit Community Cloud (grátis).")