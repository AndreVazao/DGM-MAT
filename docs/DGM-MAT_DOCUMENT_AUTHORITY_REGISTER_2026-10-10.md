# DGM-MAT — Registo de autoridade documental
Data: 2026-10-10
Estado: INVENTÁRIO INICIAL PARCIAL

## Autoridade atual
A diretiva `DGM-MAT_PRIMARY_MISSION_AND_EVOLVING_TRUTH_2026-10-10.md` é a autoridade operacional atual. Este registo classifica documentos e não substitui os respetivos detalhes técnicos.

## Classificação inicial
- CURRENT / NORMATIVE: diretiva primária de missão e verdade evolutiva.
- CURRENT / COMPLEMENTARY: `architecture/AI_PROVIDER_HISTORY_RECOVERY_AND_SCRIPT_ARCHIVE_2026-10-10.md`, `DGM-MAT_CONVERSATION_RECOVERY_AND_PROJECT_ASSEMBLY.md`, `DGM-MAT_OPERATING_MODEL.md`. Permanecem úteis, subordinados à prioridade de memória/intenção.
- CURRENT / EVIDENCE: `architecture/WEB_AI_APPS_AND_VISUAL_AUTOMATION_AUDIT_2026-10-10.md`. Regista auditoria; não prova implementação completa.
- LEGACY / PRIORITY SUPERSEDED: `OPERATIONAL_CONVERGENCE_ROADMAP.md` e `COCKPIT_CONVERGENCE_PLAN.md`. Build EXE, cockpit, federação e autonomia não precedem a recuperação de contexto. Objetivos úteis ficam como backlog secundário.
- COMPLEMENTARY / VERIFY: `DGM-MAT_ENTERPRISE_AUTONOMY_AND_ZERO_COST_CHARTER_2026-10-09.md` e `DGM-MAT_AUTONOMOUS_ENGINEERING_MODEL_2026-10-08.md`. Aplicam-se apenas quando compatíveis com a diretiva e segurança.
- CURRENT / SECURITY EVIDENCE: `DGM-MAT_GLOBAL_API_AUTH_ENFORCEMENT_2026-10-10.md`. Alterações de código não provam que a versão está carregada no processo vivo.
- CURRENT / SAFETY EVIDENCE: `DGM-MAT_HUMAN_INTERVENTION_QUEUE_2026-10-10.md`. Manter gate de manutenção antes de reiniciar.
- COMPLEMENTARY / VERIFY LIVE: `architecture/PC_COCKPIT_REALTIME_CONNECTION.md`. Testes/handshake não equivalem a validação visual completa.
- HISTORICAL / VERIFY: `SYSTEM_STATUS_REPORT.md`, `OPERATIONAL_RUNTIME.md`, `PHASE_HISTORY.md` e registos de checkpoints. São fotografias históricas, não prova do estado live.
- CURRENT / NEEDS RECONCILIATION: memória mestre do DGM-MAT, a consolidar com a diretiva e evidência atual.
- LEGACY / RECOVERY ONLY: `CONTEXTO_LEGACY_DGM-MAT.md`, `CONTEXTO_PIPELINE_LEGACY.md` e `legacy/GOD_MODE/`. Consultar para recuperar decisões, não como autoridade atual sem confirmação.
- CURRENT / COMPLEMENTARY: regras gerais e de persistência AndreOS, sem autorização para apagar histórico indiscriminadamente.

## Conflitos de prioridade detetados
1. Roteiros antigos colocavam build EXE, cockpit, federação ou autonomia à frente da recuperação de contexto. Essa prioridade foi substituída.
2. Relatórios antigos não provam o estado atual.
3. A documentação de recuperação existe, mas browser persistente, integração no cockpit e importação E2E ainda não estão comprovados como implementados.
4. Não houve remoção física de documentos. Classificar e ligar sucessores antes de qualquer eliminação.

## Atualização vinculativa — arquitetura modular e escritório virtual (2026-10-18)

**NOVA AUTORIDADE ARQUITETURAL:** [`architecture/DGM-MAT-ARCHITECTURE-CONSTITUTION-MODULAR-DEPARTMENTS-2026-10-18.md`](architecture/DGM-MAT-ARCHITECTURE-CONSTITUTION-MODULAR-DEPARTMENTS-2026-10-18.md).

**INVENTÁRIO DOCUMENTAL DESTA RECUPERAÇÃO:** [`architecture/DGM-MAT-RECOVERY-UNIFICATION-INVENTORY-2026-10-18.md`](architecture/DGM-MAT-RECOVERY-UNIFICATION-INVENTORY-2026-10-18.md). O inventário é dirigido e declara explicitamente o que ainda não foi verificado.

Esta Constituição governa a separação dos repositórios, a hierarquia central/departamentos, as dependências entre módulos, a independência do core em relação ao cockpit e a missão de inteligência de conversações. A diretiva primária de missão/verdade evolutiva continua a governar a prioridade operacional e a proveniência; os dois documentos são complementares e não se anulam.

### Inventário dirigido de documentos de escritório virtual e organização

- **NORMATIVO — arquitetura modular:** `architecture/DGM-MAT-ARCHITECTURE-CONSTITUTION-MODULAR-DEPARTMENTS-2026-10-18.md`.
- **COMPLEMENTAR — core independente e plano de implementação:** `architecture/DGM-MAT_CORE_INDEPENDENCE_AND_VIRTUAL_OFFICE_IMPLEMENTATION_PLAN_2026-10-14.md`.
- **COMPLEMENTAR — requisitos de escritório adaptável:** `architecture/DGM-MAT_ADAPTIVE_VIRTUAL_OFFICE_AND_CORE_REQUIREMENTS_2026-10-14.md`.
- **COMPLEMENTAR — fábrica, RH, hierarquia, Programação e Design:** `architecture/DGM-MAT_FACTORY_HR_DEPARTMENTAL_HIERARCHY_PROGRAMMING_AND_DESIGN_2026-10-14.md`.
- **COMPLEMENTAR — catálogo de capacidades:** `architecture/DGM-MAT_MASTER_CAPABILITY_CATALOG_2026-10-14.md`. É um catálogo de candidatos/capacidades, não prova de instalação ou execução.
- **COMPLEMENTAR — conceito da sede digital:** `architecture/DGM-MAT-DIGITAL-HEADQUARTERS-CONCEPT-2026-10-12.md`.
- **COMPLEMENTAR — índice de integração documental:** `architecture/DGM-MAT-DIGITAL-HEADQUARTERS-INTEGRATION-INDEX-2026-10-17.md`.
- **COMPLEMENTAR — soberania departamental e governação de agentes:** `future/DGM-MAT-DEPARTMENT-SOVEREIGNTY-AND-AGENT-GOVERNANCE-2026-10-13.md`.
- **COMPLEMENTAR — organização digital e ordem de construção:** `DGM-MAT_DIGITAL_ORGANIZATION_ARCHITECTURE.md` e `DGM-MAT_DIGITAL_ORGANIZATION_BUILD_ORDER.md`.
- **COMPLEMENTAR — recuperação de conversas e montagem de projetos:** `DGM-MAT_CONVERSATION_RECOVERY_AND_PROJECT_ASSEMBLY.md`.
- **EVIDÊNCIA / HISTÓRICO TÉCNICO:** `architecture/CONVERSATION_KNOWLEDGE_STORE_HARDENING_2026-10-10.md`; regista alterações e testes de checkpoints anteriores, não prova por si só o estado atual de todas as integrações.
- **GUARDRAILS COMPLEMENTARES:** `ARCHITECTURE_GUARDRAILS.md`; deve ser interpretado em conjunto com a Constituição. Qualquer frase antiga de “locked” não autoriza violar a hierarquia arquitetural aqui definida.

### Conclusões da revisão documental de 2026-10-18

1. A distinção entre core em background e cockpit opcional já estava documentada.
2. A hierarquia Patrão → chefias → agentes principais/subagentes e a soberania limitada dos departamentos já estavam documentadas.
3. A missão de recuperar conversas, separar mensagens do utilizador das respostas das IAs, preservar proveniência, relacionar conversas entre providers e agrupar projetos já estava documentada.
4. Os documentos usam estados como “proposta”, “plano”, “futuro” e “a validar”; não se deve inferir implementação completa a partir deles.
5. A recuperação PC + GitHub é uma integração de trabalho, não uma ordem para consolidar as repos satélite.
6. Não foram apagados documentos nesta atualização. O inventário identificado não demonstra que todos os documentos do repositório, todas as repos satélite, todas as branches ou todo o conteúdo local do PC tenham sido revistos linha a linha. O estado global do inventário continua **PARCIAL** até essa auditoria terminar.
7. Documentos duplicados ou antigos devem ser marcados como superados e ligados ao sucessor; a eliminação física só pode ocorrer depois de comparar conteúdo, verificar referências, preservar histórico e obter autorização explícita.

## Continuação
Completar o inventário; ler documentos em conflito; consolidar memória mestre, decisões, arquitetura e backlog; implementar recuperação incremental com proveniência e estados de cobertura; só depois retomar engenharia não urgente.

Este registo é parcial. Documentos ainda não revistos mantêm estado UNKNOWN/UNREVIEWED; não se afirma que todas as fontes ou conversas foram lidas.
