import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

ORDEM_MATERIAS = [
    "Linguagens", "História", "Geografia", "Filo / Socio",
    "Biologia", "Física", "Química", "Matemática",
]

MAPA_MENTORIAS = {1: "Estude com Danilo", 2: "Projeto Medicina"}

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

.diag-card {
    background-color: #1e1e1e;
    padding: 20px;
    border-radius: 10px;
    height: 150px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    transition: all 0.3s ease-in-out;
}
.diag-card:hover {
    transform: translateY(-5px);
    background-color: #252525;
    box-shadow: 0px 4px 15px rgba(255, 165, 0, 0.1);
}
</style>
"""


# --- Cálculos ---

def _calcular_tendencia(df_diario: pd.DataFrame) -> tuple[str, str, np.ndarray | None]:
    if len(df_diario) <= 1:
        return "#333", "Sem Dados", None

    x_ord = df_diario["data"].map(datetime.toordinal).values
    slope, intercept = np.polyfit(x_ord, df_diario["%"].values, 1)
    linha = slope * x_ord + intercept

    if slope > 0.05:
        return "#28a745", "Crescente", linha
    if slope < -0.05:
        return "#c00000", "Decrescente", linha
    return "#6c757d", "Estável", linha


def _calcular_streak(df_atividades: pd.DataFrame, id_aluno: int, hoje: datetime) -> int:
    datas_unicas = sorted(
        df_atividades[df_atividades["id_aluno"] == id_aluno]["data"].dt.date.unique(),
        reverse=True,
    )
    streak, ref = 0, hoje.date()
    for d in datas_unicas:
        if d == ref or d == ref - timedelta(days=1):
            streak += 1
            ref = d
        else:
            break
    return streak


def _calcular_hiato(
    df_atividades: pd.DataFrame, id_aluno: int, hoje: datetime
) -> tuple[str, int, str] | None:
    materias_estudadas = df_atividades[df_atividades["id_aluno"] == id_aluno]["materia"].unique()
    registros = [
        {
            "Matéria": m,
            "Dias": (
                hoje
                - df_atividades[
                    (df_atividades["id_aluno"] == id_aluno)
                    & (df_atividades["materia"] == m)
                ]["data"].max()
            ).days,
        }
        for m in ORDEM_MATERIAS
        if m in materias_estudadas
    ]
    if not registros:
        return None

    critica = pd.DataFrame(registros).sort_values("Dias", ascending=False).iloc[0]
    cor = "#ff4b4b" if critica["Dias"] > 7 else "#28a745"
    return critica["Matéria"], int(critica["Dias"]), cor


def _calcular_retencao(
    df_cont: pd.DataFrame, dados_filtrado: pd.DataFrame, hoje: datetime
) -> pd.DataFrame:
    # Curva de Ebbinghaus: retenção = acertos_% × e^(-0.03 × dias)
    df_ret = df_cont.copy()
    for idx, row in df_ret.iterrows():
        ultima_data = dados_filtrado[dados_filtrado["conteudo"] == row["conteudo"]]["data"].max()
        dias = (hoje - ultima_data).days
        df_ret.at[idx, "Retenção"] = row["%"] * np.exp(-0.03 * dias)
    return df_ret


# --- Sidebar ---

def _render_filtros_sidebar(df_alunos: pd.DataFrame) -> tuple[int, str, str, object, object]:
    st.sidebar.subheader("Configurações de Análise")

    mapa_ids = {v: k for k, v in MAPA_MENTORIAS.items()}
    ids_presentes = sorted(df_alunos["id_mentoria"].unique().tolist())
    nomes_mentorias = [MAPA_MENTORIAS.get(i, f"Mentoria {i}") for i in ids_presentes]

    mentoria_sel = st.sidebar.selectbox("Mentoria", ["Todas"] + nomes_mentorias)

    if mentoria_sel == "Todas":
        alunos_filtrados = df_alunos
    else:
        id_mentoria = mapa_ids[mentoria_sel]
        alunos_filtrados = df_alunos[df_alunos["id_mentoria"] == id_mentoria]

    if alunos_filtrados.empty:
        st.warning("Nenhum mentorado encontrado.")
        st.stop()

    nome_aluno = st.sidebar.selectbox(
        "Mentorado", sorted(alunos_filtrados["nome"].unique())
    )
    id_aluno = df_alunos[df_alunos["nome"] == nome_aluno]["id_aluno"].values[0]
    materia_sel = st.sidebar.selectbox("Disciplina", ["Todas"] + ORDEM_MATERIAS)

    st.sidebar.markdown("Período de Análise")
    hoje = datetime.now()
    data_inicio = st.sidebar.date_input("Início", hoje - timedelta(days=30), format="DD/MM/YYYY")
    data_fim = st.sidebar.date_input("Fim", hoje, format="DD/MM/YYYY")

    return id_aluno, nome_aluno, materia_sel, data_inicio, data_fim


# --- Aba: Desempenho & Consistência ---

def _render_metricas_gerais(dados: pd.DataFrame, volatilidade: float) -> None:
    m1, m2, m3, m4, m5 = st.columns(5)
    total_q = dados["total"].sum()
    total_a = dados["acertos"].sum()
    media = total_a / total_q * 100 if total_q > 0 else 0

    m1.metric("Questões Resolvidas", int(total_q))
    m2.metric("Acertos Obtidos", int(total_a))
    m3.metric("Taxa de Acerto", f"{media:.1f}%")
    m4.metric(
        "Consistência",
        f"{volatilidade:.1f}%" if not np.isnan(volatilidade) else "0.0%",
        help=(
            "**Mede a estabilidade da sua performance**  \n"
            "*Baixa oscilação indica previsibilidade e maturidade acadêmica*  \n"
            "*Mantenha-se abaixo dos **15%***"
        ),
    )
    m5.metric("Registros de Estudo", len(dados))


def _render_radar(mask_geral, df_atividades: pd.DataFrame) -> None:
    st.markdown("---")
    st.subheader("📡 Radar de Performance por Disciplina")
    st.markdown("*O seu desempenho contra a média global*")

    def media_por_materia(df_mask):
        return (
            df_atividades.loc[df_mask]
            .groupby("materia")
            .apply(
                lambda x: (x["acertos"].sum() / x["total"].sum() * 100)
                if x["total"].sum() > 0 else 0,
                include_groups=False,
            )
            .reindex(ORDEM_MATERIAS)
            .fillna(0)
        )

    mask_turma = df_atividades["materia"].isin(ORDEM_MATERIAS)
    r_aluno = media_por_materia(mask_geral).tolist()
    r_turma = media_por_materia(mask_turma).tolist()

    theta = ORDEM_MATERIAS + [ORDEM_MATERIAS[0]]
    r_aluno_fechado = r_aluno + [r_aluno[0]]
    r_turma_fechado = r_turma + [r_turma[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=r_turma_fechado, theta=theta, fill="toself", name="Média Turma",
        line_color="rgba(255,255,255,0.5)", fillcolor="rgba(255,255,255,0.1)",
        hovertemplate="Média Turma: %{r:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatterpolar(
        r=r_aluno_fechado, theta=theta, fill="toself", name="Desempenho Aluno",
        line_color="#c00000", fillcolor="rgba(192,0,0,0.3)",
        hovertemplate="Aluno: %{r:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="#444")),
        template="plotly_dark",
        height=515,
        margin=dict(l=80, r=80, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        hovermode="closest",
    )
    st.plotly_chart(fig, width="stretch")


def _render_evolucao_diaria(
    df_diario: pd.DataFrame, materia_sel: str, cor_bola: str, txt_tendencia: str, linha_tendencia
) -> None:
    st.markdown("---")
    c1, c2 = st.columns([3, 1])
    with c1:
        st.subheader(f"📌 Evolução de Desempenho - {materia_sel}")
    with c2:
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:flex-end;'
            f'height:100%;padding-top:10px;">'
            f'<span style="color:#888;font-size:0.8rem;margin-right:10px;font-weight:500;">TENDÊNCIA:</span>'
            f'<div style="background-color:{cor_bola};width:18px;height:18px;border-radius:50%;margin-right:8px;"></div>'
            f'<span style="color:white;font-size:0.95rem;font-weight:bold;">{txt_tendencia.upper()}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    fig = px.line(df_diario, x="data", y="%", markers=True, color_discrete_sequence=["#c00000"])
    fig.update_traces(
        line=dict(width=4),
        marker=dict(size=10, line=dict(width=2, color="white")),
        hovertemplate="<b>Data: %{x}</b><br>Rendimento: %{y:.1f}%<extra></extra>",
    )
    if linha_tendencia is not None:
        fig.add_scatter(
            x=df_diario["data"], y=linha_tendencia,
            name="Tendência", line=dict(color="white", dash="dash", width=2),
        )
    fig.update_layout(yaxis_range=[0, 105], template="plotly_dark", height=400, hovermode="x unified")
    st.plotly_chart(fig, width="stretch")


# --- Aba: Diagnóstico Estratégico ---

def _render_cards_diagnostico(
    df_atividades: pd.DataFrame, id_aluno: int, hoje: datetime
) -> None:
    d1, d2 = st.columns(2)

    with d1:
        streak = _calcular_streak(df_atividades, id_aluno, hoje)
        st.markdown(
            f'<div class="diag-card" style="border-top:4px solid #ffa500;">'
            f'<h4 style="margin:0;color:#ffa500;">🔥 Streak de Constância</h4>'
            f'<p style="font-size:1.6rem;font-weight:bold;margin:5px 0;">{streak} Dias</p>'
            f'<small style="color:#888;">Dias consecutivos ativos.</small></div>',
            unsafe_allow_html=True,
        )

    with d2:
        hiato = _calcular_hiato(df_atividades, id_aluno, hoje)
        if hiato:
            materia, dias, cor = hiato
            st.markdown(
                f'<div class="diag-card" style="border-top:4px solid {cor};">'
                f'<h4 style="margin:0;color:{cor};">⏳ Alerta de Hiato</h4>'
                f'<p style="font-size:1.6rem;font-weight:bold;margin:5px 0;">{materia}</p>'
                f'<small style="color:#888;">{dias} dias sem registros.</small></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="diag-card" style="border-top:4px solid #6c757d;">'
                '<h4 style="margin:0;color:#6c757d;">⏳ Alerta de Hiato</h4>'
                '<p style="font-size:1.2rem;font-weight:bold;margin:5px 0;">Sem dados</p></div>',
                unsafe_allow_html=True,
            )


def _render_conteudos_criticos(dados_filtrado: pd.DataFrame) -> pd.DataFrame:
    st.subheader(
        "⚠️ Conteúdos Críticos",
        help=(
            "**Atenção:** Rendimento entre 50% e 70%  \n"
            "**Crítico:** Rendimento < 50%"
        ),
    )
    st.markdown("*De olho nas revisões*")
    df_cont = (
        dados_filtrado
        .groupby(["materia", "conteudo"])
        .agg({"acertos": "sum", "total": "sum"})
        .reset_index()
    )
    df_cont["%"] = df_cont["acertos"] / df_cont["total"] * 100

    gaps = df_cont[df_cont["%"] < 70].sort_values("%").head(5)
    if not gaps.empty:
        for _, row in gaps.iterrows():
            if row["%"] < 50:
                st.error(f"🚨 **CRÍTICO** | {row['materia']} - {row['conteudo']}: **{row['%']:.1f}%**")
            else:
                st.warning(f"🟡 **ATENÇÃO** | {row['materia']} - {row['conteudo']}: **{row['%']:.1f}%**")
    else:
        st.success("Desempenho sólido em todos os conteúdos registrados!")

    return df_cont


def _render_retencao(df_cont: pd.DataFrame, dados_filtrado: pd.DataFrame, hoje: datetime) -> None:
    st.subheader(
        "🧠 Retenção Estimada por Conteúdo",
        help=(
            "*Curva de Esquecimento de Ebbinghaus* baseada no percentual de acertos "
            "e data de registro de cada conteúdo."
        ),
    )
    st.markdown("*A ciência por trás da retenção de conhecimento*")
    df_ret = _calcular_retencao(df_cont, dados_filtrado, hoje)
    df_ret_top = df_ret.sort_values("Retenção").head(15)

    fig = px.bar(
        df_ret_top, x="Retenção", y="conteudo", orientation="h",
        color="Retenção", color_continuous_scale="RdYlGn", range_color=[0, 100],
    )
    fig.update_traces(
        hovertemplate="<b>Conteúdo:</b> %{y}<br><b>Retenção Estimada:</b> %{x:.2f}%<extra></extra>"
    )
    fig.update_layout(
        template="plotly_dark", height=500, showlegend=False,
        xaxis_title="Retenção Estimada (%)", yaxis_title="",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, width="stretch")


# --- Histórico ---

def _render_historico(dados_filtrado: pd.DataFrame) -> None:
    with st.expander("📄 Histórico Completo de Registros"):
        df_display = dados_filtrado.copy()
        df_display["data"] = df_display["data"].dt.strftime("%d/%m/%Y")
        df_display["%"] = df_display["%"].map("{:.2f}%".format)
        df_display["acertos"] = df_display["acertos"].astype(int)
        df_display["total"] = df_display["total"].astype(int)
        st.dataframe(
            df_display[["data", "materia", "conteudo", "acertos", "total", "%"]]
            .sort_values("data", ascending=False),
            width="stretch",
            hide_index=True,
        )


# --- Ponto de entrada ---

def exibir_avaliacao_individual(df_alunos: pd.DataFrame, df_atividades: pd.DataFrame) -> None:
    st.markdown(_CSS_MODULO, unsafe_allow_html=True)
    st.title("🚀 Central de Alta Performance")
    st.subheader("*Decisões estratégicas começam com dados precisos*")

    hoje = datetime.now()

    id_aluno, nome_aluno, materia_sel, data_inicio, data_fim = _render_filtros_sidebar(df_alunos)

    mask_geral = (
        (df_atividades["id_aluno"] == id_aluno)
        & (df_atividades["data"].dt.date >= data_inicio)
        & (df_atividades["data"].dt.date <= data_fim)
        & (df_atividades["materia"].isin(ORDEM_MATERIAS))
    )
    mask_materia = (
        mask_geral if materia_sel == "Todas"
        else mask_geral & (df_atividades["materia"] == materia_sel)
    )
    dados_filtrado = df_atividades.loc[mask_materia].copy()

    if dados_filtrado.empty:
        st.info("Nenhuma atividade encontrada para os filtros selecionados.")
        return

    df_diario = (
        dados_filtrado
        .groupby(dados_filtrado["data"].dt.date)
        .agg({"acertos": "sum", "total": "sum"})
        .reset_index()
    )
    df_diario["%"] = (df_diario["acertos"] / df_diario["total"] * 100).fillna(0)
    df_diario = df_diario.sort_values("data")
    volatilidade = df_diario["%"].std()
    cor_bola, txt_tendencia, linha_tendencia = _calcular_tendencia(df_diario)

    aba_perf, aba_diag = st.tabs(["📈 Desempenho & Consistência", "🎯 Diagnóstico Estratégico"])

    with aba_perf:
        _render_metricas_gerais(dados_filtrado, volatilidade)
        _render_radar(mask_geral, df_atividades)
        _render_evolucao_diaria(df_diario, materia_sel, cor_bola, txt_tendencia, linha_tendencia)

    with aba_diag:
        st.subheader("🎯 Diagnóstico Avançado")
        _render_cards_diagnostico(df_atividades, id_aluno, hoje)
        st.markdown("---")
        df_cont = _render_conteudos_criticos(dados_filtrado)
        st.markdown("---")
        _render_retencao(df_cont, dados_filtrado, hoje)

    st.markdown("---")
    _render_historico(dados_filtrado)

    st.markdown("---")
    _, col_centro, _ = st.columns([2, 1, 2])
    with col_centro:
        st.image("logo.png", width=250)
