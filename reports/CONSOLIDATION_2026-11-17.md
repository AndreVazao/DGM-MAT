# DGM-MAT — Consolidação de PRs e estado de integração
**Data:** 2026-11-17 22:00 UTC  
**Repositório:** AndreVazao/DGM-MAT  
**Main antes da ronda:** 2cf91c5b36a9f7360cf142dc2c60be6ac2f6f18e  
**Main após os merges:** e0247e0039f8fd9976de86e89cb4859d70764b36  
**Classificação operacional:** VERIFICAÇÃO INCOMPLETA — PC offline.

## 1. Merges concluídos nesta ronda

Foram integradas por squash merge, com SHA esperado fixo e confirmação posterior do estado merged:

| PR | Âmbito | Merge commit |
|---|---|---|
| #345 | Classificação least-privilege das rotas mobile archive/restore | `ebdf83141bc4deab97a26b1823d6905b17544605` |
| #386 | Fronteira histórica efetiva derivada no servidor; não aceitar alegações client-side como prova | `23567e816c2045bc07d1ea73f33d522829851991` |
| #382 | Histórico bounded de PRs/issues GitHub e snapshot separado de trabalho aberto | `755de4622b9314754447d4a09bef4644e5fee283` |
| #387 | Freshness por fonte nos dossiers, sem inferir atualidade | `018fd78907ab19949e358eaed4b9c458a1b4bf27` |
| #376 | Consulta read-only de dossiers do projeto no chat Cockpit | `e0247e0039f8fd9976de86e89cb4859d70764b36` |

Todos os cinco PRs foram posteriormente consultados no GitHub e confirmados como `closed` + `merged=true`. A branch default `main` aponta agora para `e0247e0039f8fd9976de86e89cb4859d70764b36`.

## 2. Duplicações e PRs não integradas

- #385 não foi integrada: sobrepõe-se à cobertura de regressão mais abrangente de #386. O head da #385 continua preservado.
- #379 não foi integrada: sobrepõe-se à implementação de histórico/snapshot de #382, que foi selecionada como a versão mais completa. O head da #379 continua preservado.
- #347 não foi integrada: GitHub reportou `mergeable=false`; são 16 ficheiros e 558 adições/51 remoções numa área sensível de shutdown, autenticação, atualização e rollback. Não foi forçada nem alterada.
- PRs documentais antigas (#343, #344, #346, #368, #377, #383, #384, #388, #389), mais os planos/auditorias #349 e #359, permanecem abertas. Não foram fechadas nem apagadas; vários heads têm base antiga e GitHub reporta `mergeable=false`. Exigem consolidação explícita em vez de merge cego.

## 3. CI e limites

Antes dos merges, os checks dos heads de #345, #386, #382, #387 e #376 foram observados como concluídos com sucesso nos workflows de validação focada/build Windows; #345 também tinha validação da extensão Chrome. Snyk foi excluído como critério, conforme decisão do operador. CodeRabbit foi skipped automaticamente onde aplicável.

Os checks dos heads não equivalem a uma nova validação pós-merge da main nem a uma execução no PC. Não foi descarregado nem instalado qualquer artefacto.

## 4. Estado operacional

- O PC `PC-Vazao-Anjos` continua reportado offline.
- Não foram testados runtime, API autenticada, bootstrap/session exchange, scheduler, fila, agentes, providers, captura real de conversas, DGM-HUB, instalador ou rollback.
- Nenhuma conversa foi recuperada nesta ronda.
- Não foram feitas operações no PC, nem alterações ao working tree local.
- A configuração de proteção da main não foi alterada; a última leitura GitHub indicava `protected=false`.

## 5. Próximo passo

Consolidar as PRs documentais antigas num único relatório atualizado e manter uma única linha de implementação seguinte depois de rever a #347 (shutdown seguro) e os conflitos das branches antigas. Não forçar merges nem fechar branches de trabalho sem preservar o conteúdo e verificar que não há trabalho exclusivo.

**Conclusão:** cinco integrações de código concluídas e verificadas no GitHub. O DGM-MAT continua sem prova de funcionamento real no PC; não classificar como pronto para operação.


## 6. Atualização da consolidação — 17/11/2026, 22:05 UTC

Depois da primeira sequência, foram também integradas PRs documentais que continuavam mergeable. A sequência foi feita com revalidação do head SHA, estado e mergeability antes de cada squash merge; após cada integração aguardou-se a atualização do estado GitHub antes de continuar.

PRs documentais adicionais confirmadas merged:
- #389 — relatório diário 17/11 — `b0364c068a12ed61b5d47b9e9b59fc6f2c6557a8`.
- #388 — relatório diário 16/11 — `c38c17331b85168d31a52b1f41b94084207e2d21`.
- #384 — relatório diário 15/11 — `d0b8a78aa718538581b19aff583133cc88261018`.
- #383 — relatório diário 14/11 — `89a67673a3d4c6d328e7ec8faa48761daa35d2ec`.
- #377 — relatório diário 13/11 — `82aeec4e6bdb219d23601413da22f4b1aefaa312`.
- #368 — relatório diário 12/11 — `b3d3197d2808d7618a1920f1a7f798847b9ef4e6`.
- #359 — auditoria de recuperação de conhecimento e dossiers — `2e1586f9b31ef8fe8e5ca21d1d566adf70abaa4b`.
- #349 — plano de consulta AI em linguagem natural — `41d61fcabc4ef800cf5f4efa05d64dbddc5953c5`.
- #346 — relatório diário 11/11 — `df96918da178df88bcfc83f8c66aaaa3b41ef36d`.
- #344 — evidência de readiness do mission executor — `c7fade48b613a8a1aaad717f2758ab9dc9bb9fbb`.
- #343 — relatório diário 10/11 — `4bbbcf462561bbb60b66c570146eeb2cc22d4451`.

Total integrado nesta ronda: **16 PRs** (5 de código/funcionalidade + 11 documentais). As PRs #379 e #385 continuam preservadas sem merge por sobreposição com #382 e #386 já integradas. A #347 continua preservada sem merge por não mergeability e por tocar em shutdown/update/auth.

A PR #390 é o único PR novo criado para a consolidação desta ronda; continua aberta para revisão. O estado exato da main deve ser obtido da branch, não inferido dos SHAs individuais da tabela acima.


## 7. Encerramento das PRs redundantes — 17/11/2026

Depois de integrar #382 e #386, as PRs #379 e #385 foram encerradas com comentário explicativo. As respetivas branches continuam preservadas no GitHub; não foram apagadas. A #379 foi substituída pela funcionalidade mais abrangente de #382; a #385 pela implementação e regressões mais completas de #386.

Estado de trabalho após a consolidação:
- #390 — única PR nova ativa desta ronda, documentação de consolidação, aberta para revisão.
- #347 — PR antiga em draft, não mergeable, preservada para revisão futura do shutdown/update/rollback.
- #379 e #385 — PRs encerradas como redundantes; branches preservadas.
- Main HEAD observado após os merges documentais: `4bbbcf462561bbb60b66c570146eeb2cc22d4451`.

A PR #390 não é uma prova de funcionamento do produto; é o registo auditável das integrações e limites desta ronda.
