# Projeto 01 — Pipeline de ETL com Validação de Qualidade de Dados

[[davi-matos-marques-silva]]
[[data-quality-api]]

## 1. Problema que resolve

Dados públicos brasileiros (Receita Federal, IBGE, Banco Central) chegam
sujos: CNPJ/CPF mal formatado, encoding quebrado (latin-1 misturado com
utf-8), campos vazios, tipos inconsistentes (datas em formatos diferentes
na mesma coluna), duplicatas. Sistemas que carregam esse dado sem validar
quebram silenciosamente em produção — o pior tipo de bug, porque não dá
erro, só corrompe a análise.

Esse projeto prova que você sabe construir um pipeline que **não confia
cegamente na fonte**: valida, rejeita o que é inválido, registra por que
rejeitou, e só carrega o que passou.

## 2. Fonte de dados sugerida

Escolha uma (comece por uma só, pode expandir depois):

- **CNPJ da Receita Federal** — dataset público, pesado (vários GB),
  ótimo para mostrar que você lida com volume. https://dados.gov.br
- **IBGE — Cadastro de municípios / Censo** — menor, mais rápido de
  iterar no começo.
- **Banco Central — Taxas de câmbio / SELIC via API** — dado que atualiza,
  bom para simular pipeline incremental (não só carga única).

Recomendação: comece pelo **CNPJ** (mais "backend + dados" de verdade,
mais notório para recrutador brasileiro reconhecer o valor).

## 3. Arquitetura

```
[Fonte pública]
      │ download (CSV/ZIP)
      ▼
[Extract] ──► arquivo bruto salvo em /raw (nunca sobrescrito)
      │
      ▼
[Validate] ──► aplica regras de schema e negócio
      │         registra falhas em tabela/arquivo de erros (quarentena)
      ▼
[Transform] ──► normaliza tipos, formata CNPJ/CPF, trata encoding
      │
      ▼
[Load] ──► grava no Postgres via stored procedure (upsert idempotente)
      │
      ▼
[Report] ──► log/arquivo com métricas: linhas lidas, válidas, rejeitadas
```

Princípios:
- **Idempotência**: rodar o pipeline duas vezes com o mesmo arquivo não
  duplica dado (upsert por chave natural, ex. CNPJ).
- **Nunca falha silenciosamente**: linha inválida vai para uma tabela/
  arquivo de quarentena com o motivo da rejeição, não é descartada sem
  rastro.
- **Separação de responsabilidade**: cada etapa (extract/validate/
  transform/load) é uma função/módulo isolado, testável sozinho.

## 4. Stack técnica

- **Linguagem:** Python 3.12+
- **Manipulação de dados:** Pandas (ou Polars, se quiser diferenciar —
  mais rápido, mais moderno, bom argumento de entrevista)
- **Validação de schema:** Pydantic ou Pandera (Pandera é feito
  especificamente para validar DataFrames — mais natural aqui)
- **Banco:** PostgreSQL
- **Acesso ao banco:** SQLAlchemy + stored procedures em PL/pgSQL (para
  reforçar a parte de SQL avançado do seu currículo)
- **Orquestração (opcional, fase 2):** um script com CLI (Typer/argparse)
  é suficiente para o MVP; se quiser ir além, Airflow ou Prefect viram
  diferencial — mas só depois do pipeline "manual" estar sólido.
- **Testes:** pytest
- **Containerização:** Docker + docker-compose (Python app + Postgres)
- **CI:** GitHub Actions (lint + testes a cada push)

## 5. Estrutura de pastas sugerida

```
etl-data-quality/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
├── src/
│   ├── extract.py
│   ├── validate.py
│   ├── transform.py
│   ├── load.py
│   ├── pipeline.py        # orquestra as 4 etapas
│   └── schemas.py         # definições Pandera/Pydantic
├── sql/
│   └── procedures/
│       └── upsert_empresa.sql
├── tests/
│   ├── test_validate.py
│   ├── test_transform.py
│   └── fixtures/
│       └── sample_dirty_data.csv
└── data/
    ├── raw/                # nunca commitado (.gitignore)
    └── quarantine/         # linhas rejeitadas, nunca commitado
```

## 6. Regras de validação (exemplos concretos a implementar)

- CNPJ/CPF: formato correto + dígito verificador válido (não só regex).
- Datas: formato único após transformação (ISO 8601).
- Campos obrigatórios: não podem vir nulos (ex. razão social).
- Encoding: detectar e converter para UTF-8 de forma consistente.
- Duplicatas: mesma chave natural não entra duas vezes na mesma carga.
- Faixas de valor: campos numéricos dentro de limites plausíveis
  (ex. CEP com 8 dígitos).

Cada regra violada grava: `linha_original`, `motivo_rejeicao`,
`timestamp_processamento` — isso é o que separa um projeto de validação
de verdade de um `if` solto no meio do código.

## 7. Passo a passo de implementação

1. **Setup**: repo, Docker Compose com Postgres, estrutura de pastas.
2. **Extract**: função que baixa/lê o arquivo bruto e salva em `/raw`
   com timestamp no nome (nunca sobrescreve).
3. **Schema de validação**: definir com Pandera as regras da seção 6.
4. **Validate**: função que roda o schema contra o DataFrame, separa
   linhas válidas de inválidas, grava quarentena.
5. **Transform**: normalização (encoding, formatos, tipos) só nas
   linhas válidas.
6. **Load**: stored procedure de upsert no Postgres; função Python que
   chama a procedure em lote (batch insert, não linha a linha).
7. **Pipeline**: script que orquestra as 4 etapas e imprime/loga um
   relatório final (linhas lidas, válidas, rejeitadas, tempo total).
8. **Testes**: cobrir pelo menos cada regra de validação e um teste de
   idempotência (rodar duas vezes, checar que não duplicou).
9. **CI**: GitHub Actions rodando `pytest` a cada push.
10. **README**: seguir o padrão definido no plano de vitrine (problema →
    arquitetura → como rodar → decisões técnicas → testes).

## 8. Decisões técnicas a documentar no README (diferencial)

- Por que quarentena ao invés de simplesmente descartar linhas inválidas.
- Por que upsert idempotente ao invés de truncate-and-reload.
- Trade-off Pandas vs. Polars, se você decidir testar os dois.
- Como você lidaria com volume maior que a memória (próximo passo:
  processamento em chunks/streaming) — mesmo sem implementar, citar
  mostra que você pensa em escala.

## 9. Critério de "pronto para fixar no GitHub"

- [ ] `docker compose up` sobe tudo e roda o pipeline fim a fim.
- [ ] Testes passando com `pytest`.
- [ ] CI verde no GitHub Actions.
- [ ] README completo seguindo o padrão (problema, arquitetura, como
      rodar, decisões técnicas).
- [ ] Pelo menos um dataset real processado de ponta a ponta (não só
      dado sintético nos testes).
