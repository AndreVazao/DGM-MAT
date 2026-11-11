# DGM-MAT — atualização segura do executável Windows

**Data:** 2026-11-10
**Estado:** atualização controlada por SHA-256; requer artefacto CI validado e runtime parado de forma ordenada.

## Objetivo

Atualizar o runtime sem desinstalar nem apagar o estado persistente do DGM-MAT. O artefacto CI é um ZIP de distribuição, não um MSI. A atualização substitui o executável e o gestor de arranque, mantendo o vault e os restantes dados no mesmo local.

## Ficheiros atualizados

- `installed/DGM-MAT.exe`
- `scripts/autostart/backend_service.py`: o atalho de arranque continua a chamar este gestor; no modo `full`, passa a preferir o executável instalado e só usa `main.py` como fallback se o executável não existir.

Ambos os ficheiros são preparados, verificados por SHA-256 e substituídos como uma única operação recuperável. O manifesto regista os hashes e as cópias anteriores.

## Dados preservados

Antes da substituição, o script cria uma cópia datada de:

- `%LOCALAPPDATA%\DGM-MAT\runtime`
- `%LOCALAPPDATA%\DGM-MAT\recovery-inbox`
- `%LOCALAPPDATA%\DGM-MAT\diagnostics`
- `%LOCALAPPDATA%\DGM-MAT\reports`
- `%USERPROFILE%\.dgm-mat\recovery-ledger.sqlite3`
- `DGM-MAT-Memory`
- `memory_sync`
- `storage\runtime`: SQLite, missões, checkpoints, arquivo/inteligência de conversas, cognição, relatórios e memória runtime.
- `.runtime`: traces, relatórios de tarefas e telemetria.
- `logs`: registos do gestor e do runtime.
- `installed\.runtime`
- Executável e gestor de arranque anteriores, com SHA-256.

O script deixa deliberadamente intactos:

- `%LOCALAPPDATA%\DGM-MAT\security`: credenciais e bootstrap token; não são lidos nem copiados.
- `%USERPROFILE%\.dgm-mat\worktrees`: worktrees e trabalho em curso.
- Configuração instalada e restantes diretórios do repositório.
- `andreos-memory` e outros repositórios fora do diretório de instalação.

## Pré-condições

1. Extrair o ZIP para uma pasta temporária.
2. Confirmar que contém `DGM-MAT.exe` e `scripts\autostart\backend_service.py`.
3. O instalador valida que o processo que detém a API pertence exatamente ao `DGM-MAT.exe` de destino; nunca tenta parar um runtime de outra instalação.
4. Se a API estiver ativa, o instalador troca o bootstrap token local por uma sessão de operador e chama `POST /runtime/shutdown` em loopback. O servidor deixa de aceitar novos pedidos, envia a resposta e só depois sinaliza o proprietário do runtime para executar `Runtime.shutdown()`.
5. O instalador aguarda até 30 segundos pela libertação da porta e até 20 segundos pela saída dos processos. Se a janela `--cockpit-only` continuar aberta, pede ao operador que a feche e aborta sem matar processos nem criar backups parciais.
6. Se faltar o bootstrap token, a sessão não for operador, o servidor não suportar shutdown gerido ou o runtime não terminar, a atualização falha fechada. Não existe fallback para `Stop-Process`, `TerminateProcess` ou `.Kill()`. O modo API-only também usa o entrypoint Uvicorn gerido; processos iniciados por um Uvicorn externo não são terminados automaticamente e fazem a atualização abortar.
7. Não apagar nem renomear manualmente as pastas de memória.

## Atualização

A partir de PowerShell, depois de descarregar o ZIP e o sidecar `DGM-MAT.exe.sha256` do mesmo run oficial do GitHub Actions:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
$expectedExeSha256 = (Get-Content -LiteralPath ".\DGM-MAT.exe.sha256" -Raw).Trim().Split()[0]
if ($expectedExeSha256 -notmatch "^[A-Fa-f0-9]{64}$") { throw "Sidecar SHA-256 inválido" }
.\scripts\install_windows_update.ps1 -PackageExe "C:\Caminho\Extraido\DGM-MAT.exe" -ExpectedExeSha256 $expectedExeSha256
```

O hash deve ser obtido do sidecar oficial descarregado separadamente do executável. Não calcular o valor esperado a partir do próprio executável depois de o receber.

O instalador:

- valida o tamanho do executável e a presença do gestor de arranque;
- compara o SHA-256 do executável com o digest esperado fornecido separadamente, antes de criar diretórios/backups, parar processos ou tocar no destino;
- pede shutdown ordenado através da API local autenticada e aguarda a saída do runtime; nunca termina processos à força;
- aborta se permanecer uma janela de cockpit ou qualquer processo do executável de destino;
- só depois cria uma pasta de backup com timestamp;
- copia os dados persistentes listados acima;
- guarda o executável e o gestor de arranque anteriores;
- verifica SHA-256 do pacote contra o sidecar independente, dos ficheiros preparados e dos ficheiros instalados;
- regista no manifesto o digest esperado e a confirmação da validação prévia à mutação;
- substitui o executável e o gestor de arranque;
- grava `INSTALL-MANIFEST.json`;
- não inicia automaticamente o runtime.

O atalho `DGM-MAT Headless.lnk` mantém o seu destino para `backend_service.py start --mode full`; após a atualização, esse gestor inicia `installed\DGM-MAT.exe --headless` e valida a API e o worker da fila.

## Rollback

Usar o caminho do manifesto produzido pelo instalador:

```powershell
.\scripts\rollback_windows_update.ps1 -ManifestPath "C:\ProgramasGodMode\DGM-MAT\update-backups\<timestamp>\INSTALL-MANIFEST.json"
```

O rollback usa o mesmo shutdown ordenado e fail-closed; não mata processos. Restaura o executável e o gestor de arranque anteriores. Os dados persistentes ficam intactos, evitando sobrescrever trabalho produzido depois da atualização.

## Limites

- Não é um desinstalador MSI e não remove versões antigas nem repositórios.
- Não migra nem altera credenciais.
- Não apaga filas, missões, checkpoints, worktrees, históricos ou vaults.
- A primeira inicialização do novo executável deve ser validada separadamente; copiar os ficheiros não prova, por si só, que o runtime está saudável.

## Cockpit de chat independente

A atualização cria, quando o Windows permite, o atalho `DGM-MAT Chat.lnk` no Ambiente de Trabalho. O atalho executa:

```powershell
installed\DGM-MAT.exe --cockpit-only
```

Este modo abre apenas a interface de chat e liga-se ao backend já ativo em `127.0.0.1:8181`. Não inicia um segundo backend. Fechar a janela de chat não interrompe o serviço DGM-MAT. Se o backend estiver parado, a interface apresenta o erro de ligação sem declarar que a missão foi enviada.

## Dependências incluídas no executável frozen

A compilação Windows deve fixar e instalar as três dependências externas do runtime:

- `DGM-Contracts`
- `DGM-MAT-Agents`
- `DGM-MAT-Connectors`

O pacote `dgm_mat_connectors` é carregado dinamicamente pela fronteira de conectores; por isso, a especificação PyInstaller recolhe explicitamente os seus submódulos. A validação profunda falha rapidamente se o servidor API reportar um erro fatal de arranque, em vez de aguardar todo o período de tentativas de health-check.

A memória temporal normaliza timestamps naive e timezone-aware para UTC durante comparações, evitando falhas de ingestão de eventos no arranque.

## Arranque da aprendizagem de repositórios

No modo `full`, o gestor de serviço define limites incrementais (dois repositórios por lote, profundidade máxima de seis níveis, timeout Git de quatro segundos e intervalo de atualização de 30 minutos), mas deixa `DGM_REPOSITORY_LEARNING_ENABLED` por definir. Assim, o perfil runtime decide: standard ON por omissão; LOW_MEMORY (<4 GB RAM) OFF por omissão. Só um valor explicitamente definido pelo operador (`=1` ou `=0`) substitui essa política. O gestor de serviço nunca força `=1`.

A aprendizagem é read-only: recolhe metadados Git, manifestos e um resumo redigido do README; gera árvores de caminhos sem ler o conteúdo dos ficheiros; não altera repositórios nem executa código de projetos. Os dados duráveis ficam em `storage/cognition/repository_learning` e são agora incluídos no backup de atualização.

O worker de ajuda por IA externa continua desligado por omissão (`DGM_AUTONOMY_HELP_ENABLED=0`) até existir integração e validação explícita dos fornecedores gratuitos pretendidos.
