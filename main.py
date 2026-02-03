import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Configuração da página
st.set_page_config(page_title="Dashboard Estude com Danilo", layout="wide")

# Função para conectar ao Google Sheets
def conectar_google_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client

# Título do Dashboard
st.title("🚀 Dashboard Mentoria")

try:
    # Abre a planilha
    client = conectar_google_sheets()
    sh = client.open("Dashboar DB")
    
    # Lê a aba 'Alunos'
    aba_alunos = sh.worksheet("Alunos")
    df_alunos = pd.DataFrame(aba_alunos.get_all_records())
    
    # Exibe um seletor de teste
    st.subheader("Teste de Conexão")
    aluno_selecionado = st.selectbox("Selecione um aluno para testar:", df_alunos['nome'].tolist())
    st.write(f"Você selecionou o aluno: {aluno_selecionado}")
    
    # Mostra a tabela de alunos (apenas para validar)
    st.dataframe(df_alunos)

except Exception as e:
    st.error(f"Erro ao conectar: {e}")