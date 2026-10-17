# DGM-MAT Digital Headquarters
## Conceito de desenvolvimento futuro — 2026-10-12

**Estado:** proposta conceptual, não implementada  
**Branch:** `docs/digital-headquarters-concept-2026-10-12`  
**Objetivo:** preservar a visão visual e funcional do escritório digital antes de retomar a reconciliação dos branches locais/remotos.

> **Regra de segurança do projeto:** este documento não autoriza alterações ao backend, merges, rebases, resets, sincronizações ou substituições de componentes existentes. Antes da implementação, auditar o estado local e remoto, os branches divergentes, os contratos existentes e os pontos de integração. Preservar trabalho não validado.

## 1. Visão

O DGM-MAT Digital Headquarters é uma interface visual interativa para observar e gerir a empresa digital DGM-MAT. A experiência pode lembrar um jogo de gestão empresarial, mas não é um jogo desligado do sistema: o escritório animado é uma representação do estado real do backend.

- O proprietário humano é o dono da empresa.
- O DGM-MAT é o patrão executivo/orquestrador.
- Os agentes são trabalhadores especializados.
- Os pedidos são ordens de trabalho de clientes ou tarefas internas.
- Os departamentos representam responsabilidades e capacidades reais.
- O armazém representa a fila de trabalho, a produção, o controlo de qualidade e a expedição.
- As animações ilustram estados/eventos reais; não inventam trabalho, progresso, mensagens nem resultados.

## 2. Composição principal da interface

### Barra lateral esquerda — navegação fixa
- Visão geral
- Escritório
- Agentes
- Recrutamento e formação
- Departamentos
- Missões
- Clientes / Pedidos
- Armazém / Expedições
- Enfermaria / Recuperação
- Remodelação
- Expansão
- Memória
- Repositórios e contratos
- Auditoria e segurança
- Configurações

A navegação deve permanecer fixa enquanto o conteúdo central ou o chat tem scroll.

### Área central — escritório isométrico vivo
- Receção e entrada de pedidos.
- Gabinete do patrão DGM-MAT.
- Secretárias e postos de trabalho dos agentes.
- Salas de reunião e colaboração.
- Departamentos especializados.
- Centro de formação.
- Enfermaria e sala de recuperação.
- Armazém, produção, controlo de qualidade e expedição.
- Cais de carga, parque e viaturas de entrega simbólicas.
- Espaços que possam ser adicionados/remodelados sem redesenhar a aplicação toda.

Cada agente deve poder ser selecionado para abrir ficha com especialidade, tarefa atual, estado real, modelo/provedor quando conhecido, ferramentas autorizadas, dependências, histórico, métricas de qualidade e ações permitidas.

### Barra lateral direita — pedidos, respostas e chat
- Conversação com o DGM-MAT.
- Entrada de novos pedidos.
- Respostas e perguntas de clarificação.
- Estado dos pedidos e notificações.
- Atividade recente e eventos de agentes.
- Progresso baseado em etapas observáveis.
- Alertas de bloqueio, pedidos de autorização e expedições.
- Filtros por cliente, missão, departamento e estado.

### Painéis inferiores/superiores
- Agentes ativos / em formação / bloqueados / em recuperação.
- Pedidos por atribuir, em produção, em validação e concluídos.
- Capacidade e acumulação do armazém.
- Missões atrasadas ou bloqueadas.
- Resultados e incidentes recentes.
- Indicadores globais sem fabricar métricas quando não existem dados.

## 3. Estados visuais e semântica

| Estado real | Representação visual proposta | Regra |
|---|---|---|
| Disponível | Agente no posto, estado pronto | Só se o runtime confirmar disponibilidade |
| Em execução | Agente no posto com missão identificada | Deve existir execução real associada |
| Em colaboração | Agentes numa sala/reunião | Só quando a colaboração estiver registada |
| Em formação | Agente na área de formação | Exercícios e critérios devem existir no sistema |
| A aguardar dependência | Agente em espera, motivo visível | Não classificar como doente por estar apenas à espera |
| Bloqueado por erro | Símbolo de alerta e encaminhamento para diagnóstico | Registar causa e evidência |
| Em recuperação | Agente na enfermaria/sala de recuperação, símbolo médico | A recuperação é um fluxo técnico rastreável, não uma punição |
| Recuperado | Testes de recuperação concluídos e regresso ao estado permitido | Não reativar apenas por ter passado tempo |
| Missão concluída | Resultado entregue à validação/expedição | 100% apenas quando os critérios definidos estão cumpridos |

## 4. Enfermaria e recuperação dos agentes

A metáfora visual de «agente doente» representa indisponibilidade técnica, falha ou bloqueio — não uma condição humana real.

Fluxo proposto:
1. Detetar uma falha real ou estado de bloqueio.
2. Registar motivo, tarefa, erro, dependências e último estado saudável.
3. Suspender novas atribuições ao agente afetado, conforme a política de segurança.
4. Criar um caso de recuperação e encaminhá-lo para a enfermaria visual.
5. Diagnosticar e aplicar apenas ações de recuperação autorizadas.
6. Executar testes de saúde/funcionais definidos para o agente.
7. Reativar apenas após os testes passarem; caso contrário, manter bloqueado e pedir intervenção humana.

A sala de recuperação pode mostrar fila, diagnóstico, ação atual, tentativas, logs relevantes e critérios pendentes. Evitar ciclos automáticos infinitos de reinício.

## 5. Armazém, produção e expedição

O armazém é uma representação visual do fluxo de trabalho, não um contador decorativo.

Zonas propostas:
1. **Receção:** pedidos novos e ainda não triados.
2. **Fila de atribuição:** pedidos triados sem responsável.
3. **Produção:** tarefas efetivamente em execução.
4. **Dependências:** trabalho à espera de resposta, credencial, aprovação ou serviço externo.
5. **Controlo de qualidade:** resultados à espera de testes, revisão ou aprovação.
6. **Expedição:** artefactos/respostas prontos para envio.
7. **Entregues:** confirmação de entrega registada.
8. **Devoluções/reabertura:** trabalho devolvido por falha de validação ou requisitos não cumpridos.

As encomendas podem ser representadas por caixas com identificador curto, prioridade, cliente/projeto, estado e responsável. O tamanho/volume do armazém deve refletir quantidades reais, com limites e alertas de acumulação.

### Viaturas e pedidos externos de ajuda
Uma caixa pode simbolizar um pedido de ajuda externo, e uma viatura a sua expedição. A animação só deve iniciar depois de o backend registar a criação e o envio real do pedido. A viatura representa o ciclo do pedido (preparado, enviado, aguardando resposta, resposta recebida, fechado); não implica transporte físico literal nem garante resposta.

## 6. Recrutamento, formação e carreira

O DGM-MAT poderá propor a contratação/configuração de novos agentes, mas a criação de agentes e permissões tem de passar por políticas explícitas e persistência real.

Fluxo:
1. Definir necessidade, especialidade e missão prevista.
2. Escolher arquitetura/modelo/provedor compatível e disponível.
3. Definir ferramentas, pastas, repositórios e permissões mínimas.
4. Criar/configurar o agente e registar a origem/configuração.
5. Fornecer documentação e memória autorizadas.
6. Executar formação e tarefas de teste isoladas.
7. Avaliar qualidade, fiabilidade, segurança e uso de recursos.
8. Autorizar gradualmente tipos de missão.
9. Rever periodicamente desempenho e revogar permissões quando necessário.

O período de experiência pode ter duração configurável, mas o tempo decorrido não substitui evidência de competência. «Promoções» e funções de chefia devem alterar permissões e responsabilidades reais, não apenas o rótulo visual.

## 7. Departamentos, remodelação e expansão

A interface deve permitir propor e gerir departamentos como entidades persistentes:
- Nome, finalidade, responsável, agentes e competências.
- Missões aceites e critérios de encaminhamento.
- Ferramentas, provedores e permissões autorizados.
- Dependências com outros departamentos.
- Métricas de qualidade e capacidade.

A remodelação do escritório é uma alteração de layout persistida. A criação de uma divisão visual deve estar associada a uma configuração funcional correspondente. Permitir pré-visualização, desfazer/reverter e aprovação antes de alterações com impacto no sistema.

## 8. Arquitetura técnica proposta — a validar antes de codificar

- **Backend DGM-MAT:** fonte de verdade para missões, agentes, estados, eventos, resultados e permissões.
- **Adaptador de eventos:** converte eventos e estados existentes num contrato estável para a interface.
- **API de leitura:** disponibiliza snapshot atual, detalhes de agentes/missões e histórico.
- **Atualização em tempo real:** WebSocket ou mecanismo já existente e compatível, evitando introduzir uma segunda infraestrutura sem necessidade.
- **Frontend Digital Headquarters:** renderização do escritório, animações, navegação e painéis.
- **Persistência:** reutilizar os armazenamentos e contratos existentes depois de auditados; não criar bases de dados duplicadas por conveniência.
- **Auditoria:** registar alterações de estado, aprovações, ações externas e intervenções humanas.

Antes de escolher tecnologia de animação (canvas, SVG, WebGL, sprites ou motor 2D/3D), medir consumo na máquina-alvo e validar acessibilidade, desempenho e facilidade de manutenção. A imagem isométrica é uma referência visual; não obriga a usar um motor de jogo pesado.

## 9. Contratos/eventos conceptuais

Os nomes seguintes são propostas para discussão, não afirmam que estes eventos já existem:
- `request.received`
- `request.triaged`
- `mission.assigned`
- `mission.started`
- `mission.progress.updated`
- `mission.blocked`
- `mission.validation.started`
- `mission.completed`
- `agent.health.degraded`
- `agent.recovery.started`
- `agent.recovery.validated`
- `agent.activated`
- `department.created`
- `layout.changed`
- `external_help.dispatched`
- `external_help.response_received`
- `delivery.dispatched`
- `delivery.confirmed`

Cada evento real deverá ter identificador, timestamp, origem, entidade relacionada, correlação de missão/pedido e dados suficientes para auditar a mudança. Mapear para eventos atuais antes de acrescentar novos.

## 10. Regras não negociáveis

1. Estabilidade > funcionalidades.
2. Evidência real > pressupostos.
3. Controlo manual > automação destrutiva.
4. Investigar → decidir → alterar.
5. Preservar código e trabalho existente até prova de substituição segura.
6. Nenhuma percentagem de progresso inventada.
7. Nenhum pedido externo apresentado como enviado sem envio confirmado.
8. Nenhum agente reativado sem verificações de recuperação.
9. Nenhuma contratação/permissão crítica sem política e auditoria.
10. Não executar merges, resets, rebases, limpezas ou sincronizações como parte desta proposta.

## 11. Plano de implementação futuro

### Fase 0 — Recuperar uma base consistente
- Quando houver acesso ao PC, recolher estado read-only de todos os branches locais/remotos relevantes.
- Comparar históricos, working trees, commits não publicados e diferenças por ficheiro.
- Preservar snapshots/branches antes de qualquer reconciliação.
- Não misturar este documento conceptual com os merges pendentes.
- Confirmar contratos e APIs reais disponíveis no DGM-MAT.

### Fase 1 — Protótipo visual desligado
- Construir a composição de ecrã fiel à referência.
- Usar dados fictícios claramente identificados como demonstração.
- Validar navegação fixa esquerda, escritório central e chat direito.
- Não ligar ferramentas destrutivas nem executar tarefas reais.

### Fase 2 — Integração read-only
- Ligar snapshot de agentes, missões, pedidos e eventos reais.
- Exibir estados verdadeiros, incluindo estados desconhecidos.
- Validar reconexão, atualização, logs e comportamento quando o backend está indisponível.

### Fase 3 — Fluxo operacional
- Ligar atribuição de missões, validação, expedição e pedidos externos usando contratos já auditados.
- Exigir permissões, confirmação e auditoria para ações de impacto.

### Fase 4 — Enfermaria, formação e contratação
- Implementar diagnósticos e recuperação controlada.
- Implementar recrutamento/configuração, formação e avaliação por evidência.
- Testar falhas e impedir loops de recuperação.

### Fase 5 — Departamentos e remodelação
- Persistir departamentos, capacidades e layouts.
- Adicionar pré-visualização, aprovação e reversão.
- Medir consumo real de CPU/RAM e manter alternativa simplificada para hardware limitado.

### Fase 6 — Aceitação
- Testes de contrato, integração, segurança, reconexão e persistência.
- Confirmar que a animação nunca contradiz o backend.
- Documentar rollback e estado de entrega antes de qualquer merge.

## 12. Referências visuais

Os mockups gerados nesta conversa devem ser preservados como referências de design, não como screenshots de uma aplicação existente. O objetivo visual aprovado inclui:
- Interface empresarial escura com acentos azul/ciano.
- Navegação fixa à esquerda.
- Escritório isométrico grande ao centro.
- Chat, pedidos e atividade à direita.
- Painéis compactos para agentes, tarefas e métricas.
- Enfermaria com símbolo médico e estado de recuperação.
- Armazém com caixas/serviços acumulados, produção, expedição e viaturas.
- Formação, recrutamento, remodelação e novas divisões.

As imagens originais foram geradas durante a conversa e ainda precisam de ser anexadas como binários reais a esta branch; este documento não as finge como ficheiros já presentes no repositório.

## 13. Referências externas a avaliar — sem compromisso de adoção

- My Virtual Office: https://github.com/eliautobot/my-virtual-office
- Claude Office Visualizer / Pixel Agent Office: https://github.com/forgeekscn/pixel-agent-office

São pistas para avaliação técnica, não dependências aprovadas. Verificar licenças, atividade, arquitetura, segurança, recursos e integração com os contratos do DGM-MAT antes de reutilizar código.

---
**Próxima ação ao regressar ao PC:** auditar e reconciliar os branches com segurança primeiro; depois avaliar como integrar este conceito na arquitetura já existente. Não implementar nem fazer merge antes dessa etapa.


## 14. Adaptação ao hardware e renderização em camadas

O escritório deve suportar vários renderizadores substituíveis sobre o mesmo estado e os mesmos contratos: 3D quando as capacidades e os testes de desempenho o permitirem; 2D avançado/isométrico quando for mais adequado; 2D leve para máquinas modestas; e perfil mínimo com chat e uma personagem simples desenhada por traços. Deve existir também um modo sem animação. O perfil automático escolhe com base em capacidades e medições reais, com margem de recursos, mas o utilizador pode selecionar manualmente o modo. Se houver falhas ou perda de fluidez, a interface reduz a complexidade sem perder tarefas nem estado.

A interface funcional (chat, pedidos, memória, estado e segurança) não pode depender do 3D ou de qualquer motor de jogo. Trocar de renderizador nunca cria uma segunda fonte de verdade. Não assumir que a presença de WebGL garante bom desempenho; validar no hardware-alvo e manter sempre um fallback leve.

## 15. Rede de agentes em vários computadores

A arquitetura futura deve permitir que o DGM-MAT use workers autorizados em diferentes PCs: por exemplo, Harness num computador e Claude Code noutro, além de ferramentas locais, Ollama, ferramentas web e futuras APIs. O cérebro, a política, a memória e a validação permanecem no DGM-MAT; cada PC disponibiliza capacidades através de um gateway/adaptador e de um contrato estável.

A primeira versão distribuída deve usar registo manual e explícito dos nós, identidade individual, transporte encriptado, permissões mínimas, heartbeat e revogação. Um computador acessível na LAN não é automaticamente confiável. Começar com tarefas read-only e workspaces descartáveis; só depois permitir ações remotas aprovadas. Não expor serviços de agentes diretamente à Internet.

## 16. Política de ferramentas e custos

A preferência inicial é free/local-first: ferramentas locais gratuitas adequadas, serviços gratuitos já autorizados, outros nós autorizados e ferramentas web gratuitas. A seleção deve considerar também qualidade, confidencialidade, latência e limites. APIs pagas ficam previstas na arquitetura, mas só podem ser ativadas depois de o utilizador configurar e autorizar explicitamente o provedor e o orçamento. Nunca fazer chamadas pagas silenciosas.

A especificação detalhada, incluindo perfis, gateway, catálogo de capacidades, segurança de rede, etapas e critérios de aceitação, está em [Runtime adaptável e agentes distribuídos](DGM-MAT-ADAPTIVE-RUNTIME-AND-DISTRIBUTED-WORKERS-2026-10-12.md).
