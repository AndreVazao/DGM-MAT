# DGM-MAT — Auditoria de lacunas da inteligência de conversas
Data: 2026-10-10
Estado: revisão estática do código publicado; sem testes locais nesta etapa

## Resumo
Já existe uma base de ingestão de ficheiros exportados e extração/auditoria de código em `core/conversation_intelligence/`. Isto não equivale à missão completa de recuperar e reorganizar conversas de fornecedores. O caminho correto é estender essa base sem declarar a função concluída.

## Capacidades verificadas por leitura do código
- `ConversationRecord` guarda ID, fornecedor, título, conteúdo agregado, fonte, URL, projetos/tags e metadata.
- `ConversationIngestor` lê ficheiros JSON, HTML e texto, normaliza aliases de fornecedores e cria IDs por hash quando necessário.
- `ConversationAuditor` sugere projeto/título por contagem lexical e identifica alguns avisos de sintaxe/complexidade.
- `CodeExtractor` e `CodeConsolidator` são chamados pelo pipeline para extrair artefactos e agrupar fingerprints.
- `ConversationIntelligencePipeline` expõe ingestão de ficheiro, consolidação e resumo.

## Lacunas críticas face à diretiva primária
1. **Sem separação explícita por autor/turno:** o conteúdo é agregado num campo `content`; não há modelo de mensagens com autor, timestamp e ordem, logo não consegue distinguir com rigor pedido do utilizador e resposta da IA.
2. **Sem linha temporal de intenção:** não há estados para pedido vigente, decisão confirmada, proposta da IA, decisão substituída ou conflito.
3. **Sem grafo persistente de relações:** o auditor sugere projeto por palavras; não mantém ligações com evidência entre conversas, sucessores, correções, conflitos ou continuação.
4. **Sem catálogo durável de cobertura:** o código analisado não demonstra checkpoints de importação, estados parcial/bloqueado/retomável, paginação ou deteção de completude de conversa.
5. **Sem integração de sessão autenticada comprovada:** o pipeline lê ficheiros; não prova login persistente em fornecedores nem navegação histórica real.
6. **Sem mutação remota de títulos/grupos:** o título é apenas sugerido localmente; não prova capacidade de renomear ou agrupar na plataforma.
7. **Sem decisão baseada em evidência suficiente:** o score lexical é uma heurística, não pode declarar por si só que um pedido antigo foi revogado.
8. **Sem indexação pesquisável/arquivo de contexto completo comprovados:** a API de análise existente não equivale a um arquivo local completo de conversas.

## Sequência de implementação recomendada
### Fase 1 — modelo de evidência
Introduzir registos separados para Conversation, Message/Turn, UserIntent, AIProposal, Decision, VerifiedFact, Relationship e ArtifactProvenance. Preservar o modelo antigo através de migração compatível, sem quebrar os callers atuais.

### Fase 2 — importação e cobertura
Implementar import adapters para exportações oficiais, deduplicação determinística, checkpoints, estados `complete`, `partial`, `blocked_login`, `rate_limited`, `failed`, `needs_user` e contagem de mensagens efetivamente adquiridas.

### Fase 3 — evolução de intenção
Construir uma cronologia ordenada de pedidos/correções. Propostas de IA não se tornam decisões automaticamente. Atribuir `CURRENT`, `PROPOSED`, `SUPERSEDED`, `LEGACY`, `CONFLICT`, `UNVERIFIED` ou `RETRACTED` com referência à evidência e ao sucessor. Confiança baixa gera revisão, não eliminação.

### Fase 4 — projeto e relações
Criar classificação explicável com evidência (trechos, links e pontuação) e relações entre conversas de vários fornecedores. Exigir revisão antes de renomear/agrupar remotamente.

### Fase 5 — pesquisa e arquivo
Guardar conteúdo privado local com controlo de acesso, indexação full-text, origem, hash, autor e timestamp. Não sincronizar conteúdo pessoal bruto para Git por defeito.

### Fase 6 — UI e fornecedores
Área cockpit “Fontes de IA”, login manual em perfil dedicado, uma sessão ativa, importação read-only com preview e cancelamento. Só depois validar renomeação remota, e apenas onde suportada e autorizada.

## Critérios de aceitação
- Teste prova que pedido do utilizador e resposta da IA permanecem registos distintos.
- Uma decisão posterior substitui a anterior apenas com evidência e mantém histórico.
- Reimportar o mesmo export não duplica conversas, mensagens ou artefactos.
- Cobertura parcial nunca é rotulada como completa.
- Cada artefacto aponta para fornecedor, conversa, mensagem/turno e contexto.
- Nenhum código recuperado é executado automaticamente.
- Nenhuma credencial, cookie, token ou MFA aparece em logs, prompts, eventos ou arquivo.
- Testes e validação E2E documentados antes de declarar entrega.

## Limitações desta auditoria
Esta foi uma leitura estática dos ficheiros publicados `models.py`, `ingest.py`, `auditor.py` e `pipeline.py`. Não foram executados testes locais nem alterado o runtime. As conclusões devem ser verificadas no clone local antes de implementar mudanças.
