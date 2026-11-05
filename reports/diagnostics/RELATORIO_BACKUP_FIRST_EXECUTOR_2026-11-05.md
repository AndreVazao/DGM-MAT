# Relatório — Backup-First Executor e backend Windows
Data: 2026-11-05  
Branch: `fix/backup-first-executor-win32-2026-11-05`  
PR: [#219](https://github.com/AndreVazao/DGM-MAT/pull/219) — draft, não integrada  
Último head com CI verificado: `cf1ac4b9633be0cd467093fae27a9fe9e80cf430`

## Estado técnico verificado

- POSIX: operações relativas a directory descriptors, `O_NOFOLLOW`, identidade do root, backup externo verificado e rollback condicionado ao hash atual.
- Windows: navegação relativa a handles, `FILE_OPEN_REPARSE_POINT`, rejeição de reparse points e directory handles que bloqueiam renomeação concorrente.
- Windows target existente: o executor abre o ficheiro com handle exclusivo (share mode apenas leitura), mantém-no aberto durante backup e alteração e escreve in-place através do handle. Isto bloqueia novos handles com acesso de escrita/delete durante a operação; se houver um handle incompatível já aberto, a operação falha fechada.
- Windows target novo: criação nativa `FILE_CREATE` é atómica; o handle criado fica exclusivo durante a escrita.
- Antes da alteração é criado e verificado o backup externo e é persistido um manifesto em estado `prepared`. Depois da escrita, os bytes são relidos/verificados e o manifesto passa a `applied`.
- Rollback verifica a identidade do ficheiro (volume serial + file index). Para estado `applied`, também exige o hash resultante esperado; para estado `prepared`, pode recuperar uma escrita interrompida, desde que a identidade seja a mesma.
- Testes Windows incluem bloqueio de escrita/rename concorrente, backup/replace/manifest/rollback, criação/rollback, recuperação de escrita parcial e recusa de rollback sobre conteúdo/identidade substituídos.

## Evidência CI

| Workflow | Run | Resultado |
|---|---:|---|
| Focused PR Validation | #290 / 42064020938 | SUCCESS |
| Backup-First Executor Windows Guard | #38 / 42064020752 | SUCCESS |

O Windows Guard executou os testes nativos; 7 testes POSIX-only foram corretamente ignorados no runner Windows. O Focused PR Validation compilou e executou os regressions selecionados com sucesso.

## Bloqueios que impedem integração

1. **Revisão de segurança independente:** solicitada ao CodeRabbit para a semântica de share modes, NT APIs, recuperação de manifesto, identidade do target, lifecycle dos handles e corridas residuais. A revisão ainda não foi concluída.
2. **Snyk:** o status GitHub do check `security/snyk (andrevazao)` foi diagnosticado como `You have used your limit of private tests`. A análise Snyk não foi executada por limite de quota; não há vulnerabilidade reportada, mas também não há scan limpo. Não foi comprada quota nem desativado o scanner.
3. **Aceitação local:** falta validar o ciclo completo no Windows 10 do utilizador. CI hospedado não substitui esse teste.
4. **MissionEngine:** integração com o motor de missões ainda não feita. Issue #212 permanece aberta.

## Alterações de qualidade

- Removidas definições duplicadas dos helpers Windows.
- Removidos helpers Windows obsoletos que faziam operações sem manter o target bloqueado.
- Substituído o teste antigo de fail-closed Windows por testes de integração E2E.
- Corrigido o teste de recuperação do manifesto preparado.
- Cleanup de handles no rollback garante que o handle do diretório raiz não é fechado duas vezes.
- SAFE continua por defeito; auto-merge continua desativado; não há execução de shell arbitrário.

## Decisão

**Ainda não integrar.** Os workflows atuais passaram e a corrida anterior de substituição do target foi redesenhada usando handles exclusivos e escrita in-place. A integração depende agora da revisão de segurança independente, diagnóstico do erro Snyk e aceitação local Windows 10. Só depois ligar a primitiva ao MissionEngine, com worktree isolada, plano estruturado, allowlist de validadores, checkpoints e rollback.
