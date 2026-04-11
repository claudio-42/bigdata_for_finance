# app.py
import streamlit as st
import os
from dotenv import load_dotenv

# Importações dos Módulos
from config import PAGE_CONFIG
from views.balanco_patrimonial import render_bp_page

# 1. Configuração Inicial (Deve ser a primeira linha Streamlit)
st.set_page_config(**PAGE_CONFIG)

# 2. Carrega Variáveis de Ambiente
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# 3. Sidebar
with st.sidebar:
    st.title("Data Lake CVM")
    st.caption("Disciplina: Big Data for Finance - FAE")

# 4. Visão Principal
render_bp_page()

# 5. Rodapé Global
st.markdown("---")
c1, c2 = st.columns([3, 1])
with c1: st.caption("Desenvolvido para fins didáticos de análise de dados CVM.")
with c2: st.caption("© 2025 Prof. Me. Ivan Ribeiro Mello")