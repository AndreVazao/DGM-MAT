# Relatório — Backup-First Executor e backend Windows
Data: 2026-11-05  
Branch de origem: `fix/backup-first-executor-win32-2026-11-05`  
PR de origem: [#219](https://github.com/AndreVazao/DGM-MAT/pull/219)  
Código validado: `6c1a339753e08b0d73865cd463354e327201b0c7`

## Estado técnico atual

- **Windows é o único backend de mutação ativo.** O executor valida o top-level real do Git com `git rev-parse --show-toplevel` e rejeita pastas aninhadas/falsas.
- A navegação começa na raiz da unidade e percorre cada componente através de handles. Entradas são abertas com `FILE_OPEN_REPARSE_POINT`; junctions e outros reparse points são rejeitados.
- Componentes de caminhos Windows com padrão de alias 8.3 (`~N`) são rejeitados para impedir bypass da lista de caminhos protegidos.
- Handles de diretórios permanecem abertos sem `FILE_SHARE_DELETE`, bloqueando rename/delete concorrente dos diretórios enquanto decorre a operação.
- O backup root é criado componente a componente relativamente a handles fixados; não é usado `Path.mkdir` no caminho Windows.
- Ficheiros de destino existentes são abertos com share mode exclusivo (read sharing apenas) e write-through, mantendo o handle durante leitura, backup, escrita in-place e verificação. A operação falha fechada se existir um handle incompatível.
- Ficheiros novos usam `FILE_CREATE` atómico, write-through e permanecem exclusivos durante a escrita.
- Destinos com hard links são rejeitados, tanto em apply como em rollback, para não modificar caminhos adicionais fora da worktree.
- Backups e manifestos usam handles exclusivos durante escrita/verificação; criação pede `FILE_WRITE_THROUGH` e as escritas fazem `FlushFileBuffers`.
- Antes da mutação é persistido um manifesto `prepared`; depois da escrita e verificação do conteúdo passa a `applied`. O rollback valida schema, `rollback_available`, operação/backup coerentes, identidade da worktree, identidade do ficheiro e hash do conteúdo aplicado. A recuperação de estado `prepared` está coberta por teste.
- POSIX: apply e rollback **falham fechados**. Não existe uma primitiva POSIX portátil de replace/delete condicional capaz de excluir writers que não cooperam com um lock. A implementação POSIX insegura foi removida, em vez de continuar acessível.

## Evidência CI no código indicado

| Workflow | Run | Resultado |
|---|---:|---|
| Backup-First Executor Windows Guard | #70 / 42068106252 | **SUCCESS** |
| Focused PR Validation | #327 / 42068113317 | **SUCCESS** |

O Windows Guard executou os testes nativos em Windows. O Focused PR Validation compilou as fontes Python e executou os regressions selecionados. Ambos passaram no código `6c1a339`.

## Revisão independente e scanner

- CodeRabbit publicou anteriormente 20 comentários acionáveis. Foram tratados os pontos relevantes sobre a corrida do target Windows, hard links, backup-root path-based, manifestos POSIX, identidade da worktree, aliases 8.3, consistência do manifesto e rollback repetido.
- Foi solicitado novo review de segurança ao head atual; a ação foi aceite, mas ainda não foi publicada uma revisão completa que confirme as alterações finais.
- O check Snyk devolve exatamente `You have used your limit of private tests`. O scan não foi executado. Isto não é uma vulnerabilidade reportada nem um scan limpo. Não foi comprada quota e o scanner não foi desativado.

## Gates ainda abertos

1. Obter revisão independente atualizada, sobretudo sobre ACL herdada do backup root e durabilidade de metadados de diretório em caso de perda abrupta de energia.
2. Confirmar que o operador mantém o backup root numa localização com ACL privada; o backend herda a ACL do diretório-pai e não altera ACLs existentes.
3. Resolver a indisponibilidade de quota Snyk ou obter cobertura equivalente sem ocultar o check.
4. Executar aceitação local no Windows 10: criação/replace, backup, rollback, crash-recovery e bloqueio de writers concorrentes.
5. Só depois ligar o executor ao MissionEngine via issue #212, com worktree isolada, plano estruturado, allowlist de validadores, checkpoints e rollback.

## Decisão

**Não integrar ainda.** Os dois workflows passaram no código indicado, mas CI não substitui revisão independente nem ensaio no PC real. O executor continua desligado do MissionEngine, não executa shell arbitrário, não concede autonomia de escrita por si só e não ativa auto-merge. SAFE permanece por defeito, `approval_required=true`, `auto_merge_enabled=false`.
