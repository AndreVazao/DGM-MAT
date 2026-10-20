# DGM-MAT Fixing 9 — Addendum: PR #121 e auditoria seguinte

**Data:** 2026-10-20  
**Base:** `main` após o PR #121, commit `ab66307b760ff2e4443d7e0b744b5d48ed00c2a1`.

## Integração confirmada

- PR #119 — impedir sucesso de missão baseado apenas em flags de subtarefas: integrado no commit `5524143d8d8b0b252d7f798285ecba20be75b233`.
- PR #121 — propagar a recusa de finalização aos consumidores da fila: integrado no commit `ab66307b760ff2e4443d7e0b744b5d48ed00c2a1`.
- Backend Phase Gate run 114 (`39397632675`): os sete jobs funcionais e o resumo obrigatório terminaram com sucesso.
- CodeRabbit e Snyk reportaram sucesso no head do PR #121.

O PR #121 faz com que o handler da fila só devolva sucesso depois de a finalização durável o aceitar. Se a finalização recusar o estado ou o checkpoint, a execução propaga uma exceção e a fila não regista uma conclusão bem-sucedida.

## Auditoria de seguimento

A leitura de `core/autonomy/mission_engine.py` identificou o caminho legado `_handle_approval_pending()` que, quando recebe `last_decision == "reject"`, atualiza diretamente a missão para `FAILED` através de `_update_status`. Este caminho merece revisão antes de alteração: a semântica correta de uma rejeição humana é potencialmente `CANCELLED`, e é necessário confirmar se existe uma ação de fila durável associada e qual é o contrato dos consumidores legados. Não alterar apenas o estado da missão sem reconciliar checkpoint, decisão de aprovação, ação de fila e resultado exposto.

Também foi confirmado que:
- `_handle_running()` já não declara sucesso a partir das flags das subtarefas; sem resultado agregado e executor genérico, usa o finalizador de falha.
- O handler de execução relê o checkpoint durável e recusa missões terminais ou checkpoints indisponíveis antes de executar.
- `SafeActionQueue` marca a ação como concluída quando o handler regressa normalmente e como falhada quando o handler lança uma exceção; por isso, os contratos de retorno dos handlers continuam críticos para a veracidade do estado da fila.

## Próximo passo

Auditar e testar o caminho legado de rejeição de aprovação e todos os respetivos consumidores antes de o alterar. A correção deve:
1. preservar a decisão explícita e o ator;
2. impedir execução de ações rejeitadas;
3. manter missão e ação de fila coerentes, inclusive após reinício;
4. impedir que uma cópia em memória reabra ou substitua um estado terminal;
5. acrescentar testes de regressão para os caminhos legado e atual.

## Limites da evidência

A validação reportada nesta fase é CI remoto do GitHub Actions. Não foram executados testes locais, nem foi verificado o runtime no PC. O checkpoint não afirma que o cockpit esteja operacional ou ligado a um backend em execução.

## Seguimento concluído — PRs #123 e #124 (2026-10-20)

### PR #123 — rejeição humana = cancelamento
- Integrado na `main`: `d8b7e2f7acbf8047a261c4b38532d7110aa51d3f`.
- Backend Phase Gate run 115 (`39399546448`): sete jobs funcionais e resumo obrigatório com sucesso; Snyk e CodeRabbit com sucesso.
- A rejeição explícita passa a `CANCELLED`, não `FAILED`.
- Limite: esta alteração isolada não garantia que a missão e o registo de aprovação convergissem depois de uma interrupção.

### PR #124 — reconciliação da decisão de aprovação
- Integrado na `main`: `6bb0f790f4c390ae40c965c87dd2deddc5ac55cd`.
- Backend Phase Gate run 117 (`39400541300`): sete jobs funcionais e resumo obrigatório com sucesso; Snyk e CodeRabbit com sucesso.
- A fachada de aprovação devolve o resultado real da decisão durável.
- O checkpoint da missão só é atualizado quando a decisão durável é aceite ou quando a mesma decisão já está registada.
- `approve/approved` e `reject/rejected` são normalizados para valores canónicos.
- O scheduler recupera uma rejeição já persistida se o processo parou antes de gravar `last_decision`.
- O identificador da ação de aprovação é preservado nos metadados da missão, incluindo respostas de compatibilidade que usam `id`.

### Evidência e limites
- As verificações referidas são CI remoto no GitHub Actions; Snyk e CodeRabbit também reportaram sucesso.
- Não foram executados testes locais nem foi verificado o runtime no PC.
- Não existe transação atómica entre a base de dados da fila e o ficheiro de checkpoint da missão. A estratégia é persistir primeiro a decisão autoritativa e reconciliar o checkpoint a partir dela após reinício.
- Próximo foco técnico: auditar a recuperação completa da ação `MISSION_EXECUTION` e o ciclo de vida `APPROVED → RUNNING → terminal`, incluindo interrupções e garantia de não repetição automática de efeitos externos.

## Seguimento — missão de arquitetura, telemetria do escritório e APK (2026-10-20)

### PR #126 — primeira capacidade real além da listagem de repositórios
- Integrado na `main`: `b1bf9899de37791e91b69087498e3bfa6f2a3ddd`.
- Validação direcionada: run `39410818568`, sucesso; Snyk e CodeRabbit também passaram.
- A missão `architecture_summary` resume secções delimitadas do README e da Constituição arquitetural local, com intervalos de linhas, limites de tamanho e falha segura quando falta evidência.
- Não executa shell, não chama serviços externos e não altera documentos. Só intenções explicitamente registadas como leitura podem autoaprovar-se; pedidos mutativos continuam bloqueados.

### PR #127 — telemetria real para o escritório virtual
- Integrado na `main`: `fad039e198abe26dce86c25e27d0ae56c964c129`.
- Validação direcionada: run `39411666593`, sucesso; Snyk e CodeRabbit também passaram.
- Novo endpoint `GET /runtime/office/telemetry`, autenticado para clientes locais.
- Lê checkpoints persistidos e estados duráveis da fila; expõe contagens e eventos recentes limitados, sem goals, conteúdo de conversas ou payloads completos.
- Investigação, memória e atividade por agente continuam `unknown` até existirem fontes de eventos reais.

### Escritório digital — cockpit
- PR #3 integrado: primeira vista visual responsiva com a referência do CEO e estados sem telemetria explícitos.
- PR #4 integrado: liga os indicadores de missões, decisões pendentes, ações em execução e worker ao endpoint de telemetria; consulta apenas enquanto a vista do escritório está aberta, com atualização de 30 segundos.
- Teste de contrato do cockpit passou no run `39411786744`. O cockpit continua a ser apresentação; não é autoridade de execução.

### APK Android
- Build bem-sucedido no run [39409853967](https://github.com/AndreVazao/DGM-MAT-Mobile/actions/runs/39409853967), commit `75adce8549141e052da76ee07f4979748ee10c5c`.
- Artefacto: `DGM-MAT-Mobile-Android-APK`, ID `12259215772`, tamanho 3 698 457 bytes (cerca de 3,53 MiB), disponível até 2026-11-19. O link de execução permite descarregar o ZIP do artefacto com a conta GitHub autorizada.
- SHA-256 do artefacto ZIP: `ee075ac10ddd967aeb57b053b2f1563e03453d1fffe0f98a4a83d0002e7b50be`.
- O workflow de build foi desativado automaticamente depois do upload bem-sucedido. Não reativar para builds repetidos sem pedido explícito.
- Falta instalar o APK num dispositivo Android e verificar pairing, autenticação e conectividade real ao PC. Não há evidência de teste no dispositivo ou no PC.

### Próximas verificações, sem repetir suites históricas
1. Validar a ligação da vista do escritório ao backend real quando o cockpit e o DGM-MAT estiverem publicados/instalados no PC.
2. Instalar o APK num Android e testar pairing/autenticação; manter o workflow desativado salvo se for necessário corrigir e reconstruir.
3. Continuar a implementar executores específicos com contratos e testes próprios; não voltar a tratar um plano de subtarefas como prova de execução.

### PR #128 — estado real do repositório
- Integrado na `main`: `b56ad0845c46c5d69e8161fc7e9d359c5244af08`.
- Validação direcionada: run `39412244158`, sucesso; Snyk e CodeRabbit também passaram.
- A missão `repository_status` executa apenas `git -C <raiz-DGM-MAT> status --short --branch`, com `shell=False`, timeout de cinco segundos e sem operações de rede ou escrita.
- Se o Git devolver erro, a missão falha; nunca apresenta um relatório vazio como sucesso.

### PR #129 — pesquisa de evidência local
- Integrado na `main`: `b1c807cb34b2673ec3c13b009f880c2460314a8b`.
- Validação direcionada: run `39412590933`, sucesso; Snyk e CodeRabbit também passaram.
- A missão `local_research` reutiliza o pesquisador local com limites de tempo, ficheiros e resultados, redacção de segredos e referências a ficheiros/linhas.
- Não usa web, shell, rede nem escrita. Se não encontrar evidência, falha sem declarar conclusão.
- A intenção só é autoaprovada quando identifica explicitamente um contexto local (repo, código, documentação, workspace ou DGM-MAT). Pesquisa web e pedidos que misturam pesquisa com alterações continuam bloqueados.

### Capacidades read-only atualmente registadas
1. `list_repositories` — listagem local de repositórios.
2. `architecture_summary` — resumo com proveniência de documentos arquiteturais fixos.
3. `repository_status` — estado Git do próprio DGM-MAT.
4. `local_research` — pesquisa limitada em código/documentação local com evidência.

Estas quatro capacidades não equivalem a um executor genérico. A `HumanInterventionQueue` e os métodos locais `request_human_intervention()/resolve_human_intervention()` já existem, com checkpoint durável `WAITING_FOR_USER`, decisões de uso único e verificação antes de retomar. Ainda não estão expostos por HTTP/WebSocket. Próximo passo: auditar a integração e a recuperação após reinício e ligar uma vista local autenticada do PC cockpit aos pedidos pendentes e respostas limitadas. Não expor esta fila ao APK até existirem emparelhamento de dispositivos, scopes, revogação e proteção anti-replay. Depois, continuar com executores específicos e testes próprios.

