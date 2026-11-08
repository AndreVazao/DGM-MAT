# DGM-MAT — Aceitação Windows 10 + APK Android + Cockpit

**Data:** 2026-11-08  
**PR backend:** #285  
**Objetivo:** validar ligação real entre backend no PC, cockpit local e APK Android, com chat persistente e pesquisa de histórico. Este runbook é um procedimento futuro; **não significa que a aceitação já foi executada**.

## 0. Regras de segurança

- Não apagar instalações, bases de dados, credenciais, worktrees, logs ou backups.
- Não iniciar duas instâncias do DGM-MAT. Se `127.0.0.1:8181/health` responder, identificar a instância antes de fazer qualquer atualização.
- Não alterar flags de providers, AutoHelp ou autonomia durante a aceitação básica.
- Não introduzir passwords, cookies, tokens ou conteúdo confidencial nos prompts de teste.
- Não guardar API keys de providers no CredentialVault atual; a master key ainda precisa de proteção DPAPI/Windows Credential Manager.
- Se aparecer 401/403 inesperado, CAPTCHA, quota, erro de provider ou divergência de UI, parar e registar evidência; não contornar gates.
- O chat só é considerado LLM real se `ai_ready=true` e uma resposta do motor gratuito confirmado for observada. API saudável com `status=degraded` não é ChatGPT.

## 1. Artefactos de teste

### Backend Windows

- Repositório: `AndreVazao/DGM-MAT`.
- Execução Windows Build #329: https://github.com/AndreVazao/DGM-MAT/actions/runs/42511688188
- Artefacto: `DGM-MAT-Windows-3.12-aeb3a5a`.
- Download: https://github.com/AndreVazao/DGM-MAT/actions/runs/42511688188/artifacts/13629467310
- SHA-256 do ZIP exterior GitHub: `e128bb25cb51d5b2e629477f65f6c3d9b571b09bffd826a4009fa5a1e83129ba`.
- Tamanho: 111,221,888 bytes. Expira: 2027-02-06 18:46:50 UTC.
- O SHA-256 exterior não é o hash do EXE. Depois de extrair o artefacto exterior, validar o ZIP de distribuição `DGM-MAT-Windows-3.12-dca47d0.zip` pelo respetivo `.sha256`, e validar `package\DGM-MAT.exe` pelo sidecar `publish\DGM-MAT.exe.sha256`.

Comandos de verificação (executar apenas na pasta extraída):
```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath ".\DGM-MAT-Windows-3.12-dca47d0.zip"
Get-Content -LiteralPath ".\DGM-MAT-Windows-3.12-dca47d0.zip.sha256"
Get-Content -LiteralPath ".\publish\DGM-MAT.exe.sha256"
Get-FileHash -Algorithm SHA256 -LiteralPath ".\package\DGM-MAT.exe"
```

Se faltar um sidecar, o nome não corresponder ou qualquer digest divergir, parar. Não instalar.

O pacote inclui `package\scripts\install_windows_update.ps1` e `package\scripts\rollback_windows_update.ps1`. O instalador exige o hash esperado do EXE, recusa atualizar com runtime ativo e preserva backup. Confirmar sempre os caminhos reais antes de o invocar.

### APK Android

- Mobile PR #5 / Build #3: https://github.com/AndreVazao/DGM-MAT-Mobile/actions/runs/42511127144
- Artefacto: `DGM-MAT-Mobile-Android-APK-f5d81a157f585ab88a0cce8cb7511a60778f599c`.
- Download: https://github.com/AndreVazao/DGM-MAT-Mobile/actions/runs/42511127144/artifacts/13629676802
- ZIP exterior: 3,710,225 bytes; SHA-256 `056540c75ba52b0fe1f9411091c9052e3482dfef9019c2ccab4b15cc8b62fe8e`.
- APK: SHA-256 `da1917ad66c9392e92f6ee56f5ed3582c3e868b65ae449a8afcdf196ac6c87d3`.
- Package ID confirmado: `com.andrevazao.dgmmatmobile`.
- Expira: 2026-12-08 18:41:42 UTC.

Depois de verificar o ZIP exterior e o sidecar incluído:
```powershell
adb devices
adb install -r .\DGM-MAT-Mobile-debug.apk
adb reverse tcp:8181 tcp:8181
```
Só usar `adb reverse` quando o telemóvel está ligado por USB ao PC. Para ligação remota, usar o mecanismo Tailscale/rendezvous já configurado.

## 2. Pré-verificação Windows (read-only)

1. Confirmar Windows 10, espaço livre, Chrome e diretórios DGM-MAT existentes.
2. Verificar o runtime:
```powershell
Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 http://127.0.0.1:8181/health
```
3. Se responder HTTP 200, não iniciar outra instância nem instalar sobre a execução ativa.
4. Confirmar os dois checkouts irmãos:
   - PC cockpit: `C:\\ProgramasGodMode\\DGM-Cockpit-Frontend`; o backend procura esta pasta por defeito e serve-a em `/cockpit/`.
   - Mobile web/PWA: `C:\\ProgramasGodMode\\DGM-MAT-Mobile\\web`; o backend procura a pasta `DGM-MAT-Mobile\\web` por defeito e serve-a em `/app/`.
   O backend resolve agora a raiz dos repositórios irmãos tanto em execução Python como no EXE PyInstaller one-file: no EXE instalado, usa a localização real de `sys.executable` (`...\\DGM-MAT\\installed\\DGM-MAT.exe`) em vez do diretório temporário `_MEIPASS`. Testes cobrem os dois modos e os overrides. Se algum checkout estiver noutro local, definir `DGM_PC_COCKPIT_PATH` (pasta raiz do cockpit) e/ou `DGM_MOBILE_UI_PATH` (pasta `web` da app mobile) para caminhos absolutos antes de iniciar o backend. Nunca apontar `DGM_MOBILE_UI_PATH` para o cockpit PC.
5. Confirmar que o cockpit está montado em:
   - `http://127.0.0.1:8181/cockpit/`
   - `http://localhost:8181/cockpit/`
6. Confirmar que existe o bootstrap local em `%LOCALAPPDATA%\DGM-MAT\security\bootstrap.token`. Não copiar o conteúdo para logs, mensagens ou screenshots.

## 3. Ligação do cockpit PC

1. Abrir `http://127.0.0.1:8181/cockpit/`.
2. No popup de ligação, selecionar o `bootstrap.token` ou colar a credencial no campo password.
3. Confirmar ligação e que o campo bootstrap é limpo após o pedido de sessão.
4. Verificar que só a sessão temporária fica em `sessionStorage`; bootstrap não fica guardado no browser.
5. Criar uma conversa, enviar uma mensagem neutra como `Olá. Confirma que recebeste esta mensagem e responde apenas “ligação recebida”.`
6. Confirmar resposta persistida, thread visível e ausência de missão criada.
7. Pesquisar um termo da thread; selecionar resultado e confirmar que abre a conversa original.

## 4. Pesquisa de arquivos importados

1. Usar um termo que se saiba existir num arquivo ChatGPT previamente importado para o Recovery Ledger.
2. Confirmar que aparecem resultados de threads locais e arquivos importados.
3. Abrir um resultado ChatGPT.
4. Confirmar título, mensagens, indicação de SHA-256 verificado e modo só de leitura.
5. O visualizador mostra no máximo 50 mensagens por página nesta versão.
6. Fontes de outros providers que só tenham metadados aparecem desativadas; não assumir que têm texto pesquisável.
7. Se não existir arquivo importado, ausência de resultados é normal; não significa falha do chat local.

## 5. Emparelhamento APK

1. No PC, abrir localmente `http://127.0.0.1:8181/auth/pairing-code` e obter o código de uso único.
2. No APK, abrir o painel de ligação/USB e introduzir o código no campo password.
3. Confirmar pairing e sessão temporária.
4. A sessão mobile deve receber exatamente os scopes:
   - `local-client`
   - `mobile-read`
   - `mobile-chat`
   - `mobile-maintenance`
5. A sessão mobile **não pode receber `operator`**.
6. Confirmar que o APK mostra API disponível e o estado real do motor de IA, sem dizer que o modelo está pronto quando não está.

## 6. Testes APK

1. Criar nova conversa e enviar uma mensagem neutra.
2. Confirmar que a resposta do backend aparece e que a thread fica persistida.
3. Pesquisar a mesma mensagem no histórico local e reabrir a thread.
4. Pesquisar um termo de um arquivo ChatGPT importado e abrir o resultado read-only.
5. Confirmar que fontes só com metadados de outros providers não podem ser abertas como se tivessem mensagens.
6. Deixar a sessão expirar ou revogá-la em ambiente de teste; confirmar que o APK limpa a sessão e reabre o diálogo de pairing.
7. Confirmar que, se o PC não for encontrado, a mensagem não é apresentada como enviada; permanece local/pendente segundo o comportamento existente.

## 7. Verificação de autoridade

O backend já tem regressão TestClient para pairing, chat, persistência, pesquisa e negação de operações de operador. Se for feita uma verificação manual adicional com um token de sessão mobile:
- `GET /mobile/threads` e `GET /mobile/threads/search` devem funcionar.
- `GET /recovery/search` e `GET /recovery/sources/{provider}/{source_id}/messages` devem funcionar para fontes autorizadas.
- `GET /governance/commands/catalog` deve devolver 403.
- `POST /runtime/missions` deve devolver 403.

Não copiar token de sessão para logs ou screenshots.

## 8. Estado do motor de IA

- `api_status=ready` significa que a API respondeu; não significa que existe LLM.
- `ai_ready=true` e `ai_mode` identificam um motor disponível.
- Se `status=degraded` / `ai_ready=false`, validar apenas a API, persistência e histórico. Não declarar chatGPT-like.
- Para testar LLM, o operador tem de confirmar explicitamente um provider realmente gratuito, credenciais e quota. Só então ativar as flags de opt-in necessárias e verificar `check_health()`.
- Não usar APIs pagas nem introduzir API keys no CredentialVault atual.
- A consulta browser a ChatGPT/Grok/Gemini/DeepSeek/Qwen com aprovação manual é tratada separadamente na PR #283; não está automaticamente ligada a cada mensagem do chat.

## 9. Rollback e evidência

- Não apagar o backup gerado pelo instalador.
- Se o update Windows causar regressão, parar o runtime e usar `rollback_windows_update.ps1` com o manifesto real da atualização correspondente.
- Para APK, manter o APK anterior até o novo estar instalado e validado; `adb install -r` preserva dados da aplicação, mas não substitui backup de dados importantes.
- Registar apenas: versões, status HTTP, nomes de artefactos, hashes, estados, timestamps e mensagens de erro redigidas.
- Não registar bootstrap token, bearer session, API keys, cookies, transcripts privados ou conteúdo pessoal.

## 10. Critério de conclusão

A aceitação só fica concluída quando:
- backend responde e não há instância duplicada;
- cockpit autentica por bootstrap e comunica com o cérebro;
- chat cria resposta e persiste a conversa;
- pesquisa local e pesquisa de arquivo importado funcionam;
- APK emparelha, envia, recebe e pesquisa;
- sessão mobile não tem `operator`;
- motor gratuito confirmado responde realmente, se a aceitação pretender validar LLM;
- nenhum dado existente foi apagado nem qualquer flag foi ativada sem aprovação.

**Estado atual:** todos estes passos locais estão pendentes. CI verde e artefactos publicados não substituem a aceitação no Windows 10/Motorola.
