# DGM-MAT — Plano de aceitação Windows 10 + Chrome
**Data:** 2026-11-08  
**Aplicável a:** PR #283, head documental `75b6fa0a7a09af645aa8ee80e39384a4858550b0` e artefacto Windows Build #300 (código funcional igual ao head `042be2354a82efc3659661f1e85197c9a917692b`).  
**Objetivo:** validar instalação, arranque, persistência e consulta manual aprovada sem ativar autonomia ou introduzir risco nos dados existentes.

## 0. Regras de segurança

- Não apagar instalações, bases de dados, configurações, credenciais, worktrees, logs ou backups existentes.
- Não iniciar duas instâncias do DGM-MAT. Se a API já responder em `127.0.0.1:8181`, primeiro identificar a instância; não executar um segundo arranque.
- Não usar `DGM-MAT-FULL-MIRROR`, nem copiar por cima da instalação atual.
- Não ativar AutoHelp, execução autónoma, consultas automáticas ou fallback pago.
- Manter inicialmente desligadas as flags:
  - `DGM_BROWSER_CONSULT_ENABLED=0`
  - `DGM_BROWSER_CONSULT_FREE_CAPACITY_CONFIRMED=0`
  - `DGM_AUTONOMY_HELP_BROWSER_CONSULT_ENABLED=0`
- Não introduzir passwords, cookies, tokens, dados pessoais ou conteúdo confidencial nos prompts de teste.
- Se surgir erro de autenticação, CAPTCHA, quota, seletor desconhecido, UI diferente ou comportamento inesperado, parar o teste desse fornecedor. Nunca contornar o bloqueio.
- Esta checklist é um procedimento de aceitação; não afirma que os testes já foram executados no PC.

## 1. Artefacto oficial

Usar exclusivamente o artefacto da execução GitHub Actions:

- Repositório: `AndreVazao/DGM-MAT`
- Execução: https://github.com/AndreVazao/DGM-MAT/actions/runs/42475905948
- Nome do artefacto: `DGM-MAT-Windows-3.12-54e344e`
- Tamanho: 111,238,946 bytes
- SHA-256 do artefacto GitHub: `f5d5abefe05dd14c40043484f4601eb90cdcad45ae034d31d71fd2eb7eee97d2`
- Commit incluído: `75b6fa0a7a09af645aa8ee80e39384a4858550b0`
- Expiração indicada pelo GitHub: 2027-02-06 11:28:39 UTC.

No GitHub, abrir a execução acima, descer até **Artifacts** e descarregar exatamente o artefacto indicado. Não usar o botão genérico **Source code** nem um ZIP de uma branch.

O download de Actions é um arquivo exterior. Depois de o extrair, deverá existir o ZIP de distribuição `DGM-MAT-Windows-3.12-54e344e.zip`, o respetivo ficheiro `.sha256` e a pasta `publish\` com o sidecar `DGM-MAT.exe.sha256`. Extrair esse ZIP de distribuição para uma subpasta `package\`. O executável e a pasta `scripts\` ficam na raiz de `package\`; não existe uma segunda pasta `publish\` dentro dela.

Verificar o SHA-256 do arquivo exterior descarregado contra o digest publicado pelo GitHub. Depois verificar o ZIP de distribuição contra o conteúdo de `DGM-MAT-Windows-3.12-5f31bf7.zip.sha256`. Não confundir estes dois níveis de arquivo.

Depois de extrair o ZIP de distribuição para `package\`, verificar `package\DGM-MAT.exe` contra o sidecar `publish\DGM-MAT.exe.sha256` que veio no arquivo exterior. **O digest do artefacto GitHub não é o digest do executável.** O instalador seguro exige o digest do executável, fornecido explicitamente.

Comandos de verificação (ajustar apenas os caminhos para a pasta onde o download foi extraído):

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath ".\DGM-MAT-Windows-3.12-5f31bf7.zip"
Get-Content -LiteralPath ".\DGM-MAT-Windows-3.12-5f31bf7.zip.sha256"
Get-Content -LiteralPath ".\publish\DGM-MAT.exe.sha256"
Get-FileHash -Algorithm SHA256 -LiteralPath ".\package\DGM-MAT.exe"
```

Os hashes calculados têm de coincidir exatamente com os respetivos sidecars. Se faltar um ficheiro, o nome/commit não corresponder ou qualquer hash divergir, parar e não instalar.

## 2. Pré-verificação do PC (read-only)

Antes de substituir qualquer ficheiro:

1. Registar a versão do Windows, arquitetura, espaço livre e versão do Chrome.
2. Registar os caminhos atuais do DGM-MAT e a localização do atalho usado para iniciar o backend.
3. Verificar se existe uma instância ativa:
   
```powershell
Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 http://127.0.0.1:8181/health
```

4. Se responder HTTP 200, não iniciar outra instância. Registar a resposta e identificar o processo existente antes de qualquer atualização.
5. Se a API não responder, confirmar também que não existe processo DGM-MAT ativo nem serviço em arranque.
6. Confirmar que existe espaço para o ZIP, extração e backup. Não limpar espaço apagando dados DGM-MAT.

**Ponto de controlo:** se o estado instalado, processo ativo, diretórios de dados ou mecanismo de arranque não forem claros, parar e recolher diagnóstico. Não improvisar uma instalação paralela sobre a instalação existente.

## 3. Backup e atualização controlada

O pacote contém `scripts\install_windows_update.ps1` e `scripts\rollback_windows_update.ps1`.

O instalador:
- valida o SHA-256 do executável antes de alterar o sistema;
- recusa atualizar se o runtime/API ainda estiver ativo;
- guarda o executável anterior e os dados persistentes identificados;
- atualiza o executável instalado e o launcher `scripts\autostart\backend_service.py`;
- cria um manifesto de instalação/backup;
- não inicia o runtime no final.

Local de destino predefinido do executável:
`C:\ProgramasGodMode\DGM-MAT\installed\DGM-MAT.exe`.

Raiz de backups predefinida:
`C:\ProgramasGodMode\DGM-MAT\update-backups`.

Antes de executar, confirmar que estes caminhos correspondem à instalação real deste PC. Se não corresponderem, não executar com os valores predefinidos: definir os caminhos corretos conscientemente e manter os dados atuais preservados.

Exemplo de invocação, apenas depois de concluídas as verificações e de o utilizador autorizar a atualização:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\package\scripts\install_windows_update.ps1" -PackageExe ".\package\DGM-MAT.exe" -ExpectedExeSha256 (Get-Content ".\publish\DGM-MAT.exe.sha256" -Raw).Trim().Split(' ')[0]
```

Executar numa janela PowerShell normal do utilizador, sem elevar privilégios desnecessariamente. Guardar o caminho e conteúdo do manifesto `INSTALL-MANIFEST.json` criado pelo instalador.

Não remover backups após a instalação. O rollback disponível é:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\package\scripts\rollback_windows_update.ps1" -ManifestPath "CAMINHO_REAL_DO_BACKUP\INSTALL-MANIFEST.json"
```

O rollback só deve ser usado com o manifesto real da atualização correspondente e com o runtime parado.

## 4. Primeiro arranque — sem consultas externas

1. Iniciar o DGM-MAT pelo mecanismo/atalho de backend já utilizado no PC. O instalador não inicia o runtime automaticamente.
2. Esperar pela prontidão normal; não abrir uma segunda instância se demorar.
3. Confirmar `GET http://127.0.0.1:8181/health` com HTTP 200 e serviço identificado como DGM-MAT.
4. Confirmar que a interface/cockpit abre e comunica com o backend.
5. Confirmar que as conversas, memória, projetos, worktrees e configurações anteriores continuam presentes.
6. Confirmar que não existem erros críticos nos logs recentes.
7. Reiniciar o PC ou o serviço apenas numa janela de teste acordada; confirmar que o mecanismo normal volta a arrancar uma única instância.

Registar cada resultado como **PASS**, **FAIL** ou **NOT TESTED**, com hora, versão, evidência e log associado. Não marcar um teste como PASS apenas porque o processo abriu.

## 5. Instalação e emparelhamento da extensão Chrome

O ZIP contém a pasta `browser_extension` e os scripts de instalação.

1. Confirmar que o Chrome usado é o perfil normal do operador e que os cinco fornecedores estão autenticados manualmente, se aplicável.
2. Executar `package\scripts\install_browser_extension.bat` a partir da pasta exterior do artefacto. O script preserva a extensão anterior em `%LOCALAPPDATA%\DGM-MAT\BrowserExtension.backups\`.
3. No Chrome, ativar **Developer mode** em `chrome://extensions`.
4. Escolher **Load unpacked** e selecionar `%LOCALAPPDATA%\DGM-MAT\BrowserExtension`. Se já estiver carregada a partir dessa pasta, usar **Reload**.
5. Emparelhar apenas com o código de utilização única emitido pelo DGM-MAT local. Não partilhar nem guardar esse código no relatório.
6. Confirmar que a extensão fica ligada ao backend local e que o popup abre sem erros.
7. Confirmar que o opt-in de consulta permanece desligado e que não há mensagens enviadas automaticamente.

Se o emparelhamento falhar, recolher mensagem e logs sem copiar tokens/códigos. Não remover o perfil Chrome nem limpar dados de sessão.

## 6. Consulta manual controlada — um fornecedor de cada vez

Só iniciar esta fase após aprovação explícita do operador e confirmação de que as flags necessárias estão configuradas para o teste. Não ativar AutoHelp nem autonomia geral.

Começar por **um único fornecedor**, escolhido pelo operador e cuja conta gratuita/capacidade disponível tenha sido confirmada manualmente.

Prompt de teste recomendado, sem dados privados:

```text
Responde apenas: DGM-MAT browser acceptance test OK. Não executes ações nem peças dados adicionais.
```

Procedimento:
1. Criar uma consulta manual no popup.
2. Confirmar que o pedido aparece em `PENDING_APPROVAL`.
3. Confirmar que ainda não foi enviado antes da aprovação.
4. Aprovar explicitamente aquele pedido.
5. Observar o separador autenticado e confirmar que o envio ocorre na UI visível normal do fornecedor.
6. Confirmar que a resposta é capturada e guardada como conteúdo externo/não verificado, associada ao pedido correto.
7. Confirmar que o token de claim deixa de poder ser reutilizado e que o pedido não é reenviado.
8. Confirmar que o resultado não executa comandos, não altera ficheiros/repos e não aprova missões.
9. Repetir apenas após revisão do resultado, um fornecedor de cada vez.

Parar se surgir login, MFA, CAPTCHA, aviso de quota, plano pago, seletor desconhecido, página inesperada ou divergência entre o pedido e a resposta. Não tentar contornar esses estados.

Só depois de o primeiro fornecedor passar é que se considera testar Grok, Gemini, DeepSeek e Qwen individualmente. Não presumir que todas as contas têm plano gratuito ou quota disponível.

## 7. Testes negativos obrigatórios

- Pedido sem aprovação não pode ser reclamado/enviado.
- Sessão não emparelhada não pode reclamar nem devolver resultados.
- Claim token inválido, expirado ou já usado é rejeitado.
- Resultado de fornecedor é sempre conteúdo não confiável.
- Reinício do service worker com pedido em curso não causa replay automático; o pedido fica interrompido/bloqueado.
- Falha de auditoria/segurança bloqueia a aprovação/envio.
- Nenhuma consulta é enviada com o opt-in desligado.
- Nenhuma API paga, chave, subscrição ou fallback pago é utilizada.
- O operador consegue parar a extensão e o runtime sem perder os dados já persistidos.

## 8. Critérios de aceitação e decisão

A aceitação só fica concluída quando:
- [ ] ZIP e executável verificados por SHA-256.
- [ ] Backup e manifesto criados e confirmados.
- [ ] Executável atualizado e arranque local saudável.
- [ ] Dados/memória/configuração anteriores preservados.
- [ ] Chrome extension carregada e emparelhada.
- [ ] Opt-ins desligados por defeito.
- [ ] Uma consulta manual, individual e aprovada passou.
- [ ] Testes negativos passaram.
- [ ] Logs e relatório de evidência foram guardados sem segredos.

Depois:
- testar os restantes fornecedores gratuitos individualmente;
- repetir Snyk quando a quota do serviço estiver disponível;
- rever o relatório e só então decidir o merge da PR #283.

**Este runbook não autoriza por si só a atualização, a ativação das flags, o envio de consultas ou o merge.** A decisão continua a pertencer ao operador. As branches antigas permanecem intactas até decisão explícita de limpeza.
