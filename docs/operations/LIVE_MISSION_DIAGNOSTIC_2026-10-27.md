# Diagnóstico local de missão DGM-MAT

**Estado:** ferramenta de diagnóstico preparada; tem de ser executada no PC Windows que contém a instalação. Não representa prova de funcionamento até existir um relatório gerado pelo próprio PC.

## O que verifica

1. GET /health (processo HTTP, não saúde completa do cérebro).
2. Credencial bootstrap local em %LOCALAPPDATA%\DGM-MAT\security\bootstrap.token ou no caminho definido por DGM_LOCAL_BOOTSTRAP_FILE.
3. Troca da credencial por uma sessão local de curta duração via POST /auth/session.
4. GET /runtime/health com sessão autenticada.
5. Submissão de uma única missão read-only: “Lista os repositórios locais”.
6. Consulta do checkpoint durável GET /runtime/missions/{mission_id} até estado terminal ou timeout.

## O que NÃO faz

- Não inicia, termina nem reinicia processos.
- Não imprime nem grava tokens de autenticação.
- Não aprova missões, não repete submissões e não tenta executar ações mutáveis.
- Não envia credenciais para endereços remotos: só aceita HTTP em 127.0.0.1, localhost ou ::1.
- Não considera HTTP 200, status=success na criação, nem /health como prova de execução concluída.

## Executar no PC Windows

A partir da raiz do checkout DGM-MAT, executar:

    python scripts/diagnose_live_mission.py

O comando grava um JSON em %LOCALAPPDATA%\DGM-MAT\diagnostics\live-mission-AAAAMMDD-HHMMSS.json. Para uma pasta de relatório diferente:

    python scripts/diagnose_live_mission.py --report-dir "$env:USERPROFILE\Documents\DGM-MAT-Diagnostics"

Códigos de saída:
- 0: a missão atingiu COMPLETED; analisar o resultado e o output no relatório.
- 2: bloqueio, falha, timeout ou checkpoint inacessível. O relatório conserva o último estado observado.

## Interpretação

| Observação | Significado |
|---|---|
| process_health PASS, session_exchange bloqueado | A API responde, mas a autenticação local não está configurada/funcional. |
| runtime_health bloqueado | A sessão não é aceite ou a API runtime não está disponível. |
| missão criada e QUEUED/APPROVAL_PENDING até timeout | A criação funciona; a execução/decisão da fila continua bloqueada. O teste não aprova automaticamente. |
| FAILED | Ler error e result do checkpoint; não mascarar como sucesso. |
| COMPLETED | O ciclo chegou a estado terminal de sucesso segundo o runtime; verificar handler, output e resultado para confirmar o que foi realmente executado. |

## Limites

Este teste é intencionalmente local e não prova que o APK funciona num emulador. O teste de interface Android deve ser uma fase separada, depois de obter um APK válido e um emulador/dispositivo ligado. Os resultados só são conhecidos depois de executar esta ferramenta na máquina-alvo.
