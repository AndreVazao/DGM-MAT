# Recuperação de documentação local — 2026-11-04

**Origem:** checkout local `C:\ProgramasGodMode\DGM-MAT`, branch `diagnostic/e2e-audit-2026-10-28`.  
**Destino:** branch de recuperação baseada na `main` atual.  
**Natureza:** arquivo histórico; não representa, por si só, funcionalidades implementadas ou estado atual do runtime.

## Documentação arquitetural recuperada

Os seis documentos em `docs/architecture/archive/2026-10/` preservam decisões, investigação e propostas produzidas entre 11 e 13 de outubro de 2026:

- `ADAPTIVE_RUNTIME_CAPABILITY_AND_SHARED_AGENTS_2026-10-11.md` — perfil de capacidades do host e agentes partilhados.
- `DGM-MAT-ADAPTIVE-RUNTIME-AND-DISTRIBUTED-WORKERS-2026-10-12.md` — adaptação ao hardware, renderização progressiva e workers.
- `DGM-MAT-ADAPTIVE-TOOLS-SKILLS-AND-AUTONOMY-ROADMAP-2026-10-13.md` — matriz de ferramentas, competências e evolução da autonomia.
- `DGM-MAT-DEPARTMENT-SOVEREIGNTY-AND-AGENT-GOVERNANCE-2026-10-13.md` — soberania dos departamentos, delegação e prevenção de ciclos.
- `DGM-MAT-EXTERNAL-AGENTS-AND-SELF-IMPROVEMENT-RESEARCH-2026-10-12.md` — investigação sobre agentes externos e melhoria autónoma.
- `DGM-MAT-VIRTUAL-OFFICE-TECHNOLOGY-RESEARCH-2026-10-12.md` — pesquisa sobre escritórios virtuais e arquitetura substituível.

As propostas continuam úteis como contexto histórico, mas devem ser confrontadas com a arquitetura e as decisões atuais antes de qualquer implementação.

## Relatórios históricos recuperados

Os três relatórios em `reports/archive/2026-10/` preservam evidências e avaliações de 23, 24 e 26 de outubro:

- `RELATORIO_ANALISE_DGM-MAT_EXE_APK.md` — análise de distribuição Windows e Android.
- `RELATORIO_AVALIACAO_BLOQUEIO_LISTA_REPOSITORIOS.md` — diagnóstico do bloqueio da missão `list_repositories`.
- `RELATORIO_FINAL.md` — resumo de missão e estado de desenvolvimento em 23 de outubro.

**Privacidade:** o campo `session_id` do relatório de avaliação foi redigido como `[REDACTED]` antes de integrar o arquivo.

## Material deliberadamente não recuperado

- `installed/`: cópia de distribuição/runtime, executáveis, configurações e estado gerado; não é fonte de código e não deve ser versionada como implementação.
- `bash.exe.stackdump`: artefacto de crash local sem valor de código.
- `core/api/api_server.py.bak-rendezvous-pause-20261011`: backup de código antigo, mantido apenas no PC para eventual recuperação.
- Alterações locais de `core/autonomy/mission_engine.py`: removiam capacidades já existentes na `main` atual (incluindo sincronização governada, paginação e resolução correta da raiz); foram consideradas regressivas e não copiadas.
- Alteração local de `reports/diagnostics/RELATORIO_E2E_DGM_MAT_2026-10-28.md`: substituía a atualização de evidências de 3 de novembro por uma versão anterior; a versão já integrada na `main` foi preservada.

Nenhum ficheiro de credenciais, vault de segredos, chave API, backup de runtime ou base de dados foi copiado para esta branch.
