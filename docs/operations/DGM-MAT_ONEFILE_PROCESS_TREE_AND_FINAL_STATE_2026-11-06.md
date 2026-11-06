# DGM-MAT — processo único, árvore PyInstaller e estado final (2026-11-06)

## Interpretação correta dos dois PIDs DGM-MAT.exe

O build utiliza PyInstaller one-file (`build/dgm_mat.spec` define `EXE` sem `COLLECT`). Nesse modo, o bootloader mantém um processo-pai leve e executa o runtime num processo-filho. Isto não representa dois runtimes nem duas filas.

Na validação após instalação:

- PID 13820: bootloader/pai, lançado pelo gestor de serviço.
- PID 9928: processo-filho que efetivamente possui o listener `127.0.0.1:8181`.
- Apenas um listener DGM-MAT em 8181; `/health` saudável.
- Apenas um servidor Uvicorn DGM-HUB, PID 3840, em 8771; 8770 sem listener.

O pai é necessário ao formato one-file. Não deve ser terminado isoladamente nem confundido com uma segunda instância. Para uma distribuição com apenas um PID seria necessário migrar o empacotamento para onedir, o que não foi feito porque não é necessário para garantir um único serviço.

## Defeito corrigido no gestor de serviço

O `stop` anterior terminava apenas o PID registado (pai) e deixava o processo-filho a servir 8181. O novo `stop`:

1. recolhe descendentes do PID registado;
2. termina apenas descendentes cuja identidade DGM-MAT é validada;
3. termina depois o pai;
4. se o pai já desapareceu, identifica o PID do listener e só o termina se o executável/linha de comando forem comprovadamente DGM-MAT;
5. preserva o ficheiro de estado se a API continuar saudável.

O caso real de processo órfão (PID 7020) foi parado com sucesso pelo gestor corrigido e a porta 8181 ficou offline antes do reinício. Testes unitários cobrem árvore pai/filho e recuperação de listener órfão.

## Estado após reinício controlado

- DGM-MAT instalado: `C:\\ProgramasGodMode\\DGM-MAT\\installed\\DGM-MAT.exe`.
- SHA-256 do executável instalado: `8257EF8AD7994B4266CE99E4337AD6D36371162011330E7D196E009AF2388348`.
- Backup do instalador: `C:\\ProgramasGodMode\\DGM-MAT\\update-backups\\20261106-164136`.
- API: HTTP 200; runtime `running`, `DEGRADED=False`.
- SafeActionQueue: worker vivo, uma thread, heartbeat recente.
- Auto-help: ativo, `free-only; no paid fallback; no automatic retry`, provider permitido apenas `kilo`, resposta verificada obrigatória.
- Kilo: chamada anónima sem API key, modelo `nvidia/nemotron-3.5-lightning:free`, resposta verificada.
- LLM7: HTTP 429; removido da configuração do DGM-MAT para evitar tentativas inúteis. Codex/Claude não estavam online no Hub durante o checkup.
- A tarefa `DGM-MAT-Main-Only-Sync` está instalada, executa de quatro em quatro horas e terminou com `LastTaskResult=0`; sincroniza apenas main por fast-forward.

## Limites atuais

- O DGM-MAT está saudável, mas não tem missões ativas neste instante; ações pendentes de aprovação não foram aprovadas automaticamente.
- A extensão Chrome de arquivo de conversas ainda precisa de instalação/autorização do utilizador e validação de paginação/histórico completo.
- Nenhuma branch antiga foi eliminada; os ramos de trabalho continuam sujeitos a revisão e integração por PR.
