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
