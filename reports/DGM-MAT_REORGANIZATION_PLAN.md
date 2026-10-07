# DGM-MAT — PLANO DE REORGANIZAÇÃO E MIGRAÇÃO

## Objetivo

Transformar o atual DGM-MAT num ecossistema modular coerente, preservando funcionalidade e histórico.

Regra:
MAPEAR -> CLASSIFICAR -> COPIAR/MIGRAR -> REESCREVER INTERLIGAÇÕES -> TESTAR -> COMMITAR -> VALIDAR -> só depois remover o original.

Nunca fazer move + delete numa única operação.

## Estado atual

O mapa automático encontrou:
- 774 ficheiros Python
- 774 módulos
- 1.015 ligações internas de import
- 15 diretórios DGM-MAT-* dentro do próprio DGM-MAT

O DGM-MAT-FULL-MIRROR continua fora de qualquer operação de migração.

## Arquitetura-alvo inicial

### DGM-Core-Backend
Destino primário:
- todo o core/
- entrypoints backend/runtime quando forem backend
- backend configuration/runtime
- partes internas de shared/ que não sejam contratos públicos

Regra: se uma peça é parte do núcleo Python do DGM-MAT, o destino natural é DGM-Core-Backend, salvo prova de que pertence a outro domínio.

### DGM-Cockpit-Frontend
Destino:
- cockpit/
- widgets/views
- clientes realtime
- camada visual

Dependências do cockpit para o backend devem passar por API/contratos públicos, não por imports físicos privados.

### DGM-Contracts
Destino:
- eventos partilhados
- schemas
- DTOs
- contratos API
- enums/protocolos partilhados

### DGM-Docs
Destino:
- docs/
- arquitetura
- fases
- decisões
- documentação permanente

### DGM-MAT-Agents
Destino funcional:
- agentes concretos e especializações.
- base/runtime de agentes continua candidato ao Core.
- contratos vão para Contracts.

### DGM-MAT-Runtime
Candidato:
- runtime especializado/executores separáveis do Core.
Não mover automaticamente.

### DGM-MAT-Connectors
Integrações externas/adapters.

### DGM-MAT-Providers
Provider registry, adapters e provider-specific code.

### DGM-MAT-Memory
Integração operacional de memória específica do DGM-MAT.
A memória global AndreOS continua em OS-Memory.

### DGM-MAT-Orchestrator
Orquestração de agentes/processos, se o mapa provar uma fronteira independente.

### DGM-MAT-OS
Integração com sistema operativo, instalação, lifecycle e operações locais.

### DGM-MAT-Plugins / Marketplace / Media / Studio / Assets / Mobile / Cluster / Labs / Deploy
Avaliação individual pelo conteúdo real. O nome do repo não é prova suficiente.

## Relações de autoridade

User / Operator
-> DGM-Cockpit-Frontend
-> DGM-Core-Backend API
-> Orchestrator / Mission / Execution
-> Agents / Providers / Connectors
-> Storage / Runtime / OS
-> resultados
-> Core
-> Contracts/API
-> Cockpit

Governança:
- Core decide regras operacionais.
- Orchestrator coordena.
- Agents executam especializações.
- Providers fornecem capacidades.
- Connectors comunicam com sistemas externos.
- Runtime executa/controla processos.
- Storage persiste.
- Contracts definem interfaces partilhadas.
- Cockpit apresenta e solicita.
- OS-Memory conserva contexto histórico/meta.
- FULL-MIRROR preserva recuperação histórica.

## Interligações a eliminar

- cockpit -> imports privados do core
- agent -> caminho físico de outro repo
- repo A -> repo B através de ficheiro privado
- caminhos absolutos para C:\ProgramasGodMode\DGM-MAT\...
- dependência de singletons em memória para comunicação entre processos
- contratos duplicados

Objetivo:
- API/contract boundaries
- imports de pacotes
- eventos/queues quando apropriado
- storage como fonte de verdade
- configuração por ambiente
- testes cross-repo

## Ordem de migração

### M0
Mapa factual de imports e estrutura.

### M1
Mapa semântico:
- quem chama
- quem responde
- quem escreve
- quem lê
- quem cria
- quem aprova
- quem executa
- quem persiste
- quem observa

### M2
Classificação individual:
KEEP / CORE / COCKPIT / CONTRACT / AGENT / RUNTIME / CONNECTOR / PROVIDER / MEMORY / ORCHESTRATOR / OS / DOC / LEGACY / EXPERIMENTAL

### M3
Snapshots/branches de segurança.

### M4
Migrar Contracts e boundaries.

### M5
Extrair Core para DGM-Core-Backend e reescrever imports.

### M6
Extrair Cockpit para DGM-Cockpit-Frontend.

### M7
Extrair satélites por domínio.

### M8
Testes cross-repo e runtime real.

### M9
Só depois remover duplicações antigas do DGM-MAT.

## FULL-MIRROR

DGM-MAT-FULL-MIRROR é somente recuperação histórica.

Não mover, apagar, renomear, atualizar ou sincronizar automaticamente.

## Critério de conclusão

Um ficheiro só muda definitivamente de repo quando:
1. destino funcional identificado;
2. dependências mapeadas;
3. imports/referências reescritos;
4. destino arranca/importa;
5. testes locais passam;
6. integração cross-repo passa;
7. runtime real passa;
8. OS-Memory atualizado;
9. commit/push confirmados;
10. origem antiga só então pode ser marcada removível.

## Artefactos

- reports/DGM-MAT_INTERCONNECTION_MAP.md
- reports/dgm_mat_dependency_graph.json
- reports/DGM-MAT_REORGANIZATION_PLAN.md
- reports/DGM-MAT_EXECUTION_TOOL_SYMBOL_MATRIX.md
- tools/generate_dependency_map.py

## 2026-10-06 — execution/tool/HUB checkpoint

Completed symbol-level comparison of DGM-MCP and DGM-HUB against DGM-MAT execution, security, runtime and autonomy.

DGM-MCP is the historical PC-control/MCP boundary. MCP transport belongs at Connectors; public tool descriptors belong in Contracts; machine operations belong behind one controlled Core execution boundary. MCP must not own mission, autonomy, memory or orchestration state.

DGM-MAT currently has multiple command execution paths and multiple approval authorities. These must converge before extraction. SafeActionQueue remains the candidate durable cross-process action authority. LocalExecutor and SafeAutonomousExecutor should converge into one execution service with policy controls.

DGM-HUB remains legacy/research/reference only. TruthLayer concepts can inform Core verification. AgentLoop and ToolReasoner are not authorities. PatchOrchestrator concepts may inform the patch lifecycle.

Physical migration remains blocked. FULL-MIRROR remains untouched.


## 2026-10-06 — Contracts consolidation checkpoint

Inspected the actual current mission, execution, approval, queue, storage and event models plus DGM-MCP tool metadata/adapter implementation.

Created:
- reports/DGM-MAT_CONTRACTS_CONSOLIDATION_MATRIX.md
- reports/ADR-001-CONTRACTS-AND-EXECUTION-BOUNDARY.md

Decisions:
- ExecutionRequest is the semantic request; SafeActionQueue is a durable implementation boundary, not the public contract.
- SafeActionQueue is the leading candidate for the single durable execution/approval authority, pending schema/test validation.
- MissionEngine.pending_approvals and ApprovalManager are legacy/compatibility authorities and must converge on durable approval.
- EventEnvelope is public; EventBus is process-local routing; EventStore is persistence; RuntimeStateStore is projection only.
- DGM-MCP ToolDefinition/tool schemas become ToolDescriptor-compatible and MCP response formatting becomes an adapter over ExecutionResult.
- No physical repository migration yet. FULL-MIRROR untouched.

Next gate: implement Contracts with compatibility adapters and cross-process tests before extracting repositories.


## 2026-10-06 — ToolDescriptor + durable approval checkpoint

Completed the next contract boundary without physical repository extraction:
- Added a DGM-MAT compatibility adapter from DGM-MCP `ToolDefinition`-shaped metadata to public `ToolDescriptor`.
- The adapter accepts dataclass or mapping input and does not import DGM-MCP private runtime classes.
- Added focused tests for filesystem, unknown-tool conservative policy, and deterministic batch conversion.
- Removed `MissionEngine.pending_approvals` as a process-local authority; MissionEngine approval entry points now delegate to durable SafeActionQueue through the ApprovalManager facade.
- Removed the duplicate `approve_approval` implementation in SafeActionQueue.
- Focused contract/queue/cross-process validation: 10 passed.
- Commit: `81141fc`.

Physical migration remains blocked. FULL-MIRROR remains untouched.

Next gate: consolidate EventEnvelope persistence/live projection and then run the broader regression suite.


## 2026-10-07 — Event boundary checkpoint

Completed the Event contract gate:
- Event runtime objects are converted to complete EventEnvelope contracts before persistence/streaming.
- EventStore persists the complete envelope and supports deterministic replay.
- Existing SQLite event tables are upgraded non-destructively with a nullable envelope column.
- Legacy rows remain readable through compatibility reconstruction.
- EventBus timezone handling was hardened for aware/naive timestamps.
- Focused contract/runtime suite: 13 passed.

Next gate: broader regression and only then physical repository extraction.
FULL-MIRROR remains untouched.
