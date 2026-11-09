# DGM-MAT Digital Headquarters — avaliação de escritórios virtuais
## Pesquisa comparativa, decisão de tecnologia e plano de adaptação
**Data de referência:** 2026-10-12  
**Estado:** proposta de arquitetura; não implementada  
**Branch:** `docs/digital-headquarters-concept-2026-10-12`

## 1. Decisão executiva

**Recomendação:** não adotar já um projeto de escritório como produto final. Fazer uma prova de conceito de leitura com a arquitetura visual de um projeto existente, mas manter o DGM-MAT como fonte de verdade e o frontend como componente substituível. Em paralelo, construir o adaptador de eventos do DGM-MAT e um protótipo leve com a identidade visual aprovada.

A melhor base a investigar primeiro é **Claude Office / Pixel Agent Office** para aprender com o pipeline de eventos, máquina de estados, WebSockets e renderização 2D. **My Virtual Office** é forte como referência de produto integrado com múltiplos runtimes, mas a licença AGPL-3.0-or-later e o modelo de funcionalidades/licença exigem análise jurídica e técnica antes de reutilizar ou modificar. **My Virtual World** aproxima-se da ambição isométrica/3D, mas a licença publicada é PolyForm Noncommercial 1.0.0 para o código e CC BY-NC-SA 4.0 para ativos criativos; não é uma base apropriada para uso comercial sem licença separada. O mais seguro para o produto próprio pode ser uma implementação independente que reutilize padrões arquiteturais, sem copiar código ou ativos sem revisão.

## 2. Requisitos específicos do DGM-MAT

A interface tem de ser mais do que uma animação:
- menu fixo à esquerda;
- escritório central isométrico/3D com agentes, secretárias, departamentos e salas;
- chat/pedidos/respostas fixo à direita;
- visão global de clientes, missões, equipas e estado da empresa;
- recrutamento, formação, experiência, qualificação e atribuição de missões;
- departamentos que possam ser criados e reorganizados;
- remodelação do layout persistida e reversível;
- agentes bloqueados representados como doentes, com símbolo médico e fluxo de enfermaria/recuperação;
- armazém visual que representa fila de trabalho, produção, controlo de qualidade, expedição e acumulação;
- encomendas/caixas e viaturas como metáforas para pedidos de ajuda e entregas externas;
- histórico e auditoria;
- funcionamento local-first e acesso remoto privado, não exposição pública;
- consumo de recursos baixo o suficiente para o PC antigo;
- integração com o backend e contratos existentes, sem criar outro cérebro ou sistema de tarefas paralelo.

### Princípio de fidelidade
O backend do DGM-MAT é a fonte de verdade. O frontend apresenta estados/eventos confirmados. Movimentos decorativos podem existir quando não induzem o utilizador em erro, mas progresso, execução, bloqueios, recuperação, envio e entrega têm de refletir factos registados.

## 3. Comparação das bases pesquisadas

### A. My Virtual Office
URL: https://github.com/eliautobot/my-virtual-office  
Licença indicada no repositório: AGPL-3.0-or-later.

**Pontos fortes**
- produto self-hosted 2D especificamente orientado para presença e atividade de agentes;
- suporte declarado para OpenClaw, Hermes, Codex CLI, Claude Code, OpenCode e Antigravity através de adaptadores/Provider SDK;
- criação/gestão de agentes, chats, sessões, permissões e layout de escritório;
- foco em eventos em tempo real e controlo de agentes;
- Docker Compose e configuração local.

**Limitações para o DGM-MAT**
- é uma aplicação com o seu próprio modelo de agentes e gestão; integrar sem cuidado pode criar dois centros de autoridade;
- demo gratuita limitada a três agentes, segundo a documentação pública consultada; algumas funções são desbloqueadas por licença;
- a licença AGPL implica obrigações de disponibilização do código-fonte correspondente quando uma versão modificada é disponibilizada através de rede. Confirmar a interpretação para qualquer modo de incorporação/distribuição;
- estilo visual 2D não corresponde totalmente ao mockup isométrico 3D;
- a sua segurança e o acesso aos runtimes precisam de ser auditados antes de ligar ao backend real.

**Uso recomendado:** referência funcional e candidato para um spike temporário. Não integrar a sua base de dados nem permitir que seja autoridade sobre missões do DGM-MAT. Se for executado, usar ambiente isolado e provider mock/read-only.

### B. Claude Office / Pixel Agent Office
URLs:
- https://github.com/paulrobello/claude-office/
- https://github.com/forgeekscn/pixel-agent-office

**Pontos fortes**
- simulação de escritório pixel-art com patrão e agentes;
- arquitetura descrita com frontend Next.js/React, PixiJS, backend FastAPI, estado, eventos e WebSockets;
- pipeline de eventos de agentes e integração com hooks/providers; documentação inclui mapeamento de eventos de sessão e ferramentas;
- conceitos úteis para transições de estados, movimentação, layout, logs e representação de trabalho;
- o fork Pixel Agent Office tem funcionalidades como navegação entre pisos e visualização de sessões, segundo o README consultado.

**Limitações**
- parte da experiência foi concebida para Claude Code/OpenCode; será necessário um adaptador para DGM-MAT e outros runtimes;
- estilo pixel-art é diferente da estética isométrica pretendida;
- deve confirmar-se a licença exata no repositório upstream antes de reutilizar código/ativos;
- integrar os hooks diretamente em vários runtimes pode produzir estados inconsistentes se o DGM-MAT não for a fonte canónica;
- arquitetura Next.js + PixiJS + FastAPI pode ser pesada para a máquina-alvo se correr em conjunto com agentes locais.

**Uso recomendado:** melhor referência inicial para estudar a arquitetura de visualização orientada a eventos. Avaliar código e licença upstream antes de copiar qualquer componente. Reimplementar o contrato de eventos e o renderer com a estética DGM-MAT se isso for mais simples e sustentável.

### C. My Virtual World
URL: https://github.com/eliautobot/my-virtual-world  
Licenciamento publicado:
- código/documentação técnica: PolyForm Noncommercial License 1.0.0;
- ativos criativos: CC BY-NC-SA 4.0;
- uso comercial requer licença escrita separada, conforme a documentação do projeto.

**Pontos fortes**
- mundo 3D/voxel em Three.js com edifícios, estradas, interiores, agentes, objetos e movimento;
- servidor Python e estado persistente em JSON;
- registry de providers para normalizar descoberta, saúde, sessões, chat, interrupções e aprovações;
- sidecar de tempo real opcional para snapshots de agentes, rotas e heartbeat;
- arquitetura visual aproxima-se da ideia de escritório/cidade em que agentes se deslocam entre edifícios.

**Limitações**
- licença não comercial impede assumir que o código/ativos podem ser reutilizados livremente num futuro produto comercial;
- o modelo de licença/demonstração bloqueia funcionalidades avançadas;
- é mais próximo de um mundo virtual que de uma aplicação empresarial integrada no DGM-MAT;
- exige avaliação do consumo de Three.js, sidecar, servidor e assets;
- a integração OpenClaw/Hermes não garante compatibilidade com os contratos DGM-MAT.

**Uso recomendado:** referência visual e de arquitetura para mundo 3D, não base para fork comercial sem licença adequada. Podemos reproduzir padrões gerais de navegação/representação com código e assets próprios, após confirmar que não copiamos elementos protegidos.

### D. DeepSeek Harness (DSH)
URL: https://github.com/deepseek-ai/deepseek-harness  
Licença MIT; estado declarado: developer preview.

**Pontos fortes**
- runtime/harness de agentes com arquitetura plugin;
- perfis web, headless, SDK e ACP;
- útil como trabalhador de programação/pesquisa, não como escritório visual final;
- os plugins/perfis são uma referência para desenhar adapters substituíveis.

**Limitações**
- não é, por si só, o escritório animado desejado;
- developer preview e APIs que podem mudar;
- segurança exige isolamento;
- medir recursos no PC antigo.

**Uso recomendado:** estudar como provider externo e módulo de execução, em investigação separada da escolha do frontend.

### E. Construção própria leve
Possível stack a decidir depois da auditoria:
- UI: framework já existente no DGM-Cockpit-Frontend, se for compatível; não criar uma segunda UI stack sem necessidade.
- Renderização: canvas/SVG ou PixiJS 2D com vista isométrica simulada; Three.js apenas se a profundidade 3D for essencial e a máquina suportar.
- Backend: APIs/contratos existentes do DGM-MAT; evitar duplicar API e persistência.
- Eventos: reutilizar event store/bus já existente; se insuficiente, adicionar adaptador de leitura com contrato versionado.
- Estado visual: projeção read-only dos estados canónicos.
- Persistência de layout: armazenar configuração de apresentação separada dos dados operacionais.
- Segurança: autenticação local/privada, autorização por ação e auditoria.

**Pontos fortes:** identidade visual fiel, sem dependência de licenças de aplicações de terceiros, integração exata com os estados do DGM-MAT.  
**Limitações:** maior custo inicial de implementação e manutenção; precisamos de definir bem a máquina de estados e o renderer.

## 4. Matriz de decisão

| Critério | My Virtual Office | Claude Office | My Virtual World | Construção própria |
|---|---|---|---|---|
| Escritório animado pronto | Forte, 2D | Forte, pixel-art 2D | Forte, mundo 3D | A desenvolver |
| Múltiplos runtimes | Forte segundo README | Integrações/hooks, verificar por provider | Registry/provider, verificar compatibilidade | Controlado por nós |
| Semântica DGM-MAT | Adaptar | Adaptar | Adaptar | Exata |
| Visual do mockup aprovado | Parcial | Parcial | Mais próximo do 3D | Total |
| Licenciamento para reutilização | AGPL: rever obrigações | Confirmar upstream | PolyForm Noncommercial + assets CC BY-NC-SA | Código/assets próprios |
| Peso no PC antigo | Medir | Medir | Medir; 3D/sidecar pode pesar | Podemos otimizar |
| Risco de duplicar backend | Médio/alto | Médio | Médio/alto | Baixo se usar APIs existentes |
| Dependência de fornecedor externo | Baixa/moderada | Baixa/moderada | Baixa/moderada | Baixa |
| Recomendação | Spike isolado | Referência técnica principal | Referência visual, não fork sem licença | Destino provável se integração direta falhar |

Esta matriz é qualitativa, baseada na documentação pública consultada; não é resultado de benchmarks na máquina do utilizador.

## 5. Arquitetura recomendada

```text
DGM-MAT backend (fonte de verdade)
    |
    +-- API/eventos canónicos existentes
    |
    +-- Office Projection Adapter (read-only na primeira fase)
             |
             +-- Snapshot de agentes e missões
             +-- Estados/saúde/recuperação
             +-- Pedidos/produção/QA/expedição
             +-- Departamentos e layout
             |
             v
Digital Headquarters UI
    +-- Navegação fixa à esquerda
    +-- Escritório isométrico ao centro
    +-- Chat e pedidos à direita
    +-- Painéis e histórico
```

As ações de escrita devem ser separadas da projeção de leitura. No futuro, ações como atribuir missão, criar departamento, contratar agente ou enviar pedido externo passam por comandos autenticados, permissões, confirmação e auditoria. A animação nunca deve executar ações por si só.

## 6. Contrato de eventos da interface

Os nomes seguintes são conceptuais e precisam de ser mapeados para os eventos reais antes de serem implementados:
- `agent.state.changed`
- `agent.task.started`
- `agent.task.progress`
- `agent.blocked`
- `agent.recovery.started`
- `agent.recovery.passed`
- `request.received`
- `request.assigned`
- `work.started`
- `work.awaiting_review`
- `work.validated`
- `external_help.sent`
- `external_help.reply_received`
- `delivery.dispatched`
- `delivery.confirmed`
- `department.created`
- `office.layout.updated`

Todos devem ter ID, timestamp, origem, entidade relacionada, correlação e versão do contrato. Se o backend não fornecer progresso real, mostrar etapas, estado ou “progresso desconhecido”; não inventar percentagens.

## 7. Como representar as metáforas com rigor

### Enfermaria
- Um estado técnico de bloqueio/falha pode encaminhar o agente para a sala de diagnóstico.
- A UI apresenta causa, último estado saudável, dependência e ação de recuperação.
- Espera por resposta externa não equivale a falha.
- O agente regressa apenas depois de health checks/testes passarem.

### Armazém
- Receção = pedidos registados.
- Fila = pedidos triados sem atribuição.
- Produção = trabalho efetivamente em execução.
- Zona de dependências = aguardando aprovação/resposta/credencial.
- QA = resultado à espera de validação.
- Expedição = resultado enviado.
- Entregue = confirmação registada.
- Devoluções = trabalho reaberto após falha.

### Viaturas
A viatura é uma animação de um pedido/artefacto enviado, não prova de entrega. Só sai visualmente depois de o backend confirmar a ação de envio; só aparece como entregue quando existir confirmação real.

### Recrutamento e formação
Recrutas e progresso de formação devem corresponder a configuração real, tarefas de avaliação e competências demonstradas. O tempo decorrido não deve automaticamente aprovar um agente.

### Remodelação
O layout pode ser editável e versionado, com preview e undo. Alterar a planta não cria automaticamente permissões nem novos departamentos funcionais.

## 8. Fases de implementação

### Fase 0 — segurança de repositórios
- Resolver primeiro a auditoria local/remota, branches e working trees.
- Preservar trabalho não publicado.
- Confirmar as APIs, contratos, persistência e eventos atuais.
- Não iniciar integração antes de haver uma base conhecida.

### Fase 1 — estudo de código e licenças
- Fixar commits exatos dos candidatos.
- Confirmar licenças, ativos e dependências.
- Mapear eventos de Claude Office para os contratos DGM-MAT.
- Executar candidatos em ambiente isolado e com provider mock.
- Não copiar código/ativos até revisão de licença.

### Fase 2 — protótipo estático
- Implementar layout com dados fictícios claramente identificados.
- Validar o mockup, legibilidade, scroll, seleção de agentes e painéis.
- Testar consumo de RAM/CPU sem runtime de agente.

### Fase 3 — projeção read-only
- Ligar à API real de snapshot/eventos.
- Exibir estado real de agentes, pedidos e missões.
- Testar desconexão, reconexão, eventos duplicados/fora de ordem e estado desconhecido.

### Fase 4 — workflows e chat
- Integrar pedidos/respostas, atribuição e validação através de comandos existentes.
- Confirmar autorização e auditoria.
- Sem ações destrutivas por animação.

### Fase 5 — enfermaria, armazém e carreira
- Ligar bloqueios/recuperação aos health checks.
- Representar a fila de produção e expedição.
- Implementar formação e qualificação com evidência.

### Fase 6 — remodelação e departamentos
- Layout persistido, pré-visualização, undo e migrações.
- Departamentos como entidades reais com permissões e competências.
- Testar rollback e compatibilidade.

### Fase 7 — aceitação
- Testes de contrato, acessibilidade, segurança, recursos, persistência e reconexão.
- Verificar que todos os elementos visuais refletem o backend.
- Documentar rollback antes de qualquer merge.

## 9. Critérios de aceitação
- Menu esquerdo e chat direito mantêm posição durante scroll.
- A interface funciona sem provedor externo e sem Internet para visualizar o estado local já guardado.
- O escritório mostra “offline/desconhecido” quando não recebe dados, sem inventar estado.
- Cada agente/missão tem ligação para entidade real e histórico.
- Bloqueio, recuperação e reativação são auditáveis.
- Armazém e viaturas refletem transições de trabalho reais.
- Layout e departamentos persistem após reinício.
- Ações sensíveis exigem autorização.
- Não são introduzidos novos serviços/bases de dados sem justificação.
- O consumo é medido no PC alvo.
- Licenças de código e assets são respeitadas.

## 10. Fontes e ligações
- DeepSeek Harness: https://github.com/deepseek-ai/deepseek-harness
- DeepSeek Harness architecture: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md
- DeepSeek Harness safety: https://github.com/deepseek-ai/deepseek-harness/blob/master/SAFETY.md
- My Virtual Office: https://github.com/eliautobot/my-virtual-office
- My Virtual Office README: https://github.com/eliautobot/my-virtual-office/blob/main/README.md
- Claude Office upstream: https://github.com/paulrobello/claude-office
- Pixel Agent Office: https://github.com/forgeekscn/pixel-agent-office
- My Virtual World: https://github.com/eliautobot/my-virtual-world
- OpenHands Agent Server: https://github.com/openhands/software-agent-sdk/tree/main/openhands-agent-server
- SWE-agent: https://github.com/SWE-agent/SWE-agent

## 11. Conclusão

A recomendação é **usar os projetos existentes como referências e candidatos de prova de conceito, mas não entregar a nenhum deles o controlo do DGM-MAT**. O DGM-MAT conserva orquestração, memória, políticas, contratos e estado canónico. Os runtimes externos são trabalhadores substituíveis; o escritório é uma projeção visual do estado real.

A arquitetura visual mais segura é incremental: primeiro renderer com dados mock, depois projeção read-only do backend, depois comandos autorizados. Para o estilo desejado, avaliar um renderer isométrico leve (2D/PixiJS ou SVG/canvas) antes de comprometer o PC antigo com um mundo 3D completo.

A decisão de reutilizar código de terceiros deve ser tomada apenas depois de verificar commit, licença, dependências e implicações de distribuição. A decisão de integração só deve ocorrer depois da reconciliação dos branches e da auditoria da arquitetura atual.
