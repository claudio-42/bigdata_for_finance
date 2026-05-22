# Dicionário de Variáveis e Premissas — Setor: Alimentos

Este documento serve para mapear as contas que o nosso grupo vai puxar da camada Silver (layer_02_silver) e estruturar as variáveis para rodar os cálculos dos indicadores em Python na camada Gold.

---

## 1. Tabela De-Para (Mapeamento de Contas do Banco)

Para rodar as queries sem duplicar valores e pegar o dado correto, o grupo definiu que os filtros obrigatórios no SQL serão: `ORDEM_EXERC = 'LAST'` e `"IS_LEAF" = true`.

| Código | Descrição da Variável | Código da Conta (`CD_CONTA`) | Origem | Conta Fixa? (`ST_CONTA_FIXA`) | Regra de Tratamento / Observações |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **V01** | Ativo Circulante (AC) | `1.01` | BP | S | Padrão da CVM. |
| **V02** | Realizável a Longo Prazo (RLP) | `1.02.01` | BP | S | Vem do Ativo Não Circulante. |
| **V03** | Passivo Circulante (PC) | `2.01` | BP | S | Padrão da CVM. |
| **V04** | Exigível a Longo Prazo (ELP) | `2.02` | BP | S | Equivalente ao Passivo Não Circulante. |
| **V05** | Ativo Circulante Financeiro (ACF) | `1.01.01` + `1.01.02` | BP | N | Precisa somar Caixa (`1.01.01`) com Aplicações (`1.01.02`). |
| **V06** | Passivo Circulante Financeiro (PCF) | `2.01.04` | BP | N | Pegar só a conta de Empréstimos e Financiamentos de Curto Prazo. |
| **V07** | Ativo Circulante Operacional (ACO) | *Cálculo* | BP | N | Conta calculada no Python fazendo V01 - V05. |
| **V08** | Passivo Circulante Operacional (PCO) | *Cálculo* | BP | N | Conta calculada no Python fazendo V03 - V06. |
| **V09** | Receita Líquida de Vendas | `3.01` | DRE | S | Variável base para as margens e os giros. |
| **V10** | Lucro Bruto | `3.03` | DRE | S | Padrão da CVM. |
| **V11** | Lucro Operacional (EBIT) | `3.05` | DRE | S | Resultado Antes do Resultado Financeiro e Impostos. |
| **V12** | Lucro Líquido | `3.11` | DRE | S | Resultado final consolidado da empresa. |
| **V13** | Patrimônio Líquido (PL) | `2.03` | BP | S | Usado para calcular o ROE e Endividamento. |
| **V14** | Ativo Total | `1` | BP | S | Conta raiz. |
| **V15** | Custo das Vendas (CMV) | `3.02` | DRE | S | Vem negativo do banco de dados, precisa tratar no código usando abs(). |
| **V16** | Saldo de Estoques | `1.01.04` | BP | S | Muito importante para o setor de alimentos por causa dos grãos/insumos. |
| **V17** | Contas a Receber (Clientes) | `1.01.03` | BP | S | Valores a receber de supermercados e distribuidores. |
| **V18** | Fornecedores | `2.01.02` | BP | S | Dívida com produtores de matéria-prima. |

---

## 2. Notas de Tratamento e Regras de Negócio (Ajustes para o Código)

* **Nota 1 (Inversão do CMV):** Como os valores de custo (conta `3.02`) vêm com sinal negativo direto do banco, vamos aplicar a função `abs()` no script em Python para não quebrar as fórmulas de rotação e prazos médios.
* **Nota 2 (Contas Inexistentes):** Nem todas as empresas do setor listam aplicações financeiras de curto prazo (`1.01.02`). Se a query retornar nulo ou vazio para essa conta, o script vai considerar o valor como 0 para não travar a soma do ACF.
* **Nota 3 (Filtro IS_LEAF):** Para não duplicar ou inflar os valores na hora de somar as contas-mãe, todas as buscas feitas via SQLAlchemy vão rodar obrigatoriamente com o filtro `WHERE IS_LEAF = true`.
* **Nota 4 (Ajuste de Versões das DFPs):** Quando alguma empresa tiver reenviado os dados (gerando mais de uma versão no banco), o algoritmo vai ordenar pela coluna de versão e manter apenas o registro mais atualizado para o cálculo final.

---

## 3. Fórmulas dos Indicadores (7 Grupos)

As variáveis listadas acima serão usadas no pipeline para calcular os seguintes indicadores:

1. **Liquidez:** Corrente ($V01 / V03$), Seca ($(V01 - V16) / V03$), Geral ($(V01 + V02) / (V03 + V04)$) e Imediata ($V05 / V03$).
2. **Endividamento:** Grau de Endividamento Total ($(V03 + V04) / V14$) e Participação de Capital de Terceiros ($(V03 + V04) / V13$).
3. **Margens:** Margem Bruta ($V10 / V09$), Margem Operacional ($V11 / V09$) e Margem Líquida ($V12 / V09$).
4. **Rentabilidade:** ROA ($V12 / V14$), ROE ($V12 / V13$) e Giro do Ativo ($V09 / V14$).
5. **Atividade:** Giro de Estoques ($V15 / V16$), Giro de Clientes ($V09 / V17$) e Giro de Fornecedores ($V15 / V18$).
6. **Ciclos:** PME ($365 / \text{Giro Estoques}$), PMR ($365 / \text{Giro Clientes}$) e PMP ($365 / \text{Giro Fornecedores}$). Ciclo Operacional ($PME + PMR$) e Ciclo Financeiro ($(PME + PMR) - PMP$).
7. **Modelo Dinâmico:** Capital de Giro ($V01 - V03$), Necessidade de Capital de Giro ($V07 - V08$) e Saldo de Tesouraria ($V05 - V06$).

---

## 4. Validação Cruzada (Amostra de Teste)

Para provar que os dados que estão saindo do banco batem com a realidade, o grupo escolheu a empresa M. Dias Branco S.A. (CD_CVM: 020443) do ano de 2023 para fazer a checagem manual:

1. **Ativo Circulante (Conta 1.01):** O valor extraído do PostgreSQL bateu certinho com o balanço patrimonial oficial publicado no StatusInvest (R$ 4.015.342.000,00). Dados validados.
2. **Receita de Venda (Conta 3.01):** O saldo da DRE no banco também bateu com o número oficial do mercado (R$ 10.843.120.000,00). Dados validados.

---

## 5. Anomalias Mapeadas no Setor de Alimentos

Durante a análise prévia do setor de alimentos, encontramos alguns pontos fora da curva que o nosso código Python vai precisar tratar:

1. **Ativos Biológicos (JBS e BRF):** Empresas grandes de proteína animal deixam bilhões lançados como "Ativos Biológicos" (animais/aves em crescimento) na conta `1.01.07`. Se o nosso código calcular o Giro de Estoques olhando puramente a conta padrão de estoque (`1.01.04`), o resultado vai dar distorcido. Vamos precisar colocar um aviso ou tratar essa conta no código.
2. **Problema do PL Negativo:** Empresas que estão em crise pesada ou recuperação judicial podem apresentar Passivo maior que o Ativo (Patrimônio Líquido Negativo). Se o Python tentar calcular o ROE (Lucro dividido por PL) sem travar isso, o resultado vai dar positivo de forma errada (Prejuízo dividido por número negativo dá positivo). Vamos colocar uma trava `if PL <= 0` para deixar o resultado como nulo nesses casos.