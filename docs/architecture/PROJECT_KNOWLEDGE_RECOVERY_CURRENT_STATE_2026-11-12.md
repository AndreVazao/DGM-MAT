# DGM-MAT — auditoria do estado atual da recuperação de conhecimento e inteligência por projeto

**Data:** 2026-11-12  
**Base auditada:** `main` após merge da PR #357 (`3e6ef11dc501f70e8c550c6bdf2e8ecaf408131`)  
**Objetivo:** separar capacidades existentes, limitações comprovadas e trabalho ainda necessário para inventariar conversas, scripts e código de todos os projetos e permitir consultas de estado por projeto.

## 1. Conclusão executiva

A main já contém uma fundação técnica relevante: captura browser visível para seis providers, importação de exportações ChatGPT, pipeline de inteligência de conversas, extração de candidatos a código, sessões de Claude Code via Telescope, Vault persistente, catálogo de projetos, inventário read-only de repositórios e geração de dossiers a partir de conversas explicitamente mapeadas.

**Isto ainda não equivale ao objetivo completo do operador.** A recuperação por provider não está demonstrada como completa; o inventário local de fontes é apenas metadados para três providers; o import inbox ainda só importa automaticamente ChatGPT; o inventário de repositórios produz sobretudo metadados e árvores de caminhos, não um catálogo completo de scripts e relações de código; e o gerador de dossiers não constitui ainda uma consulta natural de estado atual do projeto no Cockpit.

A prioridade é fechar estas ligações reutilizando os componentes existentes, não criar uma segunda memória, um segundo Vault ou scanners concorrentes.

## 2. Inventário técnico confirmado na main

### 2.1 Captura de conversas por browser — seis providers

Ficheiros principais:
- `core/api/browser_capture_api.py`
- `core/recovery/recovery_ledger.py`
- `browser_extension/background.js`
- `browser_extension/content.js`
- `tests/api/test_browser_capture_api.py`
- `tests/browser_extension/test_content_capture.js`

Confirmado por leitura do código:
- A API define allowlist e schemas para ChatGPT, Gemini, Grok, DeepSeek, Qwen e Claude.
- A extensão percorre os seis providers na descoberta de conversas.
- A extensão envia descoberta, reclamação sequencial, captura e bloqueios para a API local.
- A API valida host/URL e ID de conversa, mantém estados no RecoveryLedger e arquiva capturas com hash SHA-256.
- A captura é declarada como proveniente de UI visível; a API não contacta os providers nem lê credenciais.
- O conteúdo capturado segue para o ConversationIntelligencePipeline e para o Vault, com proveniência.
- Existem testes de API e fixtures de captura para os seis providers.

Limites confirmados:
- `PROVIDER_OLDEST_BOUNDARY_EVIDENCE` está vazio na main. O código só pode considerar atingido o limite histórico mais antigo com evidência específica por provider. Portanto, não há base para declarar a captura integral do histórico.
- O endpoint de estado declara explicitamente `full_history_completeness_claimed: false`.
- Os testes de fixtures não substituem a aceitação real em browser autenticado, provider a provider.
- Não foi executado nesta auditoria qualquer acesso ao PC nem captura real de conversas.

Estado: **implementação de backend/extensão presente; cobertura histórica completa e aceitação real por provider não demonstradas.**

### 2.2 Inventário local de fontes AI — apenas metadados de três providers

Ficheiros:
- `core/recovery/ai_source_inventory.py`
- `scripts/inventory_ai_conversation_sources.py`
- `core/api/recovery_api.py`

A função `inventory_local_ai_sources` lê indicadores de aplicações e metadados do histórico Chrome. A allowlist deste inventário é apenas:
- ChatGPT
- Grok
- Gemini

O próprio resultado declara:
- `conversation_content_read: false`
- `provider_accounts_accessed: false`
- `complete_conversation_inventory: false`

Isto é útil para descobrir fontes e rotas de conversas, mas **não recupera mensagens nem equivale à captura de seis providers**. Não deve ser apresentado ao operador como inventário de conteúdo.

### 2.3 Importação de exportações locais

Em `core/api/recovery_api.py`:
- A importação oficial ChatGPT JSON/ZIP está implementada.
- A pasta de entrada está limitada a ChatGPT, Gemini e Grok.
- ChatGPT é o único provider atualmente marcado como suportado para importação automática do inbox.
- Gemini e Grok permanecem em `awaiting_provider_adapter`.
- DeepSeek, Qwen e Claude não fazem parte deste import inbox.

A captura browser visível de seis providers é um caminho separado e não deve ser confundida com os adapters de ficheiros de exportação.

Estado: **ChatGPT export funcional; adapters de exportação Gemini/Grok pendentes; sem import inbox para DeepSeek/Qwen/Claude.**

### 2.4 Pipeline de inteligência e extração de scripts/código de conversas

Ficheiros:
- `core/conversation_intelligence/ingest.py`
- `core/conversation_intelligence/pipeline.py`
- `core/conversation_intelligence/code_extractor.py`
- `core/conversation_intelligence/auditor.py`
- `core/conversation_intelligence/progress_store.py`
- `core/conversation_intelligence/knowledge_store.py`
- `core/conversation_intelligence/models.py`

Capacidades confirmadas:
- Normalização de registos JSON/HTML para conversas e mensagens.
- Identificadores, papéis, ordem e metadados.
- Checkpoints e fingerprints para evitar reprocessamento.
- Extração de blocos de código e candidatos a ficheiros, com provider/conversa/mensagem/origem quando disponível.
- Validação sintática de Python para candidatos Python.
- Auditoria de conversa e armazenamento de conhecimento/revisão.

Limites:
- Extrair um bloco de código de uma conversa não prova que seja a versão atual, que tenha sido aplicada ou que seja executável no repositório.
- A associação entre snippet e ficheiro real precisa de verificação contra paths, commits, imports/callers e testes do projeto.
- A ingestão genérica de JSON/HTML não é, por si só, um parser oficial e validado de cada provider.

Estado: **pipeline de ingestão e extração existe; reconciliação sistemática de todos os candidatos com o código real de todos os repositórios continua por fechar.**

### 2.5 Sessões de coding agents — fonte separada

Ficheiros:
- `core/conversation_intelligence/telescope_adapter.py`
- `core/conversation_intelligence/telescope_archive_importer.py`

O adapter de Telescope limita metadados a campos permitidos. O importer consegue exportar sessões de Claude Code via CLI, criar arquivo Markdown/JSON e alimentar o pipeline de inteligência.

Isto é uma fonte de sessões de agente de programação, não uma conversa do provider Claude.ai. Os relatórios devem manter categorias distintas:
- Providers conversacionais: ChatGPT, Grok, Gemini, Claude, DeepSeek, Qwen.
- Agentes/sessões locais: Codex Free, Claude Code Free e outros collectors detetados.

Estado: **importer Claude Code/Telescope presente; a cobertura de outros agentes depende dos collectors e adapters validados.**

### 2.6 Vault persistente e catálogo de projetos

Ficheiros:
- `core/vault/catalog.py`
- `core/vault/bootstrap.py`
- `docs/operations/DGM-MAT-PERSISTENT-VAULT.md`

Confirmado:
- O Vault fica fora do diretório de instalação e recusa uma raiz dentro de um worktree/repositório Git.
- Existe catálogo SQLite para projetos, conversas, mensagens, artefactos de código, referências GitHub e snapshots de árvores.
- Preserva capturas raw e conversas normalizadas com fingerprints e proveniência.
- Faz associação sugerida por aliases no título/conteúdo, distinguindo `suggested`, `ambiguous` e `unclassified`; uma associação explícita tem estado próprio.
- Tem sincronização de registos completos do progress store para o Vault.
- Tem snapshot de repositórios e verificação de referências GitHub.
- Regista atualmente nove projetos conhecidos: DGM-MAT, DGM-HUB, DGM-MCP, AndreOS Memory, DGM-MAT-Mobile, VAZAO EVSE Platform, VazaoSovereignTrader, Office Kit e Family DGM.

Limites:
- A existência de nove registos seed não prova que todos os repositórios locais/GitHub foram encontrados, associados e reconciliados.
- Associação sugerida por texto não deve ser confundida com confirmação do operador; ambiguidades têm de continuar visíveis.
- A instalação/upgrade do executável não pode substituir nem apagar o Vault.

Estado: **fundação persistente e catálogo presentes; cobertura completa e reconciliação global ainda não demonstradas.**

### 2.7 Inventário automático de repositórios locais

Ficheiros:
- `core/autonomy/repository_learning.py`
- `core/api/repository_learning_api.py`
- `docs/operations/AUTOMATIC_REPOSITORY_LEARNING_STARTUP.md`

O worker:
- descobre repositórios em roots configuradas;
- recolhe branch, SHA, estado dirty, origin e stack/manifests;
- gera árvores de caminhos limitadas e exclui pastas/ficheiros protegidos;
- lê apenas um resumo limitado do README para descrição;
- mantém cursor/estado SQLite e processa lotes retomáveis;
- não edita repositórios, não altera Git, não executa código de projeto.

A árvore é explicitamente path-only: os conteúdos dos ficheiros não são lidos por este gerador. A associação de projetos usa evidência de origin comum ou pasta pai; repositórios isolados ficam com baixa confiança e aguardam revisão semântica.

Estado: **inventário local read-only e árvores de caminhos presentes; catálogo de scripts, imports, callers, dependências e testes requer uma camada de análise estática adicional.**

### 2.8 Inventário de portfolio GitHub

Ficheiro:
- `core/repository_intelligence/github_portfolio_inventory.py`

Existe um inventário separado que compara repositórios locais e GitHub, estado de branches e divergência da branch default. Usa a ferramenta `gh` do host. Deve ser integrado no dossier como fonte GitHub, sem assumir que substitui a leitura dos conteúdos locais nem a validação de runtime.

### 2.9 Dossier de contexto por projeto

Ficheiro:
- `core/conversation_intelligence/project_context.py`
- testes: `tests/conversation_intelligence/test_project_context.py`

O `ProjectContextDossierGenerator`:
- usa páginas SQLite e escrita incremental;
- só inclui snapshots de conversas completos;
- exige mapping explícito `provider:conversation_id → project_key`;
- mantém mensagens do utilizador separadas de respostas/propostas do assistant;
- aponta cada mensagem e candidato de código para a origem;
- declara expressamente que o estado do repositório não é afirmado pelo gerador.

Limites:
- Não faz associação automática/fuzzy no gerador.
- Não reconcilia branches, PRs, commits, testes ou runtime.
- A pesquisa nesta main não encontrou uma rota Cockpit/API que transforme este gerador numa consulta natural interativa por projeto.

Estado: **gerador de dossier de conversas com evidência existe; consulta completa do estado atual do projeto ainda não existe como capacidade integrada.**

## 3. Matriz resumida de cobertura

| Área | Estado confirmado | Lacuna principal |
|---|---|---|
| Captura browser ChatGPT/Grok/Gemini/Claude/DeepSeek/Qwen | API e extensão com suporte declarado e fixtures | Aceitação real por provider e prova de limite histórico |
| Inventário Chrome local | Metadados ChatGPT/Grok/Gemini | Não contém transcrições; não cobre seis providers |
| Export ChatGPT | Importador suportado | Gemini/Grok sem adapter; restantes sem inbox |
| Sessões Claude Code/Telescope | Adapter/importer presente | Não equivale a provider Claude.ai; outros agents por validar |
| Pipeline de conversas | Ingestão, checkpoints, auditoria, code extraction | Parsers/coverage por fonte e reconciliação de snippets |
| Vault | Persistência, catálogo, projetos, capturas, artefactos | Cobertura global e associação confirmada por projeto |
| Repository learning | Metadados Git + árvore path-only | Leitura estática de scripts/imports/dependências/testes |
| GitHub portfolio | Inventário local/remoto e comparação de branches | Unificação com evidência de código e dossier |
| Project dossier | Conversas completas com mapping explícito | Estado atual Git/runtime e consulta Cockpit |

## 4. Sequência de implementação recomendada

### P0 — Auditoria operacional e cobertura real
1. Obter status real do Vault, RecoveryLedger, progress store, repository learning e extensão no PC quando estiver disponível.
2. Executar captura controlada e sequencial de pelo menos uma conversa real por provider, registando estados e bloqueios.
3. Verificar que raw capture, transcript normalizado, mensagens, artefactos e Vault têm hashes/proveniência coerentes.
4. Medir quantas conversas foram descobertas, capturadas integralmente, parcialmente, bloqueadas ou ainda não visitadas. Não declarar cobertura total sem evidência de limite histórico.

### P1 — Inventário de scripts e código por projeto
1. Criar catálogo de artefactos extraídos das conversas, com fingerprints, origem e variantes.
2. Gerar árvore atual de cada repositório e mapear manifestos, linguagens, entry points, scripts, testes e documentação.
3. Analisar imports/exports e dependências sem executar código.
4. Comparar candidatos das conversas com ficheiros reais, identificando correspondências, versões divergentes e código nunca integrado.
5. Guardar relatório por projeto no Vault, sem escrever nos repositórios de origem.

### P2 — Dossier de estado atual por projeto
Cada dossier deve reconciliar:
- conversas, decisões do operador, propostas AI e questões pendentes;
- scripts/código, path, repositório, branch e commit;
- branches, PRs, issues e commits GitHub;
- testes/builds/artifacts e respetiva data;
- inventário/runtime local quando acessível;
- gaps, dependências, duplicados e próximos passos.

Cada afirmação importante deve ligar à evidência. Memória antiga deve ser marcada como histórica e não apresentada como estado atual.

### P3 — Consulta natural no Cockpit
Adicionar pesquisa/consulta por projeto com perguntas naturais. Responder primeiro com estado resumido e permitir drill-down para conversas, scripts, branches, testes, decisões e evidência. O contexto deve ser carregado do Vault e atualizado apenas nas fontes que estiverem acessíveis.

## 5. Issues de acompanhamento

- #164 — inventário transversal de conversas e fontes.
- #208 — captura por UI visível autenticada.
- #237 — Vault persistente e inteligência por projeto.
- #240 — auditoria estática de código.
- #306/#308 — dossiers de contexto e respetivos limites/proveniência.
- #313 — chat pesquisável e consulta a providers.
- #358 — dossier vivo e consulta natural do estado de cada projeto.

A issue #358 formaliza a prioridade máxima do operador em 2026-11-12.

## 6. Guardrails inegociáveis

- Read-only durante inventário e análise: sem alterações a repositórios, branches, conversas de origem ou contas dos providers.
- Não ler cookies, passwords, tokens, localStorage/IndexedDB de autenticação nem contornar login/MFA/CAPTCHA/rate limits.
- Não enviar corpos de conversas privadas ou dados do Vault para GitHub.
- Não fundir projetos ou atribuir conversas ambíguas sem revisão.
- Não converter propostas de IA em decisões confirmadas.
- Não declarar scripts ativos apenas porque aparecem num transcript ou existem num path.
- Não declarar provider/repositório completo sem evidência de cobertura.
- Local-first, sem APIs pagas como fallback.
- Preservar checkpoints e retoma após falhas ou reinícios.
