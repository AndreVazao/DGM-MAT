# DGM-MAT — Implementação inicial da fila persistente de intervenção humana

Data: 2026-10-10
Estado: **IMPLEMENTADO E TESTADO COMO COMPONENTE LOCAL; INTEGRAÇÃO END-TO-END PENDENTE**

## O que foi implementado

Ficheiro: `core/organization/human_intervention_queue.py`

Testes: `tests/organization/test_human_intervention_queue.py`

- SQLite durável, WAL e uma ligação por operação; a fila sobrevive à recriação da instância e ao reinício do processo.
- Pedidos ligados explicitamente a `mission_id` + `step_id`, com identificador UUID, razão, instruções curtas, risco, data de criação e expiração.
- Índice único parcial impede dois pedidos ativos para o mesmo passo da mesma missão.
- Decisões limitadas a `APPROVE`, `REJECT`, `CANCEL` e `NEED_CONTEXT`; a decisão só é aceite para a missão/passo corretos e uma única vez.
- Transições controladas: `WAITING_FOR_USER → RESPONSE_RECEIVED → VERIFYING → RESUMED/CANCELLED/BLOCKED`.
- Expiração impede aprovar pedidos fora de prazo.
- `finalize(..., outcome="RESUMED")` só funciona depois de `VERIFYING`; o chamador deve verificar o estado real antes de finalizar.
- Campos limitados por tamanho, validação de risco e TTL máximo de 24 horas.
- O esquema não tem campos dedicados para segredos nem notas livres na decisão; o método de criação não aceita argumentos arbitrários como password/token. Os chamadores têm de manter `reason`/`instructions` livres de segredos.
- Sem endpoints HTTP/WebSocket, notificações, acesso remoto, execução de browser ou retoma automática nesta fase.

## Testes executados

O teste dedicado da fila passou: **7 testes aprovados**. A bateria focada de regressão passou: **15 testes aprovados** (fila, autenticação local, ciclo de missão e contrato entre processos). `compileall` e `git diff --check` passaram após a revisão final de gestão das ligações SQLite. O método de listagem expira pedidos vencidos antes de os devolver.

## Limites deliberados

Este componente **não está ainda ligado ao MissionEngine**, não muda automaticamente o estado da missão para `WAITING_FOR_USER`, não liberta workers e não retoma execução sozinho. Isto evita fingir integração que ainda não existe. A fila também não deve ser exposta ao cockpit até existir enforcement global de autenticação HTTP/WebSocket, emparelhamento, identidade e scopes de dispositivos, revogação, proteção anti-replay e migração dos clientes.

A resposta `APPROVE` significa apenas que o operador respondeu ao pedido. Não é, por si só, autorização para repetir uma ação externa incerta. A camada de orquestração deve verificar o estado real e aplicar a política de risco/idempotência antes de continuar.

## Próximas fases

1. Executar os testes focados e a suite adequada; rever diff e estado Git.
2. Integrar a fila no MissionEngine com checkpoint e estado de espera persistidos, sem prender workers de tarefas independentes.
3. Adicionar testes de concorrência, reinício em cada transição e deduplicação de notificações.
4. Fechar autenticação global de HTTP e WebSocket e migrar todos os clientes; manter API loopback-only enquanto incompleto.
5. Só depois criar endpoints mínimos autenticados, sincronização do cockpit, confirmação de dispositivo e retoma verificada.
6. Mais tarde implementar descoberta LAN, Tailscale e rendezvous Vercel; Vercel não substitui a conectividade privada.

## Segurança e custo

- FREE-ONLY / PAID-DENY.
- Sem credenciais, OTP, cookies, respostas CAPTCHA ou segredos no banco, prompts, logs ou memória.
- CAPTCHA/MFA continua a ser resolvido manualmente.
- Não abrir portas públicas automaticamente.
- Não modificar `C:\\ProgramasGodMode\\DGM-MAT-FULL-MIRROR`.
