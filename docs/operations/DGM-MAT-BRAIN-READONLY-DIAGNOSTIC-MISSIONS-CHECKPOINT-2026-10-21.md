# DGM-MAT — Checkpoint do cérebro: missões de diagnóstico read-only

**Data:** 2026-10-21  
**Estado:** implementação em branch isolada; **não validada em runtime/Windows**  
**Branch:** `feat/brain-readonly-diagnostics-missions-2026-10-21`

## Objetivo desta fatia

Dar ao cérebro um conjunto adicional de missões pequenas, reais e seguras que percorrem o pipeline existente: classificação determinística → ação durável na fila → aprovação automática apenas por allowlist read-only → executor fixo → resultado persistido → estado terminal da missão.

## Alterações preparadas

- `core/autonomy/mission_intent_router.py`: reconhece pedidos explícitos de resumo do sistema, inventário limitado de motores de IA, estado/modelos do Ollama e disponibilidade/versão do Claude Code.
- `core/autonomy/mission_engine.py`: liga esses intents ao catálogo existente `CommandExecutor`; não aceita comandos arbitrários do texto do utilizador.
- `tests/autonomy/test_read_only_diagnostic_missions.py`: adiciona testes de classificação e um teste do caminho de execução/persistência com executor substituído por um resultado determinístico.
- Nenhum provider é ativado implicitamente. Nenhum comando de escrita, instalação, elevação, arranque/paragem de processos ou shell livre foi adicionado.

## Limites e validação

- **Os testes não foram executados nesta sessão.** Não foi usado GitHub Actions, para preservar minutos.
- O teste novo usa um executor falso e prova o contrato de missão a nível de código; não prova a disponibilidade de PowerShell/Ollama/Claude Code na máquina real.
- A execução real depende de o runtime estar instalado, dos caminhos autorizados existirem e do comando concreto estar disponível. Falhas/unavailability devem terminar como falha explícita, nunca como sucesso.
- Esta alteração não resolve o executor genérico para programação arbitrária. Pedidos de alteração de código, instalação, deploy ou ações mutáveis continuam sem executor de missão genérico e não devem ser declarados concluídos.
- A auditoria end-to-end continua aberta: é necessário correr os testes focados localmente, provar criação → aprovação/política → execução real → checkpoint terminal → leitura pelo cockpit → recuperação após reinício, e só depois ligar o cockpit PC.

## Próxima sequência obrigatória

1. Integrar esta branch no checkout local apenas depois de rever o diff.
2. Executar os testes focados do router, MissionEngine, CommandExecutor, fila durável, segurança API e recuperação.
3. Corrigir regressões sem disparar workflows automáticos.
4. Executar um teste HTTP real em armazenamento temporário, incluindo caso de sucesso e falha.
5. Só então construir/ligar o cockpit conversacional PC ao mesmo contrato persistente de missões.
6. Manter o escritório digital e o cockpit móvel fora do caminho crítico até o gate backend passar.
