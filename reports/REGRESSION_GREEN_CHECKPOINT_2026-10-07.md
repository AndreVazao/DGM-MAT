# DGM-MAT Regression Green Checkpoint — 2026-10-07

## Objetivo

Fechar a dívida de regressão identificada após a consolidação dos contratos de execução, aprovação e EventEnvelope, sem consumir GitHub Actions durante o desenvolvimento normal.

## Resultado

A suíte local completa voltou a verde:

- `python -m pytest -q`
- resultado: **100% dos testes passaram**
- execução local: aproximadamente 71 s
- **nenhum workflow GitHub Actions foi disparado** para esta validação
- `python -m compileall -q core tests` passou

## Correções aplicadas

1. **RepositoryExtractor**
   - normalização dos caminhos usados nos relatórios de imports quebrados para formato portátil (`/`), eliminando divergência Windows/Linux.

2. **Cockpit**
   - `cockpit.app` passou a usar import lazy do entrypoint para eliminar ciclo `app -> main_window -> app`.
   - `MainWindow` ganhou `dispatch_message()` como fronteira pública de dispatch.
   - mensagens `execution_event` passaram a alimentar `ExecutionFeed`.
   - compatibilidade com mensagens legadas `runtime_status` preservada dentro do dispatch.
   - substituição de `asyncio.get_event_loop()` por `get_running_loop()` para evitar warning no Python moderno.

3. **Workspace protection**
   - comparação de workflows protegidos passou a normalizar separadores de caminho antes da comparação.

4. **Knowledge Engine / low-memory**
   - mantido o comportamento lazy-load no perfil de baixa memória.
   - acesso explícito a `runtime.knowledge_engine` carrega o engine sob demanda sem forçar a inicialização no boot.

5. **Runtime storage / logging**
   - removidos caminhos Windows hardcoded `C:\\DevopGodMode`.
   - `DGM_STORAGE_PATH` continua sendo override explícito.
   - `DGM_BASE_PATH` continua suportado.
   - default passa a ser `storage/runtime` relativo ao projeto instalado.
   - logging persistente passa a aceitar `DGM_LOG_PATH` e usa `storage/runtime/logs` por defeito.

6. **Runtime smoke test**
   - usa `sys.executable` em vez de assumir o comando `python3`, tornando o teste correto para Windows.

7. **Autonomy compatibility**
   - restaurado `TaskGenerator.create_strategic_task()` como compatibilidade explícita, com metadata estratégica.

8. **Testes obsoletos de paths**
   - ajustados para validar a arquitetura atual e não a antiga localização fixa `C:\\DevopGodMode`.

## Validação final

Além da suíte completa verde, foram validados separadamente:

- Repository extraction / broken imports
- Cockpit realtime dispatch
- protected workflow rules
- knowledge extraction e semantic query
- storage architecture
- runtime smoke
- strategic task generation
- persistent storage paths
- compileall

## GitHub Actions

A política definida em `GITHUB_ACTIONS_POLICY_2026-10-07.md` foi respeitada: esta fase foi validada exclusivamente localmente. Os workflows continuam manuais por defeito; não foi feito dispatch nem rerun apenas para confirmar alterações.

## Segurança de trabalho

- `DGM-MAT-FULL-MIRROR` **não foi tocado**.
- alterações locais antigas/unrelated continuam fora deste checkpoint e não foram incluídas automaticamente.
- não houve force-push.
- não houve extração física de repositórios.

## Próximo gate

Com a regressão local verde, o próximo trabalho é consolidar os limites de contratos e preparar a extração física apenas do primeiro componente com dependências já provadas, mantendo testes locais como gate principal. Nenhuma migração destrutiva deve ocorrer antes de uma cópia/validação do componente e dos seus consumidores.
