# DGM-MAT ? atualiza??o segura do execut?vel Windows

## Objetivo

Atualizar o runtime sem desinstalar nem apagar o estado persistente do DGM-MAT. O artefacto CI ? um ZIP de distribui??o, n?o um MSI. A atualiza??o substitui o execut?vel e o gestor de arranque, mantendo o vault e os restantes dados no mesmo local.

## Ficheiros atualizados

- `installed/DGM-MAT.exe`
- `scripts/autostart/backend_service.py` ? o atalho de arranque continua a chamar este gestor; no modo `full`, passa a preferir o execut?vel instalado e s? usa `main.py` como fallback se o execut?vel n?o existir.

Ambos os ficheiros s?o preparados, verificados por SHA-256 e substitu?dos como uma ?nica opera??o recuper?vel. O manifesto regista os hashes e as c?pias anteriores.

## Dados preservados

Antes da substitui??o, o script cria uma c?pia datada de:

- `%LOCALAPPDATA%\DGM-MAT\runtime`
- `%LOCALAPPDATA%\DGM-MAT\recovery-inbox`
- `%LOCALAPPDATA%\DGM-MAT\diagnostics`
- `%LOCALAPPDATA%\DGM-MAT\reports`
- `%USERPROFILE%\.dgm-mat\recovery-ledger.sqlite3`
- `DGM-MAT-Memory`
- `memory_sync`
- `storage\runtime` ? SQLite, miss?es, checkpoints, arquivo/intelig?ncia de conversas, cogni??o, relat?rios e mem?ria runtime.
- `.runtime` ? traces, relat?rios de tarefas e telemetria.
- `logs` ? registos do gestor e do runtime.
- `installed\.runtime`
- Execut?vel e gestor de arranque anteriores, com SHA-256.

O script deixa deliberadamente intactos:

- `%LOCALAPPDATA%\DGM-MAT\security` ? credenciais e bootstrap token; n?o s?o lidos nem copiados.
- `%USERPROFILE%\.dgm-mat\worktrees` ? worktrees e trabalho em curso.
- Configura??o instalada e restantes diret?rios do reposit?rio.
- `andreos-memory` e outros reposit?rios fora do diret?rio de instala??o.

## Pr?-condi??es

1. Extrair o ZIP para uma pasta tempor?ria.
2. Confirmar que cont?m `DGM-MAT.exe` e `scripts\autostart\backend_service.py`.
3. Parar o runtime. O instalador termina apenas um `DGM-MAT.exe` cujo caminho coincide exatamente com o destino.
4. Se a API local ainda responder em `127.0.0.1:8181`, a atualiza??o ? recusada para n?o copiar uma base de dados enquanto est? a ser escrita.
5. N?o apagar nem renomear manualmente as pastas de mem?ria.

## Atualiza??o

A partir de PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_windows_update.ps1 -PackageExe "C:\Caminho\Extraido\DGM-MAT.exe"
```

O instalador:

- valida o tamanho do execut?vel e a presen?a do gestor de arranque;
- cria uma pasta de backup com timestamp;
- copia os dados persistentes listados acima;
- guarda o execut?vel e o gestor de arranque anteriores;
- verifica SHA-256 do pacote, dos ficheiros preparados e dos ficheiros instalados;
- substitui o execut?vel e o gestor de arranque;
- grava `INSTALL-MANIFEST.json`;
- n?o inicia automaticamente o runtime.

O atalho `DGM-MAT Headless.lnk` mant?m o seu destino para `backend_service.py start --mode full`; ap?s a atualiza??o, esse gestor inicia `installed\DGM-MAT.exe --headless` e valida a API e o worker da fila.

## Rollback

Usar o caminho do manifesto produzido pelo instalador:

```powershell
.\scripts\rollback_windows_update.ps1 -ManifestPath "C:\ProgramasGodMode\DGM-MAT\update-backups\<timestamp>\INSTALL-MANIFEST.json"
```

O rollback restaura o execut?vel e o gestor de arranque anteriores. Os dados persistentes ficam intactos, evitando sobrescrever trabalho produzido depois da atualiza??o.

## Limites

- N?o ? um desinstalador MSI e n?o remove vers?es antigas nem reposit?rios.
- N?o migra nem altera credenciais.
- N?o apaga filas, miss?es, checkpoints, worktrees, hist?ricos ou vaults.
- A primeira inicializa??o do novo execut?vel deve ser validada separadamente; copiar os ficheiros n?o prova, por si s?, que o runtime est? saud?vel.
