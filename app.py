import streamlit as st
import streamlit_authenticator as stauth
from estilos import aplicar_estilos
from utils import carregar_dados
import modulo_individual
import modulo_simulados

st.set_page_config(page_title="Mentoria Estude com Danilo", page_icon="icon.jpg", layout="wide")
aplicar_estilos()

# Credenciais
try:
    config = st.secrets["auth"]
except KeyError:
    st.error(
        "Configurações de autenticação não encontradas. "
    )
    st.stop()

credentials = (
    config["credentials"].to_dict()
    if hasattr(config["credentials"], "to_dict")
    else config["credentials"]
)

authenticator = stauth.Authenticate(
    credentials,
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

authenticator.login(location="main")

authentication_status = st.session_state.get("authentication_status")

# Roteamento por status de autenticação
if authentication_status:
    try:
        df_alunos, df_atividades, df_simulados = carregar_dados()
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        st.stop()

    st.sidebar.image("logo.png", width="stretch")
    st.sidebar.markdown("---")

    modulo = st.sidebar.radio(
        "Painel",
        ["🚀 Central de Alta Performance", "📚 Central de Simulados"],
    )

    st.sidebar.markdown("---")
    
    if modulo == "🚀 Central de Alta Performance":
        modulo_individual.exibir_avaliacao_individual(df_alunos, df_atividades)
    elif modulo == "📚 Central de Simulados":
        modulo_simulados.exibir_modulo_simulados(df_alunos, df_simulados)

    st.sidebar.markdown("---")
    authenticator.logout("Sair", "sidebar")

elif authentication_status is False:
    st.error("Usuário ou senha incorretos.")
    st.image("logo.png", width=250)

else:  # None — tela de login
    _, col_centro, _ = st.columns([2, 1, 2])
    with col_centro:
        st.image("logo.png", width=250)
