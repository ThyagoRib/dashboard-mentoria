import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. DEFINIÇÃO DA FUNÇÃO (Deve vir antes de ser chamada)
def conectar_google_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # Busca as credenciais dos Secrets do Streamlit Cloud
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Erro ao carregar Secrets: {e}")
        return None

# 2. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dashboard Estude com Danilo", layout="wide")

st.title("🚀 Dashboard de Atividades - Mentoria")

# 3. EXECUÇÃO PRINCIPAL
try:
    client = conectar_google_sheets()
    
    if client:
        # Seu ID da planilha fornecido no log
        ID_PLANILHA = "1fh9e5mSvMYKbs1BcuknM5Cuhj8Bbqn-r_enPUt1e5_g"
        sh = client.open_by_key(ID_PLANILHA)
        
        # Tenta ler a aba 'Alunos'
        # IMPORTANTE: Verifique se o nome na aba da planilha é 'Alunos' ou 'alunos'
        aba_alunos = sh.worksheet("Alunos") 
        dados = aba_alunos.get_all_records()
        
        if not dados:
            st.warning("A aba 'Alunos' parece estar vazia.")
        else:
            df_alunos = pd.DataFrame(dados)
            st.success("Conectado com sucesso!")
            
            # Filtros básicos para teste
            st.subheader("Visualização de Alunos")
            
            # Se a coluna id_mentoria existir, criamos o filtro
            if 'id_mentoria' in df_alunos.columns:
                tipos = df_alunos['id_mentoria'].unique().tolist()
                selecao = st.multiselect("Filtrar por Tipo de Mentoria", tipos, default=tipos)
                df_filtrado = df_alunos[df_alunos['id_mentoria'].isin(selecao)]
            else:
                df_filtrado = df_alunos
                
            st.dataframe(df_filtrado, use_container_width=True)

except Exception as e:
    st.error(f"Erro detalhado na execução: {e}")
    st.info("Dica: Verifique se o nome da aba é exatamente 'Alunos' e se o e-mail da conta de serviço é EDITOR na planilha.")