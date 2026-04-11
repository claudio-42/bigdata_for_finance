# views/explorer.py
import streamlit as st
import pandas as pd
import plotly.express as px
from config import CORES_FAE
# Adicione as novas funções no import
from database import get_available_datasets, load_table_data, get_list_of_schemas, get_tables_in_schema

def render_explorer_page():
    # --- SIDEBAR DE NAVEGAÇÃO ---
    with st.sidebar:
        st.subheader("Configuração de Busca")
        
        # 1. Seleção do Schema (Dinâmico)
        schemas_disponiveis = get_list_of_schemas()
        # Tenta deixar 'layer_01_bronze' como padrão se existir
        idx_padrao = schemas_disponiveis.index('layer_01_bronze') if 'layer_01_bronze' in schemas_disponiveis else 0
        
        target_schema = st.selectbox(
            "Selecione a Camada (Schema):", 
            schemas_disponiveis, 
            index=idx_padrao
        )
        
        st.markdown("---")
        
        selected_table = None
        
        # LÓGICA HÍBRIDA:
        # Se for Bronze, usa a lógica de logs (dataset -> ano -> arquivo)
        # Se for Silver/Gold, usa a lógica de tabelas diretas
        
        if target_schema == 'layer_01_bronze':
            st.caption("📂 Modo: Navegação por Arquivos")
            dataset_type = st.selectbox("Tipo de Documento:", ['FRE', 'DFP', 'ITR', 'CAD'], index=0)
            
            df_catalog = get_available_datasets(dataset_type, schema=target_schema)
            
            if not df_catalog.empty:
                anos = sorted(df_catalog['ano_referencia'].unique(), reverse=True)
                sel_year = st.selectbox("Ano de Referência:", anos)
                
                tabelas_do_ano = df_catalog[df_catalog['ano_referencia'] == sel_year]
                selected_table = st.selectbox("Tabela / Arquivo:", tabelas_do_ano['tabela_destino'].unique())
            else:
                st.warning(f"Sem logs de carga em {target_schema}.")
                
        else:
            st.caption("🗃️ Modo: Navegação Direta")
            # Lista tabelas simples para Silver/Gold
            tabelas_schema = get_tables_in_schema(target_schema)
            
            if tabelas_schema:
                selected_table = st.selectbox("Selecione a Tabela:", tabelas_schema)
            else:
                st.warning(f"Nenhuma tabela encontrada em {target_schema}.")

    # --- ÁREA PRINCIPAL ---
    st.title(f"🔎 Explorador - {target_schema}")
    
    if selected_table:
        with st.spinner(f"Carregando {selected_table}..."):
            # Passamos o schema selecionado para a função de carga
            df = load_table_data(selected_table, schema=target_schema)
        
        if not df.empty:
            # MÉTRICAS DE TOPO
            c1, c2, c3 = st.columns(3)
            c1.metric("Linhas", f"{len(df):,}")
            c2.metric("Colunas", len(df.columns))
            memoria = df.memory_usage(deep=True).sum() / 1024**2
            c3.metric("Memória (DataFrame)", f"{memoria:.2f} MB")
            
            # ABAS
            tab1, tab2, tab3 = st.tabs(["📄 Dados Brutos", "📊 Visualização Rápida", "🔍 Estrutura"])
            
            with tab1:
                st.dataframe(df, use_container_width=True)
                st.download_button("Baixar CSV", df.to_csv(index=False).encode('utf-8'), f"{selected_table}.csv", "text/csv")
                
            with tab2:
                st.subheader("Análise Exploratória")
                cols_num = df.select_dtypes(include=['number']).columns.tolist()
                cols_txt = df.select_dtypes(include=['object', 'string']).columns.tolist()
                
                if cols_num or cols_txt:
                    cc1, cc2, cc3 = st.columns(3)
                    x = cc1.selectbox("Eixo X", cols_txt + cols_num)
                    # Eixo Y opcional para histogramas/contagens
                    y = cc2.selectbox("Eixo Y (Opcional)", cols_num) if cols_num else None
                    tipo = cc3.selectbox("Gráfico", ["Barra", "Linha", "Scatter", "Box", "Histograma"])
                    
                    try:
                        # Agregação automática se for muito grande
                        if len(df) > 5000 and y:
                            st.info("⚠️ Dados agregados (Média) para performance visual.")
                            df_viz = df.groupby(x)[y].mean().reset_index()
                        else:
                            df_viz = df.head(5000) # Limita para não travar o navegador
                        
                        if tipo == "Barra": 
                            fig = px.bar(df_viz, x=x, y=y) if y else px.bar(df_viz, x=x)
                        elif tipo == "Linha" and y: 
                            fig = px.line(df_viz, x=x, y=y)
                        elif tipo == "Scatter" and y: 
                            fig = px.scatter(df_viz, x=x, y=y)
                        elif tipo == "Box" and y: 
                            fig = px.box(df_viz, x=x, y=y)
                        elif tipo == "Histograma": 
                            fig = px.histogram(df_viz, x=x)
                        else:
                            fig = None
                            st.warning("Selecione um Eixo Y numérico para este gráfico.")

                        if fig:
                            fig.update_traces(marker_color=CORES_FAE['roxo'])
                            st.plotly_chart(fig, use_container_width=True)
                            
                    except Exception as e:
                        st.error(f"Não foi possível gerar o gráfico: {e}")
                else:
                    st.info("O dataset parece vazio ou sem colunas compatíveis.")
                    
            with tab3:
                st.markdown("### Tipagem dos Dados")
                st.table(pd.DataFrame({"Tipo Python": df.dtypes}).astype(str))
        else:
            st.warning("A tabela selecionada está vazia.")
    else:
        st.info("👈 Selecione um Schema e uma Tabela no menu lateral.")