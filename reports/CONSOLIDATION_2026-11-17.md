# DGM-MAT — Consolidação GitHub e estado operacional

**Última atualização:** 2026-11-18 10:45 UTC  
**Repositório:** `AndreVazao/DGM-MAT`  
**Main verificada:** `4bbbcf462561bbb60b66c570146eeb2cc22d4451`  
**Estado operacional:** VERIFICAÇÃO INCOMPLETA — PC ainda sem disponibilidade confirmada.

## 1. Integrações desta ronda de 17/11

Foram integradas por squash merge, com validação do SHA esperado e confirmação posterior no GitHub, 16 PRs:

### Código e funcionalidades

| PR | Conteúdo | Merge commit |
|---|---|---|
| #345 | Classificação least-privilege das rotas mobile archive/restore | `ebdf83141bc4deab97a26b1823d6905b17544605` |
| #386 | Fronteira histórica efetiva derivada no servidor | `23567e816c2045bc07d1ea73f33d522829851991` |
| #382 | Histórico bounded de PRs/issues GitHub e snapshot de trabalho aberto | `755de4622b9314754447d4a09bef4644e5fee283` |
| #387 | Freshness por fonte nos dossiers | `018fd78907ab19949e358eaed4b9c458a1b4bf27` |
| #376 | Consulta read-only de dossiers no chat Cockpit | `e0247e0039f8fd9976de86e89cb4859d70764b36` |

### Documentação e auditorias

| PR | Conteúdo | Merge commit |
|---|---|---|
| #389 | Supervisão diária 17/11 | `b0364c068a12ed61b5d47b9e9b59fc6f2c6557a8` |
| #388 | Supervisão diária 16/11 | `c38c17331b85168d31a52b1f41b94084207e2d21` |
| #384 | Supervisão diária 15/11 | `d0b8a78aa718538581b19aff583133cc88261018` |
| #383 | Supervisão diária 14/11 | `89a67673a3d4c6d328e7ec8faa48761daa35d2ec` |
| #377 | Supervisão diária 13/11 | `82aeec4e6bdb219d23601413da22f4b1aefaa312` |
| #368 | Supervisão diária 12/11 | `b3d3197d2808d7618a1920f1a7f798847b9ef4e6` |
| #359 | Auditoria de recuperação de conhecimento e dossiers | `2e1586f9b31ef8fe8e5ca21d1d566adf70abaa4b` |
| #349 | Plano de consulta AI em linguagem natural | `41d61fcabc4ef800cf5f4efa05d64dbddc5953c5` |
| #346 | Supervisão diária 11/11 | `df96918da178df88bcfc83f8c66aaaa3b41ef36d` |
| #344 | Evidência de readiness do mission executor | `c7fade48b613a8a1aaad717f2758ab9dc9bb9fbb` |
| #343 | Supervisão diária 10/11 | `4bbbcf462561bbb60b66c570146eeb2cc22d4451` |

Total: **16 PRs integradas** (5 código/funcionalidade + 11 documentação/auditoria). Os checks dos heads foram observados verdes antes dos merges; isto não substitui a validação do runtime instalado.

## 2. PRs redundantes e consolidação

- #379 foi encerrada como substituída pela #382. A branch original foi preservada.
- #385 foi encerrada como redundante face à #386. A branch original foi preservada.
- #347 foi encerrada em 18/11 como supersedida por código e testes já presentes em `main`. A branch original foi preservada. Não foi integrada nem rebaseada.

### Evidência da #347 já coberta na main

A revisão de 18/11 confirmou na main:
- `POST /runtime/shutdown` em `core/api/runtime_api.py`, classificado como operator-only em `core/api/security_policy.py`.
- Sinalização de shutdown em `core/runtime/runtime_control.py`, `core/api/api_server.py` e `main.py`.
- Instalador e rollback Windows com troca de sessão local, pedido de shutdown e política fail-closed.
- EventBus com `stop(timeout)`, join do worker e drain da fila.
- Runtime a aguardar a saída do API thread, SafeActionQueue, EventBus e workers relevantes.
- Testes atuais em `tests/api/test_runtime_shutdown.py`, `tests/runtime/test_runtime_shutdown_lifecycle.py` e `tests/operational/test_installer_graceful_shutdown.py`.

A branch da #347 tinha 36 commits exclusivos e 43 commits em falta relativamente à main na comparação observada. O CI da branch falhou por colisão de nomes de módulos pytest entre `tests/api/test_runtime_shutdown.py` e `tests/runtime/test_runtime_shutdown.py`. A main já contém o teste de lifecycle com nome distinto. Por isso, integrar a branch antiga seria arriscado e redundante.

## 3. Única PR nova desta ronda

- **PR #390:** [docs(report): consolidate DGM-MAT PR integrations 2026-11-17](https://github.com/AndreVazao/DGM-MAT/pull/390)
- Branch: `reports/consolidation-2026-11-17`
- Ficheiro: `reports/CONSOLIDATION_2026-11-17.md`
- Alteração exclusivamente documental.

Esta PR é o único trabalho novo deixado aberto após a limpeza. Deve ser revista e integrada apenas depois de o diff ser confirmado contra a main atual.

## 4. CI e limites

- Os workflows de validação focada e build Windows dos heads das cinco PRs funcionais integradas foram observados verdes antes dos respetivos merges.
- A #347 teve build Windows e validação Chrome verdes, mas a validação focada falhou por colisão de nomes pytest; a branch foi encerrada como supersedida, não integrada.
- Snyk não foi usado, conforme decisão do operador.
- CodeRabbit foi skipped automaticamente onde aplicável.
- Não foi descarregado nem instalado qualquer artefacto.

## 5. Estado operacional

- O PC `PC-Vazao-Anjos` estava reportado offline na última supervisão disponível; não há confirmação de que tenha regressado.
- Não foram executados testes no PC nesta ronda.
- Não há prova nova de API autenticada, missão real, agentes ativos, captura autenticada dos seis providers, scheduler, DGM-HUB, instalação, atualização ou rollback.
- Não foi alterada a proteção da main; a última leitura indicava `protected=false`.
- Não foram alterados ficheiros nem processos no PC.

## 6. Próxima sequência

1. Rever e fechar a PR documental #390 depois de confirmar o diff final contra a main.
2. Quando o PC estiver online, preservar primeiro o working tree e os dados; depois verificar sessão local e executar uma missão read-only.
3. Validar o shutdown/installer no Windows real antes de qualquer atualização.
4. Só depois testar agentes, recuperação autenticada de conversas e DGM-HUB.

**Conclusão:** 16 PRs integradas; as alternativas redundantes foram encerradas sem apagar branches; a implementação de shutdown já está na main; uma única PR documental (#390) permanece aberta. O DGM-MAT ainda não pode ser declarado operacionalmente pronto sem validação real no PC.
