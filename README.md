# 📊 Big Data for Finance — Pipeline CVM

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Postgres](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white)
![Gitmoji](https://img.shields.io/badge/Gitmoji-%F0%9F%8E%A8-FFDD67?style=for-the-badge)

## 🎯 Objetivo do Projeto

Este repositório é o projeto central da disciplina de **Big Data for Finance**. O objetivo é construir um **pipeline completo de Engenharia de Dados Financeiros**, do dado bruto até a análise, utilizando dados públicos de companhias abertas da B3, disponibilizados pela **CVM (Comissão de Valores Mobiliários)**.

O produto final é um **"Golden Schema"** harmonizado e validado, pronto para análise e com diversos indicadores financeiros calculados.

> 💡 **Para o aluno:** Você vai aprender na prática como dados financeiros reais chegam "sujos" do mundo real e como um pipeline de dados os transforma em algo confiável, auditável e útil para tomada de decisão.

---

## 🧠 Contexto: Por que isso é difícil?

Os dados da CVM são públicos, mas vêm com vários problemas reais que você vai aprender a resolver:

| Problema | Como resolvemos |
| :--- | :--- |
| Múltiplas versões do mesmo documento | Deduplicação via `ROW_NUMBER()` no PostgreSQL |
| Empresas não reportam todas as contas | Reconstrução de contas "pai" por soma dos filhos |
| Nomes de contas variam entre empresas | *Golden Map* de normalização de nomes |
| Hierarquia de contas precisa ser íntegra | Validação matemática vertical (pai = soma dos filhos) |
| Balanço pode estar desbalanceado | Validação da equação: Ativo − Passivo = 0 |

---

## 🏦 Os Três Demonstrativos Financeiros

Todo o pipeline gira em torno de três demonstrativos. Entendê-los é pré-requisito para contribuir com o projeto:

### Balanço Patrimonial (BP) — Grupos 1 e 2
Fotografia da empresa em um instante. **Equação fundamental:**
```
Ativo (Raiz 1) = Passivo + Patrimônio Líquido (Raiz 2)
```

### Demonstração do Resultado (DRE) — Grupo 3
Filme do desempenho no período. Funciona em cascata:
```
Receita Líquida − Custos − Despesas = Lucro/Prejuízo
```

### Demonstração dos Fluxos de Caixa (DFC) — Grupo 6
Mostra de onde veio e para onde foi o dinheiro vivo. Cross-check com o BP:
```
Saldo Final de Caixa (DFC 6.05.02) ≈ Disponibilidades no Ativo Circulante (BP 1.01.01 + 1.01.02)
```

### A Taxonomia CVM (CD_CONTA)
Os códigos de conta são hierárquicos, ou seja, o valor de um "pai" deve ser sempre a soma de seus "filhos":

```
1              → Ativo Total               (Nível 1 — Raiz)
├── 1.01       → Ativo Circulante          (Nível 2)
│   ├── 1.01.01 → Caixa e Equivalentes    (Nível 3)
│   └── 1.01.02 → Aplicações Financeiras  (Nível 3)
└── 1.02       → Ativo Não Circulante      (Nível 2)
```

---

## 🏗️ Arquitetura: Medallion (Bronze → Silver → Gold)

```
                     ┌─────────────────────────────────────────────────┐
                     │              Portal de Dados CVM                 │
                     │   (DFP Anual, ITR Trimestral, FRE, Cadastro)    │
                     └────────────────────┬────────────────────────────┘
                                          │  Download via requests
                                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│  🟤 BRONZE  (layer_01_bronze)                                         │
│  Dado bruto, sem transformação. Ingestão fiel ao que a CVM entrega.  │
│  PostgreSQL schema: bronze_01                                         │
└─────────────────────────────┬────────────────────────────────────────┘
                              │  Deduplicação, hierarquia, normalização
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ⚪ SILVER  (layer_02_silver)                                         │
│  Golden Schema (26 colunas). Validação matemática. Flags de auditoria│
│  PostgreSQL schema: silver_02                                         │
└─────────────────────────────┬────────────────────────────────────────┘
                              │  Agregações e métricas de negócio
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  🟡 GOLD  (layer_03_gold)                                             │
│  Tabelas prontas para análise, Valuation e dashboards                 │
│  PostgreSQL schema: gold_03                                           │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Dashboard Streamlit  │
                    │  (dashboard/app.py)   │
                    └─────────────────────┘
```

---

## 📁 Estrutura do Projeto

```
bigdata_for_finance/
│
├── notebooks/
│   ├── 01_bronze/                          # Ingestão de dados brutos
│   │
│   ├── 02_silver/                          # Curadoria e transformação
│   │
│   └── 03_gold/                            # Agregações finais e cálculo dos indicadores
│
├── queries/                                # Consultas que formos fazendo para compreender os dados e que valem a pena serem salvas
│
├── dashboard/                              # Aplicação Streamlit
│   ├── app.py                              # Ponto de entrada da aplicação
│   ├── config.py                           # Paleta de cores e configurações
│   ├── database.py                         # Conexão e cache PostgreSQL
│   └── views/                             # Telas do dashboard
│
│
├── .env                                    # Variáveis de ambiente (não commitado)
├── requirements.txt                        # Dependências Python
└── README.md                               # Este arquivo
```

---

## 🥈 O Silver Schema (Camada Silver)

Todas as tabelas da camada Silver seguem um padrão de **26 colunas** que permite empilhar qualquer demonstrativo com `UNION ALL`. As colunas de rastreabilidade são obrigatórias:

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `DS_CONTA_REPORTADA` | `TEXT` | Nome **original** da CVM — garante auditoria |
| `FLAG_RECONSTRUCAO` | `BOOL` | `True` se a linha foi criada sinteticamente (pai reconstruído) |
| `FLAG_NORMALIZACAO` | `BOOL` | `True` se o nome foi alterado pelo Golden Map |
| `STATUS_MATH` | `TEXT` | Resultado da validação: `'OK'`, `'DESBALANCEADO'` ou `'ZERADO'` |
| `IS_LEAF` | `BOOL` | `True` se é o nível mais analítico — **só estes devem ser somados no BI** |

> ⚠️ **Regra de Ouro:** Nunca some contas no Power BI/Looker sem filtrar `IS_LEAF = True`. Somar todos os níveis causa dupla contagem.

---

## 🗂️ Fontes de Dados (CVM)

| Dataset | Descrição | Link |
| :--- | :--- | :---: |
| **Cadastro de Cias Abertas** | Dados cadastrais (CNPJ, Situação, Setor, Governança) | [🔗](https://dados.cvm.gov.br/dataset/cia_aberta-cad) |
| **DFP (Demonstrações Financeiras Padronizadas)** | BP, DRE, DFC — dados **anuais** | [🔗](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp) |
| **ITR (Informações Trimestrais)** | BP, DRE, DFC — dados **trimestrais** | [🔗](https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr) |
| **FRE (Formulário de Referência)** | Governança, controle acionário, riscos | [🔗](https://dados.cvm.gov.br/dataset/cia_aberta-doc-fre) |

> 📂 **Diretório completo de arquivos CVM:** [http://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/](http://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/)

---

## 🛠️ Tecnologias Utilizadas

| Categoria | Tecnologia | Uso |
| :--- | :--- | :--- |
| Linguagem | Python 3.10+ | Pipeline e notebooks |
| Banco de Dados | PostgreSQL | Armazenamento de todas as camadas |
| Notebooks | Jupyter / VS Code | Desenvolvimento iterativo |
| Dashboard | Streamlit + Plotly | Visualização dos dados |
| ORM / Conexão | SQLAlchemy + psycopg2 | Interface Python ↔ PostgreSQL |
| Dados | pandas + pyarrow | Manipulação e transformação |
| Config | python-dotenv | Gerenciamento de credenciais |

---

## 🚀 Setup do Seu Projeto

> 💡 Cada aluno terá o **seu próprio repositório**. Este guia cobre apenas o setup inicial do ambiente.

### 1. Pré-requisitos

Instale antes de começar:

- [Python 3.10+](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/) — instale e deixe rodando localmente
- [VS Code](https://code.visualstudio.com/) com as extensões **Python** e **Jupyter**
- [Git](https://git-scm.com/downloads)

### 2. Crie o projeto localmente e publique no GitHub via VS Code

1. Crie a pasta `bigdata_for_finance` dentro de `Documentos`
2. Abra o VS Code e use **File → Open Folder** para abrir essa pasta
3. No painel **Source Control** (`Ctrl+Shift+G`), clique em **"Initialize Repository"**
4. Faça o primeiro commit (ex: `🎉 Iniciando o projeto`)
5. Clique em **"Publish Branch"** — o VS Code cria o repositório no GitHub e faz o push inicial automaticamente

> 💡 Não é necessário criar o repositório no GitHub antes. O VS Code faz tudo isso na etapa de publicação.

### 3. Crie a estrutura de pastas do projeto

Dentro da pasta do projeto, crie as seguintes pastas — pode fazer direto pelo VS Code (clique com o botão direito no Explorer → **New Folder**):

- `notebooks/01_bronze/`
- `notebooks/02_silver/`
- `notebooks/03_gold/`
- `queries/`
- `dashboard/`

> Consulte a seção [📁 Estrutura do Projeto](#-estrutura-do-projeto) para entender o propósito de cada pasta.

### 4. Instale as dependências Python

> ⚠️ **Contexto do laboratório:** Em ambientes com restrições de segurança (como os computadores do laboratório), não é possível criar ou ativar ambientes virtuais (`venv`). Por isso, as dependências serão instaladas diretamente no Python do sistema, o que é suficiente para o curso.

Com o arquivo `requirements.txt` fornecido pelo professor na raiz do projeto, execute no terminal do VS Code:

```bash
pip install -r requirements.txt
```

### 5. Configure o `.gitignore`

Crie um arquivo `.gitignore` na raiz do projeto com no mínimo:

```gitignore
.venv/
.env
__pycache__/
*.pyc
.ipynb_checkpoints/
```

### 6. Configure as credenciais do banco

Crie um arquivo `.env` na raiz do projeto:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bigdata_for_finance
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
```

> ⚠️ O `.env` contém suas credenciais pessoais, ele já está no `.gitignore` e **jamais deve ser commitado**.

### 7. Crie o banco de dados e os schemas no PostgreSQL

Execute no **pgAdmin** ou no terminal `psql`:

```sql
CREATE DATABASE bigdata_for_finance;

\c bigdata_for_finance

CREATE SCHEMA IF NOT EXISTS layer_01_bronze;
CREATE SCHEMA IF NOT EXISTS layer_02_silver;
CREATE SCHEMA IF NOT EXISTS layer_03_gold;
```

### 8. Pronto — aguarde as instruções do professor 🎓

A partir daqui cada aula adicionará novos notebooks e scripts ao seu projeto. Siga sempre a sequência:

```
notebooks/01_bronze/ → notebooks/02_silver/ → notebooks/03_gold/
```


---

## 📐 Regras Inegociáveis

Para manter a qualidade do pipeline, todo código deve respeitar:

1. **Safe Mode na Curadoria Vertical:** Nunca sobrescreva um valor original da CVM se `abs(valor) > 0.01`. Reconstrução de pais só preenche lacunas (nulos/zeros).

2. **IS_LEAF obrigatório:** Toda tabela Silver deve ter a coluna `IS_LEAF` corretamente calculada.

3. **Deduplicação blindada:** Sempre use `ROW_NUMBER()` particionado por `(CNPJ, DT_REFER, CD_CONTA, DS_CONTA)` ordenado por `VERSAO DESC` para garantir a versão mais recente.

4. **SQL com CTEs:** Prefira `WITH nome_cte AS (...)` para legibilidade. Use aspas duplas `"NOME_COLUNA"` no PostgreSQL.

5. **Logs legíveis:** Use emojis nos `print()` para demarcar etapas do pipeline:
   ```python
   print("🟤 [BRONZE] Iniciando download da DFP...")
   print("⚪ [SILVER] Aplicando Golden Map de normalização...")
   print("✅ [SILVER] Validação matemática concluída.")
   ```

---

*Projeto desenvolvido na disciplina de Big Data for Finance pelo Prof. Ivan Ribeiro Mello.*
