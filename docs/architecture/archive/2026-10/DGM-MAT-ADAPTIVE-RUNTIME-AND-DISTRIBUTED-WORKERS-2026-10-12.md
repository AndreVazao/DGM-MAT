# DGM-MAT — adaptação ao hardware, renderização progressiva e rede de agentes
## Requisitos arquiteturais adicionais — 2026-10-12

**Estado:** requisito conceptual/documental; não implementado nem validado em runtime  
**Branch:** `docs/digital-headquarters-concept-2026-10-12`

## 1. Princípio central: adaptar sem perder identidade

O DGM-MAT é um sistema independente. Mantém a sua própria memória, política, estado canónico, orquestração, validação e auditoria. Ferramentas externas, modelos, runtimes e computadores são capacidades que pode utilizar quando estão disponíveis, não componentes que passam a controlar o cérebro.

O sistema deve adaptar a experiência e a execução aos recursos reais do ambiente, sem exigir que todas as máquinas suportem a configuração máxima. A adaptação tem de ser mensurável, explicável, configurável e reversível.

## 2. Renderização progressiva: uma aplicação, vários níveis

A aplicação deve estar preparada para diferentes modos visuais, com o mesmo modelo de estado e as mesmas funções essenciais:

| Perfil | Representação | Quando escolher |
|---|---|---|
| 3D | Escritório tridimensional, personagens animadas e câmara/interação | Apenas quando a GPU, o navegador, a memória e o desempenho medidos suportarem a experiência com margem |
| 2D avançado | Escritório isométrico ou pixel-art, sprites, animações e salas | Quando 3D não for adequado, mas a renderização 2D tiver desempenho suficiente |
| 2D leve | Planta simplificada, personagens pequenas, movimentos essenciais e painéis compactos | Em hardware modesto ou quando a aplicação precisa de reduzir o consumo |
| Mínimo / acessível | Chat, estados, listas e um boneco muito simples (por exemplo, figura de traços) com animação mínima | Em computadores antigos, modo de poupança, falha gráfica ou preferência explícita do utilizador |
| Sem animação | Chat e interface funcional, sem movimento decorativo | Em modo de acessibilidade, diagnóstico, baixa energia ou degradação de desempenho |

Estes níveis são modos de apresentação do mesmo DGM-MAT, não aplicações independentes nem versões com capacidades de negócio diferentes. Chat, pedidos, memória, segurança e informação de estado devem continuar utilizáveis mesmo quando toda a animação é desligada.

### Seleção de perfil

1. Consultar capacidades disponíveis de forma compatível com o ambiente (browser, canvas/WebGL, memória quando exposta, dimensões e preferências de acessibilidade).
2. Executar um teste curto e representativo de renderização e medir fluidez, tempo de resposta e consumo observável.
3. Selecionar o perfil mais rico que passe os limites definidos, deixando margem para a aplicação principal.
4. Permitir ao utilizador escolher manualmente um perfil e guardar essa preferência.
5. Monitorizar falhas, perda de fluidez e pressão de recursos; reduzir gradualmente o nível se necessário.
6. Permitir regressar a um nível superior depois de novo teste, sem reiniciar ou perder o estado de trabalho.
7. Se não houver evidência suficiente, escolher o perfil leve, não presumir que o dispositivo consegue executar 3D.

A deteção não deve depender de um único número de hardware nem assumir que WebGL disponível significa que 3D é fluido. Os limites de CPU/RAM/GPU devem ser calibrados com medições reais. A aplicação deve oferecer modo automático e escolha manual.

## 3. Separar estado, lógica e apresentação

Arquitetura proposta:

- **Núcleo DGM-MAT:** identidade, política, memória, tarefas, decisões, eventos, validação e auditoria.
- **Capability & Environment Profiler:** inventário limitado de capacidades, limites configurados e medições de desempenho; não recolhe dados pessoais desnecessários.
- **Presentation Adapter:** converte o estado canónico em dados para cada renderizador.
- **Renderers substituíveis:** 3D, 2D avançado, 2D leve e modo mínimo/sem animação.
- **Frontend funcional comum:** chat, pedidos, pesquisa, histórico, acessibilidade e controlos.
- **Event/State API:** contrato comum para o escritório e para outros clientes autorizados.

Não duplicar memória, filas de tarefas, estado dos agentes ou políticas por renderizador. A mudança 3D → 2D → mínimo não pode perder uma missão nem alterar o significado do seu estado. O renderizador é uma vista do sistema, não uma fonte de verdade.

## 4. Rede de computadores e agentes distribuídos

O DGM-MAT deve ficar preparado para utilizar capacidades disponíveis em diferentes computadores autorizados numa rede local ou privada. Exemplo futuro: o computador principal executa o cérebro DGM-MAT; outro computador tem DeepSeek Harness; um terceiro tem Claude Code; outro disponibiliza inferência local ou uma ferramenta especializada. O DGM-MAT pode encaminhar uma tarefa para o nó adequado sem precisar de conhecer os detalhes internos de cada produto.

Isto é um requisito de arquitetura futura, não significa que a descoberta, a comunicação remota ou a segurança estejam já implementadas.

### Componentes propostos

- **Control plane central:** o DGM-MAT mantém as decisões, política, memória, estado canónico e registo de tarefas.
- **Node Agent / Worker Gateway:** serviço mínimo em cada computador autorizado, responsável por anunciar capacidades aprovadas, aceitar tarefas autorizadas, iniciar o adaptador local e devolver resultados.
- **Capability Registry:** catálogo de nós e capacidades, incluindo versão, disponibilidade, recursos, localização lógica, permissões e último contacto.
- **Provider/Tool Adapters:** conectores separados para Harness, Claude Code, Ollama, ferramentas CLI, API e futuras ferramentas.
- **Secure Transport:** canal autenticado e encriptado entre nós, com revogação de credenciais e controlo de acesso.
- **Task Dispatcher:** seleciona um worker segundo capacidade, disponibilidade, política, recursos, custo e preferência free/local-first.
- **Artifact & Audit Store:** guarda identificadores, logs permitidos, resultados, checksums, diffs, testes e histórico de delegação.

### Registo explícito antes de descoberta automática

A primeira versão distribuída deve privilegiar registo manual de cada nó: nome lógico, endereço permitido, identidade, capacidades e permissões. Descoberta automática na LAN só deve ser considerada mais tarde, depois de definido o modelo de confiança. Não executar agentes encontrados automaticamente só porque respondem na rede.

Um computador de um familiar ou de outra divisão não é automaticamente confiável por estar acessível. Cada nó deve ser inscrito e autorizado pelo proprietário/administrador relevante. O sistema deve distinguir rede local, VPN/rede privada e Internet pública.

## 5. Contrato independente do agente

Cada worker anuncia capacidades através de um formato interno estável do DGM-MAT, sem expor detalhes desnecessários:

- Identificador e identidade criptográfica do nó.
- Nome lógico e versão do gateway/adaptador.
- Capacidades declaradas e testadas (por exemplo, pesquisa, edição num workspace, execução de testes, inferência local).
- Ferramentas e versões disponíveis.
- Recursos declarados e medidos, limites e carga aproximada.
- Estado: online, offline, ocupado, limitado, bloqueado ou desconhecido.
- Classes de tarefas aceites e recusadas.
- Limites de tempo, concorrência, tamanho e consumo.
- Política de filesystem, shell, rede e credenciais.
- Versão do contrato e data da última verificação.

O estado de um nó deve expirar quando não houver heartbeat válido. Não representar uma máquina como disponível com base apenas no último estado histórico. A tarefa delegada deve ter identificador, prazo, critérios de aceitação, permissões mínimas, workspace de destino e um envelope de resultado verificável.

## 6. Segurança para a rede distribuída

- Autenticar cada nó individualmente; não usar uma chave partilhada universal para toda a rede.
- Encriptar transporte e validar a identidade do destino.
- Começar por tarefas read-only e workspaces descartáveis.
- Aplicar allowlists de repositórios, pastas, comandos e destinos de rede.
- Nunca enviar segredos, tokens, cookies ou memória privada por defeito.
- Partilhar apenas o contexto mínimo necessário à tarefa.
- Exigir aprovação explícita para operações remotas de escrita, instalação, publicação, Git push/merge, acesso sensível ou mudanças de segurança.
- Limitar pedidos por nó, tamanho de artefactos, tempo e concorrência.
- Registar quem delegou, para onde, com que permissões e o resultado obtido.
- Permitir desativar/revogar imediatamente um nó e cancelar tarefas pendentes.
- Tratar resultados remotos como não confiáveis até serem validados pelo DGM-MAT.
- Não permitir que um worker remoto aprove o próprio resultado ou altere a política central.
- Não expor diretamente portas de agentes à Internet; usar uma rede privada/VPN e um gateway autenticado.
- Prever atualizações e rotação de credenciais sem parar o cérebro central.

## 7. Política free/local-first e futura utilização de APIs

A seleção de ferramentas deve ser política configurável e observável, não lógica espalhada pelo código.

Ordem inicial sugerida:
1. Capacidades locais gratuitas já instaladas e adequadas à tarefa.
2. Claude Code Free e outros serviços gratuitos já autorizados, respeitando limites e disponibilidade.
3. Outros nós locais/remotos autorizados com capacidade compatível.
4. Ferramentas web gratuitas quando adequadas e permitidas.
5. APIs pagas apenas quando o utilizador as configurar e autorizar explicitamente, com orçamento e limites definidos.

Esta ordem é uma preferência, não uma promessa de que uma ferramenta gratuita está sempre disponível ou é sempre a melhor. O dispatcher deve considerar qualidade, confidencialidade, latência, conectividade, limites de uso e custo. Deve poder esperar por um limite gratuito, pedir autorização para uma alternativa ou explicar que não existe ferramenta adequada; não deve contratar serviços nem gerar despesas silenciosamente.

A arquitetura de provider deve permitir acrescentar futuramente API keys e provedores pagos sem reescrever a memória, o orquestrador, a interface ou os contratos de tarefas. Segredos devem ser guardados num mecanismo apropriado e nunca em logs, prompts de diagnóstico ou documentação versionada.

## 8. Estratégia de implementação por fases

### Etapa A — especificação e auditoria
- Auditar contratos, providers, memória, eventos, persistência e frontend existentes.
- Definir limites de recursos com medições no PC real.
- Não instalar vários runtimes nem alterar startup nesta fase.

### Etapa B — interface comum e perfil mínimo
- Construir primeiro chat funcional, estados reais e personagem mínima.
- Garantir que a aplicação continua útil com animações desativadas.
- Usar dados mock claramente identificados até a integração read-only estar pronta.

### Etapa C — renderização adaptável
- Acrescentar 2D leve e 2D avançado por adaptadores independentes.
- Medir consumo e fluidez.
- Só depois testar uma implementação 3D isolada; manter sempre fallback automático e manual.

### Etapa D — worker local isolado
- Testar um único worker local (por exemplo, Harness) numa pasta descartável.
- Comparar com Claude Code Free e a configuração atual.
- Fixar versão, medir CPU/RAM, testar cancelamento, shutdown e processos residuais.

### Etapa E — contrato de worker e catálogo
- Definir o contrato de capacidades com base nos providers já existentes.
- Registar um único nó de forma explícita.
- Testar heartbeat, indisponibilidade, timeout, cancelamento e recuperação.

### Etapa F — segundo computador
- Ligar um segundo nó numa rede privada controlada.
- Começar por tarefa read-only; depois permitir artefactos num workspace isolado.
- Testar autenticação, encriptação, revogação e isolamento entre nós.

### Etapa G — routing e APIs futuras
- Comparar workers por capacidade, recursos, custo, qualidade e política.
- Adicionar providers web/API através de adaptadores.
- Ativar provedores pagos apenas por configuração e consentimento explícitos.

Nenhuma destas etapas autoriza agora instalações, alterações de código, abertura de portas ou sincronização de branches.

## 9. Critérios de aceitação futuros

- A interface continua funcional no perfil mínimo.
- A troca de renderizador não altera tarefas nem perde estado.
- O modo automático escolhe uma opção testada e pode ser substituído manualmente.
- O perfil escolhido e a razão da escolha são observáveis.
- A aplicação degrada com elegância quando recursos diminuem.
- Um nó desconhecido ou não autorizado nunca recebe tarefas.
- Um nó offline não é mostrado como ativo.
- Tarefas remotas respeitam autorização, timeout, cancelamento e workspace permitido.
- Resultados remotos são validados localmente pelo DGM-MAT.
- A preferência free/local-first é aplicada sem chamadas pagas silenciosas.
- Adicionar/remover um provider ou nó não exige reescrever o cérebro.
- Os logs e a memória distinguem factos observados, declarações do worker e resultados validados.

## 10. Decisão a preservar

Construir uma plataforma adaptável e distribuída, não um escritório visual preso a um único motor nem um cérebro dependente de um agente externo. O DGM-MAT deve funcionar no computador mais modesto com chat e personagem mínima, escalar para 2D/3D quando houver capacidade real e, no futuro, coordenar agentes autorizados em vários computadores através de contratos e gateways seguros. O código de terceiros serve para estudar ideias e compatibilidade; respeitar licenças e preferir implementação própria ou integração formal em vez de copiar componentes sem autorização.

**Próxima ação:** quando o trabalho for retomado no PC, auditar e preservar primeiro o estado local/remoto; depois mapear esta proposta aos contratos e componentes existentes antes de escolher implementação.
