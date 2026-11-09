# Relatório diário de supervisão — DGM-MAT

**Data da ronda:** 2026-11-09  
**Repositório:** AndreVazao/DGM-MAT  
**Branch default:** main  
**Commit de main observado:** 717b92c2a4d4f70a1276630fa92bdf3f3b17b19a  
**Classificação global:** VERIFICAÇÃO INCOMPLETA  
**Falha funcional observada:** mission_edcdf5ab — FAILED  
**Âmbito:** GitHub, PC-Vazao-Anjos e API local observados; não foram feitas alterações de código, configuração, permissões ou instalação.

## 1. Estado geral

O PC-Vazao-Anjos está novamente acessível. Ao contrário da ronda anterior, foi possível confirmar processos DGM-MAT, API local, sessão autenticada de leitura, estado do runtime, fila, histórico de missões, providers e estado do ledger de recuperação.

O resultado não permite declarar o sistema operacional de ponta a ponta:

- O runtime está a responder e o worker da fila está vivo.
- O runtime está em perfil LOW_MEMORY, com cerca de 75% da memória utilizada.
- A missão mais recente observada, destinada a recuperar conversas das IAs, falhou porque o executor genérico não estava registado. O planeador local também recusou inferência por memória insuficiente.
- Existem cinco ações antigas na fila, ainda à espera de decisão; nenhuma foi aprovada nesta ronda.
- O ledger de recuperação não contém fontes/conversas importadas.
- Só Ollama aparece registado no subsistema de providers, com observação stale; nenhum provider foi reportado disponível.
- Não foi detetado processo DGM-HUB, a federação local está vazia e não existem reuniões de governação registadas.
- O GitHub tem avanços recentes importantes, mas o executável instalado não foi demonstrado como correspondente ao main atual.

A classificação global mantém-se VERIFICAÇÃO INCOMPLETA. A falha da missão identificada é uma FALHA CONFIRMADA, não uma simulação.

## 2. Comportamento local confirmado / não verificado

### 2.1 Máquina e runtime

Observações no PC-Vazao-Anjos:

- Windows 10 Home, build 19045.
- Desktop Commander 0.2.52 ligado.
- Instalação observada em C:\ProgramasGodMode\DGM-MAT.
- API a escutar em 127.0.0.1:8181.
- GET /health respondeu HTTP 200.
- Após emissão de uma sessão local efémera, GET /runtime/status respondeu com status=running e is_degraded=false.
- Recursos no momento da consulta: CPU 11,3%; memória utilizada 75,0%.
- O endpoint de autonomia reportou modo LOW_MEMORY.
- Foram observadas duas árvores lógicas de execução: runtime headless e cockpit-only, cada uma com o respetivo processo pai/filho do executável empacotado.
- O endpoint autenticado /runtime/state indicou boot_phase=EXPOSE_RUNTIME_STATE e node_status=processing.

O HTTP 200 de /health, isoladamente, não é aceite como prova funcional. A confirmação acima inclui também estado autenticado, fila, missões e providers.

### 2.2 Segurança e aprovação

O ficheiro local de configuração autónoma apresenta:

- enabled=true.
- execution_mode=SAFE.
- SAFE permite read e test; auto_merge=false e self_modification=false.
- approval_required=true.
- auto_merge_enabled=false.
- max_parallel_tasks=2.

Os campos automatic_mutations e git_operations não foram expostos neste snapshot de configuração; não são declarados ativos nem inativos sem evidência. Não foram alterados controlos, permissões, credenciais ou modos.

A documentação local classifica criação de missões, decisões de aprovação e ações de fila como operações protegidas. As consultas efetuadas foram GET/read-only.

### 2.3 Fila, missões e memória

O endpoint de telemetria do escritório reportou:

| Estado | Quantidade |
|---|---:|
| Missões registadas | 604 |
| FAILED | 558 |
| COMPLETED | 41 |
| QUEUED | 5 |
| RUNNING / APPROVAL_PENDING / WAITING_FOR_USER | 0 |

Estes números incluem histórico antigo e missões de teste; não são tratados como taxa de falha operacional sem classificação individual.

A fila tem:

- Worker vivo, um thread e heartbeat observado.
- Um handler registado: MISSION_EXECUTION.
- Cinco ações QUEUED, criadas originalmente entre 2026-10-15 e 2026-11-05, ainda à espera de decisão.
- Uma ação recente, ID 6, terminou no nível da SafeActionQueue; isso não significa que a missão associada tenha sido concluída com sucesso.

A memória local reportou 154 memórias, 12 consolidadas e 5 padrões detetados. Estes contadores não provam que existam transcrições integrais das plataformas: o ledger de recuperação reportou zero fontes.

Nenhuma das cinco ações antigas foi aprovada, rejeitada ou alterada.

### 2.4 Repository learning, AutoHelp e Telescope

Os GET específicos de repository-learning, AutoHelp e estado de Telescope não foram concluídos nesta ronda: a tentativa de consulta foi bloqueada pelo cliente e encaminhada para revisão manual. Não houve alteração de configuração nem tentativa de contornar esse bloqueio.

Consequentemente, esses três subsistemas ficam marcados como VERIFICAÇÃO INCOMPLETA, não como funcionais.

## 3. Missão funcional

### 3.1 Missão observada

**mission_id:** mission_edcdf5ab  
**Objetivo registado:** recuperar as conversas das IAs  
**Criação:** 2026-11-09 13:32:24  
**Aprovação da ação de fila:** 2026-11-09 13:36:46, por desktop-cockpit  
**Início de execução:** 2026-11-09 13:36:49  
**Estado terminal:** FAILED  
**Atualização terminal persistida:** 2026-11-09 13:36:52

Evidência no log e no registo durável:

1. A missão foi criada e a ação 6 entrou na fila.
2. A ação foi explicitamente aprovada no cockpit.
3. O MissionEngine selecionou o handler planning_only_no_executor.
4. O planeador local foi ignorado para proteger o PC: 0,83 GB de RAM disponível, abaixo dos 1,25 GB exigidos.
5. Não foi tentado fallback para provider remoto.
6. O resultado terminou com: “Mission was planned, but no generic task executor is registered. The subtasks are proposals only and were not executed.”
7. O resultado foi persistido e a missão ficou FAILED.

A ação 6 aparece COMPLETED na fila porque o handler terminou; a missão mission_edcdf5ab ficou FAILED. São estados diferentes e não devem ser confundidos.

### 3.2 Decisão desta ronda

Não foi repetida a missão falhada nem criada uma missão adicional. A causa imediata está identificada e o executável local é anterior à integração do executor tipado #300. A máquina também está em LOW_MEMORY e mantém cinco ações antigas à espera de decisão.

A main atual já contém, após a PR #300, um adaptador de missões tipadas para três operações read-only: inventário de repositório, análise de código Python e inventário de testes Python. Esse adaptador exige um ID de repositório explicitamente permitido pelo host, worker registado e recibo durável. A sua presença no GitHub não prova que esteja instalada ou configurada no PC.

Próxima aceitação: depois de resolver a atualização e confirmar a allowlist do host, executar apenas uma missão tipada e read-only, com autorização/approval aplicável, e recolher mission_id, checkpoints, recibo do worker e estado terminal. Não aprovar automaticamente as cinco ações antigas.

## 4. GitHub — estado atual, branches, PRs, issues e checks

### 4.1 Repositório

- Default branch: main.
- HEAD observado: 717b92c2a4d4f70a1276630fa92bdf3f3b17b19a.
- Branches: 76.
- PRs abertas: 4.
- Issues abertas: 21.
- Releases publicadas: 0.
- A API de branches reportou main como não protegida; o endpoint de rulesets devolveu lista vazia. Não foi alterada qualquer configuração de proteção.

[Commit main 717b92c](https://github.com/AndreVazao/DGM-MAT/commit/717b92c2a4d4f70a1276630fa92bdf3f3b17b19a)

### 4.2 PRs abertas no corte desta ronda

| PR | Estado | Conteúdo e validação |
|---|---|---|
| [#304 — autonomous recovery bootstrap](https://github.com/AndreVazao/DGM-MAT/pull/304) | Draft | Especificação de recuperação autónoma e retomável; declara explicitamente que o supervisor e a ingestão integral ainda não estão implementados. |
| [#303 — branch recovery intelligence](https://github.com/AndreVazao/DGM-MAT/pull/303) | Aberta | Analisador read-only de branches locais, divergência, commits e ficheiros exclusivos; sem fetch, checkout, merge ou eliminação. |
| [#302 — technical director quality policy](https://github.com/AndreVazao/DGM-MAT/pull/302) | Aberta | Política determinística de comparação baseline/candidate, revisão independente e gates de qualidade. Não executa providers nem aprova/integra. |
| [#295 — controlled coding executor contract](https://github.com/AndreVazao/DGM-MAT/pull/295) | Draft | Contrato de arquitetura para execução Codex/Claude governada; não é executor funcional. |

### 4.3 Checks recentes

Main 717b92c:

- [Coding Agent Dry-Run Contract #42631715897](https://github.com/AndreVazao/DGM-MAT/actions/runs/42631715897): SUCCESS.
- [Mission E2E Regression Gate #42631715772](https://github.com/AndreVazao/DGM-MAT/actions/runs/42631715772): SUCCESS.
- [Windows Executable Build #42631715837](https://github.com/AndreVazao/DGM-MAT/actions/runs/42631715837): SUCCESS.

PR #302, head 877a725893: Technical Director Quality Gate, Mission E2E Regression Gate, Focused PR Validation e Windows Executable Build concluídos com SUCCESS.

PR #303, head c6f4b705b8: Branch Recovery Intelligence, Focused PR Validation e Windows Executable Build concluídos com SUCCESS. Um conjunto anterior de runs em e8d1a0a858 falhou/foi cancelado, mas o head mais recente passou.

PR #304 e #295 são documentais/draft; não foram tratados como funcionalidades implementadas.

### 4.4 Merges recentes confirmados

- [#282](https://github.com/AndreVazao/DGM-MAT/pull/282): auditoria documental de branches antigas, merged em 2026-11-09.
- [#284](https://github.com/AndreVazao/DGM-MAT/pull/284): relatório diário anterior, merged em 2026-11-09.
- [#298](https://github.com/AndreVazao/DGM-MAT/pull/298): ordem, resultado durável e aprovação de tarefas da organização.
- [#300](https://github.com/AndreVazao/DGM-MAT/pull/300): execução de missões tipadas através de três workers read-only.
- [#301](https://github.com/AndreVazao/DGM-MAT/pull/301): planeador dry-run para Codex/Claude, sem lançamento de subprocesso.
- [#277](https://github.com/AndreVazao/DGM-MAT/pull/277): UpdateEngine deixa de fingir sucesso.

A PR [#283](https://github.com/AndreVazao/DGM-MAT/pull/283) está CLOSED sem merge e o seu head é recovery/legacy-branch-consolidation-2026-11-07. Não é a branch atual de integração browser. A referência da ronda anterior que associava #283 à implementação browser não corresponde ao estado atual do GitHub.

### 4.5 Branches de recuperação e browser

O checkout local está em recovery/local-worktree-consolidation-2026-11-09, HEAD e06d89402d9e3cd6e36a189daa3f13bee8c4d413.

Comparações GitHub:

- main local 719f53d7d151a7e605cd0e7a98dbc8c6b0387d9e → main remoto 717b92c: remoto 3 commits à frente.
- recovery/local-worktree-consolidation-2026-11-09 → main remoto: diverged, 2 commits exclusivos à frente e 185 atrás. A comparação mostra alterações em áreas como Chrome archive importer e GitHub portfolio inventory. É um candidato de recuperação, não uma branch pronta para merge.

O working tree local não apresenta alterações tracked no status consultado, mas tem entradas untracked importantes: installed/, update-backups/, update-staging-3bb982e/, update-staging-6d22e91/, update-staging-organization-task-v2/, bash.exe.stackdump e uma cópia .bak de api_server.py. Não foram removidas, movidas, adicionadas ou sobrescritas.

A branch [integration/browser-consult-mainline-2026-11-09](https://github.com/AndreVazao/DGM-MAT/tree/integration/browser-consult-mainline-2026-11-09) está diverged: 26 commits à frente e 6 atrás de main. O head c9bddd9a6d tem SUCCESS em Windows Build, Chrome Extension Validation e Focused PR Validation:

- [Windows Build #42612226880](https://github.com/AndreVazao/DGM-MAT/actions/runs/42612226880)
- [Chrome Extension Validation #42612226772](https://github.com/AndreVazao/DGM-MAT/actions/runs/42612226772)
- [Focused PR Validation #42612226884](https://github.com/AndreVazao/DGM-MAT/actions/runs/42612226884)

Esta branch contém uma proposta mais estreita para consultas browser: scope browser-consult-control separado de operator, sessão da extensão sem operator e teste do middleware real que permite a gestão de consultas mas rejeita uma rota geral de operador. O código também exige aprovação por consulta, claim token e registo de falhas sem replay automático. O branch ainda não tem PR e altera autenticação, middleware, security policy e extensão; não foi integrado, rebased ou promovido. A documentação da própria branch mantém como gate a aceitação real em Windows 10 + Chrome.

As branches antigas feat/free-tier-browser-ai-consult e feat/browser-session-operator-v1 continuam divergentes de main e não foram tratadas como linha principal.

## 5. Correções feitas e evidências

Não foi feita correção de código nesta ronda. Não encontrei uma alteração pequena que pudesse ser aplicada sem tocar em autenticação, configuração, dados ou arquitetura.

Avanços confirmados no main:

- #298 expõe tarefas tipadas da organização, resultado persistido e aprovação vinculada ao digest.
- #300 liga três intenções read-only a workers fixos e exige recibo durável antes de marcar uma missão como concluída.
- #301 cria planos de invocação Codex/Claude, mas mantém launch_enabled=false, write_allowed=false e não lança subprocessos.
- #303 propõe arqueologia read-only de branches, ainda em PR.

A main contém capacidade configurada e contratos de segurança; não há prova de que os agentes Codex/Claude tenham executado uma tarefa real.

## 6. Sincronização GitHub → PC e self-update

### 6.1 Instalação atual

O executável instalado existe e tem 111.825.469 bytes. O manifesto de instalação em update-backups/20261109-115733 regista:

- installed_at: 2026-11-09T11:57:46Z.
- new_sha256 e expected_exe_sha256: 577cdac64914b816220c14bdcfe5d660cc9ad5330889db48e7591aadfc0d9cd9.
- package_sha256_verified_before_mutation=true.
- Backup separado de data, exe e launcher.
- Configuração, credenciais, runtime/cognition data, memória e worktrees declarados como preservados.

O SHA-256 recalculado do executável instalado coincide com new_sha256 do manifesto. Isto confirma a integridade do executável em relação ao manifesto dessa instalação; não identifica, por si só, o commit de origem. Os campos de versão do PE não estavam preenchidos.

### 6.2 Staging existente

Existe update-staging-organization-task-v2 com o pacote DGM-MAT-Windows-3.12-43261c7.zip. O SHA-256 do ZIP coincide com o sidecar local:

a42314f6aac71c8a5d0641a38db49fa53d8e888128c2680e56da0c0adc3a32dd

O commit 43261c7eec18637d5d78334b6be2a1d6162e51e2 é um merge de cb33264d9fb849e7f67be29e98cc0c599437acbc em 719f53d7d151a7e605cd0e7a98dbc8c6b0387d9e. É anterior ao main atual 717b92c. O pacote está staged, não instalado, e não foi promovido.

### 6.3 Artefacto atual do main

[Windows Executable Build #42631715837](https://github.com/AndreVazao/DGM-MAT/actions/runs/42631715837) produziu:

- Artefacto: DGM-MAT-Windows-3.12-717b92c.
- Artifact ID: 13681601270.
- Tamanho do ZIP: 111.262.789 bytes.
- Digest SHA-256 do ZIP: 8eba6690fab13acfbe7b1548bdd707d9316a7e7255de6c2181f5b260a5becfe8.
- Criado em 2026-11-09 14:11:21 UTC.

O digest é do ZIP do artefacto, não do EXE. O artefacto não foi descarregado nem instalado nesta ronda. Não há GitHub Release publicada.

### 6.4 Lacuna de self-update

O UpdateEngine atual é deliberadamente fail-closed: check_for_updates() devolve None e apply_update() devolve False. Os módulos safe_updater.py e release_checker.py estão vazios. O caminho suportado continua a ser o instalador PowerShell revisto, com hash independente do EXE, backup e rollback.

Não há descoberta/download automático de release, nem self-update completo. Não foi executado rollback. Não foi atualizada a instalação local.

## 7. Conversas recuperadas e cobertura por plataforma

O ledger local devolveu:

- source_count=0.
- provider_connectors_enabled=false.
- browser_ui_capture_api=true.
- browser_extension_origin_configured=false.
- browser_ui_pairing_ready=false.
- provider_deletion_enabled=false.

Não foi importada nem capturada qualquer conversa nesta ronda.

| Plataforma | Transcrição integral confirmada nesta ronda |
|---|---|
| ChatGPT | Não |
| Grok | Não |
| Gemini | Não |
| Claude | Não |
| DeepSeek | Não |
| Qwen | Não |
| Zia | Não verificada |

Não se confunde lista de histórico, metadados de navegação, captura parcial de DOM ou memória consolidada com transcrição integral. A extensão browser candidata continua por integrar e por validar em Chrome real.

## 8. Providers, agentes e ferramentas

O endpoint de providers lista 14 nomes, mas o resumo do subsistema indica:

- registered_count=1.
- registered_names=[ollama].
- availability_observation_count=1.
- stale_observation_count=1.
- reported_available_count=0.

Ollama está stale; Grok, OpenRouter, Qwen, OpenAI, ChatGPT, Gemini, DeepSeek, Claude e outros aparecem sem observação de disponibilidade, não como providers confirmados funcionais.

A descoberta local encontrou comandos para Codex CLI, Claude Code CLI, Ollama e GitHub CLI. Isto confirma presença de executáveis, não autenticação válida, inferência, resposta ou conclusão de tarefa. Não foi feita chamada de inferência por causa do perfil LOW_MEMORY e da ausência de disponibilidade observada.

A main atual mantém o piloto Codex/Claude em dry-run: plano determinístico, allowlist do host, SHA-256 do pedido, read-only e launch_enabled=false. Não foi lançado Codex nem Claude.

## 9. DGM-HUB

- Não foi detetado processo DGM-HUB local.
- O objeto federation do runtime está vazio.
- GET /governance/meetings devolveu lista vazia.
- Não há evidência de mensagem, proposta, objeção ou decisão trocada entre DGM-MAT e DGM-HUB nesta ronda.
- Não foi alterado o modo Observer/Respond.

A ligação Hub fica NÃO VERIFICADA. Não se presume que um perfil ou repositório existente signifique que o serviço está ligado.

## 10. Riscos e bloqueios

1. O runtime local está em LOW_MEMORY; a missão recente confirmou que a inferência local foi recusada por falta de RAM.
2. A missão de recuperação falhou por ausência de executor genérico no binário/runtime instalado.
3. Cinco ações antigas continuam pendentes de decisão; não foram aprovadas.
4. A recuperação de conversas está sem fontes e sem provider connectors ativos; pairing/origin da extensão não está configurado.
5. Só Ollama está registado e a sua observação está stale.
6. DGM-HUB não foi encontrado em execução e a federação está vazia.
7. O checkout local está em branch de recuperação divergente e contém artefactos untracked que devem ser preservados.
8. A main do GitHub aparece sem branch protection e sem rulesets. Alterar estas definições requer decisão explícita do operador.
9. O artefacto mais recente do main ainda não está instalado; o staging local observado é de um commit anterior.
10. O self-update automático não está implementado.
11. A branch browser de integração é promissora, mas divergiu de main e altera autenticação/security policy; exige revisão e aceitação real antes de integração.
12. O estado de AutoHelp e repository-learning não foi concluído nesta ronda devido à revisão manual exigida pelo cliente.

## 11. Próximos passos

1. Preservar o working tree local e os diretórios installed/, update-backups/ e update-staging-*; não fazer pull/checkout/clean neste checkout.
2. Comparar e documentar os três commits de main que faltam no main local; usar worktree isolado se for necessário preparar atualização.
3. Validar o artefacto atual 717b92c e o sidecar do EXE, depois preparar instalação com backup/rollback; não aplicar sem approval explícito.
4. Confirmar a allowlist host-owned exigida pelo executor tipado #300 antes de tentar uma missão.
5. Classificar as cinco ações antigas e obter decisão do operador; não as aprovar automaticamente.
6. Concluir os GETs de AutoHelp, repository-learning e Telescope quando a revisão do cliente estiver resolvida.
7. Fazer revisão de segurança da branch integration/browser-consult-mainline, reconciliar a divergência sem rebase/force-push e só depois propor PR focada.
8. Executar aceitação real da extensão em Windows 10 + Chrome, com scope dedicado e prova de que não recebe operator.
9. Restabelecer a ligação DGM-MAT ↔ DGM-HUB e provar uma troca de mensagem/decisão com IDs e timestamps.
10. Só declarar recuperação multi-IA após importação real, hashes, checkpoints e cobertura por plataforma.
11. Propor proteção de main e rulesets em separado; nenhuma configuração foi alterada nesta ronda.
12. Implementar discovery de release/self-update apenas com assinatura/digest independente, backup, approval, validação pós-update e rollback.

## 12. Integridade da ronda

- Nenhum commit direto em main.
- Nenhum merge, rebase, force-push, reset, clean ou checkout.
- Nenhuma branch, tag, issue ou repositório apagado.
- Nenhum segredo, cookie ou token incluído neste relatório.
- Nenhuma permissão ou configuração de segurança alterada.
- Nenhuma missão repetida.
- Nenhuma atualização local aplicada.
- Nenhuma conversa marcada como recuperada sem conteúdo e proveniência.

A única alteração GitHub desta ronda é este relatório documental numa branch isolada e PR draft.


---

## Addendum — 2026-11-09, corte adicional após 15:37 UTC

Esta atualização substitui apenas os valores de estado que envelheceram desde o corte inicial do relatório. Os resultados anteriores continuam preservados como observações históricas.

### 1. Estado geral e GitHub atualizado

- `main` avançou de `717b92c2a4d4f70a1276630fa92bdf3f3b17b19a` para `82a743500257a9ee552056d53246a6b0b1f9df6b` através da PR #305.
- Inventário atual: **80 branches**, **6 PRs abertas**, **18 issues abertas**, **24 workflows** e **0 releases publicadas**.
- A branch API reporta `main.protected=false`. Não foi possível ler o endpoint de branch-protection com a integração disponível; nenhuma proteção foi alterada.
- As seis PRs abertas no corte: #309, #307, #306, #304, #302 e #295. As PRs #304 e #295 continuam draft.
- A PR #305 foi integrada. A aprendizagem de repositórios arranca agora por defeito no full runtime, usando o serviço SQLite existente e inventário local read-only.

### 2. Checks e artefactos

Main `82a7435`:
- [Windows Executable Build #42641509725](https://github.com/AndreVazao/DGM-MAT/actions/runs/42641509725): SUCCESS.
- [Mission E2E Regression Gate #42641509731](https://github.com/AndreVazao/DGM-MAT/actions/runs/42641509731): SUCCESS em Ubuntu e Windows.
- Artefacto `DGM-MAT-Windows-3.12-82a7435`, ID `13686106483`, 111.262.561 bytes, digest ZIP `sha256:257753e4dc152f31efd02d24b7c70d18236f54f4ba5f04691c0690f2e5c458ee`. Não foi descarregado nem instalado.

PR #309:
- Base `main` em `82a7435`; head `dbafc54485096651a04e9ff14228b7b4a9b17065`, 8 commits à frente e 0 atrás.
- [Focused PR Validation #42645471750](https://github.com/AndreVazao/DGM-MAT/actions/runs/42645471750): SUCCESS.
- [Chrome Extension Validation #42645471751](https://github.com/AndreVazao/DGM-MAT/actions/runs/42645471751): SUCCESS.
- [Windows Executable Build #42645471807](https://github.com/AndreVazao/DGM-MAT/actions/runs/42645471807): SUCCESS.
- Artefacto `DGM-MAT-Windows-3.12-e92a90b`, 111.262.574 bytes, digest ZIP `sha256:2146d39019bb958e8225f3f4a1c106a25c563347b00be13a65f30aa0cf5defe3`.
- A PR #309 contém a evolução de #306 mais sete commits de endurecimento. #306 continua aberta e não foi fechada; a duplicação de revisão fica assinalada para decisão posterior.

### 3. Nova correção de baixo risco — PR #312

A revisão do commit #305 revelou uma incoerência concreta: o perfil `LOW_MEMORY` já desativa scans de providers e autonomia no arranque, mas a nova política de repository-learning ignorava esse perfil e arrancava sempre por defeito. O worker é read-only e limitado, mas a descoberta inicial percorre as raízes e gera árvores de paths por lotes.

Foi criada a branch isolada `fix/repository-learning-low-memory-autostart-2026-11-09` e aberta a [PR #312](https://github.com/AndreVazao/DGM-MAT/pull/312):
- perfil standard: mantém autostart por defeito;
- perfil LOW_MEMORY: autostart fica desligado por defeito;
- `DGM_REPOSITORY_LEARNING_ENABLED=1` continua a permitir opt-in explícito, mesmo em LOW_MEMORY;
- `DGM_REPOSITORY_LEARNING_ENABLED=0` desliga em qualquer perfil;
- seis testes cobrem standard, LOW_MEMORY, opt-in e opt-out;
- documentação atualizada.

A PR altera apenas runtime policy, testes e documentação. Não muda o serviço, a base de dados, credenciais, permissões ou estado do PC. No corte de 15:37 UTC:
- [Focused PR Validation #42646429260](https://github.com/AndreVazao/DGM-MAT/actions/runs/42646429260): SUCCESS.
- [Mission E2E Regression Gate #42646429389](https://github.com/AndreVazao/DGM-MAT/actions/runs/42646429389): IN_PROGRESS.
- [Windows Executable Build #42646429266](https://github.com/AndreVazao/DGM-MAT/actions/runs/42646429266): IN_PROGRESS.

A PR #312 permanece aberta e não integrada.

### 4. PC-Vazao-Anjos — observação adicional

O Desktop Commander voltou a identificar o PC como **Online**. Para respeitar a quota remota restante, foi feita uma única recolha PowerShell read-only, sem iniciar uma missão nem criar sessão autenticada.

Observações:
- Diretório `C:\ProgramasGodMode\DGM-MAT` existe.
- Checkout: `recovery/local-worktree-consolidation-2026-11-09`, HEAD `e06d89402d9e3cd6e36a189daa3f13bee8c4d413`.
- `git diff --stat` vazio; o working tree mantém sete entradas untracked: `bash.exe.stackdump`, backup de `api_server.py`, `installed/`, `update-backups/` e três diretórios `update-staging-*`. Todos foram preservados.
- Comparação atual com `main`: branch divergente, **2 commits exclusivos à frente e 187 atrás**; contém alterações recuperadas de importer, portfolio inventory, MissionEngine e documentação. Não foi feito checkout, rebase, cherry-pick, merge ou limpeza.
- Foram observados quatro processos `DGM-MAT.exe`, em duas árvores pai/filho. A porta `127.0.0.1:8181` está em LISTEN, associada ao PID 4304.
- `GET /health`: HTTP 200, `status=healthy`.
- `GET /runtime/status` sem credencial: HTTP 401, comportamento compatível com rota autenticada. Não foi criada nem reutilizada uma sessão/token para contornar isto; estado autenticado, fila e missões não foram reconsultados neste corte.
- Memória observada: 0,75 GB livres de 2,96 GB totais, coerente com o perfil LOW_MEMORY.
- Executável instalado: 111.825.469 bytes, última escrita observada às 11:51 UTC. Não foi recalculado um hash válido nesta recolha; a verificação de manifesto/hash descrita no corpo principal permanece a evidência anterior, não uma nova verificação.
- Nenhum ficheiro local foi alterado e nenhuma atualização foi aplicada.

### 5. Missão, conversas, providers e Hub

- Não foi criada nem repetida qualquer missão nesta atualização.
- A última missão real confirmada continua a ser `mission_edcdf5ab`, FAILED por ausência de executor genérico no binário/runtime instalado. O sucesso do Mission E2E no GitHub é teste automatizado, não prova de missão concluída no PC.
- O PC ainda não recebeu o build `82a7435`; não existe prova de atualização local.
- Nenhuma conversa foi importada nesta atualização. A cobertura por plataforma mantém-se não comprovada; não se promove metadado de histórico a transcrição integral.
- Codex, Claude Code/FCC e providers web não foram invocados nesta ronda.
- DGM-HUB não foi revalidado nesta recolha. O último relatório continua a indicar ausência de processo/federação, sem nova prova em contrário.
- Observer/Respond não foi alterado.

### 6. Integridade e próximos passos

- Sem merge, commits em `main`, alterações de permissões, aprovação de ações antigas, eliminação de branches, reset, clean ou force-push.
- Correção de código feita apenas na branch/PR #312; relatório atualizado apenas na branch/PR #307.
- Próximo gate: aguardar os dois workflows ainda em execução da #312; depois, rever o diff e manter a PR isolada até aceitação.
- Para o PC: preservar o checkout divergente e os diretórios untracked; preparar eventual atualização numa worktree isolada, nunca por pull/checkout no checkout atual.
- Só depois de instalar com autorização já existente e confirmar hash/backup/rollback deverá ser tentada uma missão tipada read-only com recibo durável.
