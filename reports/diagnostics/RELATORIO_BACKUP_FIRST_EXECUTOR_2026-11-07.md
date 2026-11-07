# Relatório — Backup-First Executor: criação staged e recuperação
Data: 2026-11-07
Branch: `fix/backup-first-staged-create-recovery-2026-11-07`
Base: `c448bc5a28776b395e0dafc1c1fc5aed009af9df`

## Correção de desenho

- Ficheiros novos deixam de ser criados diretamente no caminho final do repositório.
- O conteúdo é criado/escrito num ficheiro staging dentro do diretório da transação/backup.
- A identidade NTFS é obtida e persistida no manifesto `prepared` antes da promoção atómica.
- A promoção usa rename relativo ao handle da pasta do repositório, com `replace_existing=False`.
- Crash depois de FILE_CREATE mas antes de persistir identidade: o repositório não recebe ficheiro; o staging não verificado é preservado e nunca eliminado apenas pelo nome.
- Crash depois da identidade persistida: a recuperação valida identidade e hash do staging, ou identidade do destino após promoção, antes de remover/restaurar.
- Replace existente mantém o fluxo de handle exclusivo e backup verificado.

## Limite fail-safe

Pode ficar um artefacto staging no diretório privado de backup se o processo parar entre FILE_CREATE e a persistência do file ID. Não há base segura para o apagar por nome. Este resíduo fica isolado fora da worktree; não é um ficheiro órfão do projeto nem permite sobrescrever dados.

## Validação pendente

- Windows CI com fault injection no intervalo FILE_CREATE → persistência de identidade.
- Testes focused e compilação.
- Aceitação no Windows 10: create/replace/rollback, restart, ACL herdada do backup root e concorrência.
- Revisão independente de ACL/durabilidade.

## Segurança / integração

Sem shell arbitrário, POSIX fail-closed, sem integração MissionEngine, sem auto-merge e sem ativação de mutações. SAFE e `approval_required=true` permanecem obrigatórios.
