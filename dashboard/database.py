# database.py
import os
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import streamlit as st

# ==============================================================================
# CONEXÃO COM O BANCO
# ==============================================================================

@st.cache_resource
def get_db_connection():
    """Cria a engine uma única vez e reutiliza em todos os cliques (cache_resource)."""
    user = quote_plus(os.getenv('DB_USER', 'postgres'))
    password = quote_plus(os.getenv('DB_PASS', 'password'))
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    dbname = os.getenv('DB_NAME', 'data_lake')
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")

# ==============================================================================
# QUERIES DO BALANÇO PATRIMONIAL
# ==============================================================================

@st.cache_data(ttl=3600) # Cache longo (1h) pois lista de empresas muda pouco
def get_companies_bp():
    """Retorna lista de empresas que possuem dados na tabela de Balanço Patrimonial Silver."""
    engine = get_db_connection()
    query = """
    SELECT DISTINCT "CNPJ_CIA", "DENOM_CIA"
    FROM layer_02_silver.n1_dfp_cia_aberta_bp
    ORDER BY "DENOM_CIA";
    """
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
            # Cria coluna combinada para o Dropdown
            df['LABEL_DROPDOWN'] = df['DENOM_CIA'] + ' (' + df['CNPJ_CIA'] + ')'
            return df
    except Exception as e:
        st.error(f"Erro ao listar empresas: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_dates_bp(cnpj):
    """Retorna datas disponíveis para uma empresa específica."""
    engine = get_db_connection()
    query = f"""
    SELECT DISTINCT "DT_REFER"
    FROM layer_02_silver.n1_dfp_cia_aberta_bp
    WHERE "CNPJ_CIA" = '{cnpj}'
    ORDER BY "DT_REFER" DESC;
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60) # Cache curto para permitir agilidade nos filtros
def get_bp_data_filtered(cnpj, dates, max_level):
    """
    Busca os dados do BP filtrando por CNPJ, Lista de Datas e Nível Máximo de Detalhe.
    Transforma o nível (1-5) em quantidade de dígitos da conta.
    """
    engine = get_db_connection()
    
    # Mapeamento Slider (1-5) -> Quantidade de Dígitos na conta
    # Nível 1 = 1 digito (1)
    # Nível 2 = 3 digitos (1.01)
    # Nível 3 = 5 digitos (1.01.01)
    # Nível 4 = 7 digitos (1.01.01.01)
    # Nível 5 = 9 digitos (1.01.01.01.01)
    max_digits = (max_level * 2) - 1

    # Formata lista de datas para SQL: ('2023-12-31', '2022-12-31')
    dates_str = "', '".join([str(d) for d in dates])

    query = f"""
    SELECT
        "CD_CONTA",
        "DS_CONTA",
        "DT_REFER",
        "VL_CONTA_TRATADO"
    FROM layer_02_silver.n1_dfp_cia_aberta_bp
    WHERE "CNPJ_CIA" = '{cnpj}'
      AND "DT_REFER" IN ('{dates_str}')
      AND LENGTH(REPLACE("CD_CONTA", '.', '')) <= {max_digits}
    ORDER BY "CD_CONTA", "DT_REFER";
    """

    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn)
    except Exception as e:
        st.error(f"Erro ao buscar dados do balanço: {e}")
        return pd.DataFrame()