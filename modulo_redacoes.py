import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

MAPA_MENTORIAS = {1: "Estude com Danilo", 2: "Projeto Medicina"}

_COMPETENCIAS = ["c1", "c2", "c3", "c4", "c5"]
_LABELS_COMPETENCIAS = [
    "Gramática (C1)", "Repertório (C2)", "Argumentação (C3)", 
    "Coesão (C4)", "Proposta (C5)"
]

_CSS_MODULO = """
<style>
[data-testid="stMetric"] {
    background-color: #1e1e1e;
    padding: 15px;
    border-radius: 10px;
    border-left: 3px solid #c00000;
    transition: all 0.3s ease-in-out;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-5px);
    background-color: #252525;
    box-shadow: 0px 4px 15px rgba(192, 0, 0, 0.2);
    border-left: 3px solid #ff0000;
}
</style>
"""


# --- Sidebar ---

def _render_filtros_sidebar(df_alunos: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    st.sidebar.subheader("Configurações de Análise")
    
    mentorias = ["Todas"] + [
        MAPA_MENTORIAS.get(m, m) for m in df_alunos["id_mentoria"].unique()
    ]
    mentoria_sel = st.sidebar.selectbox("Mentoria", mentorias)
    
    if mentoria_sel != "Todas":
        id_m = [k for k, v in MAPA_MENTORIAS.items() if v == mentoria_sel][0]
        alunos_filtrados = df_alunos[df_alunos["id_mentoria"] == id_m]
    else:
        alunos_filtrados = df_alunos

    lista_alunos = ["Todos"] + sorted(alunos_filtrados["nome"].unique().tolist())
    nome_sel = st.sidebar.selectbox("Mentorado", lista_alunos)

    return alunos_filtrados, nome_sel


# --- Métricas ---

def _render_metricas_gerais(df_filtrado: pd.DataFrame) -> None:
    m1, m2, m3, m4 = st.columns(4)
    
    media_total = df_filtrado["total"].mean()
    recorde = df_filtrado["total"].max()
    qtd = len(df_filtrado)
    ultima = df_filtrado.iloc[-1]["total"]

    m1.metric("Pontuação Mais Recente", f"{int(ultima)}")
    m2.metric("Maior Pontuação", f"{int(recorde)}")
    m3.metric("Pontuação Média", f"{media_total:.0f}")
    m4.metric("Redações Registradas", f"{qtd}")


# --- Visão Grupo ---

def _render_radar_grupo(df_filtrado: pd.DataFrame) -> None:
    st.subheader("🎯 Diagnóstico Estratégico: Grupo vs Alta Performance")
    
    medias_grupo = df_filtrado[_COMPETENCIAS].mean().tolist()
    
    top_5_ids = df_filtrado.groupby("id_aluno")["total"].mean().nlargest(5).index
    medias_top5 = df_filtrado[df_filtrado["id_aluno"].isin(top_5_ids)][_COMPETENCIAS].mean().tolist()

    labels_radar = _LABELS_COMPETENCIAS + [_LABELS_COMPETENCIAS[0]]
    medias_grupo_fechado = medias_grupo + [medias_grupo[0]]
    medias_top5_fechado = medias_top5 + [medias_top5[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=medias_grupo_fechado, theta=labels_radar, fill="toself",
        name="Média do Grupo", line_color="rgba(150,150,150,0.5)", marker=dict(size=0),
    ))
    fig.add_trace(go.Scatterpolar(
        r=medias_top5_fechado, theta=labels_radar, fill="toself",
        name="Top 5 Performance", line_color="#c00000",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 200], gridcolor="#444"),
            angularaxis=dict(gridcolor="#444"),
        ),
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5),
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)


# --- Visão Individual ---

def _render_evolucao_individual(df_filtrado: pd.DataFrame) -> None:
    st.subheader("📈 Curva de Performance")
    
    fig = px.line(
        df_filtrado, x="data", y="total", markers=True,
        hover_data={"data": "|%d/%m/%Y", "total": True, "tema": True},
    )
    fig.update_traces(
        line=dict(color="#c00000", width=4),
        marker=dict(size=12, color="#c00000", line=dict(color="white", width=2)),
        hovertemplate="<b>Data:</b> %{x|%d/%m/%Y}<br><b>Nota:</b> %{y} pts<br><b>Tema:</b> %{customdata[0]}<extra></extra>",
    )
    fig.update_layout(
        template="plotly_dark",
        yaxis_range=[0, 1050],
        xaxis=dict(tickformat="%d/%m", gridcolor="#333"),
        hovermode="x unified",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_radar_individual(df_filtrado: pd.DataFrame, df_redacoes: pd.DataFrame) -> None:
    st.markdown("---")
    st.subheader("🎯 Diagnóstico Estratégico")
    
    medias_aluno = df_filtrado[_COMPETENCIAS].mean().tolist()
    medias_turma = df_redacoes[_COMPETENCIAS].mean().tolist()

    labels_radar = _LABELS_COMPETENCIAS + [_LABELS_COMPETENCIAS[0]]
    medias_aluno_fechado = medias_aluno + [medias_aluno[0]]
    medias_turma_fechado = medias_turma + [medias_turma[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=medias_turma_fechado, theta=labels_radar, fill="toself",
        name="Média Geral", line_color="rgba(150,150,150,0.5)", marker=dict(size=0),
    ))
    fig.add_trace(go.Scatterpolar(
        r=medias_aluno_fechado, theta=labels_radar, fill="toself",
        name="Seu Desempenho", line_color="#c00000",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 200], gridcolor="#444"),
            angularaxis=dict(gridcolor="#444"),
        ),
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5),
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)


# --- Histórico ---

def _render_historico(df_filtrado: pd.DataFrame) -> None:
    with st.expander("📋 Ver Histórico Detalhado de Redações"):
        df_tab = df_filtrado.sort_values("data", ascending=False).copy()
        df_tab["data"] = df_tab["data"].dt.strftime("%d/%m/%Y")
        st.dataframe(
            df_tab[["data", "tema", "c1", "c2", "c3", "c4", "c5", "total"]],
            use_container_width=True, hide_index=True,
        )


# --- Ponto de entrada ---

def exibir_modulo_redacoes(df_alunos: pd.DataFrame, df_redacoes: pd.DataFrame) -> None:
    st.markdown(_CSS_MODULO, unsafe_allow_html=True)
    st.title("✍️ Central de Redações")
    st.subheader("*Avaliação técnica, progressão e consistência argumentativa*")

    alunos_filtrados, nome_sel = _render_filtros_sidebar(df_alunos)

    if nome_sel == "Todos":
        mask_geral = df_redacoes["id_aluno"].isin(alunos_filtrados["id_aluno"])
    else:
        id_aluno = df_alunos[df_alunos["nome"] == nome_sel]["id_aluno"].values[0]
        mask_geral = df_redacoes["id_aluno"] == id_aluno

    df_filtrado = df_redacoes[mask_geral].copy()
    df_filtrado["tema"] = df_filtrado["tema"].replace(["", None, np.nan], "Não informado")
    df_filtrado["data"] = pd.to_datetime(df_filtrado["data"], dayfirst=True)
    df_filtrado = df_filtrado.sort_values("data")

    if df_filtrado.empty:
        st.info("💡 Nenhuma redação registrada para os filtros selecionados.")
        return

    _render_metricas_gerais(df_filtrado)
    st.markdown("---")

    if nome_sel == "Todos":
        _render_radar_grupo(df_filtrado)
    else:
        _render_evolucao_individual(df_filtrado)
        _render_radar_individual(df_filtrado, df_redacoes)

    _render_historico(df_filtrado)

    st.markdown("---")
    col1, col_centro, col2 = st.columns([2, 1, 2])
    with col_centro:
        st.image("logo.png", width=250)
    with col1:
        st.caption("*© 2026 • Central de Performance Acadêmica - Estude com Danilo*")
    with col2:
        st.markdown('<p style="text-align: right; color: grey; font-size: 0.8rem;">Desenvolvido por Thyago Ribeiro</p>', unsafe_allow_html=True)