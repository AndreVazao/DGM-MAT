# Relatório — Backup-First Executor e backend Windows
Data: 2026-11-05  
Branch: `fix/backup-first-executor-win32-2026-11-05`  
PR: [#219](https://github.com/AndreVazao/DGM-MAT/pull/219) — draft, não integrada  
Head validado: `cf1dab9a0a6ba935d299d17f71bb87f874d375a4`

## Estado verificado

- O executor POSIX usa operações relativas a directory descriptors, `O_NOFOLLOW`, validação do root identity, backup externo verificado e rollback condicionado ao hash atual.
- O backend Windows usa `NtCreateFile` com diretórios ancorados por handles, `FILE_OPEN_REPARSE_POINT`, rejeição de reparse points, operações de ficheiros relativas ao handle e operações nativas de rename/delete.
- O caminho Windows do executor executa leitura limitada, precondição SHA-256, criação/verificação do backup externo, persistência de manifesto, verificação pós-escrita e rollback para substituição/criação.
- Testes Windows E2E cobrem substituição + backup + manifesto + rollback e criação + rollback.

## Evidência CI no head acima

| Workflow | Run | Resultado |
|---|---:|---|
| Focused PR Validation | #279 / 42062369810 | SUCCESS |
| Backup-First Executor Windows Guard | #27 / 42062369227 | SUCCESS |

O Windows Guard anterior #25 falhou porque ainda exigia que todas as escritas Windows fossem recusadas. Essa asserção obsoleta foi substituída pelos testes de integração E2E. Os testes específicos POSIX são corretamente ignorados no runner Windows.

## Bloqueios que impedem integração

1. **TOCTOU no target Windows ainda não resolvido.** O executor faz leitura/releitura e depois substitui o nome relativo ao diretório ancorado. Um processo hostil com o mesmo utilizador pode, em teoria, trocar/modificar a entrada entre a última leitura e o rename. O código não reivindica proteção contra esta corrida. É necessária uma estratégia validada de locking do target/atualização via handle ou outro mecanismo com precondição atómica.
2. **Snyk:** o check `security/snyk (andrevazao)` está em estado `error`. Isto não prova vulnerabilidade nem constitui scan limpo; a causa precisa de ser diagnosticada.
3. **Aceitação local:** falta validar o ciclo completo no Windows 10 do utilizador. CI hospedado não substitui esse teste.
4. **MissionEngine:** a integração com o motor de missões ainda não foi feita. Issue #212 permanece aberta.
5. **Autonomia:** este executor não autoriza shell arbitrário, não altera permissões globais, não ativa auto-merge e não promove o modo SAFE.

## Alterações de qualidade feitas nesta revisão

- Removidas definições duplicadas dos helpers Windows no executor.
- Substituído o teste antigo de fail-closed Windows por testes de ciclo real.
- Corrigida a importação JSON usada na validação do manifesto.
- Mantida a PR em draft e atualizada a descrição para explicitar o bloqueio TOCTOU.

## Decisão

**Não integrar ainda.** O CI atual passou, mas a segurança da substituição concorrente no Windows, o erro Snyk e a aceitação local continuam como gates. A integração com MissionEngine só deve avançar depois de a primitiva estar aprovada, mantendo SAFE por defeito, worktree isolada, allowlist de testes e rollback sem sobrescrever trabalho mais recente.
