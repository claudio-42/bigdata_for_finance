# 🥩 Análise Financeira da Minerva Foods (BEEF3)

### Pipeline de dados CVM + Dashboard interativo em Streamlit

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Postgres](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white)

---

## 🎯 Sobre o Projeto

Este repositório entrega uma **análise financeira completa da Minerva Foods (BEEF3)**, a partir de dados públicos oficiais da **CVM (Comissão de Valores Mobiliários)**. Construímos um **pipeline de engenharia de dados** que vai do arquivo bruto da CVM até um **dashboard interativo em Streamlit**, no qual é possível navegar pelos demonstrativos contábeis da empresa e por um conjunto amplo de indicadores financeiros calculados ano a ano.

O produto final responde, com base em dados auditáveis, a perguntas como: *a Minerva tem liquidez para honrar suas obrigações de curto prazo? Qual a sua estrutura de capital e o nível de endividamento? As margens e a rentabilidade (ROE, ROA, ROI) são saudáveis para o setor frigorífico? Como se comportam o ciclo financeiro e o capital de giro (modelo Fleuriet)?*

> A Minerva opera no setor de **proteína animal (carne bovina)**, marcado por margens estreitas, forte componente exportador (sensibilidade ao câmbio) e estoques que incluem **ativos biológicos**. Todas essas particularidades foram tratadas explicitamente no pipeline e nos diagnósticos do dashboard.

---

## 🧭 O que o Dashboard Cobre

O dashboard (`minerva_app_isa_v2.py`) é organizado em abas, com KPIs, gráficos e um **diagnóstico executivo automático** que cruza indicadores, tendências e o contexto setorial. As principais áreas analisadas:

| Aba | O que mostra |
| :--- | :--- |
| 📊 **Visão Geral** | KPIs do último ano (Receita Líquida, Lucro Líquido, Margem Líquida, ROE, Liquidez Corrente, Ciclo Financeiro) e diagnóstico executivo automático. |
| 💧 **Liquidez** | Liquidez corrente, seca e geral, com referências de folga de pagamento. |
| 🏦 **Endividamento** | Participação de capital de terceiros, composição do endividamento (curto vs. longo prazo) e imobilização do ativo. |
| 📈 **Margens & Rentabilidade** | Margem bruta, operacional e líquida; ROA, ROE e ROI, com leitura do efeito da alavancagem. |
| 🔄 **Atividade & Ciclos** | Giros (estoques, contas a receber/pagar) e prazos médios (PMRE, PMRV, PMPC); ciclo econômico e financeiro. |
| 🔁 **Fleuriet** | Capital de Giro Líquido (CGL), Necessidade de Capital de Giro (NCG) e Saldo de Tesouraria — identificação do "Efeito Tesoura". |
| 📋 **Tabela** | Todos os indicadores consolidados, por ano. |
| 🧾 **Balanço (BP)** | Balanço Patrimonial completo e hierárquico. |
| 🧮 **DRE** | Demonstração do Resultado do Exercício, da receita ao lucro líquido. |
| 💵 **DFC** | Demonstração dos Fluxos de Caixa, por atividade (operacional, investimento, financiamento). |

---

## 🏦 Os Três Demonstrativos na Base da Análise

Toda a análise gira em torno de três demonstrativos contábeis extraídos da CVM:

**Balanço Patrimonial (BP) — Grupos 1 e 2.** Fotografia da empresa em um instante:
```
Ativo (Raiz 1) = Passivo + Patrimônio Líquido (Raiz 2)
```

**Demonstração do Resultado (DRE) — Grupo 3.** O desempenho do período, em cascata:
```
Receita Líquida − Custos − Despesas = Lucro/Prejuízo
```

**Demonstração dos Fluxos de Caixa (DFC) — Grupo 6.** A movimentação do dinheiro, com cross-check no BP:
```
Saldo Final de Caixa (DFC 6.05.02) ≈ Disponibilidades no Ativo Circulante (BP 1.01.01 + 1.01.02)
```

Os códigos de conta da CVM (`CD_CONTA`) são **hierárquicos**: o valor de uma conta "pai" deve ser sempre a soma de seus "filhos".
```
1              → Ativo Total               (Nível 1 — Raiz)
├── 1.01       → Ativo Circulante          (Nível 2)
│   ├── 1.01.01 → Caixa e Equivalentes    (Nível 3)
│   └── 1.01.02 → Aplicações Financeiras  (Nível 3)
└── 1.02       → Ativo Não Circulante      (Nível 2)
```

---

## 🏗️ Arquitetura: Medallion (Bronze → Silver → Gold)

O pipeline segue a arquitetura **Medallion**, em que cada camada eleva a qualidade e a confiabilidade do dado.

```
                ┌─────────────────────────────────────────────────┐
                │              Portal de Dados CVM                 │
                │   (DFP Anual, ITR Trimestral, FRE, Cadastro)     │
                └────────────────────┬────────────────────────────┘
                                     │  Download via requests
                                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│  🟤 BRONZE  (layer_01_bronze)                                         │
│  Dado bruto, sem transformação. Ingestão fiel ao que a CVM entrega.   │
└─────────────────────────────┬────────────────────────────────────────┘
                              │  Deduplicação, hierarquia, normalização
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ⚪ SILVER  (layer_02_silver)                                         │
│  Golden Schema. Validação matemática. Flags de auditoria (IS_LEAF...)  │
└─────────────────────────────┬────────────────────────────────────────┘
                              │  Cálculo dos indicadores financeiros
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  🟡 GOLD  (layer_03_gold)                                             │
│  Tabela de indicadores pronta para análise e dashboards               │
└─────────────────────────────┬────────────────────────────────────────┘
                              │
                              ▼
                  ┌─────────────────────────────┐
                  │   Dashboard Streamlit        │
                  │   (minerva_app_isa_v2.py)    │
                  └─────────────────────────────┘
```

---

## 🚶 Passo a Passo do Processo (Como os Dados Foram Obtidos)

Cada notebook documenta uma etapa do pipeline. Executados em ordem, eles reproduzem toda a base que alimenta o dashboard.

### 🟤 Camada Bronze — `notebooks/01_bronze/`

A ingestão baixa os arquivos `.zip` diretamente do portal da CVM, extrai os CSVs em memória e os grava no PostgreSQL **sem transformação** — fieis ao que a CVM entrega.

1. **Coleta da DFP / ITR (agnóstica).** Um pipeline reutilizável baixa os arquivos anuais (DFP) e trimestrais (ITR) por ano, com controle de logs, deduplicação por reenvio e detecção de *schema drift*. Fonte: `dados.cvm.gov.br/dados/CIA_ABERTA/DOC/`.
2. **Coleta do FRE (Formulário de Referência).** Traz dados de governança, controle acionário e estrutura societária.
3. **Coleta do Cadastro de Companhias.** Dados cadastrais (CNPJ, situação, setor, governança), usado para identificar e filtrar as empresas elegíveis.

Cada carga é registrada em tabelas de log e gravada no schema bronze via `to_sql` em *chunks*, lendo os CSVs em `windows-1252` (encoding padrão da CVM).

### ⚪ Camada Silver — `notebooks/02_silver/`

Aqui o dado bruto vira um **Golden Schema** padronizado, validado e auditável.

0. **Análise exploratória do universo de empresas.** A partir do cadastro completo da CVM (~2.675 registros), aplica-se um **funil de filtragem**: apenas situação `ATIVO`, mercado `BOLSA`, emissor em `FASE OPERACIONAL`, e exclusão de holdings, bancos, seguradoras, financeiras e securitizadoras. A exclusão do setor financeiro é uma exigência de **comparabilidade contábil** (COSIF/SUSEP não são comparáveis ao IFRS industrial). Restam ~229 empresas operacionais comparáveis — entre elas, a Minerva.
1–2. **Consolidação das DFPs.** Os 7 tipos de demonstrativo (BPA, BPP, DRE, DRA, DMPL, DFC, DVA) são extraídos da bronze, têm a **escala normalizada** (MIL → UNIDADE), são **deduplicados por versão** (`ROW_NUMBER()` particionado, mantendo a versão mais recente) e recebem a marcação de **conta-folha (`IS_LEAF`)**.
3–5. **Reconstrução hierárquica de BP, DRE e DFC.** Cada demonstrativo é tratado individualmente: contas "pai" ausentes são reconstruídas pela soma dos filhos (em **Safe Mode** — nunca sobrescreve um valor original da CVM), os nomes de contas são padronizados por um **Golden Map**, e o resultado passa por **validação matemática** (ex.: Ativo − Passivo = 0; Lucro Bruto e EBIT batendo com a hierarquia).

Cada linha carrega colunas de **rastreabilidade**: `DS_CONTA_REPORTADA` (nome original), `FLAG_NORMALIZACAO`, `FLAG_RECONSTRUCAO`, `STATUS_MATH` e `IS_LEAF`.

> ⚠️ **Regra de ouro:** ao somar contas, sempre filtrar `IS_LEAF = True`. Somar todos os níveis hierárquicos causa dupla contagem.

### 🟡 Camada Gold — `notebooks/03_gold/`

A camada Gold transforma os demonstrativos validados em **indicadores financeiros prontos para análise**.

0. **Cálculo dos indicadores.** A partir de um mapeamento *De-Para* contábil (documentado no *data contract* `premissas_setor_alimentos.md`), as variáveis são extraídas com os filtros `ORDEM_EXERC = 'LAST'` e `IS_LEAF = true`, e os indicadores são calculados com divisões seguras (`safe_div`) e travas de negócio (ex.: PL ≤ 0 anula ROE/ROI). Tratamentos específicos do setor: estoque = estoque padrão (1.01.04) **+ ativos biológicos** (1.01.07); CPV em valor absoluto.
1. **Benchmarking setorial.** Os indicadores da Minerva são comparados ao universo de empresas, com radar de alertas (liquidez crítica, endividamento elevado, margem/ROE negativos, ciclo longo, classificação Fleuriet de risco) e scorecard de ranking setorial.

#### Indicadores calculados

- **Liquidez:** corrente, seca, geral.
- **Endividamento:** capital de terceiros / capital próprio, capital de terceiros / ativo total, garantia do capital próprio, composição do endividamento, imobilização do capital próprio e do ativo.
- **Margens:** bruta, operacional, líquida; LPA diluído.
- **Rentabilidade:** ROA, ROE, ROI.
- **Atividade:** giros (estoques, contas a receber, contas a pagar, ativo circulante); prazos médios PMRE, PMRV, PMPC, PMRAC.
- **Ciclos:** ciclo econômico e ciclo financeiro.
- **Modelo Fleuriet:** CGL, NCG, Saldo de Tesouraria e classificação de estrutura financeira (Tipos I a VI).

---

## 📁 Estrutura do Projeto

```
bigdata_for_finance/
│
├── notebooks/
│   ├── 01_bronze/                  # Ingestão dos dados brutos da CVM
│   │   ├── 2_coletando_dados_fre.ipynb
│   │   └── 3_coletando_dados_cvm_agnostico.ipynb
│   │
│   ├── 02_silver/                  # Curadoria, hierarquia e validação
│   │   ├── 0_analise_exploratoria_empresas_selecionadas.ipynb
│   │   ├── 2_reescrevendo_dfp_tratadas_na_camada_silver.ipynb
│   │   ├── 3_escrevendo_a_tabela_bp_...ipynb
│   │   ├── 4_escrevendo_a_tabela_dre_...ipynb
│   │   └── 5_escrevendo_a_tabela_dfc_...ipynb
│   │
│   └── 03_gold/                    # Cálculo de indicadores e benchmarking
│       ├── 0_calculando_indicadores_camada_gold.ipynb
│       └── 1_benchmarking_indicadores_financeiros.ipynb
│
├── premissas_setor_alimentos.md    # Data contract (De-Para e fórmulas)
├── minerva_app_isa_v2.py           # Dashboard Streamlit (arquivo único)
├── .env                            # Credenciais do banco (não versionado)
├── requirements.txt                # Dependências Python
└── README.md                       # Este arquivo
```

---

## 🗂️ Fontes de Dados (CVM)

| Dataset | Descrição | Link |
| :--- | :--- | :---: |
| **Cadastro de Cias Abertas** | CNPJ, situação, setor, governança | [🔗](https://dados.cvm.gov.br/dataset/cia_aberta-cad) |
| **DFP** | BP, DRE, DFC — dados **anuais** | [🔗](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp) |
| **ITR** | BP, DRE, DFC — dados **trimestrais** | [🔗](https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr) |
| **FRE** | Governança e controle acionário | [🔗](https://dados.cvm.gov.br/dataset/cia_aberta-doc-fre) |

> 📂 Diretório completo: [dados.cvm.gov.br/dados/CIA_ABERTA/DOC/](http://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/)

---

## 🛠️ Tecnologias

| Categoria | Tecnologia |
| :--- | :--- |
| Linguagem | Python 3.10+ |
| Banco de Dados | PostgreSQL |
| Notebooks | Jupyter / VS Code |
| Dashboard | Streamlit + Plotly |
| Conexão | SQLAlchemy + psycopg2 |
| Dados | pandas |
| Config | python-dotenv |

---

## 🚀 Como Rodar

### 1. Pré-requisitos
- Python 3.10+
- PostgreSQL rodando localmente (ou acessível remotamente)
- Git

### 2. Instale as dependências
```bash
pip install streamlit plotly pandas sqlalchemy psycopg2-binary python-dotenv
```

### 3. Configure o `.env`
Crie um arquivo `.env` na raiz com as credenciais do banco:
```env
DB_USER=seu_usuario
DB_PASS=sua_senha
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nome_do_banco
```

### 4. Construa a base (na ordem)
Execute os notebooks **bronze → silver → gold**. Ao final, a tabela de indicadores da camada Gold estará pronta para o dashboard.

### 5. Rode o dashboard
```bash
streamlit run minerva_app_isa_v2.py
```

> ☁️ **Deploy no Streamlit Cloud:** configure as credenciais em **Settings → Secrets**, separadamente (`DB_USER`, `DB_PASS`, etc.) ou via `DATABASE_URL = "postgresql://usuario:senha@host:5432/nome_do_banco"`.

---

## 📌 Premissas e Decisões Metodológicas

- **Safe Mode na curadoria:** nunca sobrescrevemos um valor original da CVM quando `abs(valor) > 0.01`. A reconstrução de contas-pai apenas preenche lacunas.
- **Filtro de unicidade:** consumo da Gold sempre com `ORDEM_EXERC = 'LAST'` e `IS_LEAF = true` para evitar duplicações por reenvio de documentos.
- **Tratamento setorial:** estoques incluem ativos biológicos (conta 1.01.07), o que tende a alongar o PMRE e o ciclo financeiro — comportamento esperado para frigoríficos.
- **PL negativo:** quando o Patrimônio Líquido é ≤ 0, ROE e ROI são anulados/sinalizados, pois perdem significado econômico.

---

*Projeto desenvolvido na disciplina de Big Data for Finance.*
