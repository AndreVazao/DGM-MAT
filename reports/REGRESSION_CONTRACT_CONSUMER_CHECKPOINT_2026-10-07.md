# DGM-MAT Regression & Contract Consumer Checkpoint — 2026-10-07

## Estado

A fronteira de contratos/eventos/aprovações permanece funcional, mas a extração física para os repositórios satélite continua BLOQUEADA até o baseline global recuperar estabilidade.

## Correções fechadas

- `runtime_api.py` deixou de ler `mission_engine.pending_approvals`; o endpoint usa a autoridade durável `ApprovalManager -> SafeActionQueue`.
- `MissionEngine._handle_approval_pending()` deixou de depender de `pending_approvals` inexistente e consulta o estado durável.
- `core/migration/import_rewriter.py` deixou de depender de `astor`; usa `ast.unparse()` nativo do Python 3.12.
- `pyproject.toml` passou a usar `pytest --import-mode=importlib`.
- `tests/operational/test_recovery.py` foi renomeado para `test_operational_recovery.py` para eliminar colisão com outro `test_recovery.py`.
- `CognitiveRepoScanner.scan()` recebeu limite de ficheiros (2000) e orçamento temporal (10s), evitando endpoints de scan potencialmente intermináveis.

## Validação

### Verde
- contratos + autonomia + mission system: 17 testes
- endpoint `/runtime/repo_scan`: 1 teste
- compileall de `core` + `tests`: OK
- instalação editable de `DGM-Contracts`: OK

### Baseline integral
A suíte completa terminou com **9 falhas**. Nenhuma das falhas reportadas é causada diretamente pela nova fronteira EventEnvelope/Execution/Approval.

Falhas atuais:
1. extractor legado: deteção de broken imports
2. cockpit: `MainWindow.dispatch_message` ausente (2 testes)
3. proteção de workflows
4. knowledge engine desativado no low-memory profile (2 testes)
5. RuntimeStorageManager ainda usa `C:\DevopGodMode\runtime`
6. runtime smoke usa `python3` em Windows
7. TaskGenerator sem `create_strategic_task`

## Decisão arquitetural

**NÃO iniciar ainda a extração física dos repositórios.**

A ordem permanece:

MAPEAR → CLASSIFICAR → COPIAR/MIGRAR → REESCREVER INTERLIGAÇÕES → TESTAR → COMMITAR → VALIDAR → só então remover origem.

Os 9 failures devem ser tratados como dívida técnica explícita, priorizando primeiro os que afetam fronteiras/runtime e deixando compatibilidade histórica para uma etapa controlada.

## Git

- commit: `22ef8fb`
- mensagem: `stabilize regression and durable approval consumers`
- push: `main -> origin/main`
- checkpoint anterior: `56019e4`

## Segurança

- FULL-MIRROR não foi tocado.
- alterações locais não relacionadas continuam fora do commit.
