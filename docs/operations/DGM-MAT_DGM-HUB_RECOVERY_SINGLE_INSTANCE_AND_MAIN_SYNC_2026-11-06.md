# Recuperação DGM-MAT / DGM-HUB — 2026-11-06

## Estado operacional verificado

- DGM-MAT: uma instância `DGM-MAT.exe --headless`, PID 7552, a servir `127.0.0.1:8181`; `/health` devolveu HTTP 200 e `service=dgm-mat`.
- DGM-HUB: uma instância `python.exe -m uvicorn run_multichat:app`, PID 3840, na porta 8771; `/api/providers` devolveu HTTP 200.
- Porta 8770: sem listener após terminar a instância antiga PID 3124.
- Não foi encontrado um segundo `DGM-MAT.exe` nem outro processo `main.py --headless` no checkup final.
- Processo auxiliar antigo `configure_hub_respond_and_free_autohelp.py` e shells associados deixaram de estar ativos. A tarefa estava bloqueada e tentava reiniciar o runtime, mudar o Hub para 8770 e ativar agentes externos sem confirmação.

## Recuperação e sincronização

- Backups e bundles dos repositórios locais guardados em `C:\\ProgramasGodMode\\DGM-MAT-Recovery\\20261106-141752`.
- DGM-MAT `main` local avançado de forma fast-forward para `origin/main` (`daa1a1e`); branch de trabalho original `feat/github-repository-portfolio-2026-11-06` e respetivas alterações mantidas intactas.
- DGM-HUB `main` avançado 11 commits por fast-forward até `4a13d7c`; três ficheiros `.dgm_truth` eliminados localmente foram copiados para a pasta de recuperação e restaurados antes do avanço.
- Novas worktrees de consolidação: `C:\\ProgramasGodMode\\_worktrees\\dgm-mat-final-consolidation-2026-11-06` e `C:\\AI\\_worktrees\\dgm-hub-final-consolidation-2026-11-06`.
- Nenhuma branch antiga foi apagada; nenhuma alteração local foi descartada; nenhum merge foi forçado.

## Integrações na branch DGM-MAT

- Inventário de portefólio GitHub/local e comparação de branches/remotes.
- Importação de arquivos de conversas exportados pela extensão Chrome, preservando originais e proveniência.
- Integração com pipeline de conversas e contexto para delegação.
- Documentação operacional, testes e scripts de importação/inventário.
- Proteção de arranque do gestor: se já existir processo DGM-MAT validado mas a API ainda não estiver saudável, recusa iniciar uma segunda instância.
- Novo sincronizador de `main` exclusivo DGM-MAT/DGM-HUB: fetch e fast-forward apenas; nunca faz push, force, rebase, reset, merge de branches de trabalho ou eliminação de branches. Divergências e commits locais à frente ficam para revisão.

## Variáveis restauradas

Restauradas a partir do backup criado pelo próprio configurador:

- `DGM_HUB_MULTICHAT_URL=http://127.0.0.1:8771`
- `DGM_AUTONOMY_HELP_ENABLED=0`
- `DGM_AUTONOMY_HELP_EXTERNAL_AGENTS_ENABLED=0`
- `DGM_AUTONOMY_HELP_FREE_CAPACITY_CONFIRMED=0`
- `DGM_AUTONOMY_HELP_PROVIDERS=codex,claude`

A ajuda externa mantém-se desligada até os providers e a capacidade gratuita serem efetivamente verificados.

## Validação e instalação

- Integração inicial: 58 testes direcionados passaram.
- O build final ainda depende de validar os novos guardas/sincronizador, publicar branches/PRs e aguardar CI/Actions.
- O executável atualmente instalado continua a ser o build anterior em `C:\\ProgramasGodMode\\DGM-MAT\\installed\\DGM-MAT.exe`; não foi substituído por um binário não validado.
- A extensão Chrome de arquivo de conversas ainda não foi instalada/autorizada; captura atual é parcial até validar paginação e histórico completo.

## Política operacional daqui em diante

1. Uma instância DGM-MAT (porta 8181) e uma instância DGM-HUB (porta 8771).
2. O launcher canónico do Hub serializa arranques com mutex, deteta processos DGM-MAT já existentes e nunca inicia uma segunda instância perante uma porta ocupada.
3. `main` local acompanha `origin/main` por fast-forward apenas; trabalho novo permanece em branches/PRs.
4. Não apagar branches antigas, não fazer push para `main`, não substituir o executável instalado antes de CI, checksum, backup e teste local.
5. DGM-MAT só pode pedir ajuda a providers que estejam realmente configurados, autenticados e disponíveis; nunca assumir capacidade gratuita.

## Próximos passos

- Executar os testes novos do gestor, sincronizador e launcher; validar sintaxe PowerShell.
- Publicar PRs separados DGM-MAT e DGM-HUB, aguardar Actions e obter artefacto Windows.
- Instalar o artefacto validado, reiniciar uma única instância e confirmar runtime, fila, Hub e logs.
- Registar tarefa periódica de sincronização apenas depois de o script ser integrado e testado.
- Continuar recuperação de conversas e testes reais de Codex/Claude/Grok/Gemini com autorização e prova de resposta.
