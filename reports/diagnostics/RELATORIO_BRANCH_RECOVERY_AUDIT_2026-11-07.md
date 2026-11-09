# DGM-MAT — auditoria de recuperação de branches antigas
**Data:** 2026-11-07  
**Repositório:** `AndreVazao/DGM-MAT`  
**Main auditado:** `c009c512593f16ee1bf085012fa700e4352433fe`  
**Âmbito:** 43 branches não-main existentes no momento da auditoria. Nenhuma branch foi apagada, alterada ou reescrita.

## Resultado executivo

- Foram encontradas **43 branches antigas** além de `main`.
- A pesquisa de PRs abertos devolveu **zero PRs abertos**. Os merges que o operador efetuou já estão refletidos no estado atual do repositório.
- Todas as 43 branches foram comparadas com `main`. Os valores ahead/behind abaixo representam a divergência Git desde o merge-base; **não representam, por si só, commits de código ainda em falta**, porque vários PRs foram integrados por squash e as branches conservaram históricos antigos.
- Foram comparados blobs de ficheiros representativos com `main`; em vários casos os hashes são exatamente iguais. Noutros, o código atual de `main` contém endurecimentos posteriores e substitui a versão antiga.
- **Não foi identificado um conjunto de código antigo que deva ser integrado diretamente em `main` sem nova revisão.** Há três peças históricas que merecem ser preservadas como referência até a limpeza final, descritas abaixo.

## Peças a preservar como referência antes de apagar

### 1. POSIX dirfd do executor — referência técnica, não integrar
Branch: `feat/mission-engine-governed-execution-2026-11-05`  
Head: `cf1ac4b9633be0cd467093fae27a9fe9e80cf430`

Contém uma implementação experimental de mutações POSIX ancoradas em descritores de diretório (`O_DIRECTORY | O_NOFOLLOW`), leitura relativa ao diretório fixado e operações de backup/rollback. A versão atual em `main` escolhe deliberadamente **fail-closed em POSIX**, porque não foi demonstrada uma primitiva portátil de replace/delete condicional que exclua escritores concorrentes. A implementação antiga não deve ser reintroduzida por cópia ou cherry-pick. Preservar apenas como material de investigação caso se venha a desenhar e testar uma solução POSIX independente.

### 2. Free-tier browser consultation — protótipo parcial, provavelmente redundante
Branch: `feat/free-tier-browser-ai-consult-2026-11-05`  
Head: `6aab53c3cdade11f2c77dfa1ff86bd7efd01844e`

Contém `BrowserConsultStore` SQLite, API de fila, auditoria de comandos, redação de segredos, confirmação explícita de capacidade free-tier, bloqueio de rate-limit/login e recuperação fail-closed após restart. É trabalho real e não foi encontrado um PR correspondente. Contudo:
- limita-se a ChatGPT, Gemini e Grok;
- não inclui um transporte/integração completo da extensão no próprio branch;
- a mainline já tem o operador de browser com aprovação do servidor e os cinco fornecedores pretendidos.
Decisão: **não integrar agora**; conservar o desenho e os testes como referência. Só recuperar se surgir uma necessidade funcional concreta que a fila atual não cubra.

### 3. CDP attachment para Chrome autenticado — explicitamente substituído
Branch: `feat/authenticated-conversation-capture-policy-2026-11-05`  
Head: `9569176620d82eafb6c8804e8c70dc60f9888d38`

O PR #209 foi fechado sem merge e declara expressamente que o protótipo standalone CDP foi substituído pelo caminho da extensão Chrome/API local no PR #210. A classe `AuthenticatedChromeSession` lê texto visível através de CDP loopback, mas não faz ingestão para o arquivo e não cobre DeepSeek/Qwen. **Não recuperar**: manter apenas a decisão arquitetural registada no PR #209.

## Trabalho já representado na mainline / versões antigas ultrapassadas

- **Chrome capture e browser operator:** branches de captura, sessão, fila, DeepSeek/Qwen, histórico virtualizado e direct-send são versões anteriores do caminho atual. A mainline tem versões posteriores e gates de aprovação. O PR #210 integrou a arquitetura da extensão; os PRs #268, #271 e #273 reforçaram os testes e removeram o envio direto não aprovado.
- **Vault e árvores de projeto:** `feat/persistent-vault-catalog-project-tree-2026-11-06` e `feat/persistent-vault-catalog-v2` têm o mesmo blob de `core/vault/catalog.py` que a mainline.
- **Workers e dispatch:** os blobs de `python_source_analyst_worker.py`, `repository_cartographer_worker.py`, `delegation.py`, `configured_readonly_workers.py` e `task_dispatcher.py` foram confirmados iguais aos da mainline em branches representativas. Outras versões antigas são subconjuntos da implementação atual, que acrescenta correlação `task_id`, resultados duráveis e validação adicional.
- **Task store:** a versão antiga de `task_manager.py` é subconjunto da atual; a mainline acrescenta conclusão idempotente com resultado e ligação à mensagem persistida.
- **Programação/readiness:** a branch de auditoria de 22-10 já teve o trabalho integrado por PR #148 numa branch sincronizada. O ficheiro `core/development/task_store.py` é idêntico ao da mainline. PR #152 foi fechado sem merge.
- **Telescope:** a branch antiga chama `sessions get` para obter detalhes; a mainline limita a consulta ao endpoint de listagem e mantém o contrato metadata-only. Não recuperar a chamada de detalhe.
- **CLI Windows:** a branch antiga `fix/local-cli-powershell-wrapper-probe` contém execução de wrappers através de `cmd.exe /c`; a mainline posterior rejeita wrappers `.cmd/.bat` e não os lança. Não recuperar.
- **Frozen runtime:** a branch antiga procura código-fonte em `_MEIPASS`; a mainline usa imports dos módulos empacotados e falha explicitamente quando a dependência não está incluída. Não recuperar a procura por source tree.
- **Executor backup-first:** PRs #207, #214, #217, #219 e #220 foram fechados sem merge ou substituídos durante a evolução. O PR #276 integrou a versão mais recente, mas mantém gates explícitos: não ligar ao MissionEngine antes de resolver os blockers de ACL, staging/ACL de destino, intenção persistente de rollback, testes adversariais e aceitação física Windows/storage. As branches antigas do executor não são uma fonte segura para merge.

## Inventário das 43 branches

`ahead` e `behind` são relativos ao merge-base com a mainline atual. O SHA é o head exato observado na auditoria e permite localizar o snapshot mesmo depois da eliminação da referência.

| Branch | Head SHA | Ahead | Behind |
|---|---|---:|---:|
| `audit/programming-department-readiness-2026-10-22` | `4d02b81392f0611feefe39dadabf5d383548823c` | 48 | 123 |
| `docs/local-agents-adaptive-context-2026-11-06` | `e2ba0610520ed3d97e371cf826a90541ff389359` | 2 | 30 |
| `docs/organization-task-persistence-gate-2026-11-07` | `3e38ef43e1a726d75a3be3853b922046b3a2eb06` | 1 | 21 |
| `feat/authenticated-conversation-capture-policy-2026-11-05` | `9569176620d82eafb6c8804e8c70dc60f9888d38` | 13 | 69 |
| `feat/backup-first-patch-executor-2026-11-05` | `7510b61d45f909f19a498efeb66c888db05c30d1` | 5 | 69 |
| `feat/bounded-worktree-execution-2026-11-04` | `84ed5d4c1ac8872e68d49877846d4956e47132a1` | 4 | 73 |
| `feat/browser-mission-queue-v1` | `d0f90b297b43990f95a896588c622480e2d6b77b` | 92 | 45 |
| `feat/browser-operator-approval-gated-v2` | `0d21e93042401ee7fafed1c6c5b858b1a7f8f030` | 39 | 18 |
| `feat/browser-recovery-deepseek-qwen-2026-11-06` | `9d116995cb88d692078206c8fc755262898b2eee` | 10 | 32 |
| `feat/browser-session-operator-v1-history` | `61f7b20bcbb6e02a7593e8d15135817df595663d` | 9 | 45 |
| `feat/browser-session-operator-v1` | `3bcb3484db0790e2191c0edd49bde65eec460359` | 6 | 32 |
| `feat/chatgpt-recovery-import-api-2026-11-03` | `aff572062ca784dbfc8ba24b65e850992b537707` | 6 | 107 |
| `feat/chrome-extension-conversation-capture-2026-11-05` | `f034f1bbb5ee3bc0bb8b97cfd53ecd77494d2c02` | 130 | 69 |
| `feat/durable-organization-task-store-v1` | `aef31e46aed08a6f2bb242243a46271936169621` | 4 | 21 |
| `feat/explicit-readonly-worker-bootstrap-v1` | `728f12ddd8b33dd82f8eb57623a56f1a4b9227ad` | 6 | 25 |
| `feat/external-agent-readiness-probe-2026-11-03` | `d7a40958e9b722bab452c8eaec4c40bf863ff385` | 17 | 107 |
| `feat/free-tier-browser-ai-consult-2026-11-05` | `6aab53c3cdade11f2c77dfa1ff86bd7efd01844e` | 9 | 68 |
| `feat/internal-repository-cartographer-worker-v1` | `414ac4c366033ea0ee120971037bd39566cee26b` | 18 | 30 |
| `feat/mission-engine-durable-organization-tasks` | `e4e37f9455dd221e86e47c6a0693897ece1f92c0` | 3 | 20 |
| `feat/mission-engine-governed-execution-2026-11-05` | `cf1ac4b9633be0cd467093fae27a9fe9e80cf430` | 47 | 60 |
| `feat/persistent-vault-catalog-project-tree-2026-11-06` | `96ac7e22f89674043702e477c13b15d2628e319e` | 90 | 32 |
| `feat/persistent-vault-catalog-v2` | `a12758970da3dd7fe6f2702b1e24988b89e7946b` | 27 | 17 |
| `feat/python-source-analyst-mainline-v1` | `c6db599205aabac97db77b57922593787526f3e0` | 3 | 26 |
| `feat/python-source-analyst-worker-v1` | `5855b260de0d3ab6fffdc319ae564ffbba7a6f5f` | 15 | 30 |
| `feat/python-test-inventory-worker-v1` | `72821080387e3c2e4c834604504dca6ebef7481b` | 8 | 24 |
| `feat/read-only-worker-task-dispatch-v1` | `0bef0212bf8c9c854fb36bf1ed36d7b612482bd6` | 7 | 23 |
| `feat/telescope-metadata-only-2026-11-03` | `30f5b338c4d82cb3e1d41ed77c73305838a5fe44` | 2 | 104 |
| `feat/typed-readonly-task-dispatch-v1` | `8d6cb91d1db9cde414b2c1f10c3b899ece3d5206` | 12 | 19 |
| `feat/worker-office-readiness-reconciliation-v1` | `1a6507810c0e1338266f84a6a9e9253fd888326a` | 6 | 22 |
| `fix/backup-first-executor-dirfd-2026-11-05` | `cec8ca47d082bb209268f7be97da8ea598ad42ba` | 23 | 60 |
| `fix/backup-first-executor-rebased-2026-11-05` | `6a6afe78594464521e1474e882ae99170e6c3a3a` | 11 | 67 |
| `fix/backup-first-executor-win32-2026-11-05` | `6c1a339753e08b0d73865cd463354e327201b0c7` | 78 | 60 |
| `fix/backup-first-executor-win32-clean-2026-11-05` | `7963aee08b9e1db44274000e7f4b44542f09c2e3` | 4 | 42 |
| `fix/browser-direct-send-approval-bypass` | `d171e466e6b940e753f1dab5e41a87eae96902eb` | 6 | 12 |
| `fix/conversation-completeness-evidence-2026-11-05` | `0eae1abe8561ab1bcd60e6bf30e1b9b75f2e2aa8` | 10 | 67 |
| `fix/delegation-requires-registered-worker-2026-11-06` | `f0a12a11439eae3dec7fec0f2d51761971635a4c` | 13 | 30 |
| `fix/frozen-external-runtime-dependencies-2026-11-04` | `c4afabda88eb46381a2a84fca371d786d3a02c06` | 1 | 82 |
| `fix/keep-autonomous-patching-no-auto-merge-2026-11-05` | `b4866bcfc8118f23b16684561d4e8637fc995ca3` | 1 | 68 |
| `fix/local-cli-powershell-wrapper-probe` | `b55ac271ef5311bef63394f29fd2f37f6e4a494f` | 4 | 12 |
| `fix/python-source-analyst-hard-bounds-v1` | `2b2a3f5a6cbc4cf37a2e0cd05c056a56c39b33b7` | 4 | 25 |
| `test/browser-virtualized-history-clean-2026-11-05` | `d9bae549a49bdf7dd4f5cc4c4f894e49a492d6f9` | 1 | 45 |
| `test/browser-virtualized-history-fixtures-2026-11-05` | `98931fa1f3f3fd4c33b8c3f08759848fb1f928a1` | 26 | 45 |
| `test/browser-virtualized-history-main-sync-2026-11-06` | `8bf186bc8de11475c679ae06390768c3902a40bb` | 1 | 32 |

## Procedimento de limpeza recomendado

1. Preservar este relatório depois do merge.
2. Antes da eliminação, manter temporariamente apenas os três snapshots de referência acima, ou criar tags/refs de arquivo com os respetivos SHAs.
3. Não fazer cherry-pick dos protótipos POSIX, CDP, free-tier consult ou dos executores antigos.
4. Depois de confirmada a preservação do relatório e de qualquer snapshot que se queira guardar, as restantes branches antigas podem ser apagadas sem perder o código que já está na mainline.
5. A branch de executor backup-first final integrada por #276 continua sujeita aos blockers documentados no próprio PR; o merge não equivale a autorização para ativar mutações autónomas.

**Limite desta auditoria:** foram comparadas as referências Git e ficheiros representativos, não foi executada uma suite de testes completa em cada snapshot antigo. A decisão de não recuperar código antigo é baseada na evolução observada da mainline, nos PRs fechados/merged e nos contratos de segurança atuais.
