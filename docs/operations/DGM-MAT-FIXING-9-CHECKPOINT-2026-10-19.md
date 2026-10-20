# DGM-MAT Fixing 9 — Checkpoint de consolidação

**Data:** 2026-10-20  
**Objetivo:** registar o estado remoto comprovado após a auditoria de providers e a recuperação da ligação missão/fila, mantendo o trabalho apenas pelo GitHub enquanto o PC está indisponível.

## Estado GitHub verificado

- Repositório: `AndreVazao/DGM-MAT`
- `main` após integrar o PR #118: `d305c797520970978c99a170a248a01d8e7f7311`
- Branch de trabalho: `fixing/operational-reality-audit-2026-10-19`
- A branch de auditoria original foi criada a partir de `ab216c67248cac83eb71c2b2bc48c8f27ed657aa`.
- PRs #97, #98, #100, #102, #103, #105, #107, #109, #111, #113, #115, #117 e #118 estão integrados.
- A atualização deste checkpoint é documental e não altera o código de runtime.

## PRs consolidados nesta fase

| PR | Resultado | Commit de integração | Evidência |
|---|---|---|---|
| #94 — incluir regressões de self-repair no phase gate | Integrado por squash | `e2f99b52d6c4e4baf8a506a2255f74f17d8b418d` | Backend Phase Gate concluído com sucesso; todos os jobs e passos reportados como success. |
| #95 — rejeitar objetivos de missão vazios | Integrado por squash | `adaea2fa9338bf18e770d2853c0d5ac59e84ebba` | Backend Phase Gate concluído com sucesso; jobs de API/fila/recuperação, segurança, cockpit, conhecimento e sintaxe reportados como success. |
| #96 — requisito do cockpit conversacional remoto | Integrado por squash | `ab216c67248cac83eb71c2b2bc48c8f27ed657aa` | Documento de arquitetura adicionado. É documentação de requisitos, não prova de conectividade remota implementada. |
| #97 — reclamação atómica de ações aprovadas | Integrado por squash | `365a190860987ca852e713f2cc936d7dfeeb5fab` | Backend Phase Gate: todos os jobs e resumo obrigatório passaram. O teste da fila cobre a rejeição de uma segunda reclamação da mesma ação. |
| #98 — autoevolução fail-closed | Integrado por squash | `6326b064518394d1838c30bb3764787ab8f615f0` | Backend Phase Gate: todos os jobs e resumo obrigatório passaram, incluindo testes de recusa de promoção/política. |
| #100 — reconciliar ações interrompidas em `RUNNING` | Integrado por squash | `ae4c153e7f535170b8de3eab525788a5978f503b` | Backend Phase Gate: todos os jobs e resumo obrigatório passaram. A recuperação fecha a ação interrompida como `FAILED`, preserva auditoria e não a reproduz automaticamente. |
| #102 — rejeitar observações de saúde datadas no futuro | Integrado por squash | `0ee0ff1cb407af1a80d5e76f7d60a3c8eecaa585` | Backend Phase Gate, resumo obrigatório, Snyk e CodeRabbit passaram. Datas mais de 30 segundos no futuro tornam a evidência inválida e a disponibilidade efetiva falsa. |
| #103 — reconciliar checkpoints de missão com a fila durável | Integrado por squash | `68a4ecd5f203c9576b603c5968bf0085f6ef6590` | Backend Phase Gate, resumo obrigatório, Snyk e CodeRabbit passaram. Repara ações em falta sem aprovação; religações existentes não duplicam ações; duplicados ficam sinalizados para revisão. |
| #105 — impedir execução com estado terminal/desatualizado | Integrado por squash | `97148c3249f7df1935470805e4006442b6194a1f` | Backend Phase Gate, resumo obrigatório, Snyk e CodeRabbit passaram. O handler relê o checkpoint durável imediatamente antes da execução e recusa checkpoints ausentes/inválidos ou missões `COMPLETED`, `CANCELLED` ou `FAILED`. Preserva a identidade do objeto em memória para atualizar referências existentes. |
| #107 — manter rejeições da fila coerentes com o estado da missão | Integrado por squash | `08b3dcdd265844698c386df1c2de043366b1c9a2` | Backend Phase Gate, resumo obrigatório, Snyk e CodeRabbit passaram. O endpoint relê o checkpoint antes de cancelar e não sobrescreve missões terminais; no arranque, uma ação durável `REJECTED` cancela a missão pendente, recuperando a janela de falha sem executar trabalho rejeitado. |
| #109 — impedir decomposição de reabrir missões terminais | Integrado por squash | `3785f62199a5925d6d71267bb5b8af905ccb9d0f` | Backend Phase Gate, resumo obrigatório, Snyk e CodeRabbit passaram. `decompose_mission` relê o checkpoint e recusa estados `COMPLETED`, `CANCELLED`, `FAILED` e `WAITING_FOR_USER`, sem criar subtarefas nem reabrir a missão. |
| #111 — atualizar o estado durável antes das transições do scheduler | Integrado por squash | `56fe2e6963afb983d655367ae25c1ceca5dd5444` | Backend Phase Gate, resumo obrigatório, Snyk e CodeRabbit passaram. Antes de timeout/transições, o scheduler atualiza do checkpoint os estados que pode alterar, evitando que uma cópia antiga em memória faça falhar ou reabra uma missão já terminalizada por outro processo. |
| #113 — listar missões a partir dos checkpoints duráveis | Integrado por squash | `210407ba75ddd56bfb5c49c6493eb700af0e1704` | Backend Phase Gate, resumo obrigatório, Snyk e CodeRabbit passaram. `GET /runtime/missions` relê cada checkpoint antes de devolver o estado, evitando mostrar `QUEUED` quando o estado persistido já é terminal. |
| #115 — proteger alterações de handoff humano contra cache obsoleta | Integrado por squash | `096af7422fdc0a05db7818dbc33a10580e4658d2` | Backend Phase Gate, resumo obrigatório, Snyk e CodeRabbit passaram. Pedir ou resolver uma intervenção humana relê o checkpoint durável primeiro; missões terminais não podem receber um novo handoff nem ser retomadas por uma decisão antiga. |

PR #71 — modelo de mensagens e conhecimento baseado em evidências — também foi confirmado como integrado anteriormente, no commit de merge `ad333bdc95f9e930445c2177d6685c6487f07ec1`.

## O que está validado e o que não está

### Validado por evidência remota
- Os PRs #94, #95, #96, #97, #98, #100, #102, #103, #105, #107, #109, #111, #113, #115, #117 e #118 estão fechados e integrados.
- O baseline de código mais recente inclui o PR #118 (`d305c797520970978c99a170a248a01d8e7f7311`).
- Os workflows de PR #94, #95, #97, #98 e #100 terminaram com sucesso; os jobs funcionais e os resumos obrigatórios foram reportados como `success`.
- Os checks Snyk e CodeRabbit reportaram sucesso nos heads de PR #97, #98, #102 e #103.
- Observações de saúde de providers datadas mais de 30 segundos no futuro são marcadas `invalid_timestamp`; `available`/`healthy` efetivos ficam falsos, mantendo os valores originalmente reportados para auditoria.
- No arranque, checkpoints de missão `CREATED`/`QUEUED` são reconciliados com ações `MISSION_EXECUTION`: uma ação em falta é criada sem aprovação, uma ação existente pode ser ligada novamente, e ações duplicadas são sinalizadas sem escolha automática.
- PR #102, PR #103, PR #105, PR #107, PR #109, PR #111, PR #113 e PR #115 passaram todos os jobs do Backend Phase Gate e o resumo obrigatório. A compilação remota passou também nos oito PRs.
- Os métodos de intervenção humana relêem agora o checkpoint antes de criar ou resolver handoffs, preservando missões terminais e decisões ainda não consumidas quando o estado persistido já mudou.
- `GET /runtime/missions` atualiza agora o estado a partir dos ficheiros duráveis antes de apresentar o cockpit/API; checkpoints ausentes ou inválidos não são apresentados como se estivessem atuais.
- O scheduler atualiza os checkpoints das missões `CREATED`, `RUNNING`, `APPROVAL_PENDING` e `WAITING_FOR_USER` antes de executar transições. A regressão simula memória `RUNNING` obsoleta contra um checkpoint durável `COMPLETED`.
- `decompose_mission` agora relê o checkpoint durável antes de criar subtarefas e só permite os estados `CREATED`, `QUEUED`, `APPROVAL_PENDING` e `RUNNING`; estados terminais e `WAITING_FOR_USER` não são reabertos.
- Rejeição da fila e estado da missão são agora reconciliados após falhas entre os dois stores: o checkpoint terminal não é sobrescrito e uma ação `REJECTED` não fica associada a uma missão pendente para sempre.
- A execução de uma ação de missão agora exige reler o checkpoint durável; o handler recusa missão terminal ou checkpoint ausente/inválido antes de entrar no bloco que poderia alterar o estado da missão.
- A fila só permite que o consumidor que ganha a atualização condicional para `RUNNING` execute a ação; a decisão de aprovação continua explícita.
- Na recuperação de missões antigas, ações `MISSION_EXECUTION` que ficaram `RUNNING` após interrupção são marcadas `FAILED` para revisão, sem replay automático.
- O enforcement de política e a promoção de autoevolução agora falham fechados enquanto os respetivos mecanismos reais não estiverem implementados.
- PR #117 protege decisões de aprovação/rejeição com leitura do checkpoint durável e validação de decisão.
- PR #118 protege os finalizadores de sucesso/falha contra checkpoints ausentes/inválidos e estados terminais; todos os jobs do Backend Phase Gate e o resumo obrigatório passaram no head do PR.

| #117 — proteger decisões de aprovação com checkpoint durável | Integrado por squash | `da52127957a3b358dd3640a91ab5aff7396e00af` | Backend Phase Gate e resumo obrigatório passaram; Snyk e CodeRabbit reportaram sucesso. A decisão de aprovação/rejeição relê primeiro o checkpoint associado e recusa missões terminais ou checkpoints indisponíveis; testes cobrem estado terminal, atualização de missão não terminal e decisão inválida. |
| #118 — impedir workers obsoletos de sobrescrever resultados terminais | Integrado por squash | `d305c797520970978c99a170a248a01d8e7f7311` | Backend Phase Gate run 111 (`39374226733`), todos os sete jobs funcionais e o resumo obrigatório passaram; Snyk e CodeRabbit reportaram sucesso. Os finalizadores de sucesso/falha atualizam o checkpoint antes de guardar, aprender ou emitir resultado e recusam checkpoints ausentes/inválidos ou missões já terminais. |

## Ainda não validado
- Sincronização do clone local em `C:\ProgramasGodMode\DGM-MAT` com o SHA remoto atual; o PC local não foi inspecionado nesta operação.
- Estado do histórico Git local/remoto de `C:\AndreOS-Memory`; a sincronização desse histórico tinha ficado pendente devido a autenticação.
- Execução funcional real do runtime no PC, interface cockpit ligada ao backend, persistência após reinício e acesso remoto a partir do Android.
- Execução direta de testes no PC local; não foi realizada nesta sessão. A evidência disponível é CI remoto nos heads dos PRs.

## Próxima fase — auditoria operacional baseada em evidências

1. Continuar a auditar a reconciliação de missões em estados terminais e a consistência dos resultados entre ficheiros, fila e API.
2. Corrigir/auditar o caminho `_handle_running`: quando todas as subtarefas aparecem como `completed`, ainda existe uma transição direta para `COMPLETED` via `_update_status`, fora dos finalizadores protegidos pelo PR #118 e sem resultado de missão agregado. Definir uma solução fail-closed baseada em evidência e testes antes de alterar o comportamento.
3. Continuar a verificar se todos os pontos de entrada e leitura de missão usam os mesmos contratos duráveis, com especial atenção à consistência entre checkpoint, fila, handoffs e resultados.
4. Verificar a integridade de observações de providers, incluindo relógios inválidos, evidência ausente e estados de registo vs. disponibilidade.
5. Confirmar que os resultados de pesquisa, aprendizagem e evolução são persistentes e nunca simulam sucesso.
6. Quando o PC estiver disponível, sincronizar e testar o clone local sem descartar alterações locais nem reescrever o histórico sem inspeção.
7. Preservar `DGM-MAT-FULL-MIRROR` como arquivo imutável e não clonar repositórios satélite para dentro do DGM-MAT.

**Regra de governação:** integridade Git, testes automatizados e funcionamento real são três resultados distintos. Um não substitui os outros.
