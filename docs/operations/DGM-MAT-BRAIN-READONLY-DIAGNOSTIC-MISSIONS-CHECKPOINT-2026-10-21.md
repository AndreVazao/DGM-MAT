# DGM-MAT — Checkpoint do cérebro: missões de diagnóstico read-only

**Data:** 2026-10-21  
**Estado:** implementação em branch isolada; **não validada em runtime/Windows**  
**Branch:** `feat/brain-readonly-diagnostics-missions-2026-10-21`  
**PR:** https://github.com/AndreVazao/DGM-MAT/pull/131

## Objetivo desta fatia

Dar ao cérebro um conjunto adicional de missões pequenas, reais e seguras que percorrem o pipeline existente: classificação determinística → ação durável na fila → aprovação automática apenas por allowlist read-only → executor fixo → resultado persistido → estado terminal da missão.

## Alterações preparadas

- `core/autonomy/mission_intent_router.py`: reconhece pedidos explícitos de resumo do sistema, inventário limitado de motores de IA, estado/modelos do Ollama e disponibilidade/versão do Claude Code.
- `core/autonomy/mission_engine.py`: liga esses intents ao catálogo existente `CommandExecutor`; não aceita comandos arbitrários do texto do utilizador.
- `tests/autonomy/test_read_only_diagnostic_missions.py`: cobre classificação dos quatro intents, rejeição de um pedido genérico de Claude Code, rejeição de uma frase que mistura diagnóstico com instalação, caminho de sucesso com executor falso e resultados de falha/indisponibilidade/timeout sem sucesso falso.
- Nenhum provider é ativado implicitamente. Nenhum comando de escrita, instalação, elevação, arranque/paragem de processos ou shell livre foi adicionado.

## Auditoria de código posterior à implementação

Leitura estática de `main.py`, `core/runtime/runtime.py`, `core/api/api_server.py`, `core/api/runtime_api.py`, `core/runtime/safe_action_queue.py` e `core/operations/command_executor.py` confirmou:

1. O caminho de arranque normal é `main.py → BootstrapEngine.prepare() → Runtime() → Runtime.bootstrap()`.
2. O consumidor durável da fila só é iniciado em `Runtime.bootstrap()`. Iniciar apenas o servidor FastAPI não prova que exista consumidor a processar missões; um arranque alternativo do servidor isolado pode deixar ações aprovadas pendentes.
3. `MissionEngine` regista o handler `MISSION_EXECUTION` na fila ao inicializar. O consumidor reclama uma ação com atualização condicional, invoca o handler e persiste o estado da ação. O resultado da missão é finalizado separadamente pelo motor e deve ser verificado no checkpoint persistido.
4. O endpoint de criação é `POST /runtime/missions`; o `status: success` dessa resposta significa criação aceite, não conclusão. O cliente tem de consultar o estado e resultado duráveis da missão.
5. `CommandExecutor` usa IDs fixos, `shell=False`, timeout e limites de saída. O resultado de Ollama/Claude indisponível não deve ser apresentado como diagnóstico bem-sucedido.
6. Os testes novos chamam diretamente `_handle_queue_execution()` e substituem o executor por um resultado determinístico; não exercitam o consumidor em thread, a API autenticada, nem reinício/recuperação.

Esta leitura é estática. Não foi executado o processo Windows, não foi iniciado um servidor HTTP e não foi observada uma missão real.

## Limites e validação

- **Os testes não foram executados nesta sessão.** Não foi usado GitHub Actions, para preservar minutos.
- A nova cobertura de falhas foi escrita, mas ainda precisa de execução local: indisponibilidade, erro de comando e timeout devem produzir missão terminal FAILED e nunca COMPLETED.
- Os testes com executor falso não provam a disponibilidade de PowerShell/Ollama/Claude Code na máquina real.
- A execução real depende do runtime instalado, de os caminhos autorizados existirem e do comando concreto estar disponível. Falhas devem terminar como falha explícita, nunca como sucesso.
- Esta alteração não resolve o executor genérico para programação arbitrária. Pedidos de alteração de código, instalação, deploy ou ações mutáveis continuam sem executor de missão genérico e não devem ser declarados concluídos.
- A auditoria end-to-end continua aberta: criação HTTP autenticada → fila real → executor real → checkpoint terminal → leitura do resultado → recuperação após reinício.
- A inicialização do consumidor deve ser testada pelo entrypoint suportado; não se deve assumir que executar apenas o módulo FastAPI inicia o runtime completo.

## Próxima sequência obrigatória

1. Executar os testes focados do router, MissionEngine, CommandExecutor, fila durável, segurança API e recuperação no PC.
2. Corrigir regressões sem disparar workflows automáticos.
3. Executar um teste HTTP real em armazenamento temporário, pelo entrypoint/runtime suportado, incluindo sucesso e falha.
4. Provar que a missão e o resultado sobrevivem a reinício e que não há replay silencioso de efeitos incertos.
5. Ligar o cockpit PC ao mesmo contrato persistente apenas depois do gate passar.
6. Manter o escritório digital e o cockpit móvel fora do caminho crítico até o gate backend passar.
