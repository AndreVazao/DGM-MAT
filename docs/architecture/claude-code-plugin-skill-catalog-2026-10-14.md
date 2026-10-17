# Complemento — catálogo detalhado de plugins e skills Claude Code — 2026-10-14

## Estado e interpretação
Este documento regista os candidatos adicionais fornecidos para avaliação. Não confirma que os nomes, funcionalidades, licenças, métricas, preços, comandos ou alegações promocionais sejam verdadeiros. Cada entrada requer identificação por URL/repositório oficial, versão/commit e revisão de licença antes de ser considerada aprovada. Nenhum item fica marcado como instalado.

## Plugins de engenharia
| Candidato | Valor possível | Decisão inicial / verificação necessária |
|---|---|---|
| Superpowers | TDD, planeamento, debugging sistemático | Prioridade alta; verificar versão e compatibilidade real |
| code-review oficial | Revisão automatizada de alterações | Prioridade alta; confirmar publisher, número de agentes e custo |
| Local-Review | Segunda revisão de alterações locais | Piloto seletivo; medir tokens e precisão |
| Deep Trilogy | Planeamento, implementação e debugging | Avaliar se acrescenta valor sobre Superpowers; evitar duplicação |
| Shipyard | IaC e revisão de segurança | Só se a stack usar Terraform/Ansible/Docker/K8s etc. |
| Vitals | Hotspots por churn/complexidade/acoplamento | Candidato leve; validar fórmula e utilidade |
| SE-CoVe | Verificação independente de respostas | Usar em tarefas de maior risco; medir custo adicional |
| pyright-lsp, typescript-lsp, rust-analyzer-lsp, gopls-lsp | Diagnósticos de tipos | Instalar apenas para linguagens usadas; LSP pode consumir RAM |
| Plannotator | Rever/aprovar planos visualmente | Útil se o fluxo suportar aprovação humana |
| GitHub plugin | Issues, PRs e repositórios via integração | Já existem integrações GitHub disponíveis; comparar antes de duplicar |
| Codex Plugin | Delegação/revisão com Codex | Prioridade de investigação; validar origem, autenticação e quotas |
| Medley | Grafo de dependências e workers | Adiar até provar interoperabilidade e custo |
| Productivity | TASKS.md, memória e dashboard | Comparar com AndreOS-Memory e cockpit antes de adotar |
| session-tools / session-summary | Gestão e análise de sessões | Avaliar em relação a logs/handoffs existentes |
| notion-memory | Memória e fluxos Notion | Só se Notion fizer parte da stack aprovada |
| youtube-transcriber | Transcrição de vídeos | Candidato para investigação/conteúdo; verificar método, limites e termos |
| whatsapp-mcp | Pesquisa/leitura/envio WhatsApp | Risco de privacidade e ações externas; não ativar sem sandbox e aprovação |
| google-drive-upload | Upload de ficheiros | Confirmar limites reais, OAuth e âmbito de permissões |
| token-efficiency-audit | Medir desperdício de tokens | Candidato de baixo risco após revisão; exigir medições reproduzíveis |

## Skills de documentos, design e testes
| Candidato | Uso | Decisão inicial |
|---|---|---|
| PDF, xlsx, docx, pptx | Documentos e ficheiros reais | Aproveitar quando necessários; testar integridade dos ficheiros |
| frontend-design, brand-guidelines | Interfaces e consistência de marca | Útil em cockpit e websites, com critérios de aceitação |
| algorithmic-art | Arte generativa | Opcional para conteúdo visual |
| webapp-testing | Testes web automatizados | Prioridade alta para projetos com UI |
| skill-creator | Skills próprias versionadas | Prioridade alta após documentar processo seguro |

## Skills de engenharia e segurança
TDD Workflow, Security Review, Coding Standards, Backend Patterns, Frontend Patterns, github-pr-review, snyk-fix, bug-hunt, test-first, pr-description, session-handoff e open-code-review são candidatos para comparar com processos e ferramentas existentes. Verificar licenças e origem; Snyk pode ter requisitos de conta/limites; github-pr-review não deve publicar comentários sem aprovação; session-handoff deve registar factos e estado verificável.

AgentShield, vela, dovtail, agentkeeper, agent-budget-guardrail, agent-approval-gate e agent-retry-safety merecem avaliação de segurança/fiabilidade. Confirmar repositórios, regras, testes, manutenção, permissões e compatibilidade antes de confiar neles. Preferir gates determinísticos e política explícita para ações destrutivas, custos e retries com side effects.

Legwork e verve podem ajudar em pesquisa e redação, mas exigem verificação das fontes e revisão humana. cognitive-rhythm-writing e japanese-tech-writing são especializadas e de prioridade baixa salvo necessidade concreta.

## Integrações e dados
- outlook, trello: avaliar apenas se as contas e APIs forem usadas; OAuth de privilégio mínimo.
- garmin: dados pessoais sensíveis; excluir do escopo geral até existir necessidade e autorização explícitas.
- imager: verificar fornecedor, preço por imagem, privacidade e disponibilidade antes de adotar.
- heliograph: ferramenta potencialmente sensível para sistemas isolados; adiar até revisão de segurança.
- Notion skills: evitar duplicar memória AndreOS sem um caso de uso claro.
- Hugging Face Skills: avaliar para modelos locais, datasets e avaliação, respeitando requisitos de hardware.
- Exa: serviço de pesquisa externo; validar quotas, retenção e custos.
- FiftyOne: só se houver projeto de computer vision/datasets.
- DeepEval: candidato para testes de regressão de LLM; avaliar dependências e consumo.
- Pixeltable / GoodMem: comparar com memória e armazenamento existentes antes de introduzir uma segunda camada.
- ClickHouse IO: só se ClickHouse estiver na arquitetura.
- AWS Agents, DataRobot e Domino Data Lab: baixa prioridade num ambiente local-first; verificar dependência de plataforma paga.
- NVIDIA Skills / cuOpt: avaliar apenas com hardware e caso de uso de otimização compatíveis.
- Anthropic Cybersecurity Skills (alegação de 817 skills): confirmar catálogo, fonte, cobertura e manutenção; não importar em massa.

## Política de custo e quotas
A afirmação de que Claude Code requer assinatura paga e os preços, quotas, poupanças (por exemplo, 20–50%) e multiplicadores de tokens são dados voláteis. Confirmar em fontes oficiais atuais. Não usar percentagens promocionais como evidência de desempenho. Para o utilizador, privilegiar recursos gratuitos/local-first e nunca permitir fallback pago automático.

## Plano de validação por candidato
1. Identificar URL oficial e publisher.
2. Confirmar licença e versão/commit.
3. Ler documentação e scripts de instalação.
4. Rever permissões, hooks, MCP, telemetria e segredos.
5. Testar numa cópia isolada sem credenciais de produção.
6. Medir qualidade, falsos positivos/negativos, CPU/RAM, tokens, tempo e custo.
7. Registar resultado e decisão: adotar, piloto, adiar ou rejeitar.
8. Só integrar depois de revisão humana.

## Aplicação à memória central
A avaliação central está em `AndreVazao/andreos-memory`, branch `docs/tooling-capability-audit-2026-10-14`, ficheiro `AndreOS/02_PROJETOS/REGISTO_AVALIACAO_FERRAMENTAS_IA_2026-10-14.md`. Este complemento deverá ser ligado ao registo central através de referência e não copiado integralmente para cada repositório. A branch principal não foi alterada.
