# DGM-MAT — Auditoria inicial de aplicações Web e automação visual
Data: 2026-10-10
Estado: investigação somente leitura; sem alteração de código ou configuração de segurança.

## Objetivo
Determinar se o DGM-MAT pode utilizar aplicações de IA já instaladas no ambiente Windows através de automação Web/visual, em vez de depender exclusivamente de APIs pagas.

## Evidência observada no PC
- Atalhos do ambiente de trabalho para ChatGPT, Grok e Gemini apontam para `chrome_proxy.exe` com IDs de aplicações Web do Chrome e perfil `Default`.
- Claude tem atalho para `C:\\ProgramasGodMode\\DGM-MAT-Claude-Agent.cmd`.
- Perplexity está instalado como aplicação própria.
- Também existem atalhos para Jules, Canva e Firebase Studio.
- Tesseract OCR 5.4.0 está instalado em `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`; idiomas instalados: `eng`, `osd`, `por`.
- Python 3.12 tem os módulos Playwright e pywinauto disponíveis. Não foram encontrados pytesseract, pyautogui ou Selenium no ambiente Python consultado; pytesseract não é obrigatório porque o serviço chama o executável Tesseract diretamente.

## Capacidades já presentes no código
`core/providers/browser/governed_browser_session.py` implementa sessão Playwright efémera com allowlist explícita de hosts HTTPS, navegação, leitura do texto da página, cliques, preenchimento de campos não sensíveis, scroll, captura de ecrã e OCR local.
`core/autonomy/mission_engine.py` expõe métodos de motor para iniciar/obter/fechar estas sessões e delegar ações.

## Limitações confirmadas
1. A sessão Playwright cria um contexto novo e não persistente; não herda automaticamente cookies, armazenamento ou autenticação do perfil Chrome `Default` usado pelos atalhos.
2. Não foram encontrados endpoints HTTP/WS dedicados para expor estes métodos do browser ao cockpit/API. A capacidade do motor não equivale ainda a uma ferramenta operacional acessível pela interface.
3. A política atual exige hosts HTTPS explicitamente autorizados, bloqueia IPs privados/loopback e não preenche campos de credenciais/sensíveis. Isto é uma barreira de segurança deliberada, mas significa que a compatibilidade com fluxos de login, subdomínios e fornecedores ainda precisa de desenho e testes.
4. OCR consegue ler ecrãs, mas por si só não fornece controlo robusto, deteção de estado, confirmação de envio nem recuperação de falhas.
5. A inspeção de interface com pywinauto não foi validada ponta a ponta nesta auditoria. Um ensaio exploratório de abertura da aplicação ChatGPT iniciou processos Chrome, mas não foi enviada nenhuma mensagem nem efetuada nenhuma ação na conta.

## Conclusão
É tecnicamente viável construir um adaptador de utilização de aplicações Web existentes, sem API paga, mas o DGM-MAT ainda não está pronto para operar essas aplicações autenticadas de forma fiável. O suporte atual é uma base de browser governado, não uma integração concluída com as sessões instaladas.

## Próximo plano recomendado
1. Criar uma capacidade explícita `provider-ui`/browser com endpoints protegidos pela autenticação global e permissões de missão.
2. Preferir uma instância/perfil de browser dedicado ao DGM-MAT, aberto em modo visível, com login manual feito pelo utilizador. Não extrair cookies, tokens ou credenciais do perfil pessoal `Default`.
3. Autorizar apenas domínios necessários por fornecedor; tratar redirects/subdomínios com allowlist documentada, sem enfraquecer a proteção de rede.
4. Fluxo de teste não destrutivo: abrir a página, verificar título/estado, ler texto não sensível, preencher apenas o compositor de mensagem, pedir confirmação humana antes de enviar, e confirmar a resposta recebida.
5. Reservar pywinauto/OCR como adaptador alternativo para aplicações sem DOM acessível. Nunca automatizar CAPTCHA/MFA, pagamentos, mudanças de segurança ou ações irreversíveis.
6. Não expor a API à LAN/Tailscale até a autenticação global estar ativa no processo em execução e os testes live estarem concluídos. Não reiniciar o Core enquanto existirem missões ativas sem janela de manutenção controlada.

## Integridade
Esta auditoria não modificou o código do motor, as sessões do utilizador, as credenciais, o perfil Chrome, as regras de rede nem o processo Core.
