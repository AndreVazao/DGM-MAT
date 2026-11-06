# DGM-MAT Conversation Archive — Chrome Extension

## Objetivo

Esta primeira fase inventaria URLs de conversas presentes no histórico local do Chrome e captura a conversa atualmente aberta em ChatGPT, Grok, Gemini ou Claude.

## Privacidade e segurança

- Funciona localmente no perfil Chrome utilizado pelo André.
- Consulta o histórico para filtrar apenas URLs dos quatro providers suportados.
- Lê o DOM da página apenas quando o utilizador carrega em **Capturar conversa aberta**.
- Não lê cookies, palavras-passe, tokens, localStorage, sessionStorage ou bases de autenticação.
- Não envia conversas para servidores externos.
- Guarda JSON em `%USERPROFILE%\Downloads\DGM-MAT-Conversation-Archive\`.
- Não renomeia, apaga ou modifica conversas nos providers.
- Se não reconhecer os nós de mensagens, assinala a captura como parcial e não inventa autores.

## Instalação

1. Abrir `chrome://extensions` no perfil Chrome já utilizado.
2. Ativar **Modo de programador**.
3. Selecionar **Carregar expandida**.
4. Escolher a pasta `C:\ProgramasGodMode\DGM-MAT\extensions\dgm-mat-conversation-archive`.
5. Fixar a extensão, se desejado.

O Chrome apresentará a permissão de histórico. É necessária para inventariar URLs e o código filtra os resultados para ChatGPT, Grok, Gemini e Claude.

## Utilização

- **Inventariar histórico das IAs** cria um JSON das conversas encontradas no histórico local. A cobertura fica explicitamente marcada como parcial.
- Abrir uma conversa individual no provider e selecionar **Capturar conversa aberta** para guardar as mensagens visíveis em JSON.

## Limitações atuais

Esta ainda não é uma recolha integral do histórico existente nas contas dos providers. Não percorre automaticamente todas as conversas da barra lateral. Primeiro precisamos de medir a cobertura real e validar os seletores DOM de cada provider antes de ativar a captura em lote.

## Ficheiros

- `inventory-*.json`
- `capture-*.json`

Ambos os formatos são compatíveis com o importador de conversas do DGM-MAT.
