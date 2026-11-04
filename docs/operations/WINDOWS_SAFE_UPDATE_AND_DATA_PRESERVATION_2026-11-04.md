# DGM-MAT — atualização segura do executável Windows

## Objetivo

Atualizar o executável sem desinstalar nem apagar o estado persistente do DGM-MAT. O pacote CI atual é um ZIP de distribuição, não um instalador MSI; por isso, o procedimento substitui apenas `DGM-MAT.exe`.

## Dados preservados

Antes da substituição, o script cria uma cópia datada de:

- `%LOCALAPPDATA%\DGM-MAT\runtime`
- `%LOCALAPPDATA%\DGM-MAT\recovery-inbox`
- `%LOCALAPPDATA%\DGM-MAT\diagnostics`
- `%LOCALAPPDATA%\DGM-MAT\reports`
- `%USERPROFILE%\.dgm-mat\recovery-ledger.sqlite3`
- `DGM-MAT-Memory`
- `memory_sync`
- `storage\runtime` ? SQLite, missions, checkpoints, conversation archive/intelligence, cognition, reports and runtime memory.
- `.runtime` ? runtime traces, task reports and telemetry.
- `installed\.runtime`
- Executável anterior e respetivo SHA-256

O script deixa deliberadamente intactos:

- `%LOCALAPPDATA%\DGM-MAT\security` — credenciais e bootstrap token; não são lidos nem copiados.
- `%USERPROFILE%\.dgm-mat\worktrees` — worktrees e trabalho em curso.
- Configuração instalada e restantes diretórios do repositório.
- `andreos-memory` e outros repositórios fora do diretório de instalação.

## Pré-condições

1. Extrair o ZIP de distribuição para uma pasta temporária.
2. Confirmar que o executável extraído se chama `DGM-MAT.exe`.
3. Fechar o DGM-MAT. O instalador termina apenas o processo `DGM-MAT.exe` cujo caminho coincide exatamente com o destino.
4. Se a API local ainda responder em `127.0.0.1:8181`, a atualização é recusada para não copiar uma base de dados enquanto está a ser escrita.
5. Não apagar nem renomear manualmente as pastas de memória.

## Atualização

A partir de PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_windows_update.ps1 -PackageExe "C:\Caminho\Extraido\DGM-MAT.exe"
```

O script:

- valida o tamanho do executável;
- cria uma pasta de backup com timestamp;
- copia os dados persistentes listados acima;
- verifica SHA-256 antes e depois da substituição;
- substitui apenas o executável;
- grava `INSTALL-MANIFEST.json`;
- não inicia automaticamente o novo runtime.

## Rollback

Usar o caminho do manifesto produzido pelo instalador:

```powershell
.\scripts\rollback_windows_update.ps1 -ManifestPath "C:\ProgramasGodMode\DGM-MAT\update-backups\<timestamp>\INSTALL-MANIFEST.json"
```

O rollback restaura apenas o executável anterior. Os dados persistentes ficam intactos, evitando sobrescrever trabalho produzido depois da atualização.

## Limites

- Não é um desinstalador MSI e não remove versões antigas nem repositórios.
- Não migra nem altera credenciais.
- Não apaga filas, missões, checkpoints, worktrees, históricos ou vaults.
- A primeira inicialização do novo executável deve ser validada separadamente; o script não declara o runtime saudável só por ter copiado o ficheiro.
