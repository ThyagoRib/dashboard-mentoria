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
    """Converte 'data' para datetime tz-naive."""
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
        df["data"] = df["data"].dt.tz_localize(None)
    return df


def _to_numeric(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    for col in colunas:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=600)
def carregar_dados() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Busca as três abas do Google Sheets. Cache de 10 min."""
    client = _conectar()
    sh = client.open_by_key(_SHEET_ID)

    df_alunos = pd.DataFrame(sh.worksheet("Alunos").get_all_records())

    df_atividades = pd.DataFrame(sh.worksheet("Atividades").get_all_records())
    df_atividades = _padronizar_data(df_atividades)
    df_atividades = _to_numeric(df_atividades, ["acertos", "total"])
    df_atividades["%"] = df_atividades.apply(
        lambda row: (row["acertos"] / row["total"] * 100) if row["total"] > 0 else 0,
        axis=1,
    )

    df_simulados = pd.DataFrame(sh.worksheet("Simulados").get_all_records())
    df_simulados = _padronizar_data(df_simulados)
    df_simulados = _to_numeric(df_simulados, ["acertos", "total"])

    return df_alunos, df_atividades, df_simulados
