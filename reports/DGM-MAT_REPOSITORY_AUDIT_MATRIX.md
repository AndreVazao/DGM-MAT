# DGM-MAT REPOSITORY AUDIT MATRIX
## Inventário factual — 2026-10-06

> Estado: auditoria/classificação. Nenhum código foi movido, apagado ou renomeado.
> FULL-MIRROR permanece intocável.

## 1. Regra de classificação
- PRODUCTION: código real que pode tornar-se autoridade de execução.
- CONTRACT: contratos, DTOs, schemas e envelopes públicos.
- UI: cockpit/interface.
- SPECIALIST: módulo especializado independente.
- INTEGRATION: integração externa.
- LAB: experimentação/reutilização, sem autoridade de produção.
- ARCHIVE: histórico/referência; não entra no runtime.
- SHELL: repositório atualmente sem conteúdo funcional.
- REVIEW: sistema real que precisa de decisão de integração antes de qualquer migração.

## 2. Matriz
| Repo | Conteúdo real atual | Classificação | Destino/autoridade pretendida | Ação agora |
|---|---|---|---|---|
| DGM-MAT | 774 Python / 1.015 imports internos; core, cockpit, shared, scripts, tests | PRODUCTION ROOT / LEGACY HOST | raiz de integração durante migração | manter como fonte de trabalho |
| DGM-Core-Backend | apenas .git + .gitkeep | SHELL | Core backend | reservar como destino |
| DGM-Contracts | apenas .git + .gitkeep | SHELL | contratos públicos | reservar como destino |
| DGM-Cockpit-Frontend | apenas .git + .gitkeep | SHELL | frontend/cockpit | reservar como destino |
| DGM-MAT-Agents | README apenas | SHELL | agentes especialistas | auditar antes de preencher |
| DGM-MAT-Runtime | README apenas | SHELL/REVIEW | runtime independente somente se provado | não extrair ainda |
| DGM-MAT-Providers | README apenas | SHELL/SPECIALIST | adapters/providers | catalogar primeiro |
| DGM-MAT-Connectors | README apenas | SHELL/INTEGRATION | integrações externas | definir fronteira pública |
| DGM-MAT-Memory | README apenas | SHELL/SPECIALIST | integração de memória DGM | não mover memória global |
| DGM-MAT-Orchestrator | README apenas | SHELL/REVIEW | orchestration somente se independente | provar necessidade |
| DGM-MAT-OS | README apenas | SHELL/SPECIALIST | lifecycle/OS integration | classificar scripts |
| DGM-MAT-Plugins | README apenas | SHELL/SPECIALIST | plugin boundary | reservar |
| DGM-MAT-Cluster | README apenas | SHELL/REVIEW | cluster/federation | não extrair |
| DGM-MAT-Deploy | README apenas | SHELL/SPECIALIST | deployment/release | classificar scripts |
| DGM-MAT-Assets | README apenas | SHELL/SPECIALIST | assets estáticos | inventariar |
| DGM-MAT-Mobile | README/LICENSE | SHELL/SPECIALIST | mobile bridge/client | extrair só após contrato |
| DGM-MAT-Marketplace | README apenas | SHELL/SPECIALIST | marketplace | reservar |
| DGM-MAT-Media | README apenas | SHELL/SPECIALIST | media pipeline | reservar |
| DGM-MAT-Studio | README apenas | SHELL/SPECIALIST | studio tooling | reservar |
| DGM-MAT-Labs | README/LICENSE | LAB | camada experimental oficial | manter como laboratório |
| DGM-HUB | runtime Python real: AgentLoop, TaskExecutor, WorkflowRuntime, tools, tests, shadow systems | REVIEW / LEGACY SYSTEM | possível fonte de componentes para Agents/Core/Deploy | preservar e auditar |
| DGM-MCP | servidor MCP real, segurança, transports, schemas, certificações | REVIEW / INTEGRATION | candidato forte a camada MCP/Connectors | integrar por contrato, não copiar cegamente |
| DGM-Experimental | apenas .git + .gitkeep | LAB/SHELL | experimentação | reservar |
| DGM-MAT-FULL-MIRROR | cópia histórica completa do DGM-MAT | ARCHIVE / SAFETY | somente recuperação/arqueologia | NÃO TOCAR |

## 3. Duplicações estruturais confirmadas
O diretório DGM-MAT contém 15 diretórios DGM-MAT-* embutidos. Eles não contêm os módulos funcionais correspondentes; são apenas manifestos/metadata (README, architecture, ecosystem, health e .gitignore).

Conclusão: não são atualmente uma segunda implementação funcional. Só poderão ser removidos da estrutura final depois de a migração dos repositórios reais estar concluída e validada.

## 4. Sistemas reais que não podem ser confundidos com shells
### DGM-HUB
Tem runtime próprio e uma auditoria extensa de sistemas shadow. O relatório identifica múltiplos agentes, sistemas de patch, error analysis, approval paths, swarm experimental, MCP experimental e bridges. É material de recuperação/reutilização, não código para copiar integralmente para DGM-MAT.

### DGM-MCP
É um sistema funcional de servidor MCP com arquitetura separada entre Clients, Transport, Protocol, Registry/Adapter, Runtime, Tools e Security. Deve permanecer especializado até existir uma fronteira contratual clara com DGM-MAT.

## 5. Labs confirmados
### DGM-MAT-Labs
Laboratório oficial do ecossistema.

### Lab-OllamaConection
Fonte histórica de reutilização: cliente HTTP Ollama, bridges MCP/HTTP locais, routing de modelos, rate limiting, accounting de tokens/custos e experiências Claude/Ollama híbridas. Estado: LAB; não é dependência de produção.

### Lab-forge-icons
Biblioteca/coleção de assets SVG reutilizáveis. Classificação: ASSET-LAB.

### Lab-ionicons.designerpack
Grande coleção de ícones SVG. Classificação: ASSET-LAB.

## 6. Destinos preliminares
- core/api -> DGM-Core-Backend
- core/autonomy -> DGM-Core-Backend inicialmente
- core/runtime -> Core inicialmente; Runtime separado somente após prova
- core/storage -> DGM-Core-Backend
- core/event_bus -> Core; envelopes -> DGM-Contracts
- core/agents -> DGM-MAT-Agents
- core/providers -> DGM-MAT-Providers
- core/connectors -> DGM-MAT-Connectors
- core/memory -> DGM-MAT-Memory
- core/realtime -> boundary Cockpit/Runtime
- cockpit -> DGM-Cockpit-Frontend
- shared/models, shared/enums, DTOs e schemas -> DGM-Contracts
- deployment/autostart/install scripts -> DGM-MAT-Deploy / DGM-MAT-OS conforme função
- experiments/research -> DGM-MAT-Labs
- MCP protocol server -> manter DGM-MCP até contrato de integração definido

## 7. Regras de segurança
1. Não mover código antes do mapa semântico e ownership matrix.
2. Não importar produção diretamente de Lab-*.
3. Não usar FULL-MIRROR como fonte de runtime.
4. Não preencher shells artificialmente.
5. Não criar Runtime/Orchestrator/Cluster apenas por nome.
6. Não absorver DGM-HUB ou DGM-MCP sem prova de autoridade, dependências e testes.
7. Toda extração deve preservar histórico e permitir rollback.
8. Objetivo primeiro: arquitetura estável, não maximizar número de repos.

## 8. Próxima fase
A próxima auditoria será file-level nos sistemas reais: DGM-MAT core/shared/cockpit/scripts; DGM-HUB src; DGM-MCP src; Labs independentes; comparação de símbolos duplicados; e matriz FILE -> DESTINATION -> REWRITE -> OWNER -> TEST.

Só depois dessa etapa começa a migração física.
