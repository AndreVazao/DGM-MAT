# GitHub Actions policy — DGM-MAT

## Regra operacional

GitHub Actions não deve ser usado como teste local. A máquina local é a primeira camada de validação; Actions é reservado para validações obrigatórias, integração real ou release.

## Triggers

Todos os workflows normais do DGM-MAT são `workflow_dispatch` only. Não existem triggers automáticos por `push`, `pull_request` ou `schedule` nos workflows de CI, build, runtime, migration, security, autonomy, analysis ou workflow validation.

A única exceção automática mantida é `release.yml`, limitada a tags `v*` (e configuração de release existente).

## Política de execução

1. Fazer testes locais primeiro.
2. Não disparar Actions apenas para confirmar que um commit existe.
3. Disparar manualmente apenas o workflow necessário para a mudança atual.
4. Preferir o workflow mais pequeno/específico em vez da suíte completa.
5. Build Windows só quando houver alteração que justifique validar o executável.
6. Security scan apenas quando houver alteração relevante ou antes de release/handoff.
7. Release apenas através de tag `v*` intencional.
8. Nunca criar workflows de polling/schedule para desenvolvimento normal.

## Estado verificado — 2026-10-07

- Workflows normais: manual only.
- `release.yml`: tag-driven.
- Não havia runs `queued` ou `in_progress` no momento da limpeza.
- Runs automáticos anteriores foram observados como `completed`; não foram reexecutados.
- Commit de contenção: `dff165c` (`ci: make workflows manual by default`).

## Objetivo

Preservar minutos do plano gratuito para validações que realmente precisam do ambiente GitHub e impedir que cada commit/teste local consuma Actions automaticamente.
