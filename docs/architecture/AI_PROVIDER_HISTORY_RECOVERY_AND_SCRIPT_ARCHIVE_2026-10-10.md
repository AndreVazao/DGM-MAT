# DGM-MAT — Arquitetura de recuperação de contexto e utilização de IAs Web
Data: 2026-10-10
Estado: decisão arquitetural aprovada para orientar implementação; não é declaração de funcionalidade já entregue.

## Objetivo de produto
Recuperar contexto e artefactos produzidos nas conversas históricas de ChatGPT, Gemini, Grok e outras ferramentas autorizadas; organizar conversas por projeto; recuperar scripts antigos mesmo quando estão acima no histórico; comparar e consolidar versões; encaminhar artefactos para repositórios e memória persistente.

## Ordem de preferência para recuperar dados
1. Exportação oficial do utilizador ou mecanismo oficial de exportação/importação, quando disponível. Importar localmente e indexar sem credenciais.
2. Interface Web autenticada, através de uma sessão de browser dedicada e governada, para pesquisa, navegação por conversas e extração de mensagens/código autorizados.
3. Automação visual Windows + OCR para páginas/controles que não possam ser lidos de forma robusta pelo DOM.
4. Nunca depender de scraping frágil como única fonte de verdade; manter origem, URL/identificador, data conhecida, fornecedor e hash do artefacto quando disponíveis.

## Arquitetura de sessão
- Não anexar o DGM-MAT ao perfil Chrome pessoal `Default` como método normal e não copiar cookies, Local Storage, tokens de sessão ou credenciais desse perfil.
- Criar um perfil de browser dedicado ao DGM-MAT, persistente no disco local com ACL restrita ao utilizador e SYSTEM, fora dos repositórios Git, sincronização cloud e backups não cifrados.
- Primeiro arranque visível a partir do cockpit: botão `Ligar fornecedor` abre a página oficial num browser visível. O utilizador autentica-se manualmente (Google, GitHub ou login próprio). Não automatizar CAPTCHA/MFA.
- Depois de a sessão ser confirmada pelo fornecedor, permitir operação headless apenas se o fornecedor e a sessão funcionarem de forma estável nesse modo. Se houver bloqueio, pedir ao utilizador para voltar ao modo visível e concluir manualmente.
- Um único proprietário de browser/profile de cada vez; lock file/processo para impedir duas instâncias simultâneas a corromper perfil. Não abrir a mesma pasta de perfil no Chrome normal e no Playwright ao mesmo tempo.
- Não guardar palavras-passe reutilizadas numa nova vault própria do DGM-MAT. Preferir sessão do perfil dedicado e autenticação manual. Se uma credencial tiver de ser guardada para uma integração suportada, usar Windows Credential Manager/DPAPI ou vault local cifrada com chave protegida pelo SO; nunca texto simples, repositório, logs, prompts, eventos ou memória.
- Não pedir nem registar uma senha única reutilizada em vários serviços. Recomendar separação de passwords e MFA como melhoria de segurança, sem bloquear a recuperação de contexto.

## Modelo de dados e memória
- Criar catálogo local de conversas com fornecedor, título, URL/ID se disponível, datas disponíveis, estado de importação, etiquetas/projetos e última posição percorrida.
- Criar índice de mensagens e artefactos pesquisável localmente; conteúdo bruto fica no armazenamento privado local, com limites de acesso e retenção configuráveis.
- Detetar blocos de código, linguagem provável, nome/path mencionado, projeto candidato, contexto adjacente, hash, versões duplicadas e relações entre artefactos.
- Guardar proveniência e excertos de contexto para não atribuir scripts a projetos errados.
- Não executar scripts recuperados automaticamente. Importar primeiro para quarentena/revisão, comparar com a base atual, correr análise estática/testes e pedir aprovação antes de aplicar alterações.
- Deduplicar sem apagar originais. Nunca substituir um script validado por uma versão histórica apenas porque parece maior.

## Navegação de históricos
- Preferir pesquisa da própria plataforma, lista de conversas e seletores DOM estáveis.
- Quando for necessário subir no histórico, usar scroll incremental, verificar que carregaram mensagens anteriores, guardar checkpoint de conversa/posição e continuar com limites por sessão.
- Extrair páginas por lotes pequenos, com pausa/backoff e limites de taxa; retomar de checkpoints em vez de reiniciar do início.
- Não contornar paywalls, controlos de acesso, CAPTCHA/MFA, limites do fornecedor ou políticas da plataforma.
- Marcar claramente `complete`, `partial`, `blocked_login`, `rate_limited`, `failed` e `needs_user`; nunca dizer que o arquivo está completo se apenas se leu a parte visível.

## Cockpit PC
Criar área `Fontes de IA` com um cartão por fornecedor:
- estado: não ligado / login necessário / ligado / sessão expirada / importação parcial / erro;
- botão `Ligar/Reautenticar` para abrir browser visível;
- botão `Testar acesso` que apenas lê metadados não sensíveis;
- botão `Importar histórico` com âmbito e pré-visualização;
- botão `Pausar` e `Terminar sessão`;
- pedidos de intervenção pendentes com motivo, URL/domínio e ação a concluir, sem mostrar segredos.
Não expor o browser remoto à rede. API continua loopback até autenticação global estar carregada e testada em runtime.

## Cockpit móvel
O telemóvel nunca recebe passwords, cookies, tokens de sessão ou códigos MFA através do canal de missões. Recebe um pedido de intervenção com fornecedor, motivo e instrução para abrir/confirmar no PC, ou link oficial seguro quando apropriado. O utilizador pode responder com decisão/contexto não sensível. Segredos são introduzidos diretamente na página oficial no PC, não copiados para o chat do DGM-MAT.

## Perfis de execução e memória
- Perfil leve: uma sessão de browser por fornecedor em uso, sem paralelismo de múltiplos browsers, lotes pequenos, sem OCR salvo necessidade.
- Perfil visual: browser visível para login, MFA, CAPTCHA, diagnósticos e confirmação.
- Perfil headless: apenas depois de login manual e teste de estabilidade, com perfil dedicado e limites de memória.
- Fechar a janela do cockpit não termina a missão nem o Core; pausas e encerramentos de browser são ações explícitas e auditadas.

## Fases de implementação
A. Inventário e contrato de fornecedor: verificar URLs, login, pesquisa, paginação, exportação oficial e limites de cada plataforma.
B. Sessão dedicada: gestão de perfil, lock, estado, iniciar visível e fechar/recuperar com segurança; sem endpoints públicos.
C. API local autenticada: operações tipadas com permissões, limites de leitura, cancelamento e logs sem conteúdo sensível.
D. Importação incremental: metadados, pesquisa, scroll, extração, checkpoints, retomada e estado parcial.
E. Indexação: catálogo por fornecedor/projeto, pesquisa full-text local, extração de código, proveniência e deduplicação.
F. Consolidação: comparar artefactos com repositórios, gerar proposta de alteração, testes e aprovação humana.
G. Headless seletivo e mobile intervention: só após E2E local estável.

## Critérios de aceitação antes de declarar pronto
- Login manual funciona sem o DGM-MAT ler/guardar a password.
- Sessão persistente do perfil dedicado sobrevive ao reinício do browser, sem exportar cookies.
- Teste confirma expiração e pede reautenticação sem loops.
- Importação pode retomar sem duplicar mensagens/artefactos.
- Scroll confirma que conteúdo anterior foi carregado antes de avançar.
- Cada artefacto preserva fornecedor/origem/contexto e nunca é executado automaticamente.
- Testes confirmam que tokens, passwords, códigos MFA e conteúdo sensível não aparecem em logs, eventos, URLs ou memória geral.
- O cockpit mostra claramente importação parcial/bloqueada e não inventa completude.
- Teste de carga confirma que apenas um browser ativo no PC de baixo consumo é suficiente para o primeiro fornecedor.

## Segurança e restrições
Não automatizar CAPTCHA/MFA, pagamentos, alterações de segurança ou ações irreversíveis. Não contornar limites de fornecedor. Não expor a API à LAN/Tailscale antes da validação de auth em runtime e pairing. Não reiniciar o Core com missões ativas sem janela de manutenção controlada.

## Estado atual conhecido
- Existe `GovernedBrowserSession` Playwright efémera com allowlist, navegação, leitura, click, fill limitado, scroll, screenshot e Tesseract OCR.
- O contexto atual é não persistente e não reutiliza o login do Chrome `Default`.
- Métodos de browser existem no MissionEngine, mas não foi encontrada API dedicada que os exponha ao cockpit.
- Portanto, esta arquitetura é plano, não implementação concluída.
