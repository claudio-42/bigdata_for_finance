# ==============================================================================
#  MINERVA FOODS (BEEF3) — Análise de Indicadores Financeiros
#  Dashboard Streamlit (ARQUIVO ÚNICO) — Big Data for Finance
# ------------------------------------------------------------------------------
#  Lê a camada Gold (layer_03_gold.mart_indicadores_financeiros) e apresenta,
#  em várias abas, KPIs, diagnóstico automático e gráficos por grupo de
#  indicadores, com a identidade visual da Minerva Foods.
#
#  Como rodar:
#     pip install streamlit plotly pandas sqlalchemy psycopg2-binary python-dotenv
#     streamlit run app.py
#
#  .env esperado (mesma pasta ou pasta-pai):
#     DB_USER=...  DB_PASS=...  DB_HOST=localhost  DB_PORT=5432  DB_NAME=...
# ==============================================================================
import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ==============================================================================
# 0. IDENTIDADE VISUAL — MINERVA FOODS
#    Cores oficiais aprox.: vermelho #E84752 | grafite #2B3D4A
#    O cabeçalho usa wordmark tipográfico (não reproduz o logotipo oficial).
# ==============================================================================
C = {
    "vermelho": "#E84752", "vermelho_escuro": "#C1323D", "vermelho_claro": "#F6B3B8",
    "grafite": "#2B3D4A", "grafite_claro": "#3E5463", "creme": "#FBF8F4",
    "cinza": "#6B7280", "cinza_borda": "#E5E7EB",
    "verde": "#1E9E5A", "ambar": "#D97706", "vermelho_risco": "#DC2626",
}

GOLD_TABLE = "layer_03_gold.mart_indicadores_financeiros"
MINERVA_CNPJ = "67.620.377/0001-14"   # Minerva S.A. (BEEF3)

# Demonstrações contábeis hierárquicas (camada Silver) — schema idêntico nas três:
#   CNPJ_CIA, DENOM_CIA, CD_CONTA, DS_CONTA, DT_REFER, VL_CONTA_TRATADO, GRUPO_DFP
# O pipeline Silver já filtra ORDEM_EXERC = 'ÚLTIMO' (sem mistura de exercícios).
SILVER_BP  = "layer_02_silver.n1_dfp_cia_aberta_bp"
SILVER_DRE = "layer_02_silver.n1_dfp_cia_aberta_dre"
SILVER_DFC = "layer_02_silver.n1_dfp_cia_aberta_dfc"


def css_minerva() -> str:
    return f"""
    <style>
        .stApp {{ background-color: {C['creme']}; }}
        h1,h2,h3,h4 {{ color: {C['grafite']}; font-weight: 700; }}
        .mnv-topbar {{
            background: linear-gradient(135deg, {C['grafite']} 0%, {C['grafite_claro']} 100%);
            border-radius: 14px; padding: 22px 28px; margin-bottom: 8px;
            display:flex; align-items:center; justify-content:space-between;
            box-shadow: 0 6px 18px rgba(43,61,74,0.18); }}
        .mnv-word {{ font-size:30px; font-weight:800; letter-spacing:3px; color:#fff; line-height:1; }}
        .mnv-word .dot {{ color: {C['vermelho']}; }}
        .mnv-sub {{ font-size:12px; letter-spacing:4px; color:{C['vermelho_claro']}; margin-top:4px; }}
        .mnv-badge {{ background:{C['vermelho']}; color:#fff; font-weight:700; font-size:13px;
                      padding:6px 14px; border-radius:20px; letter-spacing:1px; }}
        .mnv-tag {{ color:#cbd5e1; font-size:12px; text-align:right; margin-top:8px; }}
        .mnv-card {{ background:#fff; border-radius:14px; padding:16px 18px;
                     border:1px solid {C['cinza_borda']}; border-top:4px solid {C['vermelho']};
                     box-shadow:0 2px 8px rgba(43,61,74,0.06); height:100%; }}
        .mnv-card .lbl {{ font-size:12px; color:{C['cinza']}; text-transform:uppercase; letter-spacing:.5px; }}
        .mnv-card .val {{ font-size:26px; font-weight:800; color:{C['grafite']}; margin:4px 0; }}
        .mnv-card .dlt-pos {{ color:{C['verde']}; font-size:13px; font-weight:600; }}
        .mnv-card .dlt-neg {{ color:{C['vermelho_risco']}; font-size:13px; font-weight:600; }}
        .mnv-card .dlt-neu {{ color:{C['cinza']}; font-size:13px; font-weight:600; }}
        .mnv-insight {{ background:#fff; border-left:5px solid {C['vermelho']};
                        border-radius:0 10px 10px 0; padding:14px 18px; margin:8px 0;
                        box-shadow:0 2px 8px rgba(43,61,74,0.05); }}
        .mnv-insight.good {{ border-left-color:{C['verde']}; }}
        .mnv-insight.warn {{ border-left-color:{C['ambar']}; }}
        .mnv-insight.bad  {{ border-left-color:{C['vermelho_risco']}; }}
        .mnv-pill {{ display:inline-block; font-size:11px; font-weight:700; padding:2px 9px;
                     border-radius:12px; color:#fff; margin-right:8px; vertical-align:middle; }}
    </style>
    """


def header_html(razao: str, setor: str, periodo: str) -> str:
    return f"""
    <div class="mnv-topbar">
        <div>
            <div class="mnv-word">MINERVA<span class="dot">.</span>FOODS</div>
            <div class="mnv-sub">ANÁLISE DE INDICADORES FINANCEIROS</div>
        </div>
        <div>
            <span class="mnv-badge">BEEF3</span>
            <div class="mnv-tag">{razao}<br>{setor} &nbsp;|&nbsp; {periodo}</div>
        </div>
    </div>
    """


def layout_base(titulo: str = "", altura: int = 420) -> dict:
    return dict(
        title=dict(text=titulo, font=dict(size=17, color=C["grafite"], family="Arial"), x=0.01, xanchor="left"),
        height=altura, plot_bgcolor="white", paper_bgcolor="white",
        font=dict(color=C["grafite"], family="Arial"),
        margin=dict(t=64, b=48, l=56, r=28),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
        hoverlabel=dict(bgcolor=C["grafite"], font=dict(color="white")),
    )


# ==============================================================================
# 1. METADADOS DOS INDICADORES
#    unidade: 'idx' (índice ×) | 'pct' (razão→%) | 'vezes' | 'dias' | 'rs' | 'rs_ac'
#    melhor : 'alto' | 'baixo' | 'neutro'
# ==============================================================================
INDICADORES = {
    "IND_LIQUIDEZ_GERAL":     dict(label="Liquidez Geral",       grupo="Liquidez",       unidade="idx",   melhor="alto"),
    "IND_LIQUIDEZ_CORRENTE":  dict(label="Liquidez Corrente",    grupo="Liquidez",       unidade="idx",   melhor="alto"),
    "IND_LIQUIDEZ_SECA":      dict(label="Liquidez Seca",        grupo="Liquidez",       unidade="idx",   melhor="alto"),
    "IND_LIQUIDEZ_IMEDIATA":  dict(label="Liquidez Imediata",    grupo="Liquidez",       unidade="idx",   melhor="alto"),
    "IND_PCT_CP":             dict(label="Cap. Terceiros / Cap. Próprio", grupo="Endividamento", unidade="pct", melhor="baixo"),
    "IND_PCT_AT":             dict(label="Cap. Terceiros / Ativo Total",  grupo="Endividamento", unidade="pct", melhor="baixo"),
    "IND_GARANTIA_CT":        dict(label="Garantia Cap. Próprio",         grupo="Endividamento", unidade="pct", melhor="alto"),
    "IND_COMPOSICAO_ENDIV":   dict(label="Composição do Endividamento",   grupo="Endividamento", unidade="pct", melhor="baixo"),
    "IND_IMOB_CP":            dict(label="Imobilização Cap. Próprio",     grupo="Endividamento", unidade="pct", melhor="baixo"),
    "IND_IMOB_AT":            dict(label="Imobilização Ativo Total",      grupo="Endividamento", unidade="pct", melhor="neutro"),
    "IND_MARGEM_BRUTA":       dict(label="Margem Bruta",         grupo="Margens",        unidade="pct",   melhor="alto"),
    "IND_MARGEM_OPERACIONAL": dict(label="Margem Operacional",   grupo="Margens",        unidade="pct",   melhor="alto"),
    "IND_MARGEM_LIQUIDA":     dict(label="Margem Líquida",       grupo="Margens",        unidade="pct",   melhor="alto"),
    "IND_LPA_DILUIDO":        dict(label="LPA (Diluído)",        grupo="Margens",        unidade="rs_ac", melhor="alto"),
    "IND_ROA":                dict(label="ROA",                  grupo="Rentabilidade",  unidade="pct",   melhor="alto"),
    "IND_ROE":                dict(label="ROE",                  grupo="Rentabilidade",  unidade="pct",   melhor="alto"),
    "IND_ROI":                dict(label="ROI",                  grupo="Rentabilidade",  unidade="pct",   melhor="alto"),
    "IND_GIRO_ESTOQUES":      dict(label="Giro de Estoques",     grupo="Atividade",      unidade="vezes", melhor="alto"),
    "IND_GIRO_CR":            dict(label="Giro Contas a Receber",grupo="Atividade",      unidade="vezes", melhor="alto"),
    "IND_GIRO_CP":            dict(label="Giro Contas a Pagar",  grupo="Atividade",      unidade="vezes", melhor="neutro"),
    "IND_GIRO_AC":            dict(label="Giro Ativo Circulante",grupo="Atividade",      unidade="vezes", melhor="alto"),
    "IND_PMRE":               dict(label="PMRE",                 grupo="Atividade",      unidade="dias",  melhor="baixo"),
    "IND_PMRV":               dict(label="PMRV",                 grupo="Atividade",      unidade="dias",  melhor="baixo"),
    "IND_PMPC":               dict(label="PMPC",                 grupo="Atividade",      unidade="dias",  melhor="alto"),
    "IND_PMRAC":              dict(label="PMRAC",                grupo="Atividade",      unidade="dias",  melhor="baixo"),
    "IND_CICLO_ECONOMICO":    dict(label="Ciclo Econômico",      grupo="Ciclos",         unidade="dias",  melhor="baixo"),
    "IND_CICLO_FINANCEIRO":   dict(label="Ciclo Financeiro",     grupo="Ciclos",         unidade="dias",  melhor="baixo"),
    "IND_CGL":                dict(label="Capital de Giro Líquido (CGL)",     grupo="Fleuriet", unidade="rs", melhor="alto"),
    "IND_NCG":                dict(label="Necessidade de Cap. de Giro (NCG)", grupo="Fleuriet", unidade="rs", melhor="neutro"),
    "IND_ST":                 dict(label="Saldo de Tesouraria (ST)",          grupo="Fleuriet", unidade="rs", melhor="alto"),
}


# ==============================================================================
# 2. FORMATAÇÃO (padrão brasileiro)
# ==============================================================================
def _br(v, casas=2):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "N/A"
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_rs(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "N/A"
    sinal = "-" if v < 0 else ""
    a = abs(v)
    if a >= 1e9: return f"{sinal}R$ {_br(a/1e9, 2)} bi"
    if a >= 1e6: return f"{sinal}R$ {_br(a/1e6, 1)} mi"
    if a >= 1e3: return f"{sinal}R$ {_br(a/1e3, 1)} mil"
    return f"{sinal}R$ {_br(a, 0)}"


def fmt_valor(v, unidade):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "N/A"
    if unidade in ("idx", "vezes"): return f"{_br(v, 2)}×"
    if unidade == "pct":   return f"{_br(v * 100, 1)}%"
    if unidade == "dias":  return f"{_br(v, 0)} dias"
    if unidade == "rs_ac": return f"R$ {_br(v, 2)}"
    if unidade == "rs":    return fmt_rs(v)
    return _br(v)


def fmt_delta(chave, atual, anterior):
    """Variação a/a → (texto, classe) com classe ∈ {pos, neg, neu} (melhora/piora)."""
    if atual is None or anterior is None or np.isnan(atual) or np.isnan(anterior) or anterior == 0:
        return "—", "neu"
    var = (atual - anterior) / abs(anterior)
    txt = f"{'+' if var >= 0 else ''}{_br(var * 100, 1)}% a/a"
    melhor = INDICADORES.get(chave, {}).get("melhor", "neutro")
    if melhor == "neutro" or abs(var) < 0.001:
        classe = "neu"
    elif (var > 0 and melhor == "alto") or (var < 0 and melhor == "baixo"):
        classe = "pos"
    else:
        classe = "neg"
    return txt, classe


def delta_monetario(atual, anterior):
    if atual is None or anterior is None or np.isnan(atual) or np.isnan(anterior) or anterior == 0:
        return "—", "neu"
    var = (atual - anterior) / abs(anterior)
    txt = f"{'+' if var >= 0 else ''}{_br(var * 100, 1)}% a/a"
    if abs(var) < 0.001:
        return txt, "neu"
    return txt, ("pos" if var > 0 else "neg")


# ==============================================================================
# 3. CLASSIFICAÇÃO POR BENCHMARK (fundamentada no racional do projeto)
# ==============================================================================
def classificar(chave, v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "info"
    if chave == "IND_LIQUIDEZ_CORRENTE":  return "good" if v >= 1.5 else ("warn" if v >= 1.0 else "bad")
    if chave == "IND_LIQUIDEZ_GERAL":     return "good" if v >= 1.0 else ("warn" if v >= 0.8 else "bad")
    if chave == "IND_LIQUIDEZ_SECA":      return "good" if v >= 1.0 else ("warn" if v >= 0.7 else "bad")
    if chave == "IND_LIQUIDEZ_IMEDIATA":  return "good" if v >= 0.30 else ("warn" if v >= 0.10 else "bad")
    if chave == "IND_PCT_CP":             return "good" if v <= 1.0 else ("warn" if v <= 2.0 else "bad")
    if chave == "IND_COMPOSICAO_ENDIV":   return "good" if v <= 0.4 else ("warn" if v <= 0.6 else "bad")
    if chave == "IND_IMOB_CP":            return "good" if v <= 1.0 else ("warn" if v <= 1.3 else "bad")
    if chave == "IND_MARGEM_LIQUIDA":     return "good" if v >= 0.05 else ("warn" if v >= 0 else "bad")
    if chave == "IND_MARGEM_OPERACIONAL": return "good" if v >= 0.07 else ("warn" if v >= 0 else "bad")
    if chave in ("IND_ROE", "IND_ROA", "IND_ROI"): return "good" if v >= 0.10 else ("warn" if v >= 0 else "bad")
    if chave == "IND_ST":                 return "good" if v > 0 else "bad"
    if chave == "IND_CICLO_FINANCEIRO":   return "good" if v <= 60 else ("warn" if v <= 120 else "bad")
    return "info"


# ==============================================================================
# 4. UTILITÁRIOS DE SÉRIE
# ==============================================================================
def serie(df, chave):
    if chave not in df.columns:
        return pd.Series(dtype=float)
    return df.set_index("ANO")[chave].sort_index()


def ultimo(df, chave):
    s = serie(df, chave).dropna()
    return (s.index[-1], s.iloc[-1]) if len(s) else (None, np.nan)


def tendencia(s):
    s = s.dropna()
    if len(s) < 2:
        return "insuf"
    var = s.iloc[-1] - s.iloc[0]
    base = abs(s.iloc[0]) if s.iloc[0] != 0 else 1
    if abs(var) / base < 0.05:
        return "estável"
    return "subindo" if var > 0 else "caindo"


def detecta_efeito_tesoura(df):
    s = serie(df, "IND_ST").dropna()
    if len(s) < 3:
        return False
    ult = s.iloc[-3:]
    decrescente = all(ult.iloc[i] > ult.iloc[i + 1] for i in range(len(ult) - 1))
    return decrescente and ult.iloc[-1] < 0


# ==============================================================================
# 5. DIAGNÓSTICO EXECUTIVO (análises inteligentes; cada item marcado por grupo)
# ==============================================================================
def gerar_diagnostico(df):
    ins = []

    def add(grupo, nivel, titulo, texto):
        ins.append(dict(grupo=grupo, nivel=nivel, titulo=titulo, texto=texto))

    ano_lc, lc = ultimo(df, "IND_LIQUIDEZ_CORRENTE")
    if not np.isnan(lc):
        nv = classificar("IND_LIQUIDEZ_CORRENTE", lc)
        tend = tendencia(serie(df, "IND_LIQUIDEZ_CORRENTE"))
        base = (f"A liquidez corrente em {ano_lc} é de {fmt_valor(lc,'idx')}, ou seja, R$ {_br(lc,2)} de "
                f"ativo circulante para cada R$ 1,00 de dívida de curto prazo.")
        if nv == "good":
            txt = base + " Está acima da referência confortável de 1,5×, indicando folga para honrar obrigações imediatas."
        elif nv == "warn":
            txt = base + " Situa-se entre 1,0× e 1,5× — cobre o curto prazo, mas com margem apertada para um frigorífico de ciclo longo."
        else:
            txt = base + " Abaixo de 1,0×, sinaliza que o passivo circulante supera o ativo circulante — pressão de caixa relevante."
        if tend != "insuf":
            txt += f" A trajetória recente é de {('melhora' if tend=='subindo' else 'piora' if tend=='caindo' else 'estabilidade')} do índice."
        add("Liquidez", nv, "Liquidez de curto prazo", txt)

    ano_e, pct_cp = ultimo(df, "IND_PCT_CP")
    _, comp = ultimo(df, "IND_COMPOSICAO_ENDIV")
    if not np.isnan(pct_cp):
        nv = classificar("IND_PCT_CP", pct_cp)
        txt = f"Em {ano_e}, o capital de terceiros equivale a {fmt_valor(pct_cp,'pct')} do capital próprio. "
        if pct_cp > 2.0:
            txt += "É uma estrutura fortemente alavancada — comum em frigoríficos pela necessidade de capital de giro e CAPEX, mas que amplia o risco financeiro."
        elif pct_cp > 1.0:
            txt += "A dependência de terceiros supera o capital próprio, padrão típico do setor de proteína animal, intensivo em capital."
        else:
            txt += "O capital próprio ainda supera o de terceiros — estrutura relativamente conservadora para o setor."
        if not np.isnan(comp):
            txt += (f" Da dívida total, {fmt_valor(comp,'pct')} vence no curto prazo"
                    + (" — concentração elevada, que exige liquidez para rolagem." if comp > 0.6
                       else " — perfil de prazo equilibrado."))
        add("Endividamento", nv, "Estrutura de capital e endividamento", txt)

    ano_r, roe = ultimo(df, "IND_ROE")
    _, roa = ultimo(df, "IND_ROA")
    _, pl = ultimo(df, "V12_PL")
    if not np.isnan(roe):
        if not np.isnan(pl) and pl < 0:
            add("Rentabilidade", "bad", "Rentabilidade sobre o patrimônio",
                f"O Patrimônio Líquido está negativo em {ano_r} ({fmt_rs(pl)}). Nesse cenário o ROE perde "
                f"significado econômico e deve ser interpretado junto ao ROA e à estrutura de capital.")
        else:
            nv = classificar("IND_ROE", roe)
            txt = f"O ROE de {ano_r} é de {fmt_valor(roe,'pct')}"
            if not np.isnan(roa):
                spread = (roe - roa) * 100
                txt += (f", contra um ROA de {fmt_valor(roa,'pct')}. O diferencial de {_br(spread,1)} p.p. reflete o "
                        f"{'efeito favorável' if spread > 0 else 'efeito desfavorável'} da alavancagem: a dívida "
                        f"{'amplia' if spread > 0 else 'corrói'} o retorno do acionista.")
            else:
                txt += "."
            add("Rentabilidade", nv, "Rentabilidade sobre o patrimônio", txt)

    ano_m, ml = ultimo(df, "IND_MARGEM_LIQUIDA")
    if not np.isnan(ml):
        nv = classificar("IND_MARGEM_LIQUIDA", ml)
        txt = (f"A margem líquida de {ano_m} é de {fmt_valor(ml,'pct')}. O setor de carne bovina opera "
               f"estruturalmente com margens estreitas e alta sensibilidade ao ciclo do boi, ao câmbio (forte "
               f"componente exportador) e ao preço da proteína. ")
        if ml < 0:
            txt += "O resultado negativo no período indica que custos e despesas superaram a receita líquida."
        elif ml < 0.05:
            txt += "Margem baixa, mas dentro do que se espera para um frigorífico de grande escala."
        else:
            txt += "Margem saudável para o padrão do setor."
        add("Margens", nv, "Margem e contexto setorial", txt)

    ano_c, cf = ultimo(df, "IND_CICLO_FINANCEIRO")
    if not np.isnan(cf):
        nv = classificar("IND_CICLO_FINANCEIRO", cf)
        if cf < 0:
            txt = (f"O ciclo financeiro de {ano_c} é negativo ({_br(cf,0)} dias): a empresa recebe das vendas antes "
                   f"de pagar fornecedores, situação de autofinanciamento operacional.")
        else:
            txt = (f"O ciclo financeiro de {ano_c} é de {fmt_valor(cf,'dias')} — período em que o caixa fica "
                   f"comprometido entre pagar fornecedores e receber das vendas. Para frigoríficos, o estoque inclui "
                   f"ativos biológicos (conta 1.01.07 consolidada ao estoque padrão), o que tende a alongar o PMRE e o ciclo.")
        add("Ciclos", nv, "Ciclo financeiro e capital de giro", txt)

    ano_st, st_v = ultimo(df, "IND_ST")
    _, cgl = ultimo(df, "IND_CGL")
    _, ncg = ultimo(df, "IND_NCG")
    if not np.isnan(st_v):
        if detecta_efeito_tesoura(df):
            add("Fleuriet", "bad", "Alerta: possível Efeito Tesoura",
                f"O Saldo de Tesouraria vem se deteriorando de forma sucessiva e está negativo em {ano_st} "
                f"({fmt_rs(st_v)}). A configuração clássica do Efeito Tesoura indica que a NCG cresce mais rápido que "
                f"o CGL, exigindo financiamento de curto prazo crescente — sinal de atenção para a saúde financeira.")
        else:
            nv = "good" if st_v > 0 else "warn"
            txt = f"O Saldo de Tesouraria de {ano_st} é {fmt_rs(st_v)}"
            if not np.isnan(ncg) and not np.isnan(cgl):
                txt += (f", resultado de um CGL de {fmt_rs(cgl)} frente a uma NCG de {fmt_rs(ncg)}. "
                        f"{'A folga financeira cobre a necessidade operacional de giro.' if st_v > 0 else 'A necessidade de giro consome a folga de curto prazo, exigindo recursos onerosos.'}")
            else:
                txt += "."
            add("Fleuriet", nv, "Modelo dinâmico (Fleuriet)", txt)

    return ins


# ==============================================================================
# 6. GRÁFICOS (Plotly)
# ==============================================================================
def fig_liquidez(df):
    fig = go.Figure()
    mapa = {"IND_LIQUIDEZ_GERAL": C["grafite"], "IND_LIQUIDEZ_CORRENTE": C["vermelho"],
            "IND_LIQUIDEZ_SECA": C["ambar"], "IND_LIQUIDEZ_IMEDIATA": C["grafite_claro"]}
    for chave, cor in mapa.items():
        s = serie(df, chave)
        fig.add_trace(go.Scatter(x=[str(a) for a in s.index], y=s.values, mode="lines+markers",
                                 name=INDICADORES[chave]["label"], line=dict(color=cor, width=3),
                                 marker=dict(size=7), hovertemplate="%{y:.2f}×<extra></extra>"))
    fig.add_hline(y=1.5, line=dict(color=C["verde"], width=1.4, dash="dash"),
                  annotation_text="Confortável (1,5×)", annotation_position="top left")
    fig.add_hline(y=1.0, line=dict(color=C["ambar"], width=1.4, dash="dot"),
                  annotation_text="Mínimo (1,0×)", annotation_position="bottom left")
    fig.update_layout(**layout_base("Índices de Liquidez (×)"))
    fig.update_xaxes(type="category", gridcolor=C["cinza_borda"])
    fig.update_yaxes(gridcolor=C["cinza_borda"], zeroline=True, zerolinecolor=C["cinza"])
    return fig


def fig_endividamento(df):
    fig = go.Figure()
    for chave, cor in [("IND_PCT_AT", C["vermelho"]), ("IND_COMPOSICAO_ENDIV", C["ambar"]),
                       ("IND_IMOB_AT", C["grafite"])]:
        s = serie(df, chave)
        fig.add_trace(go.Bar(x=[str(a) for a in s.index], y=(s.values * 100),
                             name=INDICADORES[chave]["label"], marker_color=cor,
                             hovertemplate="%{y:.1f}%<extra></extra>"))
    fig.update_layout(**layout_base("Estrutura de Capital e Endividamento (%)"), barmode="group")
    fig.update_xaxes(type="category", gridcolor=C["cinza_borda"])
    fig.update_yaxes(ticksuffix="%", gridcolor=C["cinza_borda"])
    return fig


def fig_margens_rentab(df):
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Margens (%)", "Rentabilidade (%)"))
    for chave, cor in [("IND_MARGEM_BRUTA", C["grafite"]), ("IND_MARGEM_OPERACIONAL", C["ambar"]),
                       ("IND_MARGEM_LIQUIDA", C["vermelho"])]:
        s = serie(df, chave)
        fig.add_trace(go.Scatter(x=[str(a) for a in s.index], y=s.values * 100, mode="lines+markers",
                                 name=INDICADORES[chave]["label"], line=dict(color=cor, width=3),
                                 hovertemplate="%{y:.1f}%<extra></extra>"), row=1, col=1)
    for chave, cor in [("IND_ROA", C["grafite"]), ("IND_ROE", C["vermelho"]), ("IND_ROI", C["ambar"])]:
        s = serie(df, chave)
        fig.add_trace(go.Scatter(x=[str(a) for a in s.index], y=s.values * 100, mode="lines+markers",
                                 name=INDICADORES[chave]["label"], line=dict(color=cor, width=3),
                                 hovertemplate="%{y:.1f}%<extra></extra>"), row=1, col=2)
    fig.update_layout(**layout_base("", altura=440))
    fig.update_xaxes(type="category", gridcolor=C["cinza_borda"])
    fig.update_yaxes(ticksuffix="%", gridcolor=C["cinza_borda"], zeroline=True, zerolinecolor=C["cinza"])
    return fig


def fig_ciclos(df):
    fig = go.Figure()
    for chave, cor in [("IND_PMRE", C["vermelho_claro"]), ("IND_PMRV", C["ambar"]),
                       ("IND_PMPC", C["grafite_claro"])]:
        s = serie(df, chave)
        fig.add_trace(go.Bar(x=[str(a) for a in s.index], y=s.values, name=INDICADORES[chave]["label"],
                             marker_color=cor, hovertemplate="%{y:.0f} dias<extra></extra>"))
    s_cf = serie(df, "IND_CICLO_FINANCEIRO")
    fig.add_trace(go.Scatter(x=[str(a) for a in s_cf.index], y=s_cf.values, mode="lines+markers+text",
                             name="Ciclo Financeiro", line=dict(color=C["vermelho"], width=3),
                             marker=dict(size=8), text=[f"{v:.0f}d" for v in s_cf.values],
                             textposition="top center", textfont=dict(color=C["vermelho"], size=12),
                             hovertemplate="Ciclo Fin.: %{y:.0f} dias<extra></extra>"))
    fig.update_layout(**layout_base("Prazos Médios e Ciclo Financeiro (dias)"), barmode="group")
    fig.update_xaxes(type="category", gridcolor=C["cinza_borda"])
    fig.update_yaxes(ticksuffix=" d", gridcolor=C["cinza_borda"], zeroline=True, zerolinecolor=C["cinza"])
    return fig


def fig_fleuriet(df):
    fig = go.Figure()
    for chave, cor in [("IND_CGL", C["grafite"]), ("IND_NCG", C["ambar"])]:
        s = serie(df, chave)
        fig.add_trace(go.Bar(x=[str(a) for a in s.index], y=s.values / 1e9, name=INDICADORES[chave]["label"],
                             marker_color=cor, hovertemplate="R$ %{y:.2f} bi<extra></extra>"))
    s_st = serie(df, "IND_ST")
    fig.add_trace(go.Scatter(x=[str(a) for a in s_st.index], y=s_st.values / 1e9, mode="lines+markers",
                             name="Saldo de Tesouraria", line=dict(color=C["vermelho"], width=3.5),
                             marker=dict(size=9), hovertemplate="ST: R$ %{y:.2f} bi<extra></extra>"))
    fig.update_layout(**layout_base("Modelo Fleuriet — CGL, NCG e Tesouraria (R$ bi)"), barmode="group")
    fig.update_xaxes(type="category", gridcolor=C["cinza_borda"])
    fig.update_yaxes(ticksuffix=" bi", gridcolor=C["cinza_borda"], zeroline=True, zerolinecolor=C["grafite"])
    return fig


def tabela_indicadores(df):
    anos = sorted(df["ANO"].unique())
    linhas = []
    for chave, meta in INDICADORES.items():
        if chave not in df.columns:
            continue
        s = serie(df, chave)
        linha = {"Grupo": meta["grupo"], "Indicador": meta["label"]}
        for a in anos:
            linha[str(a)] = fmt_valor(s.get(a, np.nan), meta["unidade"])
        linhas.append(linha)
    return pd.DataFrame(linhas)


# ==============================================================================
# 7. ACESSO AO BANCO (camada Gold)
# ==============================================================================
@st.cache_resource
def get_engine():
    user = quote_plus(os.getenv("DB_USER", "postgres"))
    pwd = quote_plus(os.getenv("DB_PASS", os.getenv("DB_PASSWORD", "password")))
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db = os.getenv("DB_NAME", "data_lake")
    return create_engine(f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}")


@st.cache_data(ttl=600)
def carregar_minerva(cnpj):
    engine = get_engine()
    q = text(f'SELECT * FROM {GOLD_TABLE} WHERE "CNPJ_CIA" = :cnpj ORDER BY "DT_REFER";')
    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params={"cnpj": cnpj})
    if not df.empty:
        df["ANO"] = pd.to_datetime(df["DT_REFER"]).dt.year
    return df


# ==============================================================================
# 8. COMPONENTES DE UI
# ==============================================================================
def card_kpi(label, valor, delta_txt="—", classe="neu"):
    cls = {"pos": "dlt-pos", "neg": "dlt-neg", "neu": "dlt-neu"}[classe]
    seta = {"pos": "▲", "neg": "▼", "neu": "•"}[classe]
    return f"""<div class="mnv-card"><div class="lbl">{label}</div>
        <div class="val">{valor}</div><div class="{cls}">{seta} {delta_txt}</div></div>"""


def bloco_insight(ins):
    cor = {"good": C["verde"], "warn": C["ambar"], "bad": C["vermelho_risco"], "info": C["grafite_claro"]}[ins["nivel"]]
    rotulo = {"good": "POSITIVO", "warn": "ATENÇÃO", "bad": "RISCO", "info": "CONTEXTO"}[ins["nivel"]]
    cls = {"good": "good", "warn": "warn", "bad": "bad", "info": ""}[ins["nivel"]]
    return f"""<div class="mnv-insight {cls}">
        <span class="mnv-pill" style="background:{cor}">{rotulo}</span>
        <b style="color:{C['grafite']}">{ins['titulo']}</b>
        <div style="margin-top:6px; color:{C['grafite_claro']}; font-size:14px; line-height:1.5">{ins['texto']}</div></div>"""


def insights_do_grupo(insights, grupo):
    for ins in [i for i in insights if i["grupo"] == grupo]:
        st.markdown(bloco_insight(ins), unsafe_allow_html=True)


# ==============================================================================
# 8B. DEMONSTRAÇÕES CONTÁBEIS (BP / DRE / DFC) — camada Silver hierárquica
#     Renderizador genérico: as três demonstrações têm o mesmo schema, então uma
#     única função monta a tabela hierárquica + KPIs + gráfico de cada uma.
# ==============================================================================
ESCALAS = {"R$ (unidade)": 1, "Milhares": 1e3, "Milhões": 1e6, "Bilhões": 1e9}

# Contas de destaque no padrão CVM/DFP (usadas para KPIs/validação/gráficos).
KPIS_BP  = [("Ativo Total", "1"), ("Passivo + PL", "2"),
            ("Ativo Circulante", "1.01"), ("Patrimônio Líquido", "2.03")]
KPIS_DRE = [("Receita Líquida", "3.01"), ("Resultado Bruto", "3.03"),
            ("Result. Operacional (EBIT)", "3.05"), ("Lucro/Prejuízo Líquido", "3.11")]
KPIS_DFC = [("Caixa Operacional", "6.01"), ("Caixa de Investimento", "6.02"),
            ("Caixa de Financiamento", "6.03"), ("Variação de Caixa", "6.05")]


@st.cache_data(ttl=600)
def carregar_demonstrativo(cnpj, tabela):
    """Lê uma demonstração hierárquica completa (todas as contas) da camada Silver."""
    engine = get_engine()
    q = text(f'''SELECT "CD_CONTA","DS_CONTA","DT_REFER","VL_CONTA_TRATADO"
                 FROM {tabela}
                 WHERE "CNPJ_CIA" = :cnpj
                 ORDER BY "CD_CONTA","DT_REFER";''')
    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params={"cnpj": cnpj})
    if not df.empty:
        df["ANO"] = pd.to_datetime(df["DT_REFER"]).dt.year
        df["CD_CONTA"] = df["CD_CONTA"].astype(str)
    return df


def _load_silver(cnpj, tabela):
    """Carga protegida: nunca derruba o app se a tabela/uma conexão falhar."""
    try:
        return carregar_demonstrativo(cnpj, tabela)
    except Exception as e:
        st.error(f"Falha ao consultar {tabela}: {e}")
        return pd.DataFrame()


def _profundidade(cd):
    return str(cd).count(".")


def _valor_conta(df_long, cd, ano):
    """Valor de uma conta específica num ano (NaN se inexistente)."""
    m = df_long[(df_long["CD_CONTA"] == cd) & (df_long["ANO"] == ano)]
    return float(m["VL_CONTA_TRATADO"].iloc[0]) if not m.empty else np.nan


def _serie_conta(df_long, cd, anos):
    return np.array([_valor_conta(df_long, cd, a) for a in anos], dtype=float)


def _card_simples(label, valor):
    return f"""<div class="mnv-card"><div class="lbl">{label}</div>
        <div class="val">{valor}</div></div>"""


def pivot_demonstrativo(df_long, anos, nivel_max):
    """Pivota CD_CONTA × ANO limitando ao nível de detalhe (1=grupo … 5=analítico)."""
    if df_long.empty:
        return pd.DataFrame()
    max_dig = nivel_max * 2 - 1            # nível 1→1díg (1) | 2→3 (1.01) | 3→5 (1.01.01)
    d = df_long[df_long["ANO"].isin(anos)].copy()
    d = d[d["CD_CONTA"].str.replace(".", "", regex=False).str.len() <= max_dig]
    if d.empty:
        return pd.DataFrame()
    return (d.pivot_table(index=["CD_CONTA", "DS_CONTA"], columns="ANO",
                          values="VL_CONTA_TRATADO", aggfunc="sum")
             .reset_index().sort_values("CD_CONTA").reset_index(drop=True))


def _kpis_demonstrativo(df_long, mapa, ano_cur):
    cols = st.columns(len(mapa))
    for col, (lbl, cd) in zip(cols, mapa):
        with col:
            st.markdown(_card_simples(lbl, fmt_rs(_valor_conta(df_long, cd, ano_cur))),
                        unsafe_allow_html=True)


def _grafico_barras_contas(df_long, anos, contas, divisor, titulo, sufixo):
    """Barras agrupadas por ano para um conjunto de contas-chave (rótulos legíveis)."""
    cores = [C["grafite"], C["vermelho"], C["ambar"], C["grafite_claro"]]
    fig = go.Figure()
    xa = [str(a) for a in anos]
    maxabs = 0.0
    for (lbl, cd), cor in zip(contas, cores):
        y = _serie_conta(df_long, cd, anos) / divisor
        if np.all(np.isnan(y)):
            continue
        maxabs = max(maxabs, np.nanmax(np.abs(y)))
        fig.add_trace(go.Bar(x=xa, y=y, name=lbl, marker_color=cor,
                             text=[_br(v, 1) if pd.notna(v) else "" for v in y],
                             textposition="outside", textfont=dict(size=12),
                             cliponaxis=False,
                             hovertemplate=lbl + ": %{y:,.1f} " + sufixo + "<extra></extra>"))
    fig.update_layout(**layout_base(titulo), barmode="group")
    fig.update_xaxes(type="category", gridcolor=C["cinza_borda"])
    fig.update_yaxes(gridcolor=C["cinza_borda"], zeroline=True, zerolinecolor=C["cinza"],
                     ticksuffix=f" {sufixo}")
    if maxabs > 0:   # folga p/ os rótulos externos não cortarem
        fig.update_yaxes(range=[min(0, -maxabs * 0.15), maxabs * 1.20])
    st.plotly_chart(fig, use_container_width=True)


def _validacao_bp(df_long, anos):
    """Checa a identidade contábil Ativo = Passivo + PL ano a ano."""
    partes, ok = [], True
    for a in anos:
        at, pa = _valor_conta(df_long, "1", a), _valor_conta(df_long, "2", a)
        dif = at - pa if (pd.notna(at) and pd.notna(pa)) else np.nan
        partes.append(f"{a}: {fmt_rs(dif)}")
        if pd.notna(dif) and abs(dif) > max(1.0, abs(at) * 1e-6):
            ok = False
    detalhe = " · ".join(partes)
    if ok:
        st.success(f"✅ Balanço fechado (Ativo = Passivo + PL) em todos os anos. "
                   f"Diferença residual — {detalhe}.")
    else:
        st.error(f"⚠️ Divergência em Ativo − (Passivo + PL): {detalhe}.")


def aba_demonstrativo(df_long, anos_sel, titulo, tipo):
    """Renderiza uma demonstração (tipo ∈ {'BP','DRE','DFC'}) na identidade Minerva."""
    if df_long.empty:
        st.warning(f"Sem dados de {titulo} na camada Silver para a empresa selecionada.")
        return

    anos_disp = sorted(int(a) for a in df_long["ANO"].unique())
    anos = [a for a in anos_disp if a in anos_sel]
    fallback = False
    if not anos:                       # filtro global não bate com os anos da Silver
        anos = anos_disp[-6:]
        fallback = True

    # --- controles locais (mantêm a sidebar do Cockpit limpa) ---
    c1, c2 = st.columns(2)
    with c1:
        nivel = st.slider(f"Nível de detalhe — {titulo}", 1, 5, 3, key=f"nivel_{tipo}")
    with c2:
        escala_lbl = st.selectbox(f"Escala — {titulo}", list(ESCALAS.keys()),
                                  index=3, key=f"escala_{tipo}")
    divisor = ESCALAS[escala_lbl]
    if fallback:
        st.caption("Os anos do filtro lateral não existem nesta demonstração; "
                   f"exibindo os disponíveis ({anos[0]}–{anos[-1]}).")

    # --- KPIs do último ano ---
    mapa = {"BP": KPIS_BP, "DRE": KPIS_DRE, "DFC": KPIS_DFC}[tipo]
    _kpis_demonstrativo(df_long, mapa, max(anos))

    # --- tabela hierárquica ---
    piv = pivot_demonstrativo(df_long, anos, nivel)
    if piv.empty:
        st.info("Nenhuma conta neste nível de detalhe.")
        return
    cols_anos = sorted([c for c in piv.columns if isinstance(c, (int, np.integer))])
    tabela = pd.DataFrame({
        "Conta": piv["CD_CONTA"],
        "Descrição": [("\u2003" * _profundidade(cd)) + ds
                      for cd, ds in zip(piv["CD_CONTA"], piv["DS_CONTA"])],
    })
    for a in cols_anos:
        tabela[str(a)] = (piv[a] / divisor).map(lambda v: _br(v, 2) if pd.notna(v) else "—")

    st.markdown(f"#### {titulo} — valores em {escala_lbl}")
    col_cfg = {"Conta": st.column_config.TextColumn("Conta", width="small"),
               "Descrição": st.column_config.TextColumn("Descrição", width="large")}
    for a in cols_anos:
        col_cfg[str(a)] = st.column_config.TextColumn(str(a), width="small")
    altura = min((len(tabela) + 1) * 35 + 4, 640)
    st.dataframe(tabela, hide_index=True, use_container_width=True,
                 column_config=col_cfg, height=altura)

    # --- gráfico-chave + validação por tipo ---
    sufixo = {"R$ (unidade)": "", "Milhares": "mil", "Milhões": "mi", "Bilhões": "bi"}[escala_lbl]
    if tipo == "BP":
        _grafico_barras_contas(df_long, anos, KPIS_BP[:2], divisor,
                               f"Estrutura Patrimonial ({escala_lbl})", sufixo)
        _validacao_bp(df_long, anos)
    elif tipo == "DRE":
        _grafico_barras_contas(df_long, anos, KPIS_DRE, divisor,
                               f"Da Receita ao Lucro ({escala_lbl})", sufixo)
        st.caption("Custos e despesas já entram com sinal negativo no padrão CVM; "
                   "os subtotais (Resultado Bruto, EBIT, Lucro Líquido) somam diretamente.")
    elif tipo == "DFC":
        _grafico_barras_contas(df_long, anos, KPIS_DFC[:3], divisor,
                               f"Fluxos por Atividade ({escala_lbl})", sufixo)
        st.caption("Operacional, Investimento e Financiamento. A soma das três (mais variação "
                   "cambial) explica a variação de caixa do período (6.05).")


# ==============================================================================
# 9. APLICAÇÃO PRINCIPAL
# ==============================================================================
def main():
    st.set_page_config(page_title="Minerva Foods | Indicadores", page_icon="🥩",
                       layout="wide", initial_sidebar_state="expanded")
    load_dotenv()
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    st.markdown(css_minerva(), unsafe_allow_html=True)

    # ---- Carga ----
    try:
        df_full = carregar_minerva(MINERVA_CNPJ)
    except Exception as e:
        st.error(f"Falha ao conectar/consultar a camada Gold ({GOLD_TABLE}): {e}")
        st.stop()

    if df_full.empty:
        st.warning(f"Sem indicadores da Minerva (CNPJ {MINERVA_CNPJ}) em {GOLD_TABLE}. "
                   "Rode o notebook do Gold antes de abrir o dashboard.")
        st.stop()

    razao = str(df_full["RAZAO_SOCIAL"].dropna().iloc[0]) if df_full.get("RAZAO_SOCIAL") is not None and df_full["RAZAO_SOCIAL"].notna().any() else "MINERVA S.A."
    setor = str(df_full["SETOR"].dropna().iloc[0]) if df_full.get("SETOR") is not None and df_full["SETOR"].notna().any() else "Alimentos"

    # ---- Sidebar ----
    anos_disp = sorted(df_full["ANO"].unique())
    with st.sidebar:
        st.title("Minerva Foods")
        st.caption("BEEF3 · Big Data for Finance")
        st.markdown("---")
        st.header("Período")
        anos_sel = st.multiselect("Anos:", options=anos_disp,
                                  default=anos_disp[-6:] if len(anos_disp) > 6 else anos_disp)
    if not anos_sel:
        st.info("Selecione ao menos um ano na barra lateral.")
        st.stop()

    df = df_full[df_full["ANO"].isin(anos_sel)].sort_values("ANO").reset_index(drop=True)
    periodo = f"{min(anos_sel)}–{max(anos_sel)}" if len(anos_sel) > 1 else str(anos_sel[0])
    st.markdown(header_html(razao, setor, periodo), unsafe_allow_html=True)

    insights = gerar_diagnostico(df)

    # ---- ABAS ----
    abas = st.tabs(["📊 Visão Geral", "💧 Liquidez", "🏦 Endividamento",
                    "📈 Margens & Rentab.", "🔄 Atividade & Ciclos", "🔁 Fleuriet", "📋 Tabela",
                    "🧾 Balanço (BP)", "🧮 DRE", "💵 DFC"])

    # ----- Aba 1: Visão geral + diagnóstico completo -----
    with abas[0]:
        cur = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else None
        ano_cur = int(cur["ANO"])

        def g(row, col):
            return row[col] if (row is not None and col in row and pd.notna(row[col])) else np.nan

        st.markdown(f"#### Visão geral — {ano_cur}")
        kpis = [
            ("Receita Líquida", fmt_rs(g(cur, "V17_RECEITA_LIQ")),
             *delta_monetario(g(cur, "V17_RECEITA_LIQ"), g(prev, "V17_RECEITA_LIQ"))),
            ("Lucro Líquido", fmt_rs(g(cur, "V21_LUCRO_LIQ")),
             *delta_monetario(g(cur, "V21_LUCRO_LIQ"), g(prev, "V21_LUCRO_LIQ"))),
            ("Margem Líquida", fmt_valor(g(cur, "IND_MARGEM_LIQUIDA"), "pct"),
             *fmt_delta("IND_MARGEM_LIQUIDA", g(cur, "IND_MARGEM_LIQUIDA"), g(prev, "IND_MARGEM_LIQUIDA"))),
            ("ROE", fmt_valor(g(cur, "IND_ROE"), "pct"),
             *fmt_delta("IND_ROE", g(cur, "IND_ROE"), g(prev, "IND_ROE"))),
            ("Liquidez Corrente", fmt_valor(g(cur, "IND_LIQUIDEZ_CORRENTE"), "idx"),
             *fmt_delta("IND_LIQUIDEZ_CORRENTE", g(cur, "IND_LIQUIDEZ_CORRENTE"), g(prev, "IND_LIQUIDEZ_CORRENTE"))),
            ("Ciclo Financeiro", fmt_valor(g(cur, "IND_CICLO_FINANCEIRO"), "dias"),
             *fmt_delta("IND_CICLO_FINANCEIRO", g(cur, "IND_CICLO_FINANCEIRO"), g(prev, "IND_CICLO_FINANCEIRO"))),
        ]
        cols = st.columns(3)
        for i, (lbl, val, dtxt, cls) in enumerate(kpis):
            with cols[i % 3]:
                st.markdown(card_kpi(lbl, val, dtxt, cls), unsafe_allow_html=True)
            if i % 3 == 2 and i != len(kpis) - 1:
                cols = st.columns(3)

        st.markdown("### 🧠 Diagnóstico executivo")
        st.caption("Leitura automática cruzando indicadores, tendências e o contexto do setor frigorífico.")
        if not insights:
            st.info("Dados insuficientes para gerar o diagnóstico.")
        for ins in insights:
            st.markdown(bloco_insight(ins), unsafe_allow_html=True)

    # ----- Aba 2: Liquidez -----
    with abas[1]:
        st.plotly_chart(fig_liquidez(df), use_container_width=True)
        insights_do_grupo(insights, "Liquidez")
        st.caption("Quanto maior o índice, maior a folga de pagamento. Referências (1,5× e 1,0×) do racional do projeto.")

    # ----- Aba 3: Endividamento -----
    with abas[2]:
        st.plotly_chart(fig_endividamento(df), use_container_width=True)
        insights_do_grupo(insights, "Endividamento")
        st.caption("Participação de terceiros no ativo, concentração da dívida no curto prazo e imobilização do ativo.")

    # ----- Aba 4: Margens & Rentabilidade -----
    with abas[3]:
        st.plotly_chart(fig_margens_rentab(df), use_container_width=True)
        insights_do_grupo(insights, "Margens")
        insights_do_grupo(insights, "Rentabilidade")
        st.caption("Margens estreitas e voláteis são típicas do setor; ROE acima do ROA evidencia o efeito da alavancagem.")

    # ----- Aba 5: Atividade & Ciclos -----
    with abas[4]:
        st.plotly_chart(fig_ciclos(df), use_container_width=True)
        insights_do_grupo(insights, "Ciclos")
        st.caption("PMRE inclui ativos biológicos consolidados ao estoque (premissa do setor de proteína animal).")

    # ----- Aba 6: Fleuriet -----
    with abas[5]:
        st.plotly_chart(fig_fleuriet(df), use_container_width=True)
        insights_do_grupo(insights, "Fleuriet")
        st.caption("CGL, NCG e Saldo de Tesouraria. ST negativo e decrescente em anos sucessivos = Efeito Tesoura.")

    # ----- Aba 7: Tabela -----
    with abas[6]:
        st.markdown("#### Indicadores por ano")
        st.dataframe(tabela_indicadores(df), hide_index=True, use_container_width=True,
                     column_config={"Grupo": st.column_config.TextColumn("Grupo", width="small")})

    # ----- Abas 8–10: Demonstrações contábeis (camada Silver, hierárquicas) -----
    with abas[7]:
        st.caption("Balanço Patrimonial completo e hierárquico, direto da camada Silver "
                   "(mesma base que alimenta os indicadores do Cockpit).")
        aba_demonstrativo(_load_silver(MINERVA_CNPJ, SILVER_BP), anos_sel,
                          "Balanço Patrimonial", "BP")
    with abas[8]:
        st.caption("Demonstração do Resultado do Exercício (DRE), da receita ao lucro líquido.")
        aba_demonstrativo(_load_silver(MINERVA_CNPJ, SILVER_DRE), anos_sel,
                          "Demonstração do Resultado (DRE)", "DRE")
    with abas[9]:
        st.caption("Demonstração dos Fluxos de Caixa (DFC), por atividade.")
        aba_demonstrativo(_load_silver(MINERVA_CNPJ, SILVER_DFC), anos_sel,
                          "Demonstração dos Fluxos de Caixa (DFC)", "DFC")

    st.markdown("---")
    st.caption(f"Fonte: camada Gold (CVM/DFP) — {GOLD_TABLE}. "
               "Cabeçalho com identidade visual estilizada da Minerva Foods. © Big Data for Finance.")


if __name__ == "__main__":
    main()
