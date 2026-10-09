# Backlog técnico — ETL com validação de qualidade de dados

## Objetivo
Construir um pipeline ETL em Python para dados públicos brasileiros com validação de qualidade, quarentena de registros inválidos, normalização e carga idempotente em PostgreSQL.

## Premissas
- Entrega mínima viável (MVP): pipeline completo em Python, banco PostgreSQL, testes automatizados e documentação básica.
- Priorização:
  - P0 = obrigatório para o MVP
  - P1 = importante para robustez
  - P2 = diferencial/opcional

## Epic 1 — Setup do projeto e ambiente
### E1.1 — Criar estrutura inicial do repositório
- Objetivo: montar a base do projeto.
- Itens:
  - criar pastas `src/`, `tests/`, `sql/procedures/`, `data/raw/`, `data/quarantine/`
  - criar `README.md` inicial
  - criar `.gitignore`
- Critério de aceite:
  - estrutura do projeto está organizada e pronta para uso
- Prioridade: P0
- Estimativa: 1-2h

### E1.2 — Configurar ambiente Python
- Objetivo: garantir compatibilidade com Python 3.12+.
- Itens:
  - criar ambiente virtual
  - definir `requirements.txt`
  - instalar dependências
- Dependências sugeridas:
  - pandas ou polars
  - sqlalchemy
  - psycopg2-binary
  - pydantic
  - pandera
  - pytest
  - python-dotenv
  - typer ou argparse
- Critério de aceite:
  - ambiente funcional e dependencies instaladas
- Prioridade: P0
- Estimativa: 1h

### E1.3 — Configurar PostgreSQL via Docker
- Objetivo: rodar o banco localmente.
- Itens:
  - criar `docker-compose.yml` com serviço postgres
  - configurar volume persistente
  - expor porta padrão 5432
- Critério de aceite:
  - `docker compose up` sobe o banco sem erros
- Prioridade: P0
- Estimativa: 2h

### E1.4 — Criar Dockerfile da aplicação
- Objetivo: empacotar o app Python para execução em container.
- Itens:
  - definir imagem base
  - instalar dependências
  - copiar código fonte
  - definir entrypoint
- Critério de aceite:
  - app consegue iniciar no ambiente Docker
- Prioridade: P1
- Estimativa: 1h

## Epic 2 — Modelagem do banco e carga idempotente
### E2.1 — Definir schema da tabela de destino
- Objetivo: modelar os dados que passarão pelo pipeline.
- Campos sugeridos:
  - `id`
  - `cnpj`
  - `razao_social`
  - `data_inicio_atividade`
  - `cep`
  - `uf`
  - `municipio`
  - `raw_data_json`
  - `created_at`
  - `updated_at`
- Critério de aceite:
  - tabela criada com tipos coerentes e chave natural adequada
- Prioridade: P0
- Estimativa: 1h

### E2.2 — Definir chave natural e estratégia de upsert
- Objetivo: garantir idempotência.
- Itens:
  - definir se a chave será CNPJ, id_cadastro ou outra
  - прописar regra “update if exists, insert if not”
- Critério de aceite:
  - mesmo arquivo processado duas vezes não gera duplicação
- Prioridade: P0
- Estimativa: 1h

### E2.3 — Criar stored procedure em PL/pgSQL
- Objetivo: centralizar a regra de carga no banco.
- Itens:
  - procedure para upsert em lote
  - atualização de campos e timestamp
  - tratamento de duplicatas
- Critério de aceite:
  - procedure executa com sucesso em lote
- Prioridade: P0
- Estimativa: 3h

### E2.4 — Criar tabela de quarentena no banco
- Objetivo: registrar erros e rejeições.
- Campos sugeridos:
  - `id`
  - `source_file`
  - `row_number`
  - `raw_line`
  - `rejection_reason`
  - `processed_at`
- Critério de aceite:
  - toda linha rejeitada permanece rastreável
- Prioridade: P0
- Estimativa: 1h

## Epic 3 — Extração dos dados
### E3.1 — Implementar módulo `extract.py`
- Objetivo: encapsular a etapa de extração.
- Funcionalidades:
  - download ou leitura do arquivo
  - salvar em `data/raw` com timestamp
  - manter cópia original para rastreio
- Critério de aceite:
  - arquivo bruto é preservado e nunca sobrescrito
- Prioridade: P0
- Estimativa: 2h

### E3.2 — Definir estratégia de arquivo bruto
- Objetivo: padronizar a salvaguarda do dado.
- Opções:
  - CSV/ZIP
  - API com coleta em lote
- Critério de aceite:
  - nome do arquivo e caminho estão registrados no log
- Prioridade: P0
- Estimativa: 1h

### E3.3 — Implementar log de execução da extração
- Objetivo: registrar metadados do arquivo processado.
- Itens:
  - origem
  - nome do arquivo
  - timestamp
  - quantidade de linhas
- Critério de aceite:
  - uma execução gera registro claro de origem e destino
- Prioridade: P1
- Estimativa: 1h

## Epic 4 — Validação de qualidade e quarentena
### E4.1 — Definir regras de validação do MVP
- Objetivo: priorizar regras de negócio essenciais.
- Regras:
  - CNPJ/CPF com dígito verificador correto
  - campos obrigatórios não nulos
  - CEP com 8 dígitos
  - datas em formato consistente
  - encoding UTF-8 correto
  - duplicatas dentro da mesma carga
  - limites plausíveis de valores
- Critério de aceite:
  - todas as regras entram em uma lista central de validação
- Prioridade: P0
- Estimativa: 2h

### E4.2 — Implementar validação de schema com Pandera/Pydantic
- Objetivo: validar colunas e tipos com regras explícitas.
- Itens:
  - schema para colunas esperadas
  - validação de tipos
  - validação de indicadores obrigatórios
- Critério de aceite:
  - dados fora do schema são rejeitados de forma consistente
- Prioridade: P0
- Estimativa: 3h

### E4.3 — Implementar separação válido vs inválido
- Objetivo: dividir o DataFrame em duas saídas.
- Itens:
  - DataFrame validado
  - DataFrame rejeitado
  - cada rejeição com motivo
- Critério de aceite:
  - rejeição não é silenciosa
- Prioridade: P0
- Estimativa: 2h

### E4.4 — Salvar registros rejeitados em quarentena
- Objetivo: guardar os dados inválidos com o motivo.
- Estrutura de arquivo:
  - CSV ou parquet em `data/quarantine`
  - colunas:
    - `linha_original`
    - `motivo_rejeicao`
    - `timestamp_processamento`
    - `origem`
- Critério de aceite:
  - arquivo de quarentena é gerado corretamente
- Prioridade: P0
- Estimativa: 2h

### E4.5 — Validar encoding e caracteres especiais
- Objetivo: garantir que o dado seja convertido de forma consistente.
- Itens:
  - detectar latin-1/utf-8 misturado
  - normalizar para UTF-8
  - reportar inconsistência em falha
- Critério de aceite:
  - os textos convertidos não ficam corrompidos
- Prioridade: P1
- Estimativa: 2h

## Epic 5 — Transformação dos dados
### E5.1 — Implementar módulo `transform.py`
- Objetivo: centralizar as regras de normalização.
- Regras:
  - limpar espaços
  - remover caracteres inválidos
  - padronizar datas
  - formatar CNPJ/CPF
  - converter tipos
- Critério de aceite:
  - módulo transforma corretamente os dados válidos
- Prioridade: P0
- Estimativa: 3h

### E5.2 — Normalizar valores de texto
- Objetivo: evitar inconsistências de case e formatação.
- Itens:
  - strip
  - uppercase/lowercase em campos apropriados
  - remoção de acentos e caracteres estranhos quando necessário
- Critério de aceite:
  - padrão consistente em todos os campos
- Prioridade: P1
- Estimativa: 1h

### E5.3 — Padronizar datas para ISO 8601
- Objetivo: unificar formatos.
- Itens:
  - converter datas em formatos diferentes para `yyyy-mm-dd`
  - validar datas realistas
- Critério de aceite:
  - coluna de data segue o mesmo padrão em todas as linhas
- Prioridade: P0
- Estimativa: 2h

### E5.4 — Limpeza e padronização de CNPJ/CPF
- Objetivo: reduzir ruído do dado original.
- Itens:
  - remover máscara
  - validar dígito verificador
  - padronizar representação final
- Critério de aceite:
  - dados ficam em formato consistente e confiável
- Prioridade: P0
- Estimativa: 2h

## Epic 6 — Carga em banco e observabilidade
### E6.1 — Implementar módulo `load.py`
- Objetivo: realizar a carga em lote para o PostgreSQL.
- Funcionalidades:
  - conexão com banco
  - envio em batch
  - chamada da stored procedure
  - retorno de métricas
- Critério de aceite:
  - dados válidos são gravados no banco
- Prioridade: P0
- Estimativa: 3h

### E6.2 — Registrar métricas de execução
- Objetivo: criar relatório de processamento.
- Dados:
  - linhas lidas
  - válidas
  - rejeitadas
  - inseridas
  - atualizadas
  - tempo total
- Critério de aceite:
  - relatório final visível no console ou em arquivo
- Prioridade: P0
- Estimativa: 1h

### E6.3 — Implementar controle de erros de carga
- Objetivo: não falhar sem contexto.
- Itens:
  - log de falha de conexão
  - log de batch problemático
  - retry opcional
- Critério de aceite:
  - falhas são observáveis e diagnósticas
- Prioridade: P1
- Estimativa: 2h

## Epic 7 — Orquestração do pipeline
### E7.1 — Criar `pipeline.py`
- Objetivo: orquestrar `extract`, `validate`, `transform`, `load` e `report`.
- Fluxo:
  - carregar arquivo bruto
  - validar
  - separar rejeitados
  - transformar válidos
  - carregar
  - gerar relatório
- Critério de aceite:
  - pipeline executa end-to-end em um único comando
- Prioridade: P0
- Estimativa: 3h

### E7.2 — Implementar CLI de execução
- Objetivo: permitir rodar o pipeline de forma reprodutível.
- Opções:
  - arquivo de entrada
  - tipo de execução (local/ci)
  - modo debug
- Critério de aceite:
  - comando simples para executar uma carga
- Prioridade: P1
- Estimativa: 2h

### E7.3 — Implementar logs estruturados
- Objetivo: facilitar troubleshooting.
- Itens:
  - nível de log
  - timestamp
  - módulo
  - mensagem
- Critério de aceite:
  - logs úteis para diagnóstico em ambiente local
- Prioridade: P1
- Estimativa: 1h

## Epic 8 — Testes automatizados
### E8.1 — Criar fixtures de dados sujos
- Objetivo: preparar casos de teste.
- Itens:
  - CSV com CNPJ inválido
  - CEP inválido
  - encoding quebrado
  - data inconsistente
  - linha nula
- Critério de aceite:
  - casos cobrem as regras principais
- Prioridade: P0
- Estimativa: 1h

### E8.2 — Teste de validação de CNPJ/CPF
- Critério de aceite:
  - CPF/CNPJ inválido vai para quarentena
- Prioridade: P0
- Estimativa: 1h

### E8.3 — Teste de campos obrigatórios
- Critério de aceite:
  - campos vazios são rejeitados
- Prioridade: P0
- Estimativa: 1h

### E8.4 — Teste de encoding
- Critério de aceite:
  - encoding inconsistentes são detectados e tratatos
- Prioridade: P1
- Estimativa: 1h

### E8.5 — Teste de datas inconsistentes
- Critério de aceite:
  - data em formato inválido é rejeitada ou normalizada
- Prioridade: P0
- Estimativa: 1h

### E8.6 — Teste de duplicatas
- Critério de aceite:
  - mesmo registro repetido não entra em duplicata na carga
- Prioridade: P0
- Estimativa: 1h

### E8.7 — Teste de idempotência
- Objetivo: rodar o pipeline duas vezes e confirmar ausência de duplicidade.
- Critério de aceite:
  - número total final de registros não cresce ao repetir a execução
- Prioridade: P0
- Estimativa: 2h

### E8.8 — Teste de integração end-to-end
- Objetivo: validar fluxo completo do pipeline.
- Critério de aceite:
  - execução completa com dataset real ou fixture realista funciona
- Prioridade: P0
- Estimativa: 3h

## Epic 9 — CI/CD e documentação
### E9.1 — Criar workflow de GitHub Actions
- Objetivo: rodar testes automaticamente.
- Itens:
  - install dependencies
  - pytest
  - build opcional
- Critério de aceite:
  - CI executa em push/pull request
- Prioridade: P0
- Estimativa: 2h

### E9.2 — Escrever README completo
- Objetivo: documentar problema, arquitetura e execução.
- Conteúdo:
  - problema
  - stack
  - arquitetura
  - como rodar localmente
  - decisões técnicas
  - regras de validação
  - testes
- Critério de aceite:
  - projeto pode ser executado por qualquer pessoa seguindo o README
- Prioridade: P0
- Estimativa: 2h

### E9.3 — Documentar decisões técnicas
- Objetivo: demonstrar maturidade de solução.
- Itens:
  - quarentena vs descartar
  - upsert idempotente
  - trade-off pandas vs polars
  - estratégia para escala
- Critério de aceite:
  - decisões claras e justificadas
- Prioridade: P1
- Estimativa: 1h

### E9.4 — Validar dataset real
- Objetivo: garantir que o projeto funciona fora do ambiente sintético.
- Critério de aceite:
  - pelo menos um dataset real foi processado com sucesso
- Prioridade: P0
- Estimativa: 3h

## Priorização final para MVP
### P0 obrigatório
- E1.1, E1.2, E1.3
- E2.1, E2.2, E2.3, E2.4
- E3.1
- E4.1, E4.2, E4.3, E4.4
- E5.1, E5.3, E5.4
- E6.1, E6.2
- E7.1
- E8.1, E8.2, E8.3, E8.6, E8.7, E8.8
- E9.1, E9.2

### P1 desejável
- E1.4
- E3.3
- E4.5
- E5.2
- E6.3
- E7.2, E7.3
- E8.4, E8.5
- E9.3

### P2 opcional
- uso de Polars como alternativa
- processamento em chunks/streaming
- Airflow/Prefect para orquestração
- dashboards de métricas

## Roteiro de implementação em ordem realista
1. Fase 1: ambiente e banco
2. Fase 2: extração + schema + validação
3. Fase 3: transformação + quarentena
4. Fase 4: carga + idempotência
5. Fase 5: orquestração + relatório
6. Fase 6: testes + CI
7. Fase 7: README + dataset real + ajustes finais

## Critérios de pronto para “MVP concluído”
- `docker compose up` sobe tudo
- pipeline executa com dataset real
- dados válidos são carregados no banco
- inválidos são registrados em quarentena
- o mesmo arquivo não duplica dados
- `pytest` passa
- README explica uso e arquitetura
