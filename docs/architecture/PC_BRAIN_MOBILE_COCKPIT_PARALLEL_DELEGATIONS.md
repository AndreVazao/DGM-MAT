# DGM-MAT — Cérebro no PC, cockpit móvel e delegações paralelas

Estado: PRINCÍPIO ARQUITETURAL OBRIGATÓRIO
Data: 2026-10-10

## Regra central

**O PC é o cérebro do DGM-MAT. O telefone é apenas um cockpit remoto de comunicação e intervenção humana. O cérebro nunca pode depender do telefone para continuar a operar.**

O processo principal, memória operacional, estado das missões, planeamento, ferramentas, agentes, checkpoints, filas e coordenação residem no PC. O telefone pode desligar, ficar sem rede, perder a sessão ou estar indisponível sem parar o runtime do DGM-MAT.

## O papel do cockpit móvel

O telefone serve para:
- enviar pedidos e instruções ao DGM-MAT;
- conversar e acompanhar o progresso;
- receber mensagens/notificações quando uma decisão ou intervenção humana é necessária;
- responder a perguntas, fornecer contexto e orientar uma investigação;
- realizar manualmente passos legítimos que exigem o titular da conta, como login, CAPTCHA/MFA, consentimento ou introdução de uma password num canal seguro;
- sugerir um site ou tema para pesquisar e pedir ao DGM-MAT que avalie o que encontra.

O telefone não é o runtime, não é a fonte de verdade, não é o coordenador e não é requisito para executar tarefas autónomas. O cockpit deve ser substituível por outro cliente autorizado sem migrar o cérebro para esse cliente.

## Escritório digital e delegações

O DGM-MAT trabalha como uma empresa digital com várias delegações, equipas e missões. O orquestrador do PC mantém o estado global e distribui trabalho por delegações com responsabilidade explícita.

Quando uma delegação encontra um bloqueio que exige o utilizador, deve:
1. guardar checkpoint durável, evidência, próximo passo e limites de repetição;
2. marcar apenas a tarefa/etapa afetada como `WAITING_FOR_USER` ou `BLOCKED`;
3. enviar ao cockpit um pedido específico, com contexto suficiente para uma decisão informada;
4. libertar os recursos que não precisem de ficar presos;
5. continuar, através do orquestrador, todas as tarefas independentes e seguras das outras delegações;
6. aguardar a resposta sem fazer polling agressivo nem criar pedidos duplicados;
7. validar a resposta e verificar o estado real antes de retomar a etapa pendente.

**Uma delegação em espera não significa a empresa inteira em espera.** Só se suspende o trabalho que depende materialmente da intervenção. Outras delegações devem continuar a pesquisar, comparar, analisar, testar, documentar, organizar, identificar ficheiros, classificar conteúdo e executar alterações reversíveis previamente autorizadas. Operações destrutivas, externas, financeiras ou de efeito incerto continuam sujeitas aos respetivos gates e aprovações.

## Scheduler e recursos

O orquestrador deve manter uma fila de trabalho executável e uma fila de dependências humanas. Um pedido pendente é um estado persistente, não um bloqueio síncrono do processo principal. O scheduler deve:
- separar tarefas prontas, em execução, bloqueadas por dependência e concluídas;
- evitar que uma tarefa à espera ocupe desnecessariamente um worker;
- procurar tarefas independentes elegíveis;
- preservar prioridades, limites de recursos e dependências reais;
- evitar ciclos de espera, retries cegos e duplicação de efeitos externos;
- sobreviver ao reinício do PC através de checkpoints e filas persistentes.

Se todas as tarefas disponíveis dependerem da resposta humana, o sistema pode ficar ocioso de forma legítima, mantendo o estado e notificando o utilizador; não deve simular progresso nem inventar trabalho concluído.

## Continuidade e sincronização

A disponibilidade do telefone afeta apenas a comunicação/intervenção, nunca a integridade do cérebro. Se o telefone estiver offline, o pedido fica persistido no PC. Na reconexão, o cliente autentica-se, confirma a sincronização e obtém os pedidos pendentes sem os duplicar. Uma resposta só vale para o pedido, missão, etapa, dispositivo e prazo a que foi emitida.

Após uma intervenção, o DGM-MAT verifica o estado real do browser/serviço. Só retoma o checkpoint se a condição esperada estiver confirmada. Uma ação externa não idempotente com resultado incerto não é repetida automaticamente.

## Segurança e autonomia

- O PC mantém a fonte de verdade; o cockpit recebe apenas a informação necessária e autorizada.
- Credenciais, OTP, tokens e outros segredos não entram em prompts, memória persistente, logs ou bus genérico.
- CAPTCHA/MFA é resolvido manualmente pelo utilizador; nunca é contornado.
- A API permanece loopback-only até autenticação global de HTTP/WebSocket, emparelhamento, scopes, revogação e migração dos clientes estarem concluídos e testados.
- Manter FREE-ONLY / PAID-DENY. Nunca gastar créditos ou dinheiro sem autorização explícita.
- Estabilidade > funcionalidades; evidência > pressupostos; controlo manual > automação destrutiva.

## Critérios de aceitação

1. Desligar o telefone não interrompe uma missão local nem o scheduler do PC.
2. Uma delegação pendente não impede outras delegações de executar trabalho independente.
3. O estado pendente sobrevive ao reinício do PC e não cria pedidos duplicados.
4. A resposta móvel é autenticada, limitada ao pedido e processada no máximo uma vez.
5. Uma etapa só retoma depois de verificar o resultado real.
6. Se não houver trabalho independente, o sistema espera honestamente sem fingir atividade.
7. Logs e notificações não contêm segredos.

## Estado de implementação

Este documento fixa o comportamento-alvo. A independência arquitetural PC/cockpit e a delegação paralela só devem ser declaradas implementadas na medida em que existam testes end-to-end. A fila persistente de intervenção móvel, a autenticação global e o fluxo de pop-up/retoma permanecem pendentes até implementação e validação real.

Relacionado: `HUMAN_IN_THE_LOOP_HANDOFF.md`, `GOVERNED_BROWSER_AUTOMATION.md`.
