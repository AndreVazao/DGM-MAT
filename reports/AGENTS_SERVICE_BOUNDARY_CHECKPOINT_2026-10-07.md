# DGM-MAT Agents service-boundary checkpoint — 2026-10-07

## Objetivo

Preparar a extração física de `core/agents` para `DGM-MAT-Agents` sem permitir que o novo repositório passe a depender de módulos privados do DGM-MAT Core.

## Decisão

Foi criada uma fronteira pública de serviços em `DGM-Contracts`:

- `AgentLogger`
- `ProviderService`
- `TaskService`
- `NullAgentLogger`
- `NullProviderService`
- `NullTaskService`

O DGM-MAT Core fornece implementações concretas através de `core/agents/service_adapters.py`:

- `CoreLoggerAdapter`
- `CoreProviderServiceAdapter`
- `CoreTaskServiceAdapter`

Os agentes `ProviderAgent` e `AutonomyAgent` passaram a receber os serviços por injeção. `BaseAgent` passou a receber o logger por injeção. Os agentes simples passaram a consumir `Event` diretamente de `DGM-Contracts`.

## Extração física de validação

O conteúdo de `core/agents` foi copiado, sem apagar a origem, para:

`C:\ProgramasGodMode\DGM-MAT-Agents\src\dgm_mat_agents`

O pacote foi reestruturado para não conter imports `core.*`. A integração com Core fica fora do satélite e é feita por adapters.

Repositório GitHub: `AndreVazao/DGM-MAT-Agents`

Commits publicados:

- `cade249` — `feat(agents): establish standalone agent package`
- `527fece` — `chore: ignore Python caches`

DGM-Contracts:

- `3bf14d6` — `feat(contracts): add agent service ports`

## Validação

### DGM-Contracts

- `pytest`: **1 passed**

### DGM-MAT-Agents

- `pytest`: **2 passed**
- `compileall`: **OK**
- verificação automática de imports: **NO_CORE_IMPORTS**

### DGM-MAT

- suíte completa: **100% passou**
- duração: ~64 s
- nenhuma execução GitHub Actions utilizada

## Segurança da migração

- origem `core/agents` mantida intacta para compatibilidade e rollback
- nenhuma remoção destrutiva executada
- `DGM-MAT-FULL-MIRROR` não foi tocado
- não houve force-push
- GitHub Actions continua manual por política

## Próximo gate

Antes de remover `core/agents`, ainda é obrigatório:

1. migrar todos os consumidores de `core.agents` para `dgm_mat_agents`/fronteira pública;
2. validar imports e inicialização do Runtime através da nova fronteira;
3. adicionar teste de integração Core → Agents via adapters;
4. executar novamente a suíte completa;
5. só então transformar `core/agents` em compatibilidade mínima ou removê-lo, conforme os consumidores reais.

A extração física deste checkpoint é, portanto, **validada mas ainda não é a remoção definitiva da fonte**.


## Integration gate — completed

The Core Runtime no longer imports the standalone agent implementations directly. `core/agents/boundary.py` now owns satellite discovery and composition, with optional `DGM_AGENTS_PATH` override and the default sibling repository path.

`core/runtime/runtime.py` consumes `create_runtime_agents()` instead of importing `RepoAgent`, `ProviderAgent` and `AutonomyAgent` directly.

The stale agent import in `scripts/autostart/worker_cluster.py` was removed because that module was not actually using the class.

Validation:
- focused Core contract/autonomy/runtime suite: **14 passed**
- DGM-MAT full suite: **100% passed**, 65.38 s
- DGM-MAT-Agents: **2 passed**
- DGM-Contracts: **1 passed**
- DGM-MAT-Agents compileall: **OK**
- no GitHub Actions used

This closes the Core → Agents composition gate. `core/agents` remains preserved as source/rollback material; deletion is still deferred until a second consumer audit confirms no required legacy consumers remain.
