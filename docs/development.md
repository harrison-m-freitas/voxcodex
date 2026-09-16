# Desenvolvimento do VoxCodex M2

Este documento descreve o ambiente de desenvolvimento da implementação M2. O contrato arquitetural continua em `architecture/M2-DESIGN-V0.1.md`.

## Baseline de runtime

- Python: **3.14.7** (`.python-version`)
- uv: série **0.12.x**
- Dependências e limites: `pyproject.toml`

Crie/sincronize o ambiente a partir da raiz do repositório:

```bash
uv sync
```

O `uv.lock` deve ser gerado e versionado em um ambiente capaz de resolver a baseline Python 3.14.7. Não substitua a baseline por outra versão de Python apenas para produzir um lock local.

## Testes

Suíte completa do foundation gate:

```bash
uv run pytest tests/unit tests/integration/storage tests/integration/corpus -v
```

Suíte geral do projeto:

```bash
uv run pytest -v
```

## Metadata database

O banco local padrão é `voxcodex.db`, ignorado pelo Git. Para usar outro banco SQLite, configure uma URL SQLAlchemy:

```bash
export VOXCODEX_DATABASE_URL='sqlite:////tmp/voxcodex.db'
uv run alembic upgrade head
```

O metadata store persiste identidade, atividades, derivações, edges do DAG e usage metadata. Bytes imutáveis não pertencem ao SQLite.

## Artifact store

Durante desenvolvimento local, use:

```text
.voxcodex/artifacts/
```

Crie-o quando necessário:

```bash
mkdir -p .voxcodex/artifacts
```

`LocalBlobStore` endereça blobs como:

```text
<root>/sha256/<primeiros-2-hex>/<62-hex-restantes>
```

## Compatibility Corpus

Status sem abrir SourceArtifacts:

```bash
uv run voxcodex corpus status --registry corpus/COMPATIBILITY-CORPUS-V1.json
```

Estado congelado esperado para o Corpus v1:

```text
total=30 acquired=30 quarantined=4
```

## Regra de quarentena dos blind holdouts

Os SourceArtifacts de `CC-05`, `CC-07`, `CC-14` e `CC-18` permanecem **UNREVEALED** até o freeze do implementation candidate. Nenhum adapter, inspector, test fixture ou script de desenvolvimento pode abrir seus bytes antes do reveal autorizado.

Toda resolução de caminho de corpus deve chamar `HoldoutGuard.assert_allowed(...)` **antes de qualquer I/O**. O teste `tests/integration/corpus/test_quarantine_before_io.py` garante esse comportamento monkeypatchando `Path.open`.

Depois que um holdout for revelado, ele nunca volta a ser considerado cego.

## Verificação do CLI

```bash
uv run voxcodex --help
uv run voxcodex corpus status --registry corpus/COMPATIBILITY-CORPUS-V1.json
```

## Limitação conhecida da sandbox usada no primeiro ciclo inline

A sandbox de execução de 2026-09-14 disponibilizou Python 3.13.5, uv 0.10.0 e versões próximas — porém não idênticas — das dependências planejadas, sem acesso de rede suficiente para resolver Python 3.14.7, `rfc8785` e Hypothesis. Por isso:

- `.python-version` e `pyproject.toml` preservam a baseline aprovada;
- nenhum `uv.lock` foi fabricado;
- `rfc8785` foi fornecido apenas como dependência externa de teste fora do repositório durante essa execução;
- o property test Hypothesis permanece no repositório e fica skipped somente quando Hypothesis não está instalado;
- o gate final em Python 3.14.7 + lock real continua obrigatório antes de promover o Plan 01 como baseline de implementação.
