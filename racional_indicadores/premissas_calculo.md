# 📐 Dicionário de Premissas — Cálculo de Indicadores Financeiros

> **Finalidade:** Este documento é a fonte única de verdade para o mapeamento entre
> os conceitos financeiros dos indicadores e as contas CVM presentes na camada Silver.
> Qualquer interessado em consumir as informações deve consultar este arquivo antes de
> implementar ou revisar um cálculo de indicador, pois existem sim limitações.
>
> **Base de dados:** `layer_02_silver` (PostgreSQL)
> **Última revisão:** 2026-03-15 (revisão ST_CONTA_FIXA + mapeamento completo LPA 3.99)
> **Responsável:** Prof. Ivan Mello

---

## ⚠️ Notas Gerais Obrigatórias

### N1 — Caixa para indicadores: sempre usar DFC, nunca BP direto

| Indicador | Conta correta | Conta incorreta | Motivo |
|---|---|---|---|
| Dívida Líquida, EV, FCF Yield | `6.05.02` (DFC) | `1.01.01` (BP) | CPC 03: DFC inclui CDBs/LFTs ≤90d e caixa de grupos a venda (CPC 31) |
| Liquidez Imediata, ACF Fleuriet | `1.01.01` (BP) | `6.05.02` (DFC) | Esses ratios são definidos sobre o balanço por construção |

### N2 — Estoques ausentes (20/185 empresas)

Empresas de serviço puro não reportam `1.01.04` (Estoques). Cobertura empírica: **89.2%** (Notebook 7).
Setores 100% sem estoque: Educação, Hospedagem/Turismo, Bolsas de Valores.
Regra: `COALESCE(estoques, 0)`. Para Giro Estoques / PMRE / Ciclo Econômico, exibir **N/A** (não zero) para essas empresas.

### N3 — LPA: usar leaves originais, não o pai reconstruído

`3.99` (pai) é reconstruído pelo pipeline somando básico + diluído = valor sem sentido financeiro.
Usar sempre `3.99.01.01` (básico ON) ou `3.99.02.01` (diluído ON).

**Mapa completo das sub-contas 3.99 (validado empiricamente — 2026-03):**

| CD_CONTA | Descrição | Tipo | Empresas |
|---|---|---|---|
| `3.99.01.01` | LPA Básico ON (Ordinárias) | Básico | ~97.8% do universo |
| `3.99.01.02` | LPA Básico PN (Preferenciais) | Básico | ~64 empresas |
| `3.99.01.03` | LPA Básico PNB (Pref. Classe B) | Básico | ~9 empresas |
| `3.99.02.01` | LPA Diluído ON (Ordinárias) | Diluído | ~82.2% do universo |
| `3.99.02.02` | LPA Diluído PN (Preferenciais) | Diluído | ~64 empresas |
| `3.99.02.03` | LPA Diluído PNB (Pref. Classe B) | Diluído | ~9 empresas |

**Conclusão:** Não existe nenhuma empresa no universo que reporte apenas PN/PNB sem reportar ON. Portanto, `3.99.01.01` e `3.99.02.01` são sempre disponíveis quando qualquer LPA existe. As contas PN/PNB são suplementares — relevantes apenas para análises específicas de estrutura de capital dual-class.

---

## 📦 Variáveis do Balanço Patrimonial (BP)

### V01 — Ativo Total (AT)

| Campo | Valor |
|---|---|
| CD_CONTA | `1` |
| DS_CONTA | ATIVO TOTAL |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Usado em | ROA, ROI, PCT/AT, Imobilização AT, Liquidez Geral |

---

### V02 — Ativo Circulante (AC)

| Campo | Valor |
|---|---|
| CD_CONTA | `1.01` |
| DS_CONTA | ATIVO CIRCULANTE |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Usado em | Liquidez Corrente, Liquidez Seca, Liquidez Geral, CGL, Giro AC, PMRAC, NCG, Fleuriet |

---

### V03 — Ativo Não Circulante (ANC)

| Campo | Valor |
|---|---|
| CD_CONTA | `1.02` |
| DS_CONTA | ATIVO NÃO CIRCULANTE |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Usado em | CGL (fórmula alternativa: PL + PNC - ANC) |

---

### V04 — Realizável a Longo Prazo (RLP)

| Campo | Valor |
|---|---|
| CD_CONTA | `1.02.01` |
| DS_CONTA | ATIVO REALIZÁVEL A LONGO PRAZO |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Atenção | Inclui recebíveis LP, investimentos de longo prazo e depósitos judiciais dependendo da empresa. Representa todo o realizável fora do circulante, que é o conceito correto para Liquidez Geral. |
| Usado em | Liquidez Geral |

---

### V05 — Ativo Imobilizado

| Campo | Valor |
|---|---|
| CD_CONTA | `1.02.03` |
| DS_CONTA | IMOBILIZADO |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Atenção | Valor líquido (após depreciação acumulada). Empresas asset-heavy (energia, siderurgia) terão valores muito maiores que empresas de serviço. |
| Usado em | Imobilização de Capital Próprio, Imobilização do Ativo Total |

---

### V06 — Estoques

| Campo | Valor |
|---|---|
| CD_CONTA | `1.01.04` |
| DS_CONTA | ESTOQUES |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 89.2% (validado empiricamente — Notebook 8) |
| COALESCE? | **Sim — usar 0 quando ausente** |
| Setores sem estoque | Educação (100%), Hospedagem/Turismo (100%), Bolsas (100%), + outliers em Transporte, Energia, Varejo — todos de serviço puro ou modelo asset-light. |
| Impacto quando ausente | Liquidez Seca = Liquidez Corrente. Giro de Estoques, PMRE e Ciclo Econômico ficam indefinidos — exibir como N/A para essas empresas. |
| Usado em | Liquidez Seca, Giro Estoques, PMRE, Ciclo Econômico, NCG (ACO) |

---

### V07 — Contas a Receber / Clientes (Curto Prazo)

| Campo | Valor |
|---|---|
| CD_CONTA | `1.01.03` |
| DS_CONTA | CONTAS A RECEBER |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Atenção | Inclui clientes e outras contas a receber de curto prazo. Para indicadores que pedem especificamente "Clientes" (ex: PMRV), este é o proxy mais confiável disponível na estrutura padronizada. Sub-contas (`1.01.03.01` = Clientes, `1.01.03.02` = Outras) têm ST_CONTA_FIXA='N'. |
| Usado em | Giro Contas a Receber, PMRV, NCG (ACO), Fleuriet |

---

### V08 — Clientes Longo Prazo

| Campo | Valor |
|---|---|
| CD_CONTA | Sub-contas de `1.02.01` (não padronizadas) |
| DS_CONTA | Variável por empresa |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `N` (conta livre) |
| Cobertura | Baixa — maioria das empresas não segrega explicitamente |
| Decisão de premissa | **Desconsiderado.** Para Giro Contas a Receber, usar apenas V07 (`1.01.03`). O erro de omissão é pequeno para a maioria das empresas (recebíveis LP são residuais). |
| Usado em | Giro Contas a Receber (com limitação documentada) |

---

### V09 — Fornecedores

| Campo | Valor |
|---|---|
| CD_CONTA | `2.01.02` |
| DS_CONTA | FORNECEDORES |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Usado em | Giro Contas a Pagar, PMPC, NCG (PCO), Fleuriet |

---

### V10 — Passivo Circulante (PC)

| Campo | Valor |
|---|---|
| CD_CONTA | `2.01` |
| DS_CONTA | PASSIVO CIRCULANTE |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Usado em | Todos os indicadores de liquidez, endividamento, CGL, Composição de Endividamento, Fleuriet |

---

### V11 — Passivo Não Circulante / Exigível a Longo Prazo (ELP)

| Campo | Valor |
|---|---|
| CD_CONTA | `2.02` |
| DS_CONTA | PASSIVO NÃO CIRCULANTE |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Atenção | Na terminologia CVM atual, o "Exigível a Longo Prazo" da nomenclatura clássica corresponde ao `2.02` (Passivo Não Circulante). Inclui dívida de longo prazo, provisões e outros passivos LP. |
| Usado em | Liquidez Geral, PCT/CP, PCT/AT, Garantia CP/CT, Composição de Endividamento, CGL alternativo |

---

### V12 — Patrimônio Líquido (PL)

| Campo | Valor |
|---|---|
| CD_CONTA | `2.03` |
| DS_CONTA | PATRIMÔNIO LÍQUIDO CONSOLIDADO |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Atenção | Pode ser negativo em empresas com prejuízos acumulados. Indicadores que usam PL no denominador devem tratar divisão por negativo (ex: ROE negativo = destruição de valor, não sinal invertido). |
| Usado em | ROE, ROI, PCT/CP, Garantia CP/CT, Imobilização CP, CGL alternativo |

---

### V13 — Empréstimos e Financiamentos (Curto Prazo)

| Campo | Valor |
|---|---|
| CD_CONTA | `2.01.04` |
| DS_CONTA | EMPRÉSTIMOS E FINANCIAMENTOS |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 180/185 (97%) |
| COALESCE? | **Sim — usar 0 quando ausente** (empresa sem dívida CP) |
| Usado em | ROI (Passivo Oneroso), PCF Fleuriet |

---

### V14 — Empréstimos e Financiamentos (Longo Prazo)

| Campo | Valor |
|---|---|
| CD_CONTA | `2.02.01` |
| DS_CONTA | EMPRÉSTIMOS E FINANCIAMENTOS |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 178/185 (96%) |
| COALESCE? | **Sim — usar 0 quando ausente** (empresa sem dívida LP) |
| Usado em | ROI (Passivo Oneroso = V13 + V14) |

---

### V15 — Ativo Circulante Financeiro (ACF) — Modelo Fleuriet

| Campo | Valor |
|---|---|
| CD_CONTA | `1.01.01` + `1.01.02` |
| DS_CONTA | Caixa e Equivalentes + Aplicações Financeiras |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| Cobertura | 185/185 para `1.01.01`; 162/185 para `1.01.02` |
| COALESCE? | Sim para `1.01.02` |
| Atenção | **Usar `1.01.01` (BP), NÃO `6.05.02` (DFC).** O Modelo Fleuriet é estruturalmente baseado no balanço. `1.01.02` pode incluir aplicações não imediatas — aceita-se como proxy do financeiro circulante. |
| Usado em | Saldo de Tesouraria (ST), Efeito Tesoura |

---

### V16 — Passivo Circulante Financeiro (PCF) — Modelo Fleuriet

| Campo | Valor |
|---|---|
| CD_CONTA | `2.01.04` (= V13) |
| DS_CONTA | EMPRÉSTIMOS E FINANCIAMENTOS CP |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| COALESCE? | Sim |
| Atenção | Representa a parcela "financeira" (não operacional) do PC. Empréstimos de curto prazo são o proxy mais confiável disponível sem mapeamento manual conta a conta. |
| Usado em | Saldo de Tesouraria (ST), Efeito Tesoura |

---

### V22 — Disponibilidades (para Liquidez Imediata)

| Campo | Valor |
|---|---|
| CD_CONTA | `1.01.01` |
| DS_CONTA | CAIXA E EQUIVALENTES DE CAIXA |
| Tabela Silver | `n1_dfp_cia_aberta_bp` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Atenção | Usar `1.01.01` (BP) para Liquidez Imediata — este ratio é definido sobre o balanço. **Não usar `6.05.02` (DFC)** — ver Nota Geral N1. |
| Usado em | Liquidez Imediata, ACF Fleuriet |

---

### V23 — Saldo Final de Caixa (para Dívida Líquida / EV)

| Campo | Valor |
|---|---|
| CD_CONTA | `6.05.02` |
| DS_CONTA | SALDO FINAL DE CAIXA E EQUIVALENTES |
| Tabela Silver | `n1_dfp_cia_aberta_dfc` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Atenção | **Usar `6.05.02` (DFC) para Dívida Líquida e EV** — inclui CDBs/LFTs ≤90d (CPC 03) e caixa de grupos a venda (CPC 31). Ver casos Moura Dubeux, CBD, Copel no CLAUDE.md. |
| Usado em | Dívida Líquida (indicador futuro), EV (indicador futuro) |

---

## 📈 Variáveis da DRE

### V17 — Receita Líquida de Vendas

| Campo | Valor |
|---|---|
| CD_CONTA | `3.01` |
| DS_CONTA | RECEITA DE VENDA DE BENS E/OU SERVIÇOS |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Atenção | Já é receita **líquida** na estrutura CVM (deduções já aplicadas nas sub-contas). Não confundir com "Receita Bruta" — a CVM não exige reportar bruta separadamente. |
| Usado em | Margem Bruta, Margem Operacional, Margem Líquida, Giro CR, Giro AC, PMRV, PMRAC |

---

### V18 — Custo dos Bens e/ou Serviços Vendidos (CPV)

| Campo | Valor |
|---|---|
| CD_CONTA | `3.02` |
| DS_CONTA | CUSTO DOS BENS E/OU SERVIÇOS VENDIDOS |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Atenção | Valor negativo na Silver (despesa). Nas fórmulas, usar `ABS(CPV)` ou somar algebricamente conforme o sinal da conta. No varejo, CPV = custo das mercadorias vendidas. |
| Usado em | Margem Bruta (derivada), Giro Estoques, Giro CP, PMRE, PMPC |

---

### V19 — Lucro Bruto (Resultado Bruto)

| Campo | Valor |
|---|---|
| CD_CONTA | `3.03` |
| DS_CONTA | RESULTADO BRUTO |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Atenção | Pode ser calculado como `3.01 + 3.02` (soma algébrica) ou lido diretamente de `3.03`. Preferir `3.03` por integridade. |
| Usado em | Margem Bruta |

---

### V20 — Lucro Operacional (EBIT)

| Campo | Valor |
|---|---|
| CD_CONTA | `3.05` |
| DS_CONTA | RESULTADO ANTES DO RESULTADO FINANCEIRO E DOS TRIBUTOS |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Atenção | Equivalente ao EBIT (Earnings Before Interest and Taxes). Exclui resultado financeiro (`3.06`) e tributos (`3.08`). É a conta correta para Margem Operacional — **não usar `3.07`** (que já inclui resultado financeiro). |
| Usado em | Margem Operacional |

---

### V21 — Lucro Líquido do Exercício

| Campo | Valor |
|---|---|
| CD_CONTA | `3.11` |
| DS_CONTA | LUCRO/PREJUÍZO CONSOLIDADO DO PERÍODO |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `S` — padronizado pela CVM |
| Cobertura | 185/185 (100%) |
| COALESCE? | Não |
| Atenção | Inclui participação de minoritários. Empresas que usam `3.11.01` (Atribuído à Controladora) — quando relevante para ROE, considerar se usar `3.11` ou `3.11.01`. Para análise consolidada padrão, usar `3.11`. |
| Usado em | Margem Líquida, ROA, ROE, ROI |

---

### V25 — Lucro Básico por Ação (LPA Básico ON)

| Campo | Valor |
|---|---|
| CD_CONTA | `3.99.01.01` |
| DS_CONTA | ON (Ordinária — Lucro Básico por Ação) |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `N` — conta livre |
| FLAG_RECONSTRUCAO | `False` — dado original |
| Cobertura | **97.8%** (validado empiricamente — Notebook 8) |
| COALESCE? | Não aplicável |
| Atenção | **Não usar `3.99`** (pai reconstruído = soma básico+diluído = sem sentido). Não usar `3.99.01` (pai reconstruído). Usar exclusivamente o leaf `3.99.01.01`. Empresas com PN terão também `3.99.01.02` — ver N3. **Outlier Marisa 2021:** filtrar `ABS(VL_CONTA_TRATADO) > 10.000` antes de qualquer cálculo. |
| Unidade | R$/ação |
| Usado em | LPA (Lucro Por Ação) |

---

### V26 — Lucro Diluído por Ação (LPA Diluído ON)

| Campo | Valor |
|---|---|
| CD_CONTA | `3.99.02.01` |
| DS_CONTA | ON (Ordinária — Lucro Diluído por Ação) |
| Tabela Silver | `n1_dfp_cia_aberta_dre` |
| ST_CONTA_FIXA | `N` — conta livre |
| FLAG_RECONSTRUCAO | `False` — dado original |
| Cobertura V26 puro | 82.2% por empresa, **67.5% por empresa-período** |
| Cobertura COALESCE | **86.7% por empresa-período** (diluído direto 67.5% + fallback básico 19.2%) |
| Sem LPA (estrutural) | 13.3% do universo empresa-período — não há LPA de nenhum tipo; irreducível |
| COALESCE? | **Sim — COALESCE(V26, V25):** 29 empresas nunca reportam V26; anos pré-2015 têm cobertura historicamente menor (50 empresas em 2010 vs 135 em 2022) |
| Estratégia fallback | Gap de V26 é temporal (adoção gradual): anos mais recentes convertem para ~95% de cobertura. Fallback para V25 introduz erro ≤ R$0,05 em 95% dos casos. |
| Atenção | Considera o efeito dilutivo de opções de ações e conversíveis. Geralmente ligeiramente menor que o básico. Para análise conservadora, preferir o diluído. **Outlier Marisa 2021:** filtrar `ABS(VL_CONTA_TRATADO) > 10.000` antes de calcular. |
| Unidade | R$/ação |
| Usado em | LPA Diluído |

---

## 🔗 Mapa Rápido: Indicador → Variáveis

| Indicador | Variáveis necessárias |
|---|---|
| Liquidez Geral | V02, V04, V10, V11 |
| Liquidez Corrente | V02, V10 |
| Liquidez Seca | V02, V06, V10 |
| Liquidez Imediata | V22, V10 |
| PCT / Capital Próprio | V10, V11, V12 |
| PCT / Ativo Total | V10, V11, V01 |
| Garantia CP / CT | V12, V10, V11 |
| Composição de Endividamento | V10, V11 |
| Imobilização Capital Próprio | V05, V12 |
| Imobilização Ativo Total | V05, V01 |
| Margem Bruta | V19, V17 |
| Margem Operacional | V20, V17 |
| Margem Líquida | V21, V17 |
| LPA (Básico / Diluído) | V25 / V26 |
| ROA | V21, V01 |
| ROE | V21, V12 |
| ROI | V21, V13, V14, V12 |
| Giro Estoques | V18, V06 |
| Giro Contas a Receber | V17, V07 |
| Giro Contas a Pagar | V18, V09 |
| Giro Ativo Circulante | V17, V02 |
| PMRE | V06, V18 |
| PMRV | V07, V17 |
| PMPC | V09, V18 |
| PMRAC | V02, V17 |
| Ciclo Econômico | PMRE, PMRV |
| Ciclo Financeiro | PMRE, PMRV, PMPC |
| Capital de Giro Líquido (CGL) | V02, V10 |
| NCG | V06, V07, V09 |
| Saldo de Tesouraria (ST) | V15, V16 |