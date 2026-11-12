# Atualização do DGM-MAT no Windows — V1

## Método recomendado

Não apagues manualmente o executável instalado nem desinstales a aplicação antes de existir um pacote verificado. O atualizador suportado faz uma substituição controlada no local e preserva os dados existentes. É mais seguro do que remover primeiro a instalação atual.

O artefacto Windows inclui:
- `DGM-MAT.exe` e o respetivo ficheiro SHA-256;
- `scripts/install_windows_update.ps1`, o motor de atualização governado;
- `scripts/install_dgm_mat_update.ps1`, o wrapper de validação e elevação;
- `Install-DGM-MAT-Update.bat`, o lançador de duplo clique;
- `scripts/rollback_windows_update.ps1`;
- a extensão do browser e o respetivo instalador.

## Procedimento

1. Descarrega o ZIP e o artefacto separado `.zip.sha256` da execução bem-sucedida de **Windows Executable Build** no GitHub Actions.
2. Verifica o SHA-256 do ZIP com o checksum separado, antes de extrair ou executar qualquer ficheiro.
3. Extrai o ZIP para uma pasta normal com permissões de escrita. Não o extraías por cima da pasta de instalação do DGM-MAT.
4. Fecha a janela do cockpit DGM-MAT Chat. Não apagues nem alteres a instalação ou os dados locais.
5. Faz duplo clique em `Install-DGM-MAT-Update.bat`. Aprova o pedido UAC do Windows apenas depois de confirmares o checksum do ZIP.
6. O atualizador valida o hash do executável, confirma que o processo que escuta na porta 8181 pertence ao executável DGM-MAT esperado, pede o encerramento normal e aguarda. Nunca termina processos à força.
7. O atualizador guarda cópias do executável anterior, do launcher de serviço, das pastas de runtime/recuperação/relatórios e do Vault local completo em `update-backups`. Não elimina backups antigos nem dados do utilizador.
8. Substitui apenas os ficheiros geridos do runtime e cria `INSTALL-MANIFEST.json` com hashes e localizações das cópias. Credenciais, worktrees e memória persistente ficam intocadas.
9. O runtime permanece parado. Inicia o DGM-MAT pelo atalho habitual e valida `/health`, sessão autenticada, cockpit e fluxos essenciais.

Se um pré-requisito ou checksum falhar, a atualização é abortada antes da substituição do executável. Se o processo não pertencer ao DGM-MAT esperado ou não encerrar normalmente, o atualizador recusa-se a pará-lo.

## Reversão

Usa `scripts/rollback_windows_update.ps1` incluído no pacote, indicando a pasta exata de backup criada pelo instalador. A reversão valida os hashes do manifesto e prepara os ficheiros anteriores antes de substituir qualquer um. Não apagues o backup até a nova instalação passar a aceitação local.

## Limites importantes

- Isto é uma atualização, não uma desinstalação/reinstalação. Preserva o Vault e os dados/worktrees dos projetos.
- Nunca executes um ZIP não verificado ou cujo checksum independente não corresponda.
- Nunca copies o Vault privado, credenciais, perfis do browser ou arquivos locais para o GitHub.
- Um build Windows bem-sucedido na CI não prova que a aplicação funciona no PC. É obrigatório fazer os testes locais depois da atualização.
