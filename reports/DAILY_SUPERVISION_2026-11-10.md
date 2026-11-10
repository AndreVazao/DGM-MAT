# Relatório diário de supervisão — DGM-MAT

**Data/hora da ronda:** 2026-11-10 15:06 UTC  
**Repositório:** AndreVazao/DGM-MAT  
**Branch default:** `main`  
**HEAD observado:** `fdae0ce102c35d15ff3c4564039bdd4396aa139a`  
**Classificação global:** VERIFICAÇÃO INCOMPLETA  
**Alterações de código nesta ronda:** nenhuma  
**Âmbito:** GitHub e observação read-only do PC-Vazao-Anjos. Não foram alterados ficheiros locais, configuração, permissões, aprovações, branches existentes ou instalação.

## 1. Estado geral

A main avançou substancialmente desde o relatório de 2026-11-09. Foram integradas dez PRs recentes (#332–#342, excluindo números que não correspondem a PRs), incluindo a simplificação do cockpit, arquivo/restauro reversível de conversas, pesquisa local de conversas e, sobretudo, a verificação de capacidade do executor antes de pedir aprovação para uma missão.

O estado atual não permite declarar o DGM-MAT funcional de ponta a ponta:

- O PC-Vazao-Anjos está online e o processo DGM-MAT responde a `GET /health`.
- Existem dois processos headless `DGM-MAT.exe`; apenas um foi identificado como proprietário do listener TCP 127.0.0.1:8181. A função do segundo processo não foi determinada.
- A leitura de `/openapi.json` devolveu HTTP 401. Não foi obtida uma sessão autenticada nesta ronda.
- Não foi possível consultar estado autenticado, fila, missões, scheduler, AutoHelp, repository learning, providers ou políticas de aprovação.
- Não foi criada nem executada uma missão local. A validação E2E da main passou no CI, mas não substitui um teste funcional no PC.
- Não foi importada nenhuma conversa nesta ronda nem recebida uma resposta real de provider.
- Não foi possível revalidar o DGM-HUB localmente.

A classificação é VERIFICAÇÃO INCOMPLETA, não SEM ALTERAÇÕES: houve mudanças importantes no GitHub e foram observados limites funcionais e de acesso.

## 2. Comportamento local confirmado / não verificado

### 2.1 Observações confirmadas

- Dispositivo PC-Vazao-Anjos: online.
- Sistema operativo: Windows 10 Home, versão 10.0.19045.
- Memória física visível: 3.105.668 KB (aproximadamente 2,96 GiB).
- Memória física livre no instante da consulta: 724.952 KB (aproximadamente 0,69 GiB).
- Dois processos `DGM-MAT.exe --headless` foram observados.
- Um desses processos possui o listener em `127.0.0.1:8181`.
- `GET http://127.0.0.1:8181/health` devolveu `{"status":"healthy","service":"dgm-mat"}`.
- `GET /openapi.json` devolveu HTTP 401 Unauthorized.

O HTTP 200 de `/health` confirma apenas a resposta do endpoint de health; não demonstra autenticação, capacidade de missão, execução, persistência ou integração com providers.

### 2.2 Estado não verificado

Não foram obtidos nesta ronda:

- `/runtime/status` autenticado, configuração SAFE/approval e flags de mutação/Git.
- Estado detalhado da fila, worker heartbeat, scheduler, AutoHelp e repository intelligence.
- Ledger de recuperação e inventário de conversas importadas.
- Estado autenticado dos providers e das sessões do browser.
- Branch, HEAD e working tree local atuais.

A tentativa read-only de obter o estado Git local não devolveu conteúdo de estado utilizável. Por isso, não se assume que a branch/checkout referido no relatório anterior continue igual. Nenhuma operação Git local foi executada.

A quota do Desktop Commander foi preservada após a recolha mínima; não foram feitas novas tentativas repetidas nem alterações no computador.

## 3. Missão funcional

### 3.1 Última falha conhecida

O relatório de 2026-11-09 documenta a missão `mission_edcdf5ab`, que terminou FAILED depois de a ação da fila ter sido aprovada, mas o MissionEngine ter selecionado `planning_only_no_executor`. A conclusão da ação da fila foi incorretamente confundível com execução da missão; o registo durável da missão, porém, indicou explicitamente que as subtarefas eram apenas propostas.

A issue [#341](https://github.com/AndreVazao/DGM-MAT/issues/341) registou essa falha e foi fechada pela PR [#342](https://github.com/AndreVazao/DGM-MAT/pull/342), integrada na main em 2026-11-10 11:17:11 UTC.

### 3.2 Comportamento atual integrado

A documentação `docs/operations/MISSION_EXECUTOR_READINESS_2026-11-10.md` estabelece:

- Intenções read-only só são consideradas prontas quando existe um handler fixo suportado.
- Missões tipadas de organização exigem agente disponível, handler registado e todas as capacidades declaradas pela política da tarefa.
- Trabalho desconhecido, sem handler ou sem agente compatível passa para `WAITING_FOR_CAPABILITY`.
- Nesse estado não é criada ação de fila nem pedido de aprovação.
- A evidência de prontidão e a razão de bloqueio ficam no checkpoint.
- A espera não provoca replay automático quando um handler aparece; é necessário novo pedido do operador.
- Uma aprovação ou conclusão da fila nunca é aceite como prova de execução. A conclusão exige recibo durável do worker.

Não foi adicionado um executor genérico de shell. A PR #342 melhora a verdade do ciclo de vida e impede aprovações sem capacidade, mas não torna executáveis intenções arbitrárias.

### 3.3 Resultado desta ronda

**Missão read-only local:** NÃO EXECUTADA.  
**Razão:** não foi obtido acesso autenticado ao runtime/API; não foi criada missão nem contornada a autenticação.  
**CI:** Mission E2E Regression Gate da main passou (run #57).  
**Conclusão:** validação automatizada aprovada; execução funcional no PC ainda não demonstrada.

Não se repetiu `mission_edcdf5ab` nem qualquer outra missão falhada.

## 4. GitHub — estado, branches, PRs, issues e checks

### 4.1 Inventário atual

- Default branch: `main`.
- HEAD: `fdae0ce102c35d15ff3c4564039bdd4396aa139a`.
- Branches devolvidas pela API: 13 (main + 12 branches de trabalho).
- PRs abertas: 0.
- Issues abertas: 20.
- Releases publicadas: 0.
- Artefacto Windows da main: disponível e não expirado.
- A listagem de branches devolveu `protected=false` para main. A leitura explícita do endpoint de branch protection devolveu 403; não foi possível verificar rulesets alternativos. Nenhuma configuração de segurança foi alterada.

### 4.2 PRs recentes confirmadas como merged

| PR | Resultado |
|---|---|
| [#342 — executor readiness antes da aprovação](https://github.com/AndreVazao/DGM-MAT/pull/342) | Merged |
| [#340 — remover limites artificiais de RAM](https://github.com/AndreVazao/DGM-MAT/pull/340) | Merged |
| [#339 — correção archive/restore do cockpit](https://github.com/AndreVazao/DGM-MAT/pull/339) | Merged |
| [#338 — pesquisa de conversas em linguagem natural](https://github.com/AndreVazao/DGM-MAT/pull/338) | Merged |
| [#337 — sidebar chat-first](https://github.com/AndreVazao/DGM-MAT/pull/337) | Merged |
| [#336 — archive/restore reversível](https://github.com/AndreVazao/DGM-MAT/pull/336) | Merged |
| [#335 — defaults de repository learning](https://github.com/AndreVazao/DGM-MAT/pull/335) | Merged, posteriormente superada em parte pela política de #340 |
| [#334 — carregar contexto durável de missão](https://github.com/AndreVazao/DGM-MAT/pull/334) | Merged |
| [#333 — consulta governada a AI no cockpit](https://github.com/AndreVazao/DGM-MAT/pull/333) | Merged |
| [#332 — preservar decisão de qualidade do Technical Director](https://github.com/AndreVazao/DGM-MAT/pull/332) | Merged |

A issue [#341](https://github.com/AndreVazao/DGM-MAT/issues/341) foi fechada pela #342.

A PR [#312](https://github.com/AndreVazao/DGM-MAT/pull/312), anteriormente referida como correção LOW_MEMORY, está CLOSED sem merge. Não deve ser reaberta automaticamente: a política posterior da #340 corresponde à instrução do operador de não impor limites artificiais de RAM.

### 4.3 Branches atuais e divergência

A comparação GitHub `main...branch` devolveu estado `diverged` para as 12 branches não-main. A tabela mostra commits exclusivos reportados pela comparação e áreas de ficheiros com diferenças; os contadores de commits não provam, por si só, que o código esteja ausente da main, porque merges squash e alterações posteriores podem deixar os históricos divergentes.

| Branch | Ahead / behind | Área principal observada |
|---|---:|---|
| `feat/auto-import-vault-conversation-search-2026-11-10` | 2 / 3 | Chrome archive importer e Vault catalog |
| `feat/chat-first-sidebar-cockpit-2026-11-10` | 3 / 5 | Cockpit minimal chat e tema |
| `feat/cockpit-conversation-archive-restore-2026-11-10` | 11 / 6 | Command console, Mobile Bridge e store |
| `feat/cockpit-governed-ai-consultation-2026-11-10` | 9 / 9 | Diálogo de consulta AI e testes |
| `feat/cockpit-mission-context-loader-2026-11-10` | 3 / 8 | Diálogo de consulta e carregamento de contexto |
| `feat/proactive-conversation-search-2026-11-10` | 23 / 4 | Recovery API, MissionEngine e operator search |
| `fix/cockpit-archive-response-data-2026-11-10` | 2 / 3 | Command console e testes |
| `fix/graceful-runtime-shutdown-windows-update-2026-11-10` | 36 / 7 | API/runtime shutdown, instalador, rollback e testes |
| `fix/low-memory-service-manager-defaults-2026-11-10` | 6 / 8 | Serviço Windows e testes |
| `fix/mission-executor-readiness-2026-11-10` | 13 / 1 | MissionEngine, estados e testes |
| `fix/technical-director-quality-decision-main-2026-11-09` | 6 / 10 | Project context, Technical Director e workflow |
| `fix/unrestricted-memory-and-mission-readiness-2026-11-10` | 22 / 2 | Governance, runtime profile, Ollama e testes |

Não foi apagada nem atualizada qualquer branch. A branch de shutdown/update tem alterações em scripts de instalação/rollback e segurança; requer revisão de conteúdo antes de qualquer reutilização. As branches de conversa/importação também requerem comparação de conteúdo antes de se concluir que são trabalho novo ou duplicado.

### 4.4 Issues prioritárias ainda abertas

- [#313 — command-centre chat, histórico pesquisável, novas conversas e ask-an-AI](https://github.com/AndreVazao/DGM-MAT/issues/313).
- [#310 — execução headless governada de Codex/Claude e captura autenticada](https://github.com/AndreVazao/DGM-MAT/issues/310).
- [#308 — memória e proveniência dos project context dossiers](https://github.com/AndreVazao/DGM-MAT/issues/308).
- [#244 — instalador inteligente e self-update](https://github.com/AndreVazao/DGM-MAT/issues/244).
- [#212](https://github.com/AndreVazao/DGM-MAT/issues/212) — ligar o executor backup-first ao MissionEngine.
- [#242](https://github.com/AndreVazao/DGM-MAT/issues/242) — Codex/Claude Free via FCC e memória adaptativa.
- [#237](https://github.com/AndreVazao/DGM-MAT/issues/237) — Vault e catálogo pesquisável.
- [#215](https://github.com/AndreVazao/DGM-MAT/issues/215) — completude e histórico virtualizado.
- [#208](https://github.com/AndreVazao/DGM-MAT/issues/208) — captura autenticada ChatGPT/Gemini/Grok.

### 4.5 Checks da main

No commit `fdae0ce`:

- [Windows Executable Build #554 — run 42806219347](https://github.com/AndreVazao/DGM-MAT/actions/runs/42806219347): SUCCESS.
- [Mission E2E Regression Gate #57 — run 42806219343](https://github.com/AndreVazao/DGM-MAT/actions/runs/42806219343): SUCCESS.

O artefacto publicado pelo build é `DGM-MAT-Windows-3.12-fdae0ce`, ID `13757993868`, tamanho 115.278.337 bytes, não expirado. O SHA-256 do ZIP não foi obtido nesta ronda.

## 5. Correções feitas e links

Não foi identificada nesta ronda uma correção de código de baixo risco que justificasse uma nova PR sem primeiro rever as branches divergentes e o estado real do PC.

A correção funcional recente relevante é a PR #342, já integrada, que impede pedir aprovação para trabalho sem handler executável. Não foi alterada.

Esta ronda acrescenta apenas este relatório documental numa branch isolada. Não houve commits em main, merges, force-push, rebase, reset, eliminação de branches, alteração de remotes, permissões, segredos ou configuração de segurança.

## 6. Sincronização GitHub → PC e self-update

Estado observado:

- A main produziu um artefacto Windows recente e não expirado.
- Não há GitHub Release publicada.
- Não foi descarregado nem instalado o artefacto.
- Não foi obtido o SHA-256 do ZIP nesta ronda.
- Não foi validada a cadeia completa de origem/hash → backup → aplicação → health → teste funcional → rollback no PC.
- A branch `fix/graceful-runtime-shutdown-windows-update-2026-11-10` contém alterações divergentes nos scripts `install_windows_update.ps1` e `rollback_windows_update.ps1`, além de runtime shutdown e testes. Não existe PR aberta associada no inventário atual; não foi assumida como linha pronta para integração.

O self-update permanece NÃO COMPROVADO. O PC não foi atualizado.

## 7. Conversas recuperadas e cobertura por plataforma

**Novas conversas recuperadas nesta ronda: zero.** Não foi feita captura nem importação.

A PR [#338](https://github.com/AndreVazao/DGM-MAT/pull/338) integrou pesquisa em linguagem natural sobre o Recovery Archive local. A documentação `docs/operations/PROACTIVE_CONVERSATION_SEARCH_V1.md` limita explicitamente esta versão:

- Pesquisa apenas arquivos já importados.
- Não inicia sessões nas plataformas nem lê cookies/tokens.
- Não declara histórico integral verificado.
- A pesquisa do conteúdo das mensagens está ligada ao arquivo importado do ChatGPT; para outros fornecedores, os resultados podem limitar-se a metadados.
- A cobertura permanece parcial.

Estado de captura desta ronda:

| Plataforma | Nova captura | Cobertura integral verificada |
|---|---|---|
| ChatGPT | Não realizada | Não |
| Grok | Não realizada | Não |
| Gemini | Não realizada | Não |
| Claude | Não realizada | Não |
| DeepSeek | Não realizada | Não |
| Qwen | Não realizada | Não |

A issue #313 continua aberta porque o objetivo inclui mais do que a pesquisa local já integrada: restauração de contexto, novas conversas isoladas, pesquisa paginada no corpus real e consulta a providers com confirmação explícita.

## 8. Providers e agentes efetivamente testados

Nenhum provider externo nem agente local foi invocado nesta ronda.

A issue #310 continua aberta e descreve o trabalho ainda necessário para Codex/Claude Code: process runner com argv fixo, timeout/cancelamento, sandbox de sistema operativo, worktree isolada, recibos duráveis, verificação de autenticação/modelo/quota e QA independente.

A PR #333 documenta a distinção correta entre:
- providers de browser: ChatGPT, Gemini, Grok, DeepSeek e Qwen;
- agentes locais de execução: Codex Free e Claude Code Free;
- Claude não está configurado no transporte browser descrito nessa PR.

Estas são capacidades documentadas/configuradas, não resultados de testes live desta ronda. Não foi criada qualquer chamada paga ou fallback pago.

## 9. DGM-HUB

A ligação DGM-MAT ↔ DGM-HUB não foi testada localmente nesta ronda.

O relatório anterior de 2026-11-09 registava ausência de processo DGM-HUB, federação local vazia e nenhuma reunião de governação registada. Esse dado é histórico e não é apresentado como observação atual.

Observer/Respond não foi alterado. Não foram enviadas mensagens nem alterado o modo de interação.

## 10. Riscos e bloqueios

1. **Missões live:** falta autenticação local verificável e uma missão read-only concluída no PC.
2. **Executor:** #342 impede aprovações falsas, mas não implementa executor genérico; missões sem handler ficam corretamente à espera de capacidade.
3. **Providers/agentes:** sem prova de resposta real de Codex, Claude Code/FCC ou providers browser nesta ronda.
4. **Conversas:** arquivo e pesquisa local existem, mas a captura integral/paginada e a cobertura multi-provider continuam incompletas.
5. **Self-update:** artefacto existe, mas Release, hash independente e instalação/rollback funcional não foram demonstrados.
6. **Branches:** 12 branches divergem de main; algumas correspondem a PRs já merged por squash, outras podem conter trabalho posterior. Não é seguro apagá-las nem integrá-las apenas pelos contadores.
7. **Proteção da main:** metadados da branch indicam `protected=false`; a leitura de branch protection foi negada (403). A existência de rulesets alternativos ficou por confirmar. Nenhuma alteração foi feita.
8. **Processos locais:** dois processos headless foram observados; a função do segundo não foi determinada.
9. **Recursos:** a máquina tinha cerca de 0,69 GiB de RAM livre. A main atual não impõe limites artificiais de RAM; o sistema operativo pode paginar ou terminar processos se os recursos se esgotarem. Não foi aplicada qualquer limitação de RAM.

## 11. Próximos passos

1. Recuperar uma sessão autenticada normal no cockpit/API e ler o estado SAFE/approval, fila, missões, scheduler, providers e ledger, sem criar credenciais alternativas.
2. Identificar o papel dos dois processos headless e confirmar o estado do working tree local antes de qualquer sincronização.
3. Executar uma única missão read-only com handler fixo disponível; registar mission_id, timestamps, checkpoints, recibo do worker, evidências e estado terminal.
4. Rever conteúdo/commits das branches de auto-import, pesquisa proativa e shutdown/update antes de abrir novas PRs; evitar duplicar #313, #310 e #244.
5. Validar a pesquisa de conversas com fixtures/importações autorizadas, proveniência e estado de completude por fornecedor.
6. Testar Codex e Claude Code separadamente, sem execução de código nem acesso de escrita até existir sandbox/approval verificados.
7. Revalidar a ligação ao DGM-HUB e documentar Observer/Respond sem alterar o modo.
8. Completar a cadeia de atualização em ambiente isolado: artefacto oficial, digest verificado, backup, aplicação autorizada, teste funcional e rollback.
9. Rever com o proprietário a proteção da branch main; nenhuma alteração de segurança deve ser feita automaticamente.

**Conclusão:** a main tem CI/build verdes e o ciclo de aprovação de missões está mais honesto e seguro. O DGM-MAT ainda não foi comprovado como operacional de ponta a ponta no PC: a API autenticada, missão live, providers, arquivo multi-IA e DGM-HUB continuam por validar. Nenhuma capacidade foi declarada funcional apenas por existir código ou passar no CI.


## Nota de publicação — 2026-11-10 15:13 UTC

O inventário da secção 4.1 representa o estado observado antes da publicação deste relatório e indicava zero PRs abertas. A publicação criou a PR documental draft [#343](https://github.com/AndreVazao/DGM-MAT/pull/343), na branch `reports/daily-supervision-2026-11-10`, com um único ficheiro e sem alterações de código. Assim, após a publicação, esta é a única PR aberta criada nesta ronda. Permanece sem merge.


## Aditamento de validação posterior — 2026-11-10 19:20 UTC

Esta secção complementa os resultados recolhidos às 15:06 UTC e não altera retroativamente o âmbito da ronda inicial.

### Instalação e runtime após a ronda inicial

- O build oficial `fdae0ce` foi posteriormente instalado no PC através do instalador oficial.
- O SHA-256 do executável instalado coincide com o pacote oficial: `97C4B1FCA805E884C3AFEF54902D047F700254F96989632502C65849DD44D675`.
- Foi criado backup/manifesto em `C:\\ProgramasGodMode\\DGM-MAT\\update-backups\\20261110-125511\\INSTALL-MANIFEST.json`.
- O endpoint `/health` continua a devolver HTTP 200.
- O cliente oficial do cockpit conseguiu trocar o bootstrap local por sessão autenticada e consultar `GET /runtime/status`: HTTP 200, `status=running`, `is_degraded=false`, zero missões ativas.
- `GET /runtime/queue`: HTTP 200; worker vivo, um thread e handler `MISSION_EXECUTION`.
- A consulta `GET /runtime/missions` excedeu o timeout de leitura de 5 segundos. Não foi repetida em ciclo nem contornada.

### Cockpit desktop

- Importação de `cockpit.app` validada com Python 3.12.6 e PySide6 6.11.1.
- Foi iniciado o cockpit nativo; o processo Python GUI permaneceu ativo e responsivo, com janela `DGM-MAT - Chat` e handle de janela não nulo.
- O widget de chat foi testado com a instrução read-only `runtime status`; apresentou corretamente o estado autenticado do runtime.
- Não foi encontrado um atalho `DGM-MAT Chat` no Desktop nem nos menus de programas/startup pesquisados.
- A inspeção do código instalado confirma que esta versão é ainda uma consola de chat de missões: o histórico é mantido numa lista em memória da instância, sem sidebar de conversas, pesquisa integrada ou persistência demonstrada. Portanto, a abertura da janela e a consulta de estado passaram; a experiência ChatGPT-like pretendida ainda NÃO está funcionalmente validada.
- Não foi submetida qualquer missão nova, não foi aprovada/rejeitada qualquer ação e não foram alterados registos históricos.

### Checkout local — preservação obrigatória

A inspeção read-only encontrou o checkout em:

- Branch: `recovery/local-worktree-consolidation-2026-11-09`
- HEAD: `e06d89402d9e3cd6e36a189daa3f13bee8c4d413`
- Working tree com alteração em `scripts/autostart/backend_service.py` e ficheiros não rastreados, incluindo `installed/`, backups, staging e ficheiros de recuperação.

Não foi executado pull, checkout, reset, clean, commit ou qualquer limpeza. Estes elementos devem ser preservados até reconciliação explícita com a main e com o relatório de instalação.

### Conclusão revista

A instalação do executável, a autenticação normal do cockpit e as leituras de estado/queue estão agora comprovadas. Continua por validar uma missão read-only concluída com recibo durável, o endpoint de listagem de missões, a persistência/histórico/sidebar do cockpit, o atalho, o rollback real, os providers e o DGM-HUB. O estado global permanece **VERIFICAÇÃO INCOMPLETA**.


## Correção de evidência — cockpit oficial validado — 2026-11-10 19:27 UTC

Esta correção prevalece sobre qualquer formulação anterior neste relatório que pudesse confundir o teste Python do checkout local com o executável oficial instalado.

### Separação entre código local e executável instalado

- O primeiro processo GUI Python (PID 4416) foi iniciado a partir do checkout local `recovery/local-worktree-consolidation-2026-11-09`, cujo código de cockpit está desatualizado. Esse processo foi fechado e o seu teste visual/widget não é aceite como prova do cockpit oficial.
- O executável instalado foi iniciado separadamente com `DGM-MAT.exe --cockpit-only`, sem iniciar um segundo backend.
- A janela Qt do executável oficial foi confirmada visível, com título `DGM-MAT - Assistente`, processo GUI PID 2816 e `Responding=True`.
- Os processos backend originais PID 6052/2364 mantiveram-se ativos; não foram reiniciados.
- O código da main observada em `fdae0ce` contém sidebar com Nova conversa, pesquisa, histórico, paginação, arquivo/restauro, consulta governada a IA e estado do sistema. A inspeção da fonte confirmou os handlers e endpoints correspondentes.

### Conversas — criação, pesquisa e persistência

- `GET /mobile/threads`: HTTP 200; 24 conversas listadas antes do teste.
- `GET /mobile/threads/search?q=DGM&limit=5&offset=0`: HTTP 200; cinco resultados e `has_more=true`.
- Foi criada uma conversa de teste local, sem mensagem: título `Validação técnica cockpit — 2026-11-10`, ID `thread-14375e4504ee4365`; `POST /mobile/threads` devolveu HTTP 200.
- `GET /mobile/threads` confirmou o ID e o título exatos (25 conversas na listagem).
- A janela oficial foi fechada graciosamente e o cockpit foi iniciado novamente com `--cockpit-only`. Após o fecho/reabertura, a consulta autenticada à lista voltou a devolver HTTP 200 e confirmou que a conversa de teste continuava presente com estado `active`.
- Esta prova cobre persistência da conversa através do fecho/reabertura do cockpit enquanto o backend permaneceu ativo; não prova persistência após reinício do backend/PC.
- A conversa de teste foi mantida para inspeção no cockpit. Não contém mensagens de teste.
- Não foi submetida missão, nem executada ação de aprovação, arquivo ou restauro.

### Estado final desta validação

**Confirmado:** executável oficial abre uma janela Qt visível e responsiva; API autenticada; lista e pesquisa de conversas; criação e persistência de uma conversa após fechar/reabrir o cockpit.  
**Ainda por confirmar:** interação manual completa no ecrã, conteúdo visual de cada componente, envio de mensagem, pesquisa pela interface, arquivo/restauro pela interface, atalho Desktop e persistência após reinício do backend.  
**Classificação global:** VERIFICAÇÃO INCOMPLETA.


## Correção adicional — atalho Desktop localizado — 2026-11-10 19:29 UTC

A pesquisa inicial de atalhos não incluiu a localização Desktop redirecionada para OneDrive. A consulta correta a `[Environment]::GetFolderPath('Desktop')` encontrou o atalho existente:

- Ficheiro: `DGM-MAT Chat.lnk` no Desktop OneDrive.
- Target: `C:\\ProgramasGodMode\\DGM-MAT\\installed\\DGM-MAT.exe`.
- Argumentos: `--cockpit-only`.
- Working directory: `C:\\ProgramasGodMode\\DGM-MAT`.
- Descrição: abrir o cockpit de chat ligado ao backend local.

O atalho já estava corretamente configurado; não foi criado nem alterado. O teste anterior do executável com o mesmo argumento confirmou uma janela oficial `DGM-MAT - Assistente` visível e responsiva.


## Novo bloqueio confirmado — archive/restore e classificação da rota — 2026-11-10 21:44 UTC

- Foi tentado arquivar exclusivamente a conversa de teste `thread-14375e4504ee4365`.
- O endpoint `POST /mobile/threads/{id}/archive` devolveu HTTP 403: `Route has no security classification.`
- O teste parou imediatamente; o endpoint restore não foi chamado e a conversa de teste não foi alterada.
- Não se deve contornar nem enfraquecer a middleware. É necessário inspecionar o registo/classificador de segurança das rotas e acrescentar a classificação explícita correta, com testes de autorização para arquivo/restauro.
- O achado foi registado na issue #313. A quota Desktop Commander está a 13% disponível; o próximo ciclo deve privilegiar inspeção do código e testes determinísticos no GitHub/CI, reservando nova execução remota para uma verificação agrupada depois da correção.

## Documentação da readiness

- PR #344 criada: [docs: record mission executor readiness validation](https://github.com/AndreVazao/DGM-MAT/pull/344).
- Corrige o estado obsoleto `awaiting CI validation` do documento de readiness, regista os runs Windows build #42806219347 e Mission E2E Regression Gate #42806219343 e distingue esses resultados de uma missão read-only real ainda não concluída.
- PR #344 está aberta, não mergeada. O combined status mostra apenas `security/snyk` pendente; não o usaremos como bloqueio porque a quota mensal gratuita do Snyk está esgotada. Nenhuma alteração de código/runtime foi feita nesta PR.


## Correção preparada — classificação archive/restore — 2026-11-10 21:48 UTC

A inspeção da fonte na main confirmou a causa exata do HTTP 403:

- `core/api/mobile_bridge.py` regista `POST /threads/{thread_id}/archive` e `POST /threads/{thread_id}/restore`.
- `core/api/auth_middleware.py` aplica classificação fail-closed e devolve 403 quando não existe entrada explícita.
- `core/api/security_policy.py` classificava create, messages e rename, mas omitia archive e restore.

Foi preparada a PR #345: [fix(security): classify mobile conversation archive and restore routes](https://github.com/AndreVazao/DGM-MAT/pull/345).

Alterações na branch `fix/classify-mobile-thread-archive-restore`:
- Classificar os dois endpoints como `MOBILE_CHAT`, exigindo o scope `mobile-chat`.
- Testar a classificação por template e por caminho concreto.
- Testar a autorização de sessão mobile-chat para arquivar/restaurar.
- Testar que uma sessão apenas `local-client` recebe 403 e não altera o estado da conversa.

A PR está aberta e mergeável. O único check reportado neste momento é `security/snyk` pendente; não será usado como bloqueio devido à quota mensal gratuita esgotada. Não foi feito bypass à middleware, merge ou instalação. A correção ainda aguarda CI de testes e validação real no PC.
