try:
    client = conectar_google_sheets()
    
    ID_PLANILHA = "1fh9e5mSvMYKbs1BcuknM5Cuhj8Bbqn-r_enPUt1e5_g" 
    sh = client.open_by_key(ID_PLANILHA)
    
    # Tenta ler a aba 'Alunos' (Verifique se o nome na aba é exatamente este)
    aba_alunos = sh.worksheet("Alunos")
    dados = aba_alunos.get_all_records()
    
    if not dados:
        st.warning("A aba 'Alunos' parece estar vazia.")
    else:
        df_alunos = pd.DataFrame(dados)
        st.success("Conectado com sucesso!")
        
        # Filtros básicos para teste
        st.subheader("Filtros de Teste")
        col1, col2 = st.columns(2)
        
        with col1:
            mentoria = st.multiselect("Filtrar por Mentoria", df_alunos['id_mentoria'].unique())
        
        # Aplica filtro se selecionado
        df_filtrado = df_alunos
        if mentoria:
            df_filtrado = df_alunos[df_alunos['id_mentoria'].isin(mentoria)]
            
        st.dataframe(df_filtrado)

except Exception as e:
    st.error(f"Erro detalhado: {e}")
    st.info("Dica: Verifique se o e-mail da conta de serviço foi adicionado como EDITOR na planilha.")