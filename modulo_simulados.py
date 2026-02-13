import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import math

ORDEM_AREAS = ["Linguagens", "Humanas", "Natureza", "Matemática"]
TOTAL_QUESTOES_COMPLETO = 180
NUM_AREAS = 4

_CORES_AREAS = {
    "Linguagens": "#4d0000",
    "Humanas":    "#800000",
    "Natureza":   "#b30000",
    "Matemática": "#ff3333",
}

_CSS_MODULO = """
<style>
.simu-card {
    background-color: #1e1e1e;
    padding: 15px;
    border-radius: 10px;
    min-height: 130px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    transition: all 0.3s ease-in-out;
    border: none;
}
.simu-card:hover {
    transform: translateY(-5px);
    background-color: #252525;
    box-shadow: 0px 8px 25px rgba(192, 0, 0, 0.3);
}
</style>
"""


# --- Helpers ---

def _filtrar_simulados_completos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna (simulados_validos, df_completos) — apenas provas com 4 áreas e 180 questões."""
    check = (
        df.groupby(["id_aluno", "tipo", "numero", "ano"])
        .agg({"area": "nunique", "total": "sum", "acertos": "sum"})
        .reset_index()
    )
    simulados_validos = check[
        (check["area"] == NUM_AREAS) & (check["total"] == TOTAL_QUESTOES_COMPLETO)
    ]
    chaves = ["id_aluno", "tipo", "numero", "ano"]
    df_completos = df.merge(simulados_validos[chaves], on=chaves)
    return simulados_validos, df_completos


def _posicao_ranking(idx: int) -> str:
    emojis = {0: "🥇", 1: "🥈", 2: "🥉"}
    return emojis.get(idx, f"{idx + 1}º")


# --- Aba: Desempenho & Consistência ---

def _render_cards_records(simulados_validos: pd.DataFrame, df_completos: pd.DataFrame) -> None:
    if df_completos.empty:
        st.info("💡 Realize um simulado completo para habilitar as métricas.")
        return

    medias_por_area = df_completos.groupby("area")["acertos"].mean()
    melhor_area_nome = medias_por_area.idxmax()
    melhor_area_val  = math.ceil(medias_por_area.max())
    pior_area_nome   = medias_por_area.idxmin()
    pior_area_val    = math.ceil(medias_por_area.min())
    melhor_nota_total = simulados_validos["acertos"].max()
    qtd_completos     = len(simulados_validos)

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, "#28a745", "🏆 Melhor Área",  melhor_area_nome, f"{int(melhor_area_val)}", "acertos"),
        (c2, "#c00000", "⚠️ Ponto de Melhoria",    pior_area_nome,   f"{int(pior_area_val)}",  "acertos"),
        (c3, "#c00000", "🎯 Recorde Individual",       "Simulado Geral", f"{int(melhor_nota_total)}", "/180"),
        (c4, "#c00000", "📝 Simulados Concluídos",  "Concluídos",     f"{qtd_completos}",           "simulados"),
    ]
    for col, cor, label, titulo, valor, sufixo in cards:
        with col:
            st.markdown(
                f'<div class="simu-card" style="border-left:4px solid {cor};">'
                f'<p style="color:#888;margin:0;font-size:0.85em;">{label}</p>'
                f'<h3 style="margin:5px 0;font-size:1.15em;">{titulo}</h3>'
                f'<p style="color:{cor};font-weight:bold;margin:0;font-size:1.4em;">'
                f'{valor} <span style="font-size:0.6em;color:#888;">{sufixo}</span></p></div>',
                unsafe_allow_html=True,
            )


def _render_diagnostico_geral(df_base: pd.DataFrame) -> None:
    col_esq, col_dir = st.columns([1, 1.2])

    df_radar = df_base.groupby("area")["rendimento_perc"].mean().reset_index()
    categorias = df_radar["area"].tolist() + [df_radar["area"].tolist()[0]]
    valores    = df_radar["rendimento_perc"].tolist() + [df_radar["rendimento_perc"].tolist()[0]]

    with col_esq:
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=valores, theta=categorias, fill="toself",
            line=dict(color="#c00000"),
            hovertemplate="<b>%{theta}</b><br>Média: %{r:.1f}%<extra></extra>",
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            template="plotly_dark", margin=dict(t=40, b=40),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_dir:
        df_vol = (
            df_base.groupby("area")["total"].sum()
            .reindex(ORDEM_AREAS).fillna(0).reset_index()
        )
        fig_vol = px.bar(
            df_vol, y="area", x="total", orientation="h",
            color="area", color_discrete_map=_CORES_AREAS, text_auto=True,
        )
        fig_vol.update_traces(hovertemplate="<b>%{y}</b><br>Questões: %{x}<extra></extra>")
        fig_vol.update_layout(
            template="plotly_dark", showlegend=False,
            yaxis={"categoryorder": "array", "categoryarray": ORDEM_AREAS[::-1]},
            margin=dict(t=40),
        )
        st.plotly_chart(fig_vol, use_container_width=True)


def _render_diagnostico_area(df_base: pd.DataFrame, area_sel: str) -> None:
    col_esq, col_dir = st.columns([1, 1.2])

    df_area = df_base[df_base["area"] == area_sel].copy()
    df_plot = (
        df_area.groupby(df_area["data"].dt.date)["rendimento_perc"]
        .mean().reset_index().sort_values("data")
    )

    with col_esq:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=df_plot["rendimento_perc"].mean(),
            number={"suffix": "%"},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#c00000"}},
        ))
        fig_gauge.update_layout(template="plotly_dark", height=380)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_dir:
        fig_line = px.line(df_plot, x="data", y="rendimento_perc", markers=True)
        fig_line.update_traces(
            line=dict(color="#c00000", width=2),
            hovertemplate="<b>Data: %{x}</b><br>Média: %{y:.1f}%<extra></extra>",
        )
        if len(df_plot) > 1:
            x_ord = pd.to_datetime(df_plot["data"]).apply(lambda x: x.toordinal())
            slope, intercept = np.polyfit(x_ord, df_plot["rendimento_perc"], 1)
            fig_line.add_trace(go.Scatter(
                x=df_plot["data"], y=slope * x_ord + intercept,
                mode="lines", line=dict(color="white", width=1.5, dash="dash"),
                hoverinfo="skip",
            ))
        fig_line.update_layout(
            template="plotly_dark", height=380, yaxis_range=[0, 105], showlegend=False,
        )
        st.plotly_chart(fig_line, use_container_width=True)


def _render_historico_simulados(
    df_base: pd.DataFrame, df_alunos: pd.DataFrame, nome_sel: str
) -> None:
    with st.expander("📄 Histórico Completo de Simulados"):
        df_hist = df_base.copy()
        df_hist["Data_Str"] = df_hist["data"].dt.strftime("%d/%m/%Y")
        df_hist["%"] = (df_hist["acertos"] / df_hist["total"] * 100).map("{:.2f}%".format)
        colunas = ["Data_Str", "tipo", "numero", "ano", "area", "acertos", "total", "%"]

        if nome_sel == "Todos":
            df_hist = df_hist.merge(df_alunos[["id_aluno", "nome"]], on="id_aluno")
            colunas = ["nome"] + colunas

        st.dataframe(
            df_hist[colunas].sort_values("Data_Str", ascending=False).rename(columns={"Data_Str": "Data"}),
            use_container_width=True, hide_index=True,
        )


# --- Aba: Ranking & Posicionamento ---

def _render_ranking_geral(df_simulados: pd.DataFrame, df_alunos: pd.DataFrame) -> None:
    st.subheader("🏆 Ranking Geral - Simulados Completos")
    c1, c2, c3 = st.columns(3)
    with c1:
        r_tipo = st.selectbox("Tipo", sorted(df_simulados["tipo"].unique()), key="r_t")
    with c2:
        r_num = st.selectbox(
            "Número",
            sorted(df_simulados[df_simulados["tipo"] == r_tipo]["numero"].unique()),
            key="r_n",
        )
    with c3:
        r_ano = st.selectbox(
            "Ano",
            sorted(
                df_simulados[
                    (df_simulados["tipo"] == r_tipo) & (df_simulados["numero"] == r_num)
                ]["ano"].unique()
            ),
            key="r_a",
        )

    df_f = df_simulados[
        (df_simulados["tipo"] == r_tipo)
        & (df_simulados["numero"] == r_num)
        & (df_simulados["ano"] == r_ano)
    ]
    if df_f.empty:
        return

    rp = df_f.pivot_table(index="id_aluno", columns="area", values="acertos", aggfunc="sum").reset_index()
    ct = df_f.groupby("id_aluno")["total"].sum().reset_index()
    rf = rp.merge(ct, on="id_aluno")
    rf = rf[rf["total"] == TOTAL_QUESTOES_COMPLETO].copy()

    if rf.empty:
        st.info("Sem registros de 180 questões para este filtro.")
        return

    areas_presentes = [a for a in ORDEM_AREAS if a in rf.columns]
    rf["Total Acertos"] = rf[areas_presentes].sum(axis=1)
    rf = (
        rf.merge(df_alunos[["id_aluno", "nome"]], on="id_aluno")
        .sort_values("Total Acertos", ascending=False)
        .reset_index(drop=True)
    )
    rf["Posição"] = [_posicao_ranking(i) for i in range(len(rf))]

    st.dataframe(
        rf[["Posição", "nome"] + areas_presentes + ["Total Acertos"]].rename(columns={"nome": "Aluno"}),
        use_container_width=True, hide_index=True,
    )


def _render_ranking_individual(
    simulados_validos: pd.DataFrame,
    df_simulados: pd.DataFrame,
    id_aluno_focado: int,
    nome_sel: str,
) -> None:
    st.subheader(f"Histórico de Posicionamento: {nome_sel}")

    if simulados_validos.empty:
        st.info("💡 Realize um simulado completo (180 questões) para habilitar o ranking.")
        return

    resumo = []
    for _, row in simulados_validos.iterrows():
        comp = df_simulados[
            (df_simulados["tipo"] == row["tipo"])
            & (df_simulados["numero"] == row["numero"])
            & (df_simulados["ano"] == row["ano"])
        ]
        comp_pivot = comp.pivot_table(index="id_aluno", columns="area", values="acertos", aggfunc="sum").reset_index()
        comp_total = (
            comp.groupby("id_aluno")["acertos"].sum().reset_index()
            .rename(columns={"acertos": "Total Acertos"})
        )
        comp_qtd = comp.groupby("id_aluno")["total"].sum().reset_index()

        rank = (
            comp_pivot
            .merge(comp_total, on="id_aluno")
            .merge(comp_qtd, on="id_aluno")
        )
        rank = (
            rank[rank["total"] == TOTAL_QUESTOES_COMPLETO]
            .sort_values("Total Acertos", ascending=False)
            .reset_index(drop=True)
        )

        try:
            idx = rank[rank["id_aluno"] == id_aluno_focado].index[0]
            linha = {
                "Simulado": f"{row['tipo']} {row['numero']} ({row['ano']})",
                "Posição":  f"{_posicao_ranking(idx)} de {len(rank)}",
            }
            for area in ORDEM_AREAS:
                linha[area] = int(rank.loc[idx, area]) if area in rank.columns else 0
            linha["Total"] = int(rank.loc[idx, "Total Acertos"])
            resumo.append(linha)
        except (IndexError, KeyError):
            continue

    if resumo:
        df_resumo = pd.DataFrame(resumo)
        st.dataframe(
            df_resumo[["Simulado", "Posição"] + ORDEM_AREAS + ["Total"]],
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("💡 Realize um simulado completo (180 questões) para habilitar o ranking.")


# --- Ponto de entrada ---

def exibir_modulo_simulados(df_alunos: pd.DataFrame, df_simulados: pd.DataFrame) -> None:
    st.markdown(_CSS_MODULO, unsafe_allow_html=True)
    st.title("📚 Central de Simulados")
    st.subheader("*Simulados revelam padrões, estratégia corrige trajetórias*")

    # Filtros laterais
    lista_alunos = ["Todos"] + sorted(df_alunos["nome"].unique().tolist())
    nome_sel = st.sidebar.selectbox("Mentorado", lista_alunos, key="simu_aluno")

    areas_disponiveis = ["Todas"] + sorted(df_simulados["area"].unique().tolist())
    area_sel = st.sidebar.selectbox("Área", areas_disponiveis)

    if nome_sel == "Todos":
        df_base = df_simulados.copy()
        id_aluno_focado = None
    else:
        id_aluno_focado = df_alunos[df_alunos["nome"] == nome_sel]["id_aluno"].values[0]
        df_base = df_simulados[df_simulados["id_aluno"] == id_aluno_focado].copy()

    simulados_validos, df_completos = _filtrar_simulados_completos(df_base)
    df_base["rendimento_perc"] = df_base["acertos"] / df_base["total"] * 100

    tab_perf, tab_rank = st.tabs(["📈 Desempenho & Consistência", "🏆 Ranking & Posicionamento"])

    with tab_perf:
        st.markdown("### 📊 Análise de Performance")
        _render_cards_records(simulados_validos, df_completos)

        st.markdown("---")
        titulo_diag = area_sel if area_sel != "Todas" else "Visão Global"
        st.subheader(f"🎯 Leitura Analítica: {titulo_diag}")

        if area_sel == "Todas":
            _render_diagnostico_geral(df_base)
        else:
            _render_diagnostico_area(df_base, area_sel)

        st.markdown("---")
        _render_historico_simulados(df_base, df_alunos, nome_sel)

    with tab_rank:
        if nome_sel == "Todos":
            _render_ranking_geral(df_simulados, df_alunos)
        else:
            _render_ranking_individual(simulados_validos, df_simulados, id_aluno_focado, nome_sel)

    st.markdown("---")
    _, col_centro, _ = st.columns([2, 1, 2])
    with col_centro:
        st.image("logo.png", width=250)
