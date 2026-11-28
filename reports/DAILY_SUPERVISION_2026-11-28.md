# Supervisão diária DGM-MAT — 28/11/2026

**Estado geral: VERIFICAÇÃO INCOMPLETA**  
**Observação GitHub: 28/11/2026, aproximadamente 02:44–02:48 UTC**

## 1. Estado geral

- Repositório: [AndreVazao/DGM-MAT](https://github.com/AndreVazao/DGM-MAT)
- Branch default: `main`.
- HEAD observado: `ef1ba89b29822d3d2d225596c56026f62af053bc`.
- Último commit de código observado na main: `55f3cfa1a4fe8aeeac453b52358b14a78e0190f3`; os commits seguintes até ao HEAD são relatórios diários.
- Branches enumeradas: **69** antes da criação desta branch documental.
- PRs abertas: **1** — [#405](https://github.com/AndreVazao/DGM-MAT/pull/405), Draft.
- Issues abertas: **22**.
- Workflows presentes em `.github/workflows`: **25**.
- Actions runs totais reportados pelo endpoint: **3912**.
- Releases: **0**.

As PRs #399–#404 foram integradas em 27/11 entre 06:14 e 06:15 UTC. A #399 introduziu a primeira fatia de evidência GitHub para dossiers; #400–#404 publicaram relatórios diários. A #405 é agora a única PR aberta.

A issue [#358](https://github.com/AndreVazao/DGM-MAT/issues/358) aparece fechada desde 27/11. A PR #405 continua a estender o dossier, sem reabrir a issue.

## 2. Comportamento local

**Não verificado.** O Desktop Commander reportou o computador principal offline, versão do agente 0.2.52 e último contacto há cerca de 269 horas. Não foram feitas chamadas de execução remota ao PC.

Continuam sem observação local:
- processos, working tree, versão instalada e launcher;
- API local, health/readiness autenticado e sessão;
- fila, missões ativas, scheduler, auto-help e repository intelligence;
- Vault, extensão/importador e cobertura de conversas;
- configuração efetivamente carregada, auditoria e DGM-MAT ↔ DGM-HUB.

A listagem de tabs do browser também não pôde ser usada: o conector exigiu o contexto do browser de origem. Não foram abertas sessões autenticadas nem capturadas conversas.

## 3. Missão funcional

**Não submetida.** Sem observar primeiro a queue e as missões ativas no runtime local, iniciar uma missão poderia interferir com trabalho existente.

- Mission ID: não aplicável.
- Timestamps/progresso/resultado: não disponíveis.
- Estado terminal: não aplicável.

Não foi repetida nenhuma missão bloqueada ou falhada.

## 4. GitHub, branches, PRs e checks

### Main e inventário

- HEAD: `ef1ba89b29822d3d2d225596c56026f62af053bc`.
- Commit de código mais recente na main: `55f3cfa1a4fe8aeeac453b52358b14a78e0190f3`.
- [Windows Build da main #45950578225](https://github.com/AndreVazao/DGM-MAT/actions/runs/45950578225): SUCCESS para o commit de código `55f3cfa`.
- Foram enumerados 69 branches; não se inferiu que branches sem PR possam ser eliminadas.

### PR #405 — catálogo de fontes do Vault

[PR #405 — expose bounded source-file evidence from Vault snapshots](https://github.com/AndreVazao/DGM-MAT/pull/405)

- Estado: aberta, Draft, mergeable.
- Branch: `feat/dossier-bounded-source-catalog-2026-11-27`.
- HEAD observado: `d752a00a2258832a4aa124f5f4f96c440a944ddf`.
- Comparação com main: **7 commits ahead / 0 behind**.
- 2 ficheiros alterados: implementação e testes.
- Catálogo limitado a 200 entradas, derivado apenas do snapshot imutável do Vault; devolve metadados e hashes, nunca conteúdo-fonte.

Foi identificada uma lacuna no filtro de nomes sensíveis: nomes como `credentials-prod.py` não eram excluídos. A mesma PR foi atualizada com exclusão de diretórios sensíveis, nomes/prefixos comuns de credenciais, tokens e segredos e extensões de chaves/keystores; os conjuntos de filtros foram movidos para fora do ciclo de entradas. Foi acrescentado teste de regressão, preservando um ficheiro normal `tokenizer.py`.

Validação:
- [Focused PR Validation #46099364832](https://github.com/AndreVazao/DGM-MAT/actions/runs/46099364832): **FAILURE** no primeiro teste da nova regra, porque o prefixo com hífen não estava coberto.
- A regra foi corrigida.
- [Focused PR Validation #46099519306](https://github.com/AndreVazao/DGM-MAT/actions/runs/46099519306): **SUCCESS**, incluindo compilação e regressões afetadas e Windows installer digest gate.
- [Windows Executable Build #46099519305](https://github.com/AndreVazao/DGM-MAT/actions/runs/46099519305): **SUCCESS** às 02:48:38 UTC.
- Artefacto PR: `DGM-MAT-Windows-3.12-8792637`, 115,432,512 bytes, [run #46099519305](https://github.com/AndreVazao/DGM-MAT/actions/runs/46099519305), digest `sha256:2d86bc75ead522191a5ad23af6113b7f01f48a48042d22e22aceafed3d29b528`, expira em 26/02/2027.
- O artefacto corresponde ao HEAD PR `d752a00a2258832a4aa124f5f4f96c440a944ddf`; não foi descarregado nem instalado.
- A PR permanece Draft; o comentário do CodeRabbit indica que drafts não são revistos automaticamente. Não foi feita revisão independente pelo bot nesta ronda.

### Branches antigas comparadas

- `fix/graceful-runtime-shutdown-windows-update-2026-11-10` / PR #347: 36 commits ahead e 52 behind, com divergência elevada. Os scripts de update/rollback e `runtime_control.py` na main já contêm a implementação e salvaguardas mais recentes. Não foi feito cherry-pick/rebase.
- `test/browser-capture-boundary-claims-all-providers` / PR #385: 4 ahead e 25 behind. A main já contém cobertura mais abrangente de limites de completude para providers. Não foi duplicado trabalho.
- `feat/dossier-live-github-work-items` / PR #379: fechada sem merge e explicitamente substituída pela evolução #382, que está na main. Não foi integrada em duplicado.
- Nenhuma branch foi apagada.

## 5. Segurança e governação

A metadata atual de `main` devolve:
- `protected: false`;
- `protection.enabled: false`;
- `required_status_checks.enforcement_level: off`, sem contexts/checks obrigatórios;
- endpoint de rulesets: lista vazia (`[]`).

O endpoint detalhado `branches/main/protection` devolveu HTTP 403 `Resource not accessible by integration`.

**Risco confirmado pela metadata observável:** a main não apresenta proteção clássica ativa nem rulesets visíveis e não exige status checks no payload consultado. O endpoint detalhado continua inacessível. Foi publicado um comentário com a evidência na [issue #402](https://github.com/AndreVazao/DGM-MAT/issues/402#issuecomment-7232569587). Não foram alteradas regras, permissões, bypass ou settings.

A configuração versionada em `config/autonomous_runtime.json` declara:
- `execution_mode=SAFE`;
- permissões SAFE: `read` e `test`;
- `approval_required=true`;
- `auto_merge_enabled=false`.

O subsistema `core/autonomy/repository_learning.py` reporta `automatic_mutations=false` e `git_operations=read-only`. Isto é evidência do código/configuração versionados, não confirmação da configuração carregada no PC offline.

## 6. Correções e registos publicados

- PR #405 atualizada com filtro mais robusto de metadados sensíveis e teste de regressão; a validação focada ficou verde.
- [Comentário na issue #402](https://github.com/AndreVazao/DGM-MAT/issues/402#issuecomment-7232569587): revalidação da proteção de main.
- [Comentário na issue #244](https://github.com/AndreVazao/DGM-MAT/issues/244#issuecomment-7232579705): lacuna de health-check e teste funcional pós-update/rollback.
- Nenhuma alteração foi feita diretamente na main; sem merge, fecho, eliminação, force-push, rebase/reset ou alteração de credenciais/settings.

## 7. Sincronização e self-update

Artefacto da main:
- [Windows Build #45950578225](https://github.com/AndreVazao/DGM-MAT/actions/runs/45950578225).
- Nome: `DGM-MAT-Windows-3.12-55f3cfa`.
- Tamanho: 115,430,043 bytes.
- Digest reportado pelo GitHub: `sha256:5aa00eca22541d81a489142862f72513f70b6c7d9fe147ee2433c16ee10607a3`.
- Expiração indicada: 25/02/2027.
- É um artefacto de Actions, não uma Release; não foi descarregado nem instalado.

O instalador atual verifica SHA-256 antes de mutações, solicita shutdown gracioso, preserva dados/launcher, verifica ficheiros staged/instalados e grava manifesto. O rollback verifica hashes e restaura executável/launcher.

**Lacuna confirmada:** os scripts não executam restart, health/readiness nem teste funcional pós-instalação ou pós-rollback. A validação profunda em CI não substitui aceitação no PC real. A proposta foi registada na [issue #244](https://github.com/AndreVazao/DGM-MAT/issues/244#issuecomment-7232579705); não alterei scripts de produção sem desenho/revisão.

Nenhuma atualização local foi aplicada ou declarada.

## 8. Conversas recuperadas e cobertura por plataforma

**Capturas novas confirmadas: 0.**

- ChatGPT: não verificado.
- Grok: não verificado.
- Gemini: não verificado.
- Claude: não verificado.
- DeepSeek: não verificado.
- Qwen: não verificado.

Não houve sessão autenticada de browser acessível. Não foram enviados títulos ou corpos privados ao GitHub. DOM parcial, histórico de navegação e metadados não foram contabilizados como transcrição integral.

## 9. Providers, agentes e DGM-HUB

- Codex/FCC: não testado — PC offline.
- Claude Code/FCC: não testado — PC offline.
- Agentes locais: não testados.
- CodeRabbit: comentário automático de Draft não revisto; sem review independente.
- DGM-MAT ↔ DGM-HUB: não verificado.
- Observer/Respond: não verificado; nenhum modo foi alterado.

Não foram usados providers pagos nem alteradas credenciais.

## 10. Riscos e bloqueios

1. Proteção de `main` ausente na metadata observável: risco de push direto e falta de checks obrigatórios.
2. PC offline impede validação de runtime, missão, Vault, providers, conversas e DGM-HUB.
3. Self-update sem health-check/teste funcional pós-instalação e pós-rollback.
4. PR #405 permanece Draft e sem revisão independente do CodeRabbit.

## 11. Próximos passos

1. O proprietário deve configurar proteção efetiva da main e depois pedir revalidação read-only.
2. Aguardar resultado do Windows Build #46099519305; manter #405 Draft até revisão independente.
3. Quando o PC voltar online, inspecionar working tree/processos/queue/approval antes de qualquer missão; depois executar uma única missão read-only.
4. Validar Codex/FCC, Claude Code/FCC, providers de browser e DGM-HUB com respostas reais, sem custos nem bypass.
5. Retomar captura autenticada e paginada de conversas, preservando proveniência, checkpoints, hashes e estados parciais.
6. Desenhar e testar o ciclo pós-update/rollback em ambiente controlado antes de alterar o instalador de produção.

## 12. Classificação final

**VERIFICAÇÃO INCOMPLETA.** GitHub foi revalidado; uma correção pequena e isolada foi feita na PR #405 e tanto a validação focada como a build Windows do HEAD atual passaram. A proteção da main apresenta risco confirmado na metadata observável. A PR continua Draft e sem revisão independente do CodeRabbit. PC/runtime, missão funcional, conversas, providers locais e DGM-HUB continuam não verificados.

**Sem operações destrutivas ou alterações na main.**

## Post-publication checkpoint

- Relatório versionado na branch `reports/daily-supervision-2026-11-28`, criada a partir do HEAD observado da main.
- Commit do relatório atualizado: `b43702fe2adb8bf91edf53913b8257b039e9609c`.
- Branches após publicação: **70**; PRs abertas continuam **1** (#405).
- Não foi aberta uma PR documental adicional, preservando uma única PR de trabalho aberta.
- O ficheiro foi novamente lido através do GitHub após a atualização.
