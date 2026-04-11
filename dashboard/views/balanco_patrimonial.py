# views/balanco_patrimonial.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots # <--- NOVO IMPORT NECESSÁRIO
from database import get_companies_bp, get_dates_bp, get_bp_data_filtered

# ==============================================================================
# FUNÇÕES AUXILIARES (UI & FORMATADORES)
# ==============================================================================

def formatar_moeda_br(valor):
    """
    Converte float para string no padrão brasileiro: 1.000,00
    """
    if pd.isna(valor):
        return "-"
    # 1. Formata com padrão americano (vírgula no milhar, ponto no decimal)
    texto = f"{valor:,.2f}"
    # 2. Faz a troca: Vírgula vira X, Ponto vira Vírgula, X vira Ponto
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")

def style_validation_row(val):
    """
    Pinta de vermelho se houver diferença contábil significativa, verde se zerado.
    """
    if isinstance(val, (int, float)):
        # Tolerância de 0.01 para erros de arredondamento
        if abs(val) > 0.01: 
            return 'background-color: #ffcccc; color: #cc0000; font-weight: bold'
        return 'background-color: #e6fffa; color: #006600; font-weight: bold'
    return ''

# ==============================================================================
# LÓGICA PRINCIPAL DA PÁGINA
# ==============================================================================

def render_bp_page():
    
    # --- 1. SIDEBAR: FILTROS E PARÂMETROS ---
    with st.sidebar:
        st.header("Filtros de Análise")
        
        # A. Seleção de Empresa
        df_empresas = get_companies_bp()
        if df_empresas.empty:
            st.warning("Base de dados indisponível.")
            return

        mapa_empresas = dict(zip(df_empresas['LABEL_DROPDOWN'], df_empresas['CNPJ_CIA']))
        
        selected_label = st.selectbox(
            "Selecione a Empresa:",
            options=df_empresas['LABEL_DROPDOWN'].tolist(),
            placeholder="Digite o nome..."
        )
        selected_cnpj = mapa_empresas[selected_label]
        
        st.markdown("---")

        # B. Seleção de Datas
        df_dates = get_dates_bp(selected_cnpj)
        available_dates = df_dates['DT_REFER'].astype(str).tolist()
        
        if not available_dates:
            st.error("Sem dados para esta empresa.")
            return

        # Padrão: Seleciona as 5 últimas datas disponíveis se possível
        selected_dates = st.multiselect(
            "Selecione os Períodos:",
            options=available_dates,
            default=available_dates[:5] if len(available_dates) >= 5 else available_dates
        )
        
        if not selected_dates:
            st.warning("Selecione pelo menos uma data.")
            return

        st.markdown("---")

        # C. Parâmetros Visuais
        level_selected = st.slider("Nível de Detalhe:", 1, 5, 3)
        scale_option = st.radio(
            "Escala de Valores:",
            ["Unidade (R$)", "Milhares (Mil)", "Milhões (MM)", "Bilhões (Bi)"],
            index=1
        )
        
        # Mapa de Escalas
        escala_map = {
            "Unidade (R$)": 1,
            "Milhares (Mil)": 1000,
            "Milhões (MM)": 1000000,
            "Bilhões (Bi)": 1000000000
        }
        divisor = escala_map[scale_option]

    # --- 2. CABEÇALHO DA PÁGINA ---
    nome_empresa = selected_label.split(' (')[0]
    st.title(f"{nome_empresa}")
    st.caption(f"**CNPJ:** {selected_cnpj} | **Análise de Balanço Patrimonial**")

    # --- 3. CARGA E TRANSFORMAÇÃO DE DADOS ---
    with st.spinner(f"Processando dados de {nome_empresa}..."):
        df_raw = get_bp_data_filtered(selected_cnpj, selected_dates, level_selected)
        
        if df_raw.empty:
            st.info("Nenhum dado encontrado.")
            return

        # Aplica escala
        df_raw['VL_CONTA_TRATADO'] = df_raw['VL_CONTA_TRATADO'] / divisor
        
        # Pivot: Linhas=Contas, Colunas=Datas
        df_pivot = df_raw.pivot_table(
            values='VL_CONTA_TRATADO',
            index=['CD_CONTA', 'DS_CONTA'],
            columns='DT_REFER',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Converte colunas Timestamp -> string 'YYYY-MM-DD' (DT_REFER vem como DATE do PostgreSQL)
        df_pivot.columns = [
            c.strftime('%Y-%m-%d') if hasattr(c, 'strftime') else c
            for c in df_pivot.columns
        ]

        # Garante que as colunas de data sejam strings ordenadas
        cols_dates = sorted([c for c in df_pivot.columns if c not in ['CD_CONTA', 'DS_CONTA']])

        # Reorganiza colunas finais
        df_pivot = df_pivot[['CD_CONTA', 'DS_CONTA'] + cols_dates]

    # --- 4. CÁLCULOS FINANCEIROS ---
    df_ativo = df_pivot[df_pivot['CD_CONTA'].str.startswith('1')].copy()
    df_passivo = df_pivot[df_pivot['CD_CONTA'].str.startswith('2')].copy()

    # Helpers para totais
    get_total = lambda df, code: df[df['CD_CONTA'] == code][cols_dates].iloc[0] if not df[df['CD_CONTA'] == code].empty else pd.Series(0, index=cols_dates)

    total_ativo = get_total(df_ativo, '1')
    total_passivo = get_total(df_passivo, '2')
    diff_check = total_ativo - total_passivo

    # --- CÁLCULO DE CRESCIMENTO (YoY e CAGR) ---
    var_pct = total_ativo.pct_change().fillna(0) # YoY

    # CAGR Total
    if len(total_ativo) >= 2:
        val_inicial = total_ativo.iloc[0]
        val_final = total_ativo.iloc[-1]
        anos = len(total_ativo) - 1
        if val_inicial > 0:
            cagr_val = (val_final / val_inicial) ** (1/anos) - 1
        else:
            cagr_val = 0
    else:
        cagr_val = 0

    # Cria linha de validação para a tabela final
    row_check = pd.DataFrame([diff_check.tolist()], columns=cols_dates)
    row_check.insert(0, 'DS_CONTA', 'Diferença (Ativo - Passivo)')

    # --- 5. VISUALIZAÇÃO: TABELAS DE DETALHE ---
    
    col_config_dates = {col: st.column_config.TextColumn(col, width="small") for col in cols_dates}
    
    col_config_base = {
        "CD_CONTA": st.column_config.TextColumn("Conta", width="small"),
        "DS_CONTA": st.column_config.TextColumn("Descrição", width="medium"),
        **col_config_dates
    }

    def show_table(df_input, header_emoji, header_title):
        st.subheader(f"{header_emoji} {header_title} ({scale_option})")
        df_view = df_input.copy()
        for c in cols_dates:
            df_view[c] = df_view[c].apply(formatar_moeda_br)
            
        # --- CÁLCULO MÁGICO DE ALTURA ---
        # 35px por linha de dados + 38px do cabeçalho + 3px de borda/folga
        # Limitamos a 600px para não ficar infinito se tiver 1000 linhas (cria scroll nesse caso)
        altura_dinamica = (len(df_view) + 1) * 35 + 3
        
        # Opcional: Trava em um máximo se quiser (ex: max(altura, 600))
        # Se quiser mostrar TUDO sem scroll nunca, remova a função min()
        
        st.dataframe(
            df_view,
            hide_index=True,
            use_container_width=True,
            column_config=col_config_base,
            height=altura_dinamica # <--- AQUI A MÁGICA
        )

    show_table(df_ativo, "🟢", "Ativo")
    st.markdown("###")
    show_table(df_passivo, "🔴", "Passivo e Patrimônio Líquido")
    st.markdown("###")

    # --- 6. VISUALIZAÇÃO: GRÁFICO AVANÇADO (SUBPLOTS) ---
    st.subheader("✅ Validação e Crescimento")
    
    eixo_x_str = [str(d) for d in cols_dates] 

    # --- CÁLCULO DINÂMICO DE ESCALA (RESPONSIVIDADE) ---
    # 1. Finanças: Pega o maior valor e adiciona 25% de folga para caber os rótulos
    max_valor_fin = max(total_ativo.max(), total_passivo.max())
    range_fin = [-max_valor_fin * 1.25, max_valor_fin * 1.25]

    # 2. Porcentagem: Pega a maior variação e adiciona 35% de folga
    max_valor_pct = var_pct.abs().max()
    if pd.isna(max_valor_pct) or max_valor_pct == 0: max_valor_pct = 0.10
    range_pct = [-max_valor_pct * 1.35, max_valor_pct * 1.35]
    # ---------------------------------------------------

    # --- CRIAÇÃO DO SUBPLOT ---
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.20, # <--- AUMENTADO (De 0.15 para 0.20) para separar bem os gráficos
        row_heights=[0.70, 0.30], # Leve ajuste para dar mais peso ao gráfico de barras
        subplot_titles=(f"Equilíbrio Patrimonial ({scale_option})", "Variação do Ativo (YoY)")
    )

    # Estilo dos Rótulos
    fonte_rotulos = dict(color='black', size=15, family="Arial")

    # --- ROW 1: BARRAS (ATIVO/PASSIVO) ---
    fig.add_trace(go.Bar(
        x=eixo_x_str,
        y=total_ativo.values,
        name='Ativo Total',
        marker_color='#2E8B57',
        text=[formatar_moeda_br(v) for v in total_ativo.values], 
        textposition='outside',
        textfont=fonte_rotulos,
        hovertemplate='Ativo: %{y:,.2f}<extra></extra>'
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=eixo_x_str,
        y=total_passivo.values * -1, 
        name='Passivo + PL',
        marker_color='#CD5C5C',
        text=[formatar_moeda_br(v) for v in total_passivo.values],
        textposition='outside',
        textfont=fonte_rotulos,
        hovertemplate='Passivo: %{text}<extra></extra>'
    ), row=1, col=1)

    # --- ROW 2: LINHA (CRESCIMENTO) ---
    fig.add_trace(go.Scatter(
        x=eixo_x_str,
        y=var_pct.values,
        name='Crescimento (%)',
        mode='lines+markers+text',
        line=dict(color='#00008B', width=3),
        marker=dict(size=8, symbol='circle', color='#00008B'),
        text=[f"{v:.1%}" if i > 0 else "" for i, v in enumerate(var_pct.values)], 
        textposition="bottom center",
        textfont=dict(color='#00008B', size=15, weight='bold'),
        hovertemplate='Crescimento: %{y:.2%}<extra></extra>'
    ), row=2, col=1)

    # --- LAYOUT FINAL ---
    fig.update_layout(
        # Título Geral
        title=dict(
            text=f"Análise de Evolução | CAGR de Ativo Total do Período Selecionado: {cagr_val:.1%}",
            font=dict(size=20),
            x=0.01,   # Alinhado à esquerda
            y=0.98,   # Bem no topo da área da figura
            xanchor='left',
            yanchor='top'
        ),
        barmode='relative',
        plot_bgcolor='white',
        height=800, # Aumentei altura total para acomodar os espaços
        showlegend=True,
        
        # LEGENDA: POSICIONAMENTO CRÚRGICO
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.95,          # Sobe bem a legenda (entra na margem superior)
            xanchor="center",
            x=0.5,
            bgcolor='rgba(255,255,255,0)',
            font=dict(color="black", size=12)
        ),
        
        # MARGENS: A chave para não sobrepor
        # t=160 cria um "cabeçalho" branco gigante onde cabem Título + Legenda + Título do Subplot 1
        margin=dict(t=160, b=50, l=50, r=50), 
    )

    # --- FORMATAÇÃO DOS EIXOS ---
    
    # Eixo Y da Linha 1 (Barras)
    fig.update_yaxes(
        title_text="Valor Monetário",
        showgrid=True, gridcolor='#eee', zeroline=True, zerolinecolor='black',
        range=range_fin, # <--- APLICA O CÁLCULO DE RESPONSIVIDADE AQUI
        row=1, col=1
    )
    # Linha Zero Forte
    fig.add_shape(type='line', y0=0, y1=0, x0=-0.5, x1=len(cols_dates)-0.5, 
                  line=dict(color='black', width=1.5), row=1, col=1)

    # Eixo Y da Linha 2 (Crescimento)
    fig.update_yaxes(
        title_text="Crescimento (%)",
        tickformat='.0%',
        showgrid=True, gridcolor='#eee', zeroline=True, zerolinecolor='gray',
        range=range_pct, # <--- APLICA O CÁLCULO DE RESPONSIVIDADE AQUI
        row=2, col=1
    )
    # Linha Zero Pontilhada
    fig.add_shape(type='line', y0=0, y1=0, x0=-0.5, x1=len(cols_dates)-0.5, 
                  line=dict(color='gray', width=1, dash='dot'), row=2, col=1)
    
    fig.update_xaxes(type='category', row=1, col=1)
    fig.update_xaxes(type='category', row=2, col=1)
    
    # Ajuste manual da posição dos Títulos dos Subplots (Annotations)
    # Isso garante que eles fiquem no lugar certo
    fig.update_annotations(
        x=0,             # Força a posição para o início do eixo X (0 = Esquerda)
        xanchor='left',  # Ancora o texto pela esquerda (ele cresce para a direita)
        font_size=16,    # Tamanho da fonte
        yshift=30        # Sobe o título 30 pixels para desgrudar do gráfico (ajuste conforme gosto)
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 7. NOTA EXPLICATIVA ---
    with st.expander("ℹ️ Entenda as Métricas de Crescimento"):
        st.markdown(f"""
        **1. CAGR ({cagr_val:.1%}):** *Compound Annual Growth Rate* (Taxa de Crescimento Anual Composta). 
        Representa a taxa de retorno necessária para um investimento crescer do seu saldo inicial para o saldo final, assumindo que os lucros foram reinvestidos ao final de cada ano da vida do investimento.
        
        $ \\displaystyle CAGR = \\left( \\frac{{Valor_{{Final}}}}{{Valor_{{Inicial}}}} \\right)^{{\\frac{{1}}{{n}}}} - 1 $
        
        Onde:
        * **$Valor_{{Final}}$**: Valor do Ativo Total no último período selecionado.
        * **$Valor_{{Inicial}}$**: Valor do Ativo Total no primeiro período selecionado.
        * **$n$**: Número de anos (ou períodos) decorridos.

        ---
        **2. Crescimento do Ativo Total (Linha Azul - YoY):** *Year over Year*. É a variação percentual simples do Ativo em relação ao período imediatamente anterior (mostrada no gráfico inferior).
        """)

    # --- 8. TABELA DE CHECK FINAL ---
    st.dataframe(
        row_check.style
            .map(style_validation_row, subset=cols_dates)
            .format(formatar_moeda_br, subset=cols_dates),
        hide_index=True,
        use_container_width=True,
        column_config={
            "DS_CONTA": st.column_config.TextColumn("Status da Validação", width="large"),
            **col_config_dates
        }
    )

    if diff_check.abs().max() > 0.1:
        st.error(f"⚠️ Existem divergências contábeis significativas na escala {scale_option}!")
    else:
        st.success("Balanço validado: Ativo = Passivo + PL em todos os períodos.")