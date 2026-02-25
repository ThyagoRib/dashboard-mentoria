import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

_SHEET_ID = "1fh9e5mSvMYKbs1BcuknM5Cuhj8Bbqn-r_enPUt1e5_g"
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _conectar() -> gspread.Client:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=_SCOPES
    )
    return gspread.authorize(creds)


def _padronizar_data(df: pd.DataFrame) -> pd.DataFrame:
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce").dt.tz_localize(None)
    return df


def _to_numeric(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    for col in colunas:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

@st.cache_data(ttl=600)
def carregar_dados() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    client = _conectar()
    sh = client.open_by_key(_SHEET_ID)

    df_alunos = pd.DataFrame(sh.worksheet("Alunos").get_all_records())

    df_atividades = pd.DataFrame(sh.worksheet("Atividades").get_all_records())
    df_atividades = _padronizar_data(df_atividades)
    df_atividades = _to_numeric(df_atividades, ["acertos", "total"])
    df_atividades["%"] = (df_atividades["acertos"] / df_atividades["total"] * 100).fillna(0)

    df_simulados = pd.DataFrame(sh.worksheet("Simulados").get_all_records())
    df_simulados = _padronizar_data(df_simulados)
    df_simulados = _to_numeric(df_simulados, ["acertos", "total"])

    df_redacoes = pd.DataFrame(sh.worksheet("Redações").get_all_records())
    df_redacoes = _padronizar_data(df_redacoes)

    colunas_red = ["c1", "c2", "c3", "c4", "c5", "total"]
    df_redacoes = _to_numeric(df_redacoes, colunas_red)

    return df_alunos, df_atividades, df_simulados, df_redacoes