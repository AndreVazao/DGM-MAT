# DGM-MAT — Acesso multi-dispositivo, descoberta automática e dashboards

Estado: DECISÃO ARQUITETURAL / IMPLEMENTAÇÃO POR FASES
Data: 2026-10-10

## 1. Objetivo e contexto de utilização

O utilizador trabalha frequentemente na estrada, conduzindo camiões em rotas pela Europa. Precisa de aceder ao DGM-MAT pelo telefone sem saber nem escrever IPs, mesmo quando está fora de casa e do país. Em casa, pretende um dashboard completo no PC e a possibilidade de instalar apenas o dashboard noutros PCs/portáteis, ligando-os ao cérebro que pode estar numa torre discreta a funcionar como servidor.

## 2. Regra central: cérebro no servidor, clientes substituíveis

- O **DGM-MAT Core** corre no PC servidor em background, como serviço/processo supervisionado, sem depender de janelas de terminal abertas nem do dashboard estar iniciado.
- O servidor mantém estado de missões, memória operacional, agentes, scheduler, filas, checkpoints, ferramentas, logs operacionais protegidos e fonte de verdade.
- O telefone é um **cockpit móvel leve** para chat, conversas, seleção de projeto, seleção de provedor, envio de pedidos, notificações e intervenções humanas.
- O dashboard desktop/web é um **cockpit avançado** com gestão de missões, delegações, projetos, ficheiros, ferramentas, estado de saúde, diagnósticos, aprovações, configuração, logs e controlos de execução.
- Um dashboard instalado noutro PC é apenas um cliente. Não deve duplicar nem criar outro cérebro, nem exigir que o runtime principal seja executado nesse cliente.
- A perda de ligação de qualquer cliente não pode parar o servidor nem apagar ou duplicar missões.

## 3. Descoberta automática sem escrever IPs

A experiência pretendida é: abrir o cockpit, autenticar-se, encontrar o servidor autorizado, estabelecer ligação e sincronizar o estado. Não pedir ao utilizador para memorizar endereços IP.

### 3.1 Descoberta em casa

1. O dashboard procura um servidor DGM-MAT previamente emparelhado na rede local através de descoberta local suportada (por exemplo, mDNS/DNS-SD) e/ou um registo de servidor conhecido.
2. O servidor anuncia apenas informação mínima de descoberta; nunca transmite segredos nem permite executar comandos só por estar na mesma LAN.
3. O cliente valida a identidade do servidor e a sessão autenticada antes de mostrar dados ou enviar comandos.
4. Se a descoberta local falhar, mostrar um estado compreensível e permitir nova tentativa/reemparelhamento autorizado, sem pedir ao utilizador que escreva IPs como procedimento normal.

### 3.2 Descoberta fora de casa / na Europa

A solução deve combinar **Tailscale para conectividade privada** com um **serviço de rendezvous/descoberta**, potencialmente alojado no Vercel, para ajudar os clientes autenticados a encontrar o servidor correto.

Fluxo pretendido:
1. O servidor DGM-MAT inicia uma ligação de saída autenticada ao serviço de rendezvous e publica heartbeat, identidade opaca do servidor, versão/protocolo e estado de disponibilidade mínimo.
2. O telefone ou portátil autentica-se com a identidade do utilizador/dispositivo e pede os servidores que já foram emparelhados.
3. O rendezvous devolve metadados mínimos de ligação, nunca passwords, tokens de acesso reutilizáveis ou dados das missões.
4. Quando o cliente e o servidor estão no mesmo tailnet, o cliente usa Tailscale para estabelecer ligação privada autenticada e encriptada. O utilizador não escreve IPs manualmente.
5. O cliente verifica identidade do servidor, autorização, versão e estado da sessão antes de sincronizar pedidos, conversas ou notificações.
6. Quando não existe conectividade privada, a app explica que o servidor está inacessível e mantém o trabalho local em execução. Uma ligação de relay externa só pode ser acrescentada numa fase própria, com autenticação ponta-a-ponta, limites de acesso, análise de custos e threat model; não se deve abrir automaticamente uma porta pública como fallback.

**Limite importante:** o Vercel é um possível plano de descoberta/rendezvous, não um túnel mágico para a rede doméstica. Um serviço alojado no Vercel não consegue, por si só, tornar um PC atrás de NAT diretamente acessível. O PC tem de iniciar uma ligação de saída, e a conectividade real tem de ser fornecida por Tailscale ou por um relay seguro deliberadamente concebido. A integração concreta deve ser validada antes de ser prometida como funcional.

## 4. Papel do Tailscale

- Usar a rede privada Tailscale para ligar servidor e dispositivos autorizados, incluindo quando o utilizador está fora de Portugal.
- O servidor não deve exigir IPs Tailscale escritos manualmente no uso normal; os clientes recorrem à descoberta/rendezvous e à identidade do dispositivo.
- Confirmar se o telefone e o portátil estão autenticados no tailnet certo e se as políticas permitem a ligação.
- Restringir ACLs/grants ao servidor e às portas necessárias; não tratar pertença à rede como substituto da autenticação da aplicação.
- Não expor a API diretamente à Internet nem ativar Tailscale Funnel/publicação pública como atalho.
- Se o cliente estiver offline, o Core continua o trabalho e conserva os pedidos pendentes localmente.

## 5. Cockpit móvel: simples e contínuo

A experiência móvel deve ser semelhante a uma conversa ChatGPT, otimizada para uso rápido:
- lista de conversas e criação de conversa;
- seletor de projeto ativo;
- seletor de provedor/modelo permitido pela política FREE-ONLY / PAID-DENY;
- caixa de mensagem para pedidos e contexto;
- estado das missões e notificações;
- pop-ups/painéis de intervenção humana para perguntas, aprovações, consentimento e instruções;
- para login, CAPTCHA/MFA e passwords, canal temporário seguro e vinculado à missão/etapa/origem, sem inserir segredos em prompts, logs, memória ou bus genérico;
- fila de notificações e pedidos pendentes quando o telefone esteve offline, sem duplicar respostas;
- estado claro: servidor online/offline, sincronização atualizada/pendente e última confirmação de contacto.

A app móvel não deve tentar reproduzir todos os controlos avançados do dashboard desktop. Deve privilegiar comunicação, seleção rápida e intervenção segura.

## 6. Dashboard desktop avançado

O dashboard completo deve poder ser aberto no próprio servidor ou instalado como cliente noutro PC/portátil. Deve incluir, por módulos:
- chat e histórico de conversas;
- projetos e repositórios;
- provedor/modelo selecionado e limites/custos claramente apresentados;
- quadro de missões, delegações, agentes, dependências e checkpoints;
- tarefas pendentes de intervenção humana;
- saúde do Core, recursos de hardware, serviços e conectores;
- gestão de ficheiros e resultados de investigação;
- aprovações, políticas, auditoria e controlos de pausa/retoma;
- logs e diagnósticos com segredos redigidos;
- configurações e estado de sincronização/dispositivos.

O dashboard não pode ser um requisito para o Core continuar a trabalhar. Fechar o dashboard não encerra missões nem serviços. Instalar o dashboard noutro PC não instala automaticamente outro Core, salvo escolha explícita do utilizador.

## 7. Serviço em background e arranque

O Core deve arrancar de forma supervisionada, sem janelas de consola visíveis, com logs rotativos e estado de saúde verificável. O dashboard é iniciado separadamente e liga-se ao Core. O instalador deve distinguir claramente os componentes Core/Servidor, Dashboard e Cockpit móvel. O encerramento do dashboard não pode parar o Core; a paragem do Core deve exigir uma ação administrativa deliberada ou política de manutenção.

A instalação como serviço Windows e as opções de reinício devem ser introduzidas com cuidado e testadas para não criar processos duplicados, ciclos de arranque ou perda de dados. A experiência deve incluir um controlo explícito para parar/reiniciar o Core.

## 8. Sincronização e continuidade

- A fonte de verdade reside no servidor/PC Core.
- Clientes sincronizam estado e mensagens com identificadores estáveis, cursores/checkpoints e deduplicação.
- Offline não significa perder pedidos: o servidor continua trabalho independente; intervenções humanas aguardam na fila persistente.
- Ao reconectar, autenticar primeiro, reconciliar estado e só depois permitir ações.
- Cada resposta humana fica vinculada a dispositivo, utilizador, pedido, missão, etapa, origem e prazo; uso único, revogação e proteção contra replay.
- Verificar o resultado real de qualquer intervenção antes de retomar; não repetir automaticamente ações externas não idempotentes de resultado incerto.

## 9. Segurança obrigatória antes de acesso remoto

A auditoria preliminar identificou rotas HTTP e WebSockets que não parecem protegidas globalmente por autenticação e um cliente móvel que não envia sessão autenticada. Por isso:
- manter a API limitada a loopback enquanto a autenticação global e migração de clientes não estiverem completas;
- proteger HTTP, WebSockets, rendezvous, emparelhamento e intervenções;
- implementar pairing explícito, identidade por dispositivo, tokens curtos/rotativos ou mecanismo equivalente, scopes mínimos, expiração e revogação;
- proteger contra CSRF, replay, origem não autorizada, brute force e abuso de notificações;
- não confiar apenas em CORS, endereço IP, Tailscale ou ocultação de URLs;
- nunca guardar ou transmitir segredos de utilizador em texto simples no rendezvous;
- não publicar endpoint remoto antes de testes negativos e validação ponta-a-ponta.

## 10. Fases de implementação

1. **Especificação e inventário:** documentar Core, clientes, APIs atuais, portas, runtime e dependências; preservar o funcionamento local.
2. **Separação Core/Dashboard:** garantir processo em background independente e dashboard que pode fechar sem interromper missões.
3. **Segurança:** autenticação global HTTP/WebSocket, pairing, scopes, revogação, auditoria e migração de clientes; manter loopback até passar testes.
4. **Cockpit móvel:** chat, projetos, provedores, notificações, fila offline e intervenção humana segura.
5. **Descoberta LAN:** servidor emparelhado encontrado sem introdução manual de IP.
6. **Tailscale:** conectividade privada multi-dispositivo e validação real fora da LAN.
7. **Rendezvous Vercel:** registo/heartbeat de saída do servidor, descoberta autenticada, expiração de presença e recuperação de ligação; não transportar segredos ou conteúdo das missões.
8. **Dashboard noutros PCs:** instalação do cliente, seleção automática do Core emparelhado e modo avançado.
9. **Teste de viagem:** telefone fora da rede doméstica, servidor em background, suspensão/retoma de rede, reconexão, pedidos pendentes e intervenção humana.

## 11. Critérios de aceitação

- O utilizador abre o telefone na Europa, autentica-se e encontra o servidor sem escrever IPs.
- O servidor continua a executar tarefas independentes com o telefone offline.
- Uma torre pode alojar o Core sem monitor ou dashboard aberto.
- Um portátil pode executar só o dashboard e comunicar com o Core autorizado na rede doméstica.
- Fechar/reiniciar um cliente não interrompe missões do Core.
- Perder Tailscale/rendezvous resulta em estado offline explícito, nunca numa exposição pública automática.
- A app só mostra/aciona dados depois de autenticação e emparelhamento válidos.
- Os pedidos de intervenção sobrevivem à desconexão e são processados uma única vez.
- Não há segredos nos prompts, logs, memória persistente ou metadados de rendezvous.
- Não se gastam créditos ou dinheiro sem autorização; política FREE-ONLY / PAID-DENY.

## Estado de implementação

Esta é uma decisão arquitetural e um plano de fases, não uma declaração de que a descoberta Vercel, integração Tailscale, dashboard multi-PC, autenticação global ou intervenção móvel já estejam implementados. Cada fase só pode ser marcada concluída após implementação e testes reais. Prioridades: estabilidade > funcionalidades; evidência > pressupostos; controlo manual > automação destrutiva.

Relacionado: `PC_BRAIN_MOBILE_COCKPIT_PARALLEL_DELEGATIONS.md`, `HUMAN_IN_THE_LOOP_HANDOFF.md`, `GOVERNED_BROWSER_AUTOMATION.md`.
