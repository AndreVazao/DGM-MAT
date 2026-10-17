# Pesquisa — escritório virtual empresarial de agentes DGM-MAT
**Data:** 2026-10-14  
**Estado:** pesquisa de referências e proposta arquitetural; sem instalação, clone, merge ou execução de projetos externos.

## 1. Objetivo
Conceber um escritório visual isométrico/3D que seja uma interface operacional do DGM-MAT. Os bonecos representam agentes reais e os seus movimentos refletem estados e eventos confirmados no runtime. A visualização não é a fonte da verdade: tarefas, eventos, permissões, filas e entregáveis continuam no backend e na memória persistente.

## 2. Referências públicas encontradas
Estas referências servem para estudar padrões; não são aprovadas para adoção. A maturidade, licença, dependências, requisitos, segurança e comportamento atual devem ser revistos no commit exato antes de qualquer teste.

| Ref. | Projeto | Padrões úteis | Limitações/riscos a verificar |
|---|---|---|---|
| VIS-001 | [AgentSystemLabs/agent-office](https://github.com/AgentSystemLabs/agent-office) | Escritório cartoon 3D; cada repositório ocupa um piso; elevador para mudar de projeto; agentes em mesas e terminais; tarefas, issues e PRs. Licença MIT indicada no repositório. | Repositório em evolução rápida; README pede Node.js 20+, CLI de agente, Git e GitHub CLI. O caminho de instalação e dependências não deve ser aplicado diretamente ao PC de recursos limitados. |
| VIS-002 | [Hermes Virtual Office / dian003 fork](https://github.com/dian003/virtual-office) | Divisões com mesas; reuniões; comunicação A2A com avatar a deslocar-se; revisores caminham até ao posto; quadro Kanban sincronizado com tarefas; distingue visualização de execução. | Fork de outro projeto; validar upstream, licença, dependências, operações de escrita e acoplamento ao Hermes. |
| VIS-003 | [harishkotra/agent-office](https://github.com/harishkotra/agent-office) | Pixel art, agentes com Ollama, memória persistente, quadro de tarefas, deslocação até às mesas e conversa entre agentes. | A alegação de execução local não garante desempenho no hardware-alvo; testar modelos, consumo e permissões. |
| VIS-004 | [forgeekscn/pixel-agent-office](https://github.com/forgeekscn/pixel-agent-office) | Estados visuais de agentes, chefe/subagentes, navegação multi-piso e sessões de trabalho. | Confirmar que cada estado visual é alimentado por eventos reais e verificar versão/licença. |
| VIS-005 | [KbWen/agent-virtual-office](https://github.com/KbWen/agent-virtual-office) | Personagens em pixel art ligados a sinais de sessões reais Claude Code/Codex/Gemini; estados como trabalhar, bloqueado e concluído. | Acesso de rede, autenticação e versão de Node requerem revisão; evitar exposição na LAN sem autenticação. |
| VIS-006 | [yakobusdamar/ai-agent-office-simulation](https://github.com/yakobusdamar/ai-agent-office-simulation) | Animação de mensagens/envelopes que percorrem fisicamente o escritório; sequência legível de delegação e retorno de resultados. | O README descreve uma demonstração pré-definida, não um sistema de agentes real. Usar apenas como referência visual. |
| VIS-007 | [OneByJorah/VirtOffice](https://github.com/OneByJorah/VirtOffice) | Avatares 3D, vista isométrica e estados de agentes via servidor leve com SSE/polling/webhooks. | Direcionado a Hermes AgentOS; verificar esforço de adaptação, segurança e licença. |
| VIS-008 | [DeskRPG / ishkkman fork](https://github.com/ishkkman/agent-office) | Escritório 2D em pixel art, personagens, canais, NPCs, tarefas e reuniões. | Fork de outro projeto; conferir origem e licença dos ativos. |
| VIS-009 | [Agent Office 3D — Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=thomasarisu.agent-office) | Escritório com várias salas; agentes sentam-se para trabalhar e deslocam-se para espaços adequados ao papel. | Extensão VS Code: rever permissões, versão e dependência da sessão local. |
| VIS-010 | [gdd-rock/rockoffice](https://github.com/gdd-rock/rockoffice) | Diorama 3D, múltiplas personagens e salas funcionais. | Descrição pública indica projeto de pequena dimensão; maturidade e ligação a tarefas reais por validar. |
| VIS-011 | [krasovsky22/agent-office-sims](https://github.com/krasovsky22/agent-office-sims) | Three.js + Colyseus, movimento sincronizado e colisões num espaço 3D partilhado. | O próprio README descreve o sistema como protótipo de presença; agentes e quadro de tarefas são etapas futuras. |

## 3. Lições aplicáveis ao DGM-MAT
1. **Representação ligada a eventos reais:** a fonte de verdade é o runtime/Orchestrator, não a animação.
2. **Estado do agente separado da pose:** `working`, `waiting`, `blocked`, `reviewing`, `travelling`, `delivering`, `recovering` e `idle` são estados de domínio; sentar, andar, falar ou transportar são animações.
3. **Movimento determinístico:** rotas por pontos de passagem, colisões e destinos definidos. O avatar não deve atravessar paredes, pisos ou mobiliário.
4. **Eventos explicáveis:** ao selecionar um agente, mostrar tarefa atual, departamento, dependências, última ação confirmada, bloqueio, evidência e próximo passo.
5. **Visualização leve:** iniciar com poucos polígonos/instâncias, câmera isométrica fixa e detalhes sob pedido. Evitar física complexa e renderização dispendiosa no PC de 2 núcleos e ~3 GB RAM.
6. **UI e motor separados:** o backend pode operar sem o escritório aberto; perder a visualização nunca interrompe o trabalho.
7. **Acessibilidade e fallback:** vista compacta 2D/lista, zoom, pausa visual e redução de movimento; a operação continua disponível sem 3D.
8. **Segurança por contrato:** não executar ações só porque alguém clicou num boneco. Cliques abrem informação ou iniciam ações autorizadas com confirmação adequada.

## 4. Conceito do edifício empresarial DGM-MAT
A hierarquia exata dos pisos será configurável. Proposta inicial:

- **Piso 0 — Receção, expedição e armazém:** entrada de pedidos, triagem, fila de trabalho, encomendas prontas, entregas e rastreio de artefactos.
- **Pisos de departamentos:** engenharia/programação, investigação, QA e diagnóstico, segurança, memória/documentação, conectores e operações. A disposição final deve respeitar os departamentos e contratos que já existam no DGM-MAT; não criar equipas duplicadas apenas para preencher o cenário.
- **Piso superior — Direção/Boss:** visão global, prioridades, escalamentos, decisões pendentes, indicadores e relatórios. O boss coordena; não tem de executar todas as tarefas.
- **Salas partilhadas:** salas de reunião, biblioteca/arquivo, laboratório isolado, zona de recuperação/enfermaria e espaços de descanso.
- **Núcleo vertical:** elevadores de passageiros e, se necessário, um elevador de carga. Escadas podem ser apenas decorativas no primeiro MVP.

O escritório é um mapa de departamentos lógicos; não obriga a executar um processo por piso nem a criar processos de sistema independentes para cada agente.

## 5. Nova regra: telefone, pedido, encomenda e recolha presencial
O fluxo solicitado fica registado como comportamento de primeira classe:

1. Um agente deteta uma dependência e cria um pedido com ID, remetente, destinatário/departamento, conteúdo, prioridade, prazo e permissões.
2. O pedido pode ser comunicado visualmente por telefone/chamada, mensagem ou reunião. A chamada é um evento visível, mas não substitui o registo persistente.
3. O departamento destinatário aceita, rejeita com motivo ou pede esclarecimentos.
4. Se for um resultado digital, a encomenda representa um artefacto verificável (ficheiro, relatório, resultado de teste, pacote, credencial temporária referenciada — nunca segredos em texto visual).
5. Estados logísticos possíveis: `requested → accepted → preparing → ready → in_transit → delivered → acknowledged`; estados alternativos: `rejected`, `cancelled`, `failed`, `expired`. A transição tem de ser confirmada pelo backend.
6. Quando a política define **recolha presencial**, o agente termina ou pausa a sua atividade atual de forma segura, levanta-se, caminha até ao elevador, seleciona o piso, aguarda a viagem, desloca-se ao balcão/estante de recolha, valida o ID da encomenda, recolhe-a e regressa ao destino.
7. Se a tarefa não exigir presença física, usar entrega digital direta e evitar animação desnecessária. O modo de entrega é determinado pela natureza do pedido/política, não por aleatoriedade.
8. A encomenda não desaparece ao ser tocada: a recolha e a entrega mudam o estado persistente e deixam rasto de auditoria.
9. Se o agente estiver ocupado, bloqueado, sem autorização ou se o elevador estiver indisponível, a viagem aguarda ou é cancelada com estado explicável; nunca se simula uma entrega concluída.

### Estados visuais recomendados
- Telefone: tocar, a ligar, em chamada, sem resposta, chamada concluída.
- Pedido: envelope/cartão com ID e prioridade.
- Preparação: agente do departamento de destino a trabalhar no item.
- Pronto: encomenda na prateleira identificada.
- Transporte: agente/carrinho a mover-se pela rota correta.
- Elevador: chamar, portas a abrir, embarcar, em trânsito, desembarcar.
- Entrega: confirmar destinatário, apresentar resumo/artefacto, obter reconhecimento.
- Bloqueio: ícone e explicação ligados ao evento real; não colocar o agente na enfermaria por mera animação.

## 6. Enfermaria e armazém já definidos
- **Enfermaria/sala de recuperação:** agentes realmente bloqueados, com causa, dependência e ação de recuperação visíveis. Só entram quando o estado real indica bloqueio/recuperação; não representa doença humana nem diagnóstico médico.
- **Armazém:** volume de serviços pendentes, em preparação, prontos e expedidos. Contagens derivadas das filas e estados persistentes; não de objetos decorativos arbitrários.
- **Entrega externa:** encomenda embalada e viatura a sair do armazém quando existe pedido externo e expedição real confirmada. O veículo não é enviado por mera estética.

## 7. Arquitetura proposta
### Camada A — Fonte de verdade
DGM-MAT Orchestrator/Runtime, estado de tarefas, eventos, contratos, permissões, artefactos e memória persistente.

### Camada B — Modelo de domínio do escritório
Entidades sugeridas:
- `OfficeFloor`, `Department`, `Room`, `Desk`, `AgentPresence`
- `Task`, `DependencyRequest`, `Package`, `Delivery`, `ElevatorTrip`
- `OfficeEvent`, `Route`, `AuditRecord`

Cada entidade tem identificador estável e referência ao objeto real do runtime. A camada visual não cria tarefas nem confirma resultados.

### Camada C — Adaptador de eventos
Traduz eventos do runtime para comandos de animação: agente atribuído, tarefa iniciada, pedido criado, pedido aceite, artefacto pronto, transporte iniciado, entrega reconhecida, bloqueio e recuperação. Eventos idempotentes, ordenados quando necessário, com timestamp e correlação por ID.

### Camada D — Simulação e apresentação
Renderização 3D isométrica; sistema de navegação por waypoints; elevadores como máquinas de estado; animações sem chamada de LLM; atualização incremental e fallback 2D.

### Camada E — Controlo humano
Selecionar agente, inspecionar prova, abrir tarefa, autorizar ação, pausar a visualização e ver histórico. A confirmação visual não concede permissões ao agente.

## 8. MVP por fases
1. **MVP-0 — planta estática:** edifício em pisos, departamentos, boss, armazém e enfermaria; sem movimento autónomo.
2. **MVP-1 — presença real:** avatares para agentes existentes; estado ligado ao runtime; clique abre tarefa/log.
3. **MVP-2 — rotas:** andar entre mesas e salas, navegação e colisões básicas.
4. **MVP-3 — comunicação:** telefone/chamada visual, pedidos e estados persistentes.
5. **MVP-4 — logística vertical:** elevadores, preparação, recolha e entrega de encomendas.
6. **MVP-5 — operação empresarial:** armazém, expedição externa, reuniões, escalamentos ao boss e métricas.
7. Cada fase exige testes locais e medição de RAM/CPU; a visualização nunca deve ser dependência crítica do backend.

## 9. Critérios de aceitação
- Cada avatar representa um agente registado; nenhum agente fictício é contado como capacidade real.
- Cada animação de tarefa/logística tem evento correlacionado e histórico consultável.
- Nenhuma encomenda é marcada entregue sem confirmação persistente.
- Os agentes não atravessam geometria; os elevadores não transportam passageiros sem sequência de estados válida.
- O backend funciona quando a vista 3D fecha ou falha.
- A vista compacta mantém os mesmos estados e ações essenciais.
- Sem instalação automática de projetos de referência; qualquer reutilização exige auditoria de licença, dependências, segurança e recursos.
- Nenhum clone de terceiros ou repositório Labs é alterado ou sincronizado como parte desta investigação.

## 10. Plano de pesquisa técnica antes de escolher uma base
Para cada projeto: registar URL, licença, data/commit, runtime/framework, modo de integração, fonte dos estados, uso de rede, autenticação, armazenamento, telemetria, dependências, requisitos de RAM/CPU, instalação/desinstalação e riscos. Inspecionar estática e historial antes de executar. Comparar arquitetura e padrões, não copiar código/ativos sem confirmar licença. A seleção deve privilegiar adaptação mínima e separação clara entre backend DGM-MAT e renderer.

## Fontes consultadas
- AgentSystemLabs, Agent Office: https://github.com/AgentSystemLabs/agent-office
- Hermes Virtual Office fork: https://github.com/dian003/virtual-office
- Local-first pixel office: https://github.com/harishkotra/agent-office
- Pixel Agent Office: https://github.com/forgeekscn/pixel-agent-office
- Agent Virtual Office: https://github.com/KbWen/agent-virtual-office
- Animated office workflow: https://github.com/yakobusdamar/ai-agent-office-simulation
- VirtOffice: https://github.com/OneByJorah/VirtOffice
- DeskRPG fork: https://github.com/ishkkman/agent-office
- Agent Office 3D extension: https://marketplace.visualstudio.com/items?itemName=thomasarisu.agent-office
- RockOffice: https://github.com/gdd-rock/rockoffice
- Agent Office Sims: https://github.com/krasovsky22/agent-office-sims
