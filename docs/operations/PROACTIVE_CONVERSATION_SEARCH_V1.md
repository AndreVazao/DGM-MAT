# Pesquisa proativa de conversas — v1

## Objetivo

Permitir que o operador peça no chat, em linguagem natural, para procurar conversas de um fornecedor e receber o resultado no próprio chat, sem abrir o painel de recuperação.

Exemplo: "busca conversas do ChatGPT sobre o projeto VAZAO EVSE"

## Fluxo implementado

1. O interpretador reconhece a intenção conversation_search.
2. O router classifica-a como pesquisa local, read-only e elegível para autoexecução.
3. O MissionEngine envia a tarefa para o handler específico, sem pedir aprovação manual.
4. A pesquisa consulta o índice e os arquivos de conversas previamente importados para o Recovery Archive.
5. Os resultados são deduplicados por fornecedor/ID, associados aos termos encontrados e preservam URL, data, estado de captura e excerto.
6. É criado um relatório Markdown local, escrito atomicamente em %USERPROFILE%\\.dgm-mat\\reports\\conversation-search (ou no diretório configurado por DGM_CONVERSATION_SEARCH_REPORT_DIR).
7. O chat apresenta a contagem, os termos pesquisados, o caminho do relatório e uma pré-visualização dos resultados.

## Limites explícitos

- Esta versão pesquisa arquivos locais que já foram importados. Não inicia sessão nas contas dos fornecedores.
- Não lê cookies, tokens, palavras-passe, bases de autenticação ou armazenamento privado do browser.
- Não percorre automaticamente todas as conversas da barra lateral dos fornecedores.
- O histórico integral não é considerado verificado; a cobertura fica sempre marcada como parcial.
- A ausência de resultados significa apenas que não houve correspondência no arquivo importado disponível.
- A pesquisa é limitada a três termos, 15 resultados por termo e aos limites de leitura já aplicados pelo Recovery API.
- Os relatórios são derivados e não alteram nem eliminam os arquivos originais.

## Próxima fase

Ligar a captura autorizada do Chrome ao inbox local do DGM-MAT, para que o operador possa pedir a pesquisa no chat e o sistema consiga verificar automaticamente se existem novos arquivos/capturas importáveis. A captura em lote continuará limitada ao conteúdo visível e aos controlos normais da interface; não haverá leitura de credenciais nem evasão de proteções do fornecedor.

A fase seguinte deve acrescentar uma apresentação visual de resultados no chat (resumo, fontes e destino) sem reintroduzir painéis técnicos.
