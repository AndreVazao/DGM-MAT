# Catálogo mestre de capacidades DGM-MAT — 2026-10-14

## Estado e finalidade
- Estado: **inventário consolidado para investigação; não aprovado para instalação**.
- Branch documental: `docs/tooling-capability-audit-2026-10-14`.
- Objetivo: consolidar as duas listas recebidas (plugins/integrações e skills/agentes/ferramentas) sem tratar nomes, funcionalidades, licenças ou alegações promocionais como verificadas.
- Fonte principal de política: [auditoria inicial](tooling-capability-audit-2026-10-14.md).
- Fonte complementar de detalhe: [catálogo complementar Claude Code](claude-code-plugin-skill-catalog-2026-10-14.md).
- A presente lista não autoriza instalação, permissões, pagamentos, acesso a dados ou execução em produção.

## Regras de identidade e validação
Cada candidato recebe um ID estável. Um nome alternativo ou duplicado deve apontar para o mesmo ID após validação; não criar duas integrações só porque aparecem em listas diferentes.
- **V0 — por identificar:** nome mencionado, URL oficial e repositório ainda por confirmar.
- **V1 — origem identificada:** origem oficial, licença, versão/commit e manutenção registados.
- **V2 — revisto:** permissões, dados enviados, dependências, custos e risco documentados.
- **V3 — testado isoladamente:** testes reproduzíveis e medições de RAM/CPU/latência/qualidade.
- **V4 — aprovado para integração:** contrato, fallback, auditoria, reversão e responsável definidos.
Nenhum item desta lista é automaticamente V1–V4.

## Catálogo com IDs únicos

### A. Orquestração, planeamento e produtividade
| ID | Candidato(s) normalizados | Uso potencial | Estado |
|---|---|---|---|
| ORCH-001 | Superpowers | Fluxo de planeamento e engenharia | V0 |
| ORCH-002 | Plannotator | Rever/partilhar planos | V0 |
| ORCH-003 | Productivity | Rotinas de produtividade | V0 |
| ORCH-004 | Shipyard | Orquestração/entrega de tarefas | V0 |
| ORCH-005 | Deep Trilogy | Fluxos de raciocínio/engenharia a avaliar | V0 |
| ORCH-006 | Medley | Composição de ferramentas/fluxos | V0 |
| ORCH-007 | session-tools | Utilitários de sessão | V0 |
| ORCH-008 | session-summary | Resumos e handoff de sessão | V0 |
| ORCH-009 | session-handoff | Transferência de contexto | V0 |
| ORCH-010 | legwork | Delegação/execução de trabalho a investigar | V0 |
| ORCH-011 | verve | Agente/fluxo candidato | V0 |
| ORCH-012 | cognitive-rhythm-writing | Escrita/ritmo de trabalho | V0 |
| ORCH-013 | japanese-tech-writing | Escrita técnica multilingue | V0 |

### B. Qualidade de código, revisão e testes
| ID | Candidato(s) normalizados | Uso potencial | Estado |
|---|---|---|---|
| ENG-001 | code-review; Local-Review; open-code-review; github-pr-review | Revisão de alterações e PRs; verificar sobreposição antes de escolher | V0 |
| ENG-002 | TDD Workflow; test-first; webapp-testing | Testes orientados ao comportamento | V0 |
| ENG-003 | Bug-hunt | Diagnóstico de defeitos | V0 |
| ENG-004 | Coding Standards | Regras de estilo e consistência | V0 |
| ENG-005 | Backend Patterns; Frontend Patterns | Padrões de implementação | V0 |
| ENG-006 | pyright-lsp; typescript-lsp; rust-analyzer-lsp; gopls-lsp | Diagnósticos de linguagem; avaliar custo local | V0 |
| ENG-007 | Vitals | Métricas/qualidade a confirmar | V0 |
| ENG-008 | SE-CoVe | Verificação de engenharia a confirmar | V0 |
| ENG-009 | snyk-fix | Remediação de segurança; validar licença e dados | V0 |
| ENG-010 | skill-creator | Criar/validar skills | V0 |
| ENG-011 | token-efficiency-audit | Medir/otimizar consumo de tokens | V0 |
| ENG-012 | AgentShield | Segurança de agentes a investigar | V0 |

### C. Segurança, governação e fiabilidade de agentes
| ID | Candidato(s) normalizados | Uso potencial | Estado |
|---|---|---|---|
| SAFE-001 | agentkeeper | Guardrails/gestão de agentes a confirmar | V0 |
| SAFE-002 | agent-budget-guardrail | Limites de orçamento/quotas | V0 |
| SAFE-003 | agent-approval-gate | Aprovação humana para ações sensíveis | V0 |
| SAFE-004 | agent-retry-safety | Retentativas idempotentes/seguras | V0 |
| SAFE-005 | vela | Segurança/controlo a identificar | V0 |
| SAFE-006 | dovtail | Segurança/controlo a identificar | V0 |
| SAFE-007 | Anthropic Cybersecurity Skills | Skills de cibersegurança; rever âmbito e licença | V0 |

### D. Documentos, design e conteúdo
| ID | Candidato(s) normalizados | Uso potencial | Estado |
|---|---|---|---|
| DOC-001 | PDF skills | Ler/criar/validar PDF | V0 |
| DOC-002 | XLSX skills | Folhas de cálculo | V0 |
| DOC-003 | DOCX skills | Documentos Word | V0 |
| DOC-004 | PPTX skills | Apresentações | V0 |
| DOC-005 | frontend-design; brand-guidelines | Interfaces e consistência visual | V0 |
| DOC-006 | algorithmic-art | Arte generativa | V0 |
| DOC-007 | imager | Imagens; identificar produto exato | V0 |
| DOC-008 | heliograph | Imagens/conteúdo a identificar | V0 |
| DOC-009 | youtube-transcriber | Transcrição de vídeo | V0 |
| DOC-010 | pr-description | Descrições de pull request | V0 |

### E. Integrações, conectores e dados
| ID | Candidato(s) normalizados | Uso potencial | Estado |
|---|---|---|---|
| INT-001 | GitHub plugin | Issues, PRs e repositórios | V0 |
| INT-002 | Codex plugin | Fluxo de programação; confirmar integração oficial e limites | V0 |
| INT-003 | notion-memory; Notion skills | Memória/documentação; deduplicar entradas | V0 |
| INT-004 | google-drive-upload | Upload de ficheiros; rever permissões | V0 |
| INT-005 | whatsapp-mcp | Mensagens; dados pessoais e aprovação obrigatória | V0 |
| INT-006 | Outlook skills | Correio/calendário; escopo mínimo | V0 |
| INT-007 | Trello skills | Quadros e tarefas | V0 |
| INT-008 | Garmin skills | Dados de dispositivo pessoal; **excluir da memória geral por defeito** | V0 |
| INT-009 | Hugging Face | Modelos/datasets; rever licença e requisitos | V0 |
| INT-010 | Exa | Pesquisa web/API; validar quota/custo | V0 |
| INT-011 | FiftyOne | Inspeção de datasets multimodais | V0 |
| INT-012 | DeepEval | Avaliação de aplicações LLM | V0 |
| INT-013 | Pixeltable | Dados multimodais/pipelines | V0 |
| INT-014 | GoodMem | Memória de agentes | V0 |
| INT-015 | ClickHouse IO | Analytics/dados | V0 |
| INT-016 | AWS Agents; DataRobot; Domino; NVIDIA/cuOpt | Ferramentas de plataforma/dados/otimização; verificar custo e requisitos | V0 |

### F. Ecossistema de escritórios virtuais e visualização de agentes
| ID | Projeto candidato | Função a investigar | Estado |
|---|---|---|---|
| VIS-001 | AgentSystemLabs/agent-office | Escritório 3D, elevador por projeto, terminais por agente, filas e quadros | V0 |
| VIS-002 | dian003/virtual-office (Hermes Virtual Office fork) | Divisões, reuniões, circulação A2A e quadro de tarefas | V0 |
| VIS-003 | harishkotra/agent-office | Escritório pixel-art, agentes locais/Ollama, memória e movimentação | V0 |
| VIS-004 | forgeekscn/pixel-agent-office | Estado de sessões, chefe/subagentes, pisos e visualização | V0 |
| VIS-005 | KbWen/agent-virtual-office | Estado real de sessões de programação visualizado em pixel art | V0 |
| VIS-006 | yakobusdamar/ai-agent-office-simulation | Animação demonstrativa; não confundir com sistema operacional real | V0 |
| VIS-007 | OneByJorah/VirtOffice | Visualização 3D com estados em tempo real via servidor leve | V0 |
| VIS-008 | ishkkman/agent-office (DeskRPG lineage) | Escritório 2D, NPCs, tarefas e reuniões | V0 |
| VIS-009 | Agent Office 3D (VS Code Marketplace) | Agentes por sessão, salas e movimentos | V0 |
| VIS-010 | gdd-rock/rockoffice | Simulação 3D com múltiplos agentes | V0 |

### G. Candidatos de integração que exigem maior cautela
- Plugins ou skills que possam executar comandos, alterar ficheiros, enviar mensagens, aceder a credenciais, abrir portas de rede ou fazer push exigem revisão manual antes de qualquer ativação.
- Ferramentas de terceiros/clones e labs permanecem apenas referências de estudo; não alterar, sincronizar ou integrar automaticamente.
- Nomes ambíguos (por exemplo, Vitals, Vela, Dovtail, Heliograph, Imager, Deep Trilogy) ficam em V0 até se encontrar a origem exata.

## Critérios de priorização para a máquina do utilizador
1. Compatibilidade com Windows e CPU de 2 núcleos / cerca de 3 GB RAM.
2. Local-first e sem API paga obrigatória; não aceitar fallback pago silencioso.
3. Sem serviços residentes pesados; testar primeiro sem instalação, em ambiente isolado.
4. Permissões mínimas, registo de ações e aprovação humana para efeitos externos.
5. Integração por adaptadores/contratos; separar visualização do estado real do runtime.
6. Reutilizar capacidades já disponíveis no DGM-MAT antes de adicionar dependências.

## Plano de trabalho
1. Confirmar URL oficial, autor, versão/commit, licença e manutenção.
2. Agrupar duplicados por função, mantendo todos os nomes alternativos como aliases.
3. Verificar segurança, telemetria, permissões, dependências e dados transmitidos.
4. Fazer avaliação estática antes de executar.
5. Testar um candidato de cada vez, com limites de tempo/RAM/CPU e sem credenciais reais.
6. Registar resultados, evidência, decisão e reversão; atualizar o estado V0→V4 apenas com provas.
7. Aprovação humana antes de instalação persistente, acesso a contas, envio de mensagens, push ou alteração de produção.

## Ligações de referência
- Auditoria inicial: [tooling-capability-audit-2026-10-14.md](tooling-capability-audit-2026-10-14.md)
- Lista complementar: [claude-code-plugin-skill-catalog-2026-10-14.md](claude-code-plugin-skill-catalog-2026-10-14.md)
- Conceito de escritório virtual: [DGM-MAT virtual office research](DGM-MAT_VIRTUAL_OFFICE_RESEARCH_2026-10-14.md)
- Memória central: `AndreOS/02_PROJETOS/CATALOGO_MESTRE_CAPACIDADES_DGM_MAT_2026-10-14.md`

## Requisitos organizacionais documentados
- [Fábrica de agentes, RH, hierarquia departamental, Programação multi-linguagem e Design/UI/UX](DGM-MAT_FACTORY_HR_DEPARTMENTAL_HIERARCHY_PROGRAMMING_AND_DESIGN_2026-10-14.md) — visão e requisitos registados em 2026-10-14; não constitui prova de implementação nem autorização de instalação.
