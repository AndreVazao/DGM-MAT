# Relatório — Backup-First Executor: crash recovery e validação
Data: 2026-11-07
Branch: `fix/backup-first-staged-create-recovery-2026-11-07`
Base: `c448bc5a28776b395e0dafc1c1fc5aed009af9df`
Código validado: `588b9d8a38f21185240ae9e4726eb784cb2b829b`

## Correções de desenho

### Create
- Ficheiros novos são escritos num staging no diretório da transação/backup.
- Identidade NTFS e hash são persistidos no manifesto `prepared` antes da promoção atómica, relativa a handles fixados e sem overwrite.
- O backup root e o repositório têm de estar no mesmo volume NTFS.
- O volume é consultado pelo handle; o executor falha fechado se não for NTFS ou não anunciar `FILE_PERSISTENT_ACLS`.
- Crash antes da persistência da identidade: o destino do repositório permanece inexistente; o staging não verificado é preservado, nunca eliminado apenas pelo nome.
- Crash após identidade, antes da promoção: recuperação valida identidade e hash do staging.
- Crash após promoção, antes do manifesto `applied`: recuperação valida identidade e hash do destino.
- Se uma criação em estado `prepared` tiver sido alterada por outro escritor, rollback recusa apagar o conteúdo.

### Replace
- O ficheiro existente é aberto com handle exclusivo enquanto a operação está ativa e o backup original é verificado por SHA-256.
- Uma descoberta posterior revelou que, após crash, o handle exclusivo deixa de proteger contra escritores independentes.
- Para um manifesto `prepared`, rollback só restaura se os bytes atuais corresponderem exatamente ao hash original ou ao hash do resultado pretendido.
- Conteúdo parcial de uma escrita interrompida ou conteúdo de um escritor independente (terceiro hash) é preservado; rollback pára e exige recuperação manual.
- A recuperação não promete distinguir escrita parcial de escrita independente após morte do processo; ambos são tratados como conteúdo não verificável.
- Erros inesperados de rollback incluem tipo e mensagem da exceção interna.

## Fault injection e testes

Cobertura nativa Windows:
- Create: interrupção imediatamente após FILE_CREATE, após identidade persistida/antes da promoção, após promoção/antes do manifesto `applied`, falha na gravação do manifesto e conflito com conteúdo mais recente.
- Replace: interrupção após escrita parcial, conteúdo de escritor independente e recuperação quando o conteúdo atual corresponde ao resultado esperado.
- Volume: rejeição de filesystem sem NTFS/ACL persistente e rejeição de backup root noutro volume.
- Handles: reparse points, exclusividade, hard links, renames relativos e proteção da árvore.

## Validação CI — código `588b9d8`

- Windows Guard [42362955666](https://github.com/AndreVazao/DGM-MAT/actions/runs/42362955666): **SUCCESS — 49 passed, 8 skipped**. Os 8 skips são testes POSIX-only, intencionalmente fail-closed.
- Focused PR Validation [42362955616](https://github.com/AndreVazao/DGM-MAT/actions/runs/42362955616): **SUCCESS** — compilação e regressões selecionadas.
- Tentativas intermédias falhadas foram analisadas e corrigidas: expectativa antiga de auto-restauro, fixture manual de manifesto com JSON inválido. Não foram ocultadas.
- Snyk mantém status `error`; não houve scan limpo nem aprovação de segurança.
- CodeRabbit recebeu pedido manual de review, confirmou que o trigger foi executado; ainda não existe revisão substantiva.

## Gates ainda abertos

1. **ACL efetiva do backup root:** o código confirma suporte de ACL persistente no volume, mas ainda não inspeciona se ACLs herdadas/configuradas permitem acesso a outros utilizadores. Não afirmar que o backup está privado.
2. **Revisão independente:** aguardar análise substantiva externa do código atual.
3. **Windows 10 operador:** validar create/replace, backup, rollback, restart/recovery e concorrência no PC real.
4. **Durabilidade do armazenamento:** write-through/FlushFileBuffers não substituem a aceitação no controlador/dispositivo real.
5. **Snyk:** scanner continua indisponível/erro; cobertura de segurança incompleta.

## Política de integração

- PR #276 permanece draft até os gates acima estarem resolvidos.
- PR #220 permanece predecessor histórico aberto/draft; não integrar.
- Nenhuma integração MissionEngine, nenhuma escrita em projetos reais e nenhum auto-merge.
- SAFE por defeito, aprovação explícita, allowlist de paths/repositórios, diff review, checkpoints duráveis e rollback continuam obrigatórios.
- PC do operador está offline até 2026-11-09; não foi feita aceitação local.


## ACL hardening and exact-head validation — 2026-11-07 10:30 UTC

### Effective backup-root ACL

The backup root is now secured and verified through pinned native Windows handles:

- The root DACL is explicitly set with `SetSecurityInfo` and `PROTECTED_DACL_SECURITY_INFORMATION`, preventing broad parent ACL inheritance.
- Grants are limited to the current process user, Local SYSTEM and Built-in Administrators.
- All three principals receive full control inheritable by files and child directories.
- The DACL audit reads owner, DACL and protected-DACL state through `GetSecurityInfo`; it rejects null/absent DACLs, unexpected SIDs, deny/unsupported ACE types, non-inheritable grants, inherit-only/no-propagate ACEs and insufficient masks.
- The transaction directory is independently audited. It is expected to inherit the restricted root DACL and therefore is checked without requiring its own protected-DACL flag.
- `READ_CONTROL` is requested for audit handles. `WRITE_DAC` is requested only on the final backup-root handle, not on drive/ancestor directories.
- Rollback reopens and verifies the protected root and transaction directory before reading manifests or restoring files.

The ACL change is fail-closed. If the current process cannot secure and verify the dedicated backup root, no transaction is written.

### Exact current head

Head: `c9662b8ff73b30024ffd96711b290add44e2bc02`

- Windows Guard [42364111315](https://github.com/AndreVazao/DGM-MAT/actions/runs/42364111315): **SUCCESS — 50 passed, 8 skipped**. The 8 skips are POSIX-only tests, intentionally disabled because POSIX conditional mutation/rollback is not implemented.
- Focused PR Validation [42364111361](https://github.com/AndreVazao/DGM-MAT/actions/runs/42364111361): **SUCCESS** — source compilation and selected regressions.
- The Windows Guard test output reached 100%; all executed tests passed. The 8 skips are expected policy skips.
- Intermediate Windows failures were not suppressed: missing READ_CONTROL, a path-traversal variable leak, fixture argument forwarding, transaction-vs-root DACL semantics and protected-DACL query flags were investigated and corrected.

### Remaining gates

1. Independent substantive security review of this exact head. CodeRabbit trigger acknowledgement is not a review.
2. Windows 10 operator-PC acceptance: create/replace, ACL, backup verification, rollback, process restart/recovery and concurrent writers.
3. Real storage/controller write-through and abrupt-power-loss acceptance.
4. Snyk remains `error`; no clean scan or security approval is claimed.

PR #276 remains draft. PR #220 is closed as superseded, without merge, with branch/history retained. No MissionEngine integration, no real-project mutation and no auto-merge. SAFE default and explicit approval remain mandatory.


## CodeRabbit review follow-up — 2026-11-07

The independent CodeRabbit review was published against head `d348c164a50493a229e95749ea1bbe631bcb9173`. It identified seven security findings, two test-coverage findings and a docstring-coverage warning. This review is substantive; the earlier acknowledgement was not treated as approval.

### Changes committed after that review

- `e8b5e02`: Windows 8.3 alias detection now accepts one or more digits after `~`, covering aliases such as `CREDE~10.JSO`.
- `e8b5e02`: rollback validates the manifest state before entering the missing-destination create cleanup path.
- `e8b5e02`: automatic replacement restoration is gated on whether target mutation actually started, avoiding a rewrite when validation or backup fails before mutation.
- `674da67`: native `UNICODE_STRING` names are rejected before construction if their UTF-16 byte length or maximum length would exceed the 16-bit fields.
- `98b8e8a` and `06d38a9`: Windows-only tests cover missing/mismatched replacement hashes and multi-digit 8.3 aliases.

### Current validation status

Current PR head: `06d38a9015731d7560ce642c26662580b6915cb9`.

The commits above have been pushed to the existing PR branch. The GitHub connector did not yet report workflow runs or combined statuses for this exact head at the time this report update was prepared. Therefore no CI success is claimed for these changes.

### Findings still open — do not merge

1. **Backup root ownership/scope:** prove the configured backup root is a dedicated directory before changing its DACL; reject shared directories and repository parents without altering their existing ACLs.
2. **Created-file security:** ensure staged content receives the destination directory's security policy before atomic promotion, without exposing untrusted staging content.
3. **Mutation/rollback intent durability:** persist and verify rollback intent/outcome so restart during rollback can resume safely.
4. **Native path identity:** validate opened path components against their native long names, not only syntactic 8.3 patterns.
5. **ACL adversarial tests:** exercise broad SID grants, absent/null DACLs, unprotected roots and invalid inheritance flags through the actual ACL auditor.
6. **Docstrings:** CodeRabbit reported 11.32% coverage for the touched complex functions against its 80% threshold; this remains unresolved.
7. **Independent re-review:** request a fresh review of the corrected head after the remaining findings are addressed.

### Operational gates unchanged

- Windows 10 operator-PC acceptance is not available while the operator PC is offline.
- Real storage write-through and abrupt-power-loss acceptance remain outstanding.
- Snyk has not produced a clean result.
- PR remains draft; no merge, no MissionEngine integration, no real-project mutation and no auto-merge.
- POSIX mutation remains deliberately disabled.
