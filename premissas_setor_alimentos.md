# 📑 Data Contract — Camada Gold (Setor: Alimentos)

**Escopo:** Definição das variáveis contábeis, fontes físicas, regras de normalização e fórmulas dos indicadores financeiros para o setor de Alimentos e Bebidas.
**Base de Origem:** layer_02_silver (PostgreSQL)  
**Tabela Física Fonte:** layer_02_silver.dfp_cia_aberta_consolidado  
**Destino:** layer_03_gold.indicadores_setor_alimentos  
**Alinhamento:** Dicionário de Diretrizes do Prof. Ivan Mello  

---

## 1. Mapeamento de Variáveis (De-Para Contábil)

Para garantir a unicidade dos registos no pipeline em Python e evitar duplicações por reenvios de documentos, o consumo dos dados exige a aplicação estrita dos filtros: ORDEM_EXERC = 'LAST' e "IS_LEAF" = true.

| Código | Descrição da Variável | Código da Conta (CD_CONTA) | Origem | Conta Fixa? | Regra de Negócio / Tratamento Obrigatório |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **V01** | Ativo Total | 1 | BP | Sim | Linha base para o cálculo de ROA, ROI e estrutura de capitais. |
| **V02** | Ativo Circulante | 1.01 | BP | Sim | Parâmetro de liquidez e modelo de Fleuriet. |
| **V04** | Realizável a Longo Prazo | 1.02.01 | BP | Sim | Filtro de curto/longo prazo para a Liquidez Geral. |
| **V05** | Ativo Imobilizado | 1.02.03 | BP | Sim | Valor líquido das contas imobilizadas (pós-depreciação). |
| **V06** | Estoques Totais | 1.01.04 (+ 1.01.07) | BP | Não | **Regra do Setor:** Soma do Estoque padrão (1.01.04) com os Ativos Biológicos (1.01.07) para JBS e BRF. Se nulo, usar 0. |
| **V07** | Contas a Receber (Clientes) | 1.01.03 | BP | Sim | Direitos de curto prazo com clientes. Base do PMRV. |
| **V09** | Fornecedores | 2.01.02 | BP | Sim | Obrigações operacionais de curto prazo. Base do PMPC. |
| **V10** | Passivo Circulante | 2.01 | BP | Sim | Obrigações financeiras e operacionais de curto prazo. |
| **V11** | Passivo Não Circulante | 2.02 | BP | Sim | Equivalente ao Exigível a Longo Prazo. |
| **V12** | Patrimônio Líquido | 2.03 | BP | Sim | Se for $\le 0$, disparar trava de nulo no Python para ROE/ROI. |
| **V13** | Empréstimos e Financ. (CP) | 2.01.04 | BP | Sim | Mapeia o risco bancário imediato e serve como o PCF. |
| **V14** | Empréstimos e Financ. (LP) | 2.02.01 | BP | Sim | Dívida onerosa de longo prazo. Base do Capital Empregado. |
| **V15** | Ativo Circ. Financeiro (ACF)| 1.01.01 + 1.01.02 | BP | Não | Caixa/Disponibilidades (1.01.01) somado a Aplicações (1.01.02). |
| **V16** | Passivo Circ. Financeiro (PCF)| 2.01.04 (=V13) | BP | Não | Equivalente aos empréstimos de curto prazo para o modelo Fleuriet. |
| **V17** | Receita Líquida de Vendas | 3.01 | DRE | Sim | Base nominal de todas as margens e giros do pipeline. |
| **V18** | Custo das Vendas (CPV) | 3.02 | DRE | Sim | **Tratamento:** Extraído como valor negativo. Obrigatório aplicar abs(V18). |
| **V19** | Lucro Bruto | 3.03 | DRE | Sim | Resultado deduzido apenas o custo de fabricação. |
| **V20** | Lucro Operacional (EBIT) | 3.05 | DRE | Sim | Lucro antes dos efeitos financeiros e fiscais. |
| **V21** | Lucro Líquido do Exercício | 3.11 | DRE | Sim | Linha final de resultado atribuído aos acionistas. |
| **V22** | Disponibilidades (Caixa) | 1.01.01 | BP | Sim | Recurso em caixa estrito. Usado na Liquidez Imediata. |
| **V25** | LPA Básico ON | 3.99.01.01 | DRE | Não | Captura direta da folha de detalhe. Proibido usar a conta mãe 3.99. |
| **V26** | LPA Diluído ON | 3.99.02.01 | DRE | Não | Fallback automático para V25 usando COALESCE(V26, V25). |

---

## 2. Regras de Saneamento e Tratamento de Exceções

**N1 — Inversão Estatística do Custo (V18):** O pipeline extrai a conta 3.02 com sinal negativo do PostgreSQL. O contrato estipula a conversão matemática obrigatória (abs(V18)) para mitigar o erro de prazos médios negativos.
**N2 — Diretriz para Empresas sem Estoque:** Caso alguma empresa integrada ao pipeline não reporte estoques (V06), o sistema atribuirá zero para o cálculo de liquidez, mas forçará a saída como **'N/A'** nos indicadores de Giro de Estoque, PMRE e Ciclo Económico, impedindo divisões por zero.
**N3 — Validação Analítica de Outliers (Caso Marisa):** Conforme mapeado no histórico das DFP, a folha 3.99 sofre truncamento. O script deve ler exclusivamente os nós folhas (3.99.01.01 e 3.99.02.01), aplicando a cláusula de barreira abs(VL_CONTA_TRATADO) > 10000 para limpar anomalias de registo de 2021.
**N4 — Consolidação Intertemporal:** O algoritmo coletará as informações agrupando por empresa e data de referência, capturando o maior número de versão (MAX(VERSAO)) para expurgar balanços retificados secundários.

---

## 3. Especificação Algorítmica dos Indicadores (7 Grupos Oficiais)

Os cálculos de tempo e giros operacionais adotam rigorosamente o ano comercial de **360 dias**.

### 3.1 Grupo 1: Liquidez
**Liquidez Geral:** $(V02 + V04) / (V10 + V11)$
**Liquidez Corrente:** $V02 / V10$
**Liquidez Seca:** $(V02 - V06) / V10$
**Liquidez Imediata:** $V22 / V10$

### 3.2 Grupo 2: Endividamento e Estrutura de Capitais
**Participação de Capital de Terceiros / Capital Próprio:** $((V10 + V11) / V12) \times 100$
**Participação de Capital de Terceiros / Ativo Total:** $((V10 + V11) / V01) \times 100$
**Garantia do Capital Próprio ao Capital de Terceiros:** $(V12 / (V10 + V11)) \times 100$
**Composição do Endividamento:** $(V10 / (V10 + V11)) \times 100$
**Imobilização do Capital Próprio:** $(V05 / V12) \times 100$
**Imobilização do Ativo Total:** $(V05 / V01) \times 100$

### 3.3 Grupo 3: Margens
**Margem Bruta:** $(V19 / V17) \times 100$
**Margem Operacional:** $(V20 / V17) \times 100$
**Margem Líquida:** $(V21 / V17) \times 100$
**Lucro por Ação (LPA):** Mapeado via query direta da folha COALESCE(V26, V25)

### 3.4 Grupo 4: Rentabilidade
**ROA (Retorno sobre o Ativo):** $(V21 / V01) \times 100$
**ROE (Retorno sobre o Patrimônio):** Se $V12 > 0 \rightarrow (V21 / V12) \times 100$, caso contrário retornar Nulo (evita distorções de PL negativo).
**ROI (Retorno sobre o Investimento):** $(V21 / (V13 + V14 + V12)) \times 100$

### 3.5 Grupo 5: Atividade (Giros e Prazos — Base de 360 Dias)
**Giro dos Estoques:** $V18 / V06$ | **PMRE (Prazo Médio de Estoque):** $(V06 \times 360) / V18$
**Giro de Contas a Receber:** $V17 / V07$ | **PMRV (Prazo Médio de Recebimento):** $(V07 \times 360) / V17$
**Giro de Contas a Pagar:** $V18 / V09$ | **PMPC (Prazo Médio de Pagamento):** $(V09 \times 360) / V18$
**Giro do Ativo Circulante:** $V17 / V02$ | **PMRAC:** $(V02 \times 360) / V17$

### 3.6 Grupo 6: Ciclos Operacionais
**Ciclo Económico:** $PMRE + PMRV$
**Ciclo Financeiro:** $PMRE + PMRV - PMPC$

### 3.7 Grupo 7: Modelo Dinâmico de Capital de Giro (Fleuriet)
**Capital de Giro Líquido (CGL):** $V02 - V10$
**Ativo Circulante Operacional (ACO):** $V06 + V07$
**Passivo Circulante Operacional (PCO):** $V09$
**Necessidade de Capital de Giro (NCG):** $ACO - PCO$
**Saldo de Tesouraria (ST):** $V15 - V16$

---

## 4. Validação Cruzada de Controle (M. Dias Branco — 2023)

Ponto de controlo estático inserido no pipeline para assegurar o funcionamento dos mapeamentos:
1. **Ativo Circulante (V02):** R$ 4.015.342.000,00 (PostgreSQL integrado vs Demonstrações Oficiais).
2. **Receita Líquida (V17):** R$ 10.843.120.000,00 (PostgreSQL integrado vs Demonstrações Oficiais).

---

## 5. Idiossincrasias e Ajustes Setoriais (Alimentos)

1. **Fusão de Contas de Armazenamento:** Devido às características biológicas da cadeia de fornecimento de proteína animal (JBS e BRF), o script Python obrigatoriamente consolidará os montantes da conta 1.01.07 (Ativos Biológicos de Curto Prazo) à variável padrão de Estoque (V06). Ignorar esta premissa gerará distorções críticas nas métricas de atividade de frigoríficos.
2. **Tratamento de Alavancagem Crítica:** Bloqueio condicional implementado para inibir o output de ROE e ROI quando o denominador apresentar resultado menor ou igual a zero, preservando a coherence estatística da camada Gold.