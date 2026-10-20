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
