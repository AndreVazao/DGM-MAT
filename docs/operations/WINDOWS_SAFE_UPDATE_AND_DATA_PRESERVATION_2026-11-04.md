# DGM-MAT — atualização segura do executável Windows

**Data:** 2026-11-04`r`n**Estado:** implementação local em validação; não instalar até existir artefacto CI validado.

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
3. Parar o runtime. O instalador termina apenas um `DGM-MAT.exe` cujo caminho coincide exatamente com o destino.
4. Se a API local ainda responder em `127.0.0.1:8181`, a atualização é recusada para não copiar uma base de dados enquanto está a ser escrita.
5. Não apagar nem renomear manualmente as pastas de memória.

## Atualização

A partir de PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_windows_update.ps1 -PackageExe "C:\Caminho\Extraido\DGM-MAT.exe"
```

O instalador:

- valida o tamanho do executável e a presença do gestor de arranque;
- cria uma pasta de backup com timestamp;
- copia os dados persistentes listados acima;
- guarda o executável e o gestor de arranque anteriores;
- verifica SHA-256 do pacote, dos ficheiros preparados e dos ficheiros instalados;
- substitui o executável e o gestor de arranque;
- grava `INSTALL-MANIFEST.json`;
- não inicia automaticamente o runtime.

O atalho `DGM-MAT Headless.lnk` mantém o seu destino para `backend_service.py start --mode full`; após a atualização, esse gestor inicia `installed\DGM-MAT.exe --headless` e valida a API e o worker da fila.

## Rollback

Usar o caminho do manifesto produzido pelo instalador:

```powershell
.\scripts\rollback_windows_update.ps1 -ManifestPath "C:\ProgramasGodMode\DGM-MAT\update-backups\<timestamp>\INSTALL-MANIFEST.json"
```

O rollback restaura o executável e o gestor de arranque anteriores. Os dados persistentes ficam intactos, evitando sobrescrever trabalho produzido depois da atualização.

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
