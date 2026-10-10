# DGM-MAT — Human-in-the-Loop, sincronização móvel e retoma de missões

Estado: ESPECIFICADO / AINDA NÃO IMPLEMENTADO END-TO-END
Data: 2026-10-10

## Objetivo

O DGM-MAT deve trabalhar autonomamente dentro das permissões autorizadas e pedir intervenção humana quando um passo exigir o titular da conta: autenticação, desafio CAPTCHA/MFA, consentimento ou confirmação. O pedido deve chegar ao cockpit móvel autenticado. Se o utilizador estiver offline, a missão aguarda com o estado guardado e retoma apenas depois de sincronização estável e verificação do resultado.

## Fluxo obrigatório

1. Guardar um checkpoint durável da missão, passo atual, passos concluídos, resultado esperado e política de retry.
2. Mudar a missão para um estado explícito como `WAITING_FOR_USER`; criar um pedido único com ID, motivo, instruções, risco e validade.
3. Mostrar pop-up no cockpit autenticado. A notificação do sistema operativo deve ser genérica e não incluir dados sensíveis; abre o pedido dentro da sessão protegida.
4. Se o telefone estiver offline ou dessincronizado, manter o pedido pendente, sem duplicar missões, saltar a aprovação ou avançar às cegas.
5. Ao reconectar, validar sessão e dispositivo, confirmar sincronização estável por heartbeat/acknowledgement e reconciliar os IDs do pedido, missão e passo.
6. Para CAPTCHA/MFA, o utilizador resolve manualmente no serviço/sessão legítimos. O sistema não pode contornar, automatizar nem delegar a resolução. Se não for possível interagir com segurança na sessão viva, pedir ao utilizador que conclua o passo no PC e confirme pelo telefone.
7. Aceitar a resposta apenas para o pedido e ação específicos, com validade, autorização, nonce/ID único e proteção contra repetição.
8. Verificar o estado real da página/serviço após a intervenção; só depois retomar do checkpoint ou repetir o passo seguro. Ações externas com efeito incerto não podem ser repetidas automaticamente.
9. Registar transições e evidência sem guardar conteúdo secreto em logs, memória, screenshots, mensagens de agentes ou artefactos.

## Regras de segurança

- O método atual `browser_fill` continua a recusar campos sensíveis. Não enviar valores secretos para o contexto do modelo, message bus genérico, logs ou memória persistente.
- Qualquer futura introdução de dados sensíveis exige um canal dedicado, autenticado, cifrado, temporário, ligado a um único pedido/sessão/campo, sem eco nem persistência e com eliminação imediata após utilização. Preferir que o utilizador introduza diretamente o valor na sessão viva.
- Nunca guardar/exportar cookies ou estado de autenticação do browser. Não mostrar valores sensíveis em notificações.
- O utilizador pode aprovar, rejeitar, cancelar ou pedir mais contexto. A aprovação aplica-se apenas à ação descrita.
- Manter FREE-ONLY / PAID-DENY e não contornar limites, paywalls, termos ou controlos anti-bot.

## Estados e recuperação

Estados previstos: `PENDING`, `NOTIFIED`, `WAITING_FOR_DEVICE`, `WAITING_FOR_USER`, `RESPONSE_RECEIVED`, `VERIFYING`, `RESUMED`, `EXPIRED`, `CANCELLED`, `BLOCKED`.

A fila e o checkpoint têm de ser persistentes antes de notificar. A entrega pode ser repetida tecnicamente, mas o pedido deve ser processado uma única vez. Depois de reinício, o DGM-MAT reconcilia o pedido com o estado real do browser/serviço. Timeout, revogação ou resultado incerto deixam a missão em pausa com uma explicação clara.

## Pré-requisitos antes de expor ao telefone

- Concluir enforcement global de autenticação para HTTP e WebSocket e migrar todos os clientes.
- Implementar emparelhamento de dispositivos, scopes, revogação, transporte seguro, proteção anti-replay e trilho de auditoria.
- Implementar fila durável de pedidos humanos, contrato de API restrito, pop-up móvel e retomada segura.
- Manter a API loopback-only e browser fora do cockpit até a revisão de segurança e os testes passarem.

## Testes de aceitação

- Utilizador offline: pedido/checkpoint persistem sem duplicação.
- Reconexão: pedido correto é retomado; respostas antigas/repetidas são recusadas.
- Cancelamento, rejeição ou expiração não deixam a missão continuar.
- Dados sensíveis nunca aparecem em logs, base de dados, prompt, screenshots ou memória.
- CAPTCHA/MFA exige intervenção manual.
- Retoma só depois de confirmar o resultado real.
- Ações externas não idempotentes com resultado incerto não são repetidas automaticamente.
- Reinício em qualquer transição recupera um estado verdadeiro.

## Maturidade e próximo passo

Esta capacidade está **ESPECIFICADA**, não implementada end-to-end. O pop-up móvel, sincronização estável, canal seguro de intervenção, fila durável e retoma automática ainda não foram verificados. A integração atual de browser permanece interna ao MissionEngine; não está exposta pela API/cockpit.

Próxima sequência: auditar bootstrap de sessão e todos os clientes HTTP/WebSocket; desenhar autenticação global e emparelhamento; implementar fila e máquina de estados com testes; só depois integrar o pop-up móvel e o mecanismo de retoma. Não expor controlo remoto do browser antes dos pré-requisitos.