# views/monitoring.py
import streamlit as st
import plotly.express as px
from datetime import datetime
from config import CORES_FAE  # Importando as cores globais
from database import get_lake_metadata

def render_monitoring_page():
    st.title("🏥 Saúde e Volumetria do Data Lake")
    st.markdown(f"**Status:** Atualizado em *{datetime.now().strftime('%d/%m/%Y às %H:%M')}*")
    
    df_auditoria = get_lake_metadata(schema='layer_01_bronze')
    
    if not df_auditoria.empty:
        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 Tabelas", len(df_auditoria))
        c2.metric("🔢 Total Linhas", f"{df_auditoria['qtd_linhas_int'].sum():,.0f}".replace(",", "."))
        c3.metric("💾 Tamanho Total", f"{df_auditoria['tamanho_gb'].sum():.2f} GB")
        c4.metric("🏆 Maior Tabela", f"{df_auditoria['tamanho_mb'].max():.1f} MB")
        
        st.markdown("---")
        
        # GRÁFICO
        df_viz = df_auditoria.head(15).copy()
        
        def definir_cor(idx):
            return '1. Líder' if idx == 0 else '2. Vice' if idx == 1 else '3. Outros'
        
        df_viz['categoria_cor'] = [definir_cor(i) for i in range(len(df_viz))]
        
        mapa_cores = {
            '1. Líder': CORES_FAE['roxo'], 
            '2. Vice': CORES_FAE['dourado'], 
            '3. Outros': CORES_FAE['azul_esverdeado']
        }
        
        fig = px.bar(
            df_viz, x='tamanho_mb', y='nome_tabela', 
            orientation='h', color='categoria_cor', 
            color_discrete_map=mapa_cores, text_auto='.1f',
            title="<b>Top 15 Tabelas por Tamanho (MB)</b>", height=600
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(plot_bgcolor='white', showlegend=False)
        fig.update_traces(textposition="inside", cliponaxis=False, textfont_color='black')
        
        col_graf, col_tab = st.columns([2, 1])
        with col_graf: st.plotly_chart(fig, use_container_width=True)
        with col_tab:
            st.subheader("🔍 Detalhes Técnicos")
            st.dataframe(df_auditoria[['nome_tabela', 'linhas_txt', 'total_disco_txt']], use_container_width=True, height=500)
    else:
        st.warning("⚠️ Nenhuma tabela encontrada. Rode o ETL.")