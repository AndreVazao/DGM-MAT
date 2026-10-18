# Inventário de recuperação e arquitetura modular DGM-MAT
**Data:** 2026-10-18  
**Branch de trabalho:** `fix/backend-end-to-end-stabilization-final-2026-10-18`  
**Estado:** inventário documental dirigido — parcial; não equivale à auditoria de todas as repos, branches ou conteúdo do PC.

## 1. Finalidade

Distinguir a recuperação/unificação do trabalho PC + GitHub da arquitetura permanente de repositórios modulares. Identificar os documentos que definem o escritório virtual, a hierarquia dos departamentos, a independência do cérebro e a recuperação de conversas; estabelecer quais documentos são normativos, complementares, evidência ou históricos; evitar eliminações antes de verificar conteúdo e referências.

## 2. Decisão resultante

A fonte normativa para fronteiras modulares é [DGM-MAT-ARCHITECTURE-CONSTITUTION-MODULAR-DEPARTMENTS-2026-10-18.md](DGM-MAT-ARCHITECTURE-CONSTITUTION-MODULAR-DEPARTMENTS-2026-10-18.md). O README e o registo de autoridade documental apontam para ela.

A recuperação integra alterações e história de trabalho do PC e do GitHub. Não é uma migração de todos os departamentos para `AndreVazao/DGM-MAT`. As repos satélite mantêm-se separadas; DGM-MAT conserva a autoridade central.

## 3. Documentos revistos e classificação

| Documento | Classificação após esta revisão | Papel e tratamento |
|---|---|---|
| `docs/architecture/DGM-MAT-ARCHITECTURE-CONSTITUTION-MODULAR-DEPARTMENTS-2026-10-18.md` | **NORMATIVO — arquitetura** | Prevalece em modularidade, hierarquia, contratos, independência do core e política de recuperação. Alteração apenas por aditamento explicitamente autorizado. |
| `docs/DGM-MAT_PRIMARY_MISSION_AND_EVOLVING_TRUTH_2026-10-10.md` | **NORMATIVO — missão/proveniência** | Governa a prioridade operacional, evolução de intenção e distinção entre pedido, proposta, decisão e verdade verificada. Complementa a Constituição. |
| `docs/DGM-MAT_DOCUMENT_AUTHORITY_REGISTER_2026-10-10.md` | **REGISTO DE AUTORIDADE** | Catálogo e classificação de documentos; atualizado para apontar à Constituição e registar os limites desta auditoria. |
| `docs/DGM-MAT_DIGITAL_ORGANIZATION_ARCHITECTURE.md` | **COMPLEMENTAR — organização** | Define HQ, departamentos, agentes, evidência, memória e Conversation Intelligence. A própria descrição separa funções; não prova que todos os workers estejam ativos. |
| `docs/DGM-MAT_DIGITAL_ORGANIZATION_BUILD_ORDER.md` | **COMPLEMENTAR — sequência** | Organiza kernel, runtime, governação, workers, departamentos-piloto, fleet de Conversation Intelligence e escala. Estados “started/next” exigem confirmação contra código/testes atuais. |
| `docs/DGM-MAT_DIGITAL_OFFICE_ROSTER_2026-10-09.md` | **COMPLEMENTAR + EVIDÊNCIA HISTÓRICA** | Identifica funções e código organizacional encontrado à data; declara expressamente que delegação não equivale a execução autónoma. Revalidar antes de afirmar estado atual. |
| `docs/architecture/DGM-MAT_CORE_INDEPENDENCE_AND_VIRTUAL_OFFICE_IMPLEMENTATION_PLAN_2026-10-14.md` | **COMPLEMENTAR — plano** | Core headless, APIs/contratos, cockpit opcional, renderer isolado e gates de implementação. |
| `docs/architecture/DGM-MAT_ADAPTIVE_VIRTUAL_OFFICE_AND_CORE_REQUIREMENTS_2026-10-14.md` | **COMPLEMENTAR — requisitos** | Escritório adaptável, pisos/departamentos, estado real dos agentes, balcões departamentais e prioridade do cérebro. |
| `docs/architecture/DGM-MAT_FACTORY_HR_DEPARTMENTAL_HIERARCHY_PROGRAMMING_AND_DESIGN_2026-10-14.md` | **COMPLEMENTAR — organização/fábrica** | Hierarquia, RH, laboratório, Programação, Design, contratação/formação e regras de integração. Não autoriza instalação automática de candidatos. |
| `docs/architecture/DGM-MAT_MASTER_CAPABILITY_CATALOG_2026-10-14.md` | **CATÁLOGO / PROPOSTA** | Inventário de capacidades e candidatos; níveis de maturidade indicativos. Não é prova de disponibilidade ou autorização de integração. |
| `docs/architecture/DGM-MAT-DIGITAL-HEADQUARTERS-CONCEPT-2026-10-12.md` | **COMPLEMENTAR — conceito visual** | Pisos, salas, estados visuais, armazém, enfermaria, adaptação ao hardware e rede de agentes. |
| `docs/future/DGM-MAT-DIGITAL-HEADQUARTERS-CONCEPT-2026-10-12.md` | **DUPLICADO EXATO IDENTIFICADO** | A árvore da branch devolveu o mesmo blob SHA que o documento de `docs/architecture/`. Antes de remover uma cópia, confirmar todas as referências e atualizar links. Não apagar nesta fase. |
| `docs/architecture/DGM-MAT-DIGITAL-HEADQUARTERS-INTEGRATION-INDEX-2026-10-17.md` | **ÍNDICE COMPLEMENTAR** | Relaciona documentos de conceito/requisitos e declara que a auditoria documental não equivale a validação de software/runtime. |
| `docs/architecture/DGM-MAT_VIRTUAL_OFFICE_RESEARCH_2026-10-14.md` | **PESQUISA / PROPOSTA** | Compara referências públicas sem aprovar automaticamente clones; recomenda separar fonte de verdade, modelo, adaptador, simulação e controlo humano. |
| `docs/future/DGM-MAT-DEPARTMENT-SOVEREIGNTY-AND-AGENT-GOVERNANCE-2026-10-13.md` | **COMPLEMENTAR — governação** | Define soberania operacional limitada, pedidos de ajuda, anti-loop, memória governada e contratação/criação de agentes sob autoridade central. |
| `docs/future/DGM-MAT-ADAPTIVE-RUNTIME-AND-DISTRIBUTED-WORKERS-2026-10-12.md` | **COMPLEMENTAR — workers** | Pesquisa/arquitetura de runtime adaptável e distribuição; confirmar implementação contra testes e repositórios atuais. |
| `docs/future/DGM-MAT-EXTERNAL-AGENTS-AND-SELF-IMPROVEMENT-RESEARCH-2026-10-12.md` | **PESQUISA / PROPOSTA** | Colaboradores externos substituíveis e autoaperfeiçoamento governado; não concede autoridade a providers externos. |
| `docs/future/DGM-MAT-VIRTUAL-OFFICE-TECHNOLOGY-RESEARCH-2026-10-12.md` | **PESQUISA / PROPOSTA** | Tecnologias de visualização e escritório; não equivale a decisão de instalar uma framework. |
| `docs/architecture/PC_BRAIN_MOBILE_COCKPIT_PARALLEL_DELEGATIONS.md` | **PRINCÍPIO ARQUITETURAL COMPLEMENTAR** | PC como cérebro, telefone como cockpit, trabalho paralelo e tarefas bloqueadas sem bloquear a organização inteira. |
| `docs/architecture/BACKEND_DESKTOP_MOBILE_BOUNDARIES.md` | **COMPLEMENTAR — fronteiras** | Fronteiras backend/desktop/móvel; alinhar qualquer implementação com a Constituição. |
| `docs/architecture/CONVERSATION_INTELLIGENCE_EVIDENCE_MODEL_V1_2026-10-10.md` | **COMPLEMENTAR — modelo de evidência** | Proveniência, ingestão e estado incremental das conversas. |
| `docs/architecture/CONVERSATION_INTELLIGENCE_GAP_ASSESSMENT_2026-10-10.md` | **EVIDÊNCIA / GAP ANALYSIS** | Identifica limites de modelo agregado, ausência de relações persistentes e falta de integração web comprovada; revalidar contra código atual. |
| `docs/architecture/CONVERSATION_KNOWLEDGE_STORE_HARDENING_2026-10-10.md` | **EVIDÊNCIA / CHECKPOINT** | Regista hardening, regressões e limites de validação em checkpoints anteriores; não substitui novos testes. |
| `docs/architecture/AI_PROVIDER_HISTORY_RECOVERY_AND_SCRIPT_ARCHIVE_2026-10-10.md` | **COMPLEMENTAR — recuperação** | Exportações oficiais primeiro, browser dedicado quando necessário, extração com contexto, quarentena e proveniência. |
| `docs/DGM-MAT_CONVERSATION_RECOVERY_AND_PROJECT_ASSEMBLY.md` | **COMPLEMENTAR — protocolo funcional** | Inventariar providers, separar turnos, relacionar projetos, recuperar código, comparar variantes, montar árvores e validar. |
| `docs/ARCHITECTURE_GUARDRAILS.md` | **GUARDRAILS COMPLEMENTARES** | Regras de bootstrap, API, UI, kernel, memória, federação e ciclos de import. Não substitui a Constituição de 2026-10-18. |
| `docs/architecture/DGM-MAT-BACKEND-END-TO-END-STABILIZATION-GATE-2026-10-17.md` | **GATE DE TESTES** | Critérios de validação do backend; testes verdes provam apenas o âmbito efetivamente executado. |
| `docs/architecture/DGM-MAT-CAPABILITY-EVIDENCE-MATRIX-2026-10-17.md` | **MATRIZ DE EVIDÊNCIA** | Liga capacidades a testes/evidência e lacunas; manter alinhada com o código real. |

## 4. Conclusões técnicas extraídas da documentação

1. **O cérebro deve funcionar sem cockpit.** A UI, renderer e telefone são clientes/projeções; não são fonte única de verdade nem donos do ciclo de vida das missões.
2. **Os departamentos têm responsabilidades, chefias e autonomia delimitadas.** A autonomia operacional não lhes permite mudar a política central, permissões, memória nuclear ou validação final.
3. **A modularidade já era uma intenção explícita.** A recuperação atual não revoga nem substitui essa intenção.
4. **A inteligência de conversações é um requisito de produto, não apenas importação de ficheiros.** Tem de distinguir autor/turno, preservar contexto e proveniência, comparar propostas de IAs, reconhecer correções e decisões substituídas e ligar conversas ao mesmo projeto.
5. **O estado dos documentos é frequentemente “plano”, “proposta”, “futuro” ou “a validar”.** Isso não deve ser comunicado como capacidade implementada.
6. **A implementação existente tem lacunas documentadas historicamente.** Em particular, separar autor/turno, grafo de relações, cobertura completa de providers e renomeação remota necessitam de verificação atual e testes E2E.
7. **Há pelo menos uma duplicação documental exata** do conceito da sede digital entre `docs/architecture/` e `docs/future/`. O mesmo conteúdo não deve ser mantido em dois sítios indefinidamente, mas a remoção só ocorre após auditoria de referências e confirmação de que o índice canónico aponta para a cópia mantida.
8. **Não se fez uma leitura semântica linha a linha de todos os documentos de todas as pastas, nem de todas as repos satélite, branches e conteúdos locais do PC.** O inventário é dirigido e explicitamente parcial.

## 5. Próximas ações de auditoria — ordem obrigatória

1. Obter a lista completa das repos autorizadas e confirmar visibilidade, branch principal, estado e permissões.
2. Comparar árvore/commits do ramo de recuperação com os ramos do PC e GitHub; registar origem de cada bloco de trabalho.
3. Inventariar imports, manifests, dependências, callers e workflows de DGM-MAT, Contracts, Runtime, Orchestrator, Agents, Connectors e Cockpit.
4. Verificar se a CI tenta instalar satélites por dependência legítima e corrigir o acesso privado de forma segura; não remover dependências para “fazer passar” o workflow.
5. Confirmar com testes se a implementação de conversas separa mensagens/turnos e suporta ligações entre providers; implementar lacunas sem perder o pipeline atual.
6. Pesquisar referências ao documento duplicado da sede digital, eleger uma localização canónica e só então remover a cópia redundante com registo.
7. Só classificar um documento como `SUPERADO` quando houver sucessor explícito e referências atualizadas. Não apagar histórico sem autorização.

## 6. Regra de comunicação de estado

- **DOCUMENTADO** não significa **IMPLEMENTADO**.
- **IMPLEMENTADO** não significa **VALIDADO**.
- **TESTE PASSOU** só vale para o teste e commit realmente executados.
- **NÃO ACESSÍVEL** não significa **INEXISTENTE**.
- **NÃO ENCONTRADO** não significa **NUNCA EXISTIU**.
- Qualquer conclusão que não tenha sido verificada deve permanecer marcada como pendente.

