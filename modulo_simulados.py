import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import math
import streamlit.components.v1 as components

MAPA_MENTORIAS = {1: "Estude com Danilo", 2: "Projeto Medicina"}

ORDEM_AREAS = ["Linguagens", "Humanas", "Natureza", "Matemática"]
DIA_1 = ["Linguagens", "Humanas"]
DIA_2 = ["Natureza", "Matemática"]
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

def _filtrar_simulados_completos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
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
        (c2, "#c00000", "⚠️ Ponto de Melhoria", pior_area_nome, f"{int(pior_area_val)}", "acertos"),
        (c3, "#c00000", "🎯 Recorde Individual", "Simulado Geral", f"{int(melhor_nota_total)}", "/180"),
        (c4, "#c00000", "📝 Simulados Concluídos", "Concluídos", f"{qtd_completos}", "simulados"),
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
    if df_base.empty:
        st.warning("Sem dados disponíveis para os filtros selecionados.")
        return
    col_esq, col_dir = st.columns([1, 1.2])
    df_radar = df_base.groupby("area")["rendimento_perc"].mean().reset_index()
    if df_radar.empty:
        st.info("Dados insuficientes para gerar o gráfico radar.")
        return
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
    if df_area.empty:
        st.info(f"Sem dados registrados para a área: {area_sel}")
        return
    df_area["data"] = pd.to_datetime(df_area["data"])
    df_plot = (
        df_area.groupby("data")["rendimento_perc"]
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
            hovertemplate="<b>Data: %{x|%d/%m/%Y}</b><br>Média: %{y:.1f}%<extra></extra>",
        )
        if len(df_plot) > 1:
            x_ord = df_plot["data"].apply(lambda x: x.toordinal())
            slope, intercept = np.polyfit(x_ord, df_plot["rendimento_perc"], 1)
            fig_line.add_trace(go.Scatter(
                x=df_plot["data"], y=slope * x_ord + intercept,
                mode="lines", line=dict(color="white", width=1.5, dash="dash"),
                hoverinfo="skip",
            ))
        fig_line.update_layout(
            template="plotly_dark", height=380, yaxis_range=[0, 105], showlegend=False,
            xaxis=dict(tickformat="%d/%m/%y")
        )
        st.plotly_chart(fig_line, use_container_width=True)

def _render_historico_simulados(df_base: pd.DataFrame, df_alunos: pd.DataFrame, nome_sel: str) -> None:
    if df_base.empty:
        return
    with st.expander("📄 Histórico Completo de Simulados"):
        df_hist = df_base.copy()
        df_hist["data"] = pd.to_datetime(df_hist["data"])
        df_hist["Data"] = df_hist["data"].dt.strftime("%d/%m/%Y").fillna("Data N/D")
        df_hist["%"] = (df_hist["acertos"] / df_hist["total"] * 100).fillna(0).map("{:.1f}%".format)
        colunas_originais = ["Data", "tipo", "numero", "ano", "area", "acertos", "total", "%"]
        if nome_sel == "Todos":
            df_hist = df_hist.merge(df_alunos[["id_aluno", "nome"]], on="id_aluno")
            colunas_finais = ["nome"] + colunas_originais
        else:
            colunas_finais = colunas_originais
        df_render = df_hist.sort_values("data", ascending=False)[colunas_finais]
        st.dataframe(df_render, use_container_width=True, hide_index=True)

def _render_ranking_geral(df_simulados: pd.DataFrame, df_alunos: pd.DataFrame, df_base: pd.DataFrame) -> None:
    st.subheader("🏆 Ranking Geral")
    if df_base.empty:
        st.info("Sem dados disponíveis para montar o ranking.")
        return
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        r_tipo = st.selectbox("Tipo", sorted(df_simulados["tipo"].unique(), key=str), key="r_t")
    with c2:
        nums = df_simulados[df_simulados["tipo"] == r_tipo]["numero"].unique()
        r_num = st.selectbox("Número", sorted(nums, key=str), key="r_n")
    with c3:
        anos = df_simulados[(df_simulados["tipo"] == r_tipo) & (df_simulados["numero"] == r_num)]["ano"].unique()
        r_ano = st.selectbox("Ano", sorted(anos, key=str), key="r_a")
    with c4:
        r_visao = st.selectbox("Visão", ["Completo", "Dia 1 (Ling/Hum)", "Dia 2 (Nat/Mat)"], key="r_v")

    df_f = df_simulados[(df_simulados["tipo"] == r_tipo) & (df_simulados["numero"] == r_num) & (df_simulados["ano"] == r_ano)]
    df_f = df_f[df_f["id_aluno"].isin(df_base["id_aluno"].unique())]
    if df_f.empty:
        st.warning("⚠️ Nenhum registro encontrado para este simulado.")
        return
    rp = df_f.pivot_table(index="id_aluno", columns="area", values="acertos", aggfunc="sum").reset_index()
    for area in ORDEM_AREAS:
        if area not in rp.columns: rp[area] = np.nan
    ct = df_f.groupby("id_aluno")["total"].sum().reset_index()
    rf = rp.merge(ct, on="id_aluno")

    if r_visao == "Completo":
        rf = rf[rf["total"] == TOTAL_QUESTOES_COMPLETO].copy()
        if rf.empty: return
        rf["Total Dia 1"] = rf[DIA_1].sum(axis=1)
        rf["Total Dia 2"] = rf[DIA_2].sum(axis=1)
        rf["Total Geral"] = rf["Total Dia 1"] + rf["Total Dia 2"]
        colunas_exibir = ["Posição", "Aluno"] + ORDEM_AREAS + ["Total Dia 1", "Total Dia 2", "Total Geral"]
    elif r_visao == "Dia 1 (Ling/Hum)":
        rf = rf[rf[DIA_1].notnull().all(axis=1)].copy()
        if rf.empty: return
        rf["Total Dia 1"] = rf[DIA_1].sum(axis=1)
        colunas_exibir = ["Posição", "Aluno"] + DIA_1 + ["Total Dia 1"]
    else:
        rf = rf[rf[DIA_2].notnull().all(axis=1)].copy()
        if rf.empty: return
        rf["Total Dia 2"] = rf[DIA_2].sum(axis=1)
        colunas_exibir = ["Posição", "Aluno"] + DIA_2 + ["Total Dia 2"]

    rf = rf.merge(df_alunos[["id_aluno", "nome"]], on="id_aluno").rename(columns={"nome": "Aluno"})
    col_notas = [c for c in colunas_exibir if c not in ["Posição", "Aluno"]]
    st.markdown("---")
    col_ordem_sel = st.radio("Ordenar ranking por:", col_notas, index=len(col_notas)-1, horizontal=True)
    top_10 = rf.sort_values(col_ordem_sel, ascending=False).head(10)
    medias_top10 = top_10[col_notas].mean().round(0).to_dict()
    linha_media = {"Posição": "---", "Aluno": "📊 MÉDIA TOP 10", **medias_top10, "is_media": 1}
    rf["is_media"] = 0
    rf_final = pd.concat([rf, pd.DataFrame([linha_media])], ignore_index=True)
    for col in col_notas: rf_final[col] = pd.to_numeric(rf_final[col]).fillna(0).astype(int)
    rf_final = rf_final.sort_values(by=[col_ordem_sel, "is_media"], ascending=[False, True]).reset_index(drop=True)
    pos_aluno = 0
    list_pos = []
    for _, row in rf_final.iterrows():
        if row["is_media"] == 1: list_pos.append("---")
        else:
            list_pos.append(_posicao_ranking(pos_aluno))
            pos_aluno += 1
    rf_final["Posição"] = list_pos
    st.dataframe(rf_final[colunas_exibir].style.apply(lambda r: ['background-color: rgba(192, 0, 0, 0.2); font-weight: bold' if r['Aluno'] == "📊 MÉDIA TOP 10" else ''] * len(r), axis=1), use_container_width=True, hide_index=True)

def _render_ranking_individual(df_simulados: pd.DataFrame, id_aluno_focado: int, nome_sel: str) -> None:
    st.subheader(f"Histórico de Posicionamento: {nome_sel}")
    r_visao_ind = st.selectbox("Filtrar Histórico por", ["Completo", "Dia 1 (Ling/Hum)", "Dia 2 (Nat/Mat)"], key="r_v_ind")
    aluno_simus = df_simulados[df_simulados["id_aluno"] == id_aluno_focado][["tipo", "numero", "ano"]].drop_duplicates()
    if aluno_simus.empty:
        st.info("💡 Realize simulados para habilitar o histórico de ranking.")
        return
    resumo = []
    for _, row in aluno_simus.iterrows():
        comp = df_simulados[(df_simulados["tipo"] == row["tipo"]) & (df_simulados["numero"] == row["numero"]) & (df_simulados["ano"] == row["ano"])]
        comp_pivot = comp.pivot_table(index="id_aluno", columns="area", values="acertos", aggfunc="sum").reset_index()
        for area in ORDEM_AREAS:
            if area not in comp_pivot.columns: comp_pivot[area] = np.nan
        comp_qtd = comp.groupby("id_aluno")["total"].sum().reset_index()
        rank = comp_pivot.merge(comp_qtd, on="id_aluno")
        if r_visao_ind == "Completo":
            rank = rank[rank["total"] == TOTAL_QUESTOES_COMPLETO].copy()
            if rank.empty: continue
            rank["Total Dia 1"] = rank[DIA_1].sum(axis=1)
            rank["Total Dia 2"] = rank[DIA_2].sum(axis=1)
            rank["Sort_Col"] = rank["Total Dia 1"] + rank["Total Dia 2"]
            cols_interesse = ORDEM_AREAS + ["Total Dia 1", "Total Dia 2", "Sort_Col"]
            map_nomes = {"Sort_Col": "Total Geral"}
        elif r_visao_ind == "Dia 1 (Ling/Hum)":
            rank = rank[rank[DIA_1].notnull().all(axis=1)].copy()
            if rank.empty: continue
            rank["Sort_Col"] = rank[DIA_1].sum(axis=1)
            cols_interesse = DIA_1 + ["Sort_Col"]
            map_nomes = {"Sort_Col": "Total Dia 1"}
        else:
            rank = rank[rank[DIA_2].notnull().all(axis=1)].copy()
            if rank.empty: continue
            rank["Sort_Col"] = rank[DIA_2].sum(axis=1)
            cols_interesse = DIA_2 + ["Sort_Col"]
            map_nomes = {"Sort_Col": "Total Dia 2"}
        if id_aluno_focado in rank["id_aluno"].values:
            rank = rank.sort_values("Sort_Col", ascending=False).reset_index(drop=True)
            idx = rank[rank["id_aluno"] == id_aluno_focado].index[0]
            linha = {"Simulado": f"{row['tipo']} {row['numero']} ({row['ano']})", "Posição": f"{_posicao_ranking(idx)} de {len(rank)}"}
            for col in cols_interesse: linha[map_nomes.get(col, col)] = int(rank.loc[idx, col]) if not np.isnan(rank.loc[idx, col]) else 0
            resumo.append(linha)
    if resumo: st.dataframe(pd.DataFrame(resumo), use_container_width=True, hide_index=True)
    else: st.warning("⚠️ Nenhum registro completo encontrado.")

def _render_registro_ausencia(df_alunos_filt: pd.DataFrame, df_simu: pd.DataFrame) -> None:
    st.subheader("🕵️ Controle de Assiduidade")
    c1, c2 = st.columns(2)
    with c1: data_ini = st.date_input("Data Inicial", value=pd.to_datetime("today") - pd.Timedelta(days=4), format="DD/MM/YYYY")
    with c2: data_fim = st.date_input("Data Final", value=pd.to_datetime("today"), format="DD/MM/YYYY")

    df_simu_temp = df_simu.copy()
    df_simu_temp["data"] = pd.to_datetime(df_simu_temp["data"]).dt.date
    alunos_com_registro = df_simu_temp[(df_simu_temp["data"] >= data_ini) & (df_simu_temp["data"] <= data_fim)]["id_aluno"].unique()
    alunos_ausentes = df_alunos_filt[~df_alunos_filt["id_aluno"].isin(alunos_com_registro)].copy()
    lista_nomes = sorted(alunos_ausentes["nome"].tolist())

    if lista_nomes:
        st.error(f"⚠️ {len(lista_nomes)} alunos não realizaram simulados neste período.")
        st.dataframe(alunos_ausentes[["nome"]].sort_values("nome"), use_container_width=True, hide_index=True)
        texto_copiar = "\\n".join(lista_nomes)
        html_button = f"""
            <button id="copy-btn" style="background-color: #4d0000; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; width: 30%; margin-top: 10px;">📋 Copiar Lista de Nomes</button>
            <script>
            document.getElementById('copy-btn').onclick = function() {{
                const text = `{texto_copiar}`;
                navigator.clipboard.writeText(text).then(function() {{
                    const btn = document.getElementById('copy-btn');
                    btn.innerText = '✅ Copiado!'; btn.style.backgroundColor = '#235f30';
                    setTimeout(() => {{ btn.innerText = '📋 Copiar Lista de Nomes'; btn.style.backgroundColor = '#4d0000'; }}, 2000);
                }});
            }};
            </script>
        """
        components.html(html_button, height=60)
    else: st.success("✅ Excelente! Todos os alunos realizaram simulados no período.")

def exibir_modulo_simulados(df_alunos: pd.DataFrame, df_simulados: pd.DataFrame) -> None:
    st.markdown(_CSS_MODULO, unsafe_allow_html=True)
    st.title("📚 Central de Simulados")
    st.subheader("*Simulados revelam padrões, estratégia corrige trajetórias*")

    st.sidebar.subheader("Configurações de Análise")
    mapa_ids = {v: k for k, v in MAPA_MENTORIAS.items()}
    ids_presentes = sorted(df_alunos["id_mentoria"].unique().tolist())
    nomes_mentorias = [MAPA_MENTORIAS.get(i, f"Mentoria {i}") for i in ids_presentes]
    mentoria_sel = st.sidebar.selectbox("Mentoria", ["Todas"] + nomes_mentorias)

    if mentoria_sel == "Todas": alunos_filtrados = df_alunos
    else: alunos_filtrados = df_alunos[df_alunos["id_mentoria"] == mapa_ids[mentoria_sel]]

    lista_alunos = ["Todos"] + sorted(alunos_filtrados["nome"].unique().tolist())
    nome_sel = st.sidebar.selectbox("Mentorado", lista_alunos, key="simu_aluno")
    area_sel = st.sidebar.selectbox("Área", ["Todas"] + sorted(df_simulados["area"].unique().tolist()))

    if nome_sel == "Todos":
        df_base = df_simulados[df_simulados["id_aluno"].isin(alunos_filtrados["id_aluno"])].copy()
        id_aluno_focado = None
    else:
        id_aluno_focado = df_alunos[df_alunos["nome"] == nome_sel]["id_aluno"].values[0]
        df_base = df_simulados[df_simulados["id_aluno"] == id_aluno_focado].copy()

    simulados_validos, df_completos = _filtrar_simulados_completos(df_base)
    df_base["rendimento_perc"] = (df_base["acertos"] / df_base["total"] * 100).fillna(0)

    # --- Lógica de Abas Dinâmicas ---
    titulos_abas = ["📈 Desempenho & Consistência", "🏆 Ranking & Posicionamento"]
    if nome_sel == "Todos":
        titulos_abas.append("🚫 Registro de Ausência")
    
    abas = st.tabs(titulos_abas)

    with abas[0]:
        st.markdown("### 📊 Análise de Performance")
        _render_cards_records(simulados_validos, df_completos)
        st.markdown("---")
        st.subheader(f"🎯 Leitura Analítica: {area_sel if area_sel != 'Todas' else 'Visão Global'}")
        if area_sel == "Todas": _render_diagnostico_geral(df_base)
        else: _render_diagnostico_area(df_base, area_sel)
        st.markdown("---")
        _render_historico_simulados(df_base, df_alunos, nome_sel)

    with abas[1]:
        if nome_sel == "Todos": _render_ranking_geral(df_simulados, df_alunos, df_base)
        else: _render_ranking_individual(df_simulados, id_aluno_focado, nome_sel)

    if nome_sel == "Todos":
        with abas[2]:
            _render_registro_ausencia(alunos_filtrados, df_simulados)

    st.markdown("---")
    col1, col_centro, col2 = st.columns([2, 1, 2])
    with col_centro: st.image("logo.png", width=250)
    with col1: st.caption("*© 2026 • Central de Performance Acadêmica - Estude com Danilo*")
    with col2: st.markdown('<p style="text-align: right; color: grey; font-size: 0.8rem;">Desenvolvido por Thyago Ribeiro</p>', unsafe_allow_html=True)