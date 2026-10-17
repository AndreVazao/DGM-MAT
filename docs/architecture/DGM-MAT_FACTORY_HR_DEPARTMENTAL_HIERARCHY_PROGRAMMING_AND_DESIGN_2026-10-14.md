# DGM-MAT — Fábrica de Agentes, Recursos Humanos, hierarquia departamental, Programação e Design
**Data:** 2026-10-14  
**Estado:** Requisito de visão e arquitetura documentado; ainda não implementado nem validado em runtime.  
**Branch documental:** `docs/tooling-capability-audit-2026-10-14`

## 1. Objetivo e princípio orientador

Registar de forma duradoura a visão organizacional do DGM-MAT: uma organização digital com departamentos, chefias, equipas de agentes, Recursos Humanos (RH), uma fábrica que inclui laboratórios de investigação, e escritórios virtuais que mostram o trabalho real do sistema.

O DGM-MAT deve saber receber uma necessidade, identificar quem a deve tratar, investigar o que já existe, decidir se reutiliza/adapta/constrói uma solução, testar a solução e encaminhar o agente ou resultado para o departamento adequado. Deve também saber descobrir onde procurar informação sobre as próprias capacidades e repositórios, sem depender de alguém lhe repetir manualmente o mapa em cada tarefa.

**Regra fundamental:** a representação visual mostra a organização; não substitui nem determina a realidade operacional. O runtime, os registos persistentes, os contratos e os eventos verificáveis são a fonte da verdade.

Este documento regista intenção e requisitos. Não autoriza instalação de software, execução de código externo, concessão de permissões, pagamentos, alterações de produção, merge para `main` ou modificações de clones/Labs.

## 2. Hierarquia organizacional: boss, chefias, agentes principais e subagentes

A organização deve ter uma hierarquia explícita e consultável:

1. **Boss / direção:** define objetivos, prioridades, restrições e aprova decisões que excedem a autonomia delegada.
2. **Chefe de departamento:** responde pelo trabalho, distribuição de tarefas, coordenação, qualidade e comunicação do departamento.
3. **Agente principal / chefe de equipa:** coordena uma equipa especializada, divide o trabalho, atribui subtarefas, reúne resultados e verifica a integração.
4. **Subagentes / especialistas:** executam tarefas delimitadas, comunicam resultados e evidências ao agente principal.
5. **Ferramentas e serviços auxiliares:** não são automaticamente agentes; têm identificadores, permissões, estado e contratos próprios quando aplicável.

Cada departamento tem um chefe identificável e vários empregados/agentes conforme a carga e as necessidades. Um departamento pode ter várias equipas; cada equipa tem um agente principal e os seus subagentes. Se um departamento for pequeno, a mesma entidade pode acumular funções, mas as responsabilidades devem continuar explícitas nos registos.

O agente principal não deve limitar-se a encaminhar mensagens: deve manter o plano de trabalho da equipa, gerir dependências, evitar tarefas duplicadas, detetar conflitos, solicitar esclarecimentos quando necessário, integrar alterações e verificar o resultado conjunto. O chefe de departamento supervisiona a equipa e responde pela qualidade do departamento; não elimina a responsabilidade individual nem os registos de execução dos subagentes.

### Requisitos de coordenação
- Identificadores estáveis para departamentos, chefias, equipas, agentes e tarefas.
- Relações explícitas `reports_to`, `managed_by`, `member_of` e `delegated_to`.
- Objetivos, permissões, competências, dependências, prazos e critérios de aceitação definidos por tarefa.
- Comunicação estruturada entre agente principal e subagentes, com resultados, evidências, erros e estado.
- Um agente principal consolida resultados antes de apresentar uma conclusão ao chefe ou ao boss.
- Gestão de concorrência e conflitos de ficheiros; não permitir que dois agentes alterem a mesma área sem coordenação.
- Escalonamento para a chefia quando há bloqueio, ambiguidade, risco, conflito de requisitos ou necessidade de aprovação.
- Auditoria de quem decidiu, executou, verificou e aprovou cada alteração.
- Não confundir hierarquia visual com autorização técnica: as permissões reais são impostas pelo core e pelos contratos.

## 3. Identidade visual: agentes existentes e agentes próprios do DGM-MAT

A visualização deve distinguir duas origens, de forma imediata e consistente:

- **Pessoas:** agentes, ferramentas com identidade de agente ou trabalhadores digitais que já existiam e foram instalados, configurados ou integrados por nós antes de serem recrutados/criados pelo processo do DGM-MAT.
- **Robôs:** agentes que o próprio processo do DGM-MAT contratou, construiu, gerou ou configurou especificamente para responder a uma necessidade identificada pelo sistema.

A distinção é visual, mas tem de corresponder a metadados verificáveis. Cada agente regista, no mínimo, origem, data de criação/integração, versão, competências, departamento, chefe, agente principal, permissões, estado, tarefas e proveniência. A origem não muda apenas porque o agente muda de departamento ou de função. Se a origem for desconhecida, mostrar “por determinar” em vez de inventar uma categoria.

Os movimentos dos bonecos devem refletir eventos reais: deslocar-se para uma reunião quando a reunião existe, ir para o laboratório quando a tarefa está atribuída lá, ficar à espera quando há bloqueio e entrar em recuperação quando existe uma falha registada. Nunca mostrar atividade fictícia como prova de execução.

## 4. Fábrica de Agentes com laboratórios integrados

A fábrica é uma capacidade organizacional do DGM-MAT, não apenas uma animação nem necessariamente um único executável. Deve incluir espaços lógicos com responsabilidades distintas:

1. **Receção de necessidades e especificações:** recebe do RH a função pretendida, competências, limites, contexto, orçamento permitido e critérios de aceitação.
2. **Laboratórios de investigação:** pesquisam repositórios, projetos existentes, bibliotecas, skills, modelos, ferramentas, documentação e abordagens que possam resolver a necessidade.
3. **Laboratório de experiências:** avalia candidatos em isolamento e mede compatibilidade, segurança, qualidade, consumo de RAM/CPU, latência e dependências.
4. **Área de construção/configuração:** reutiliza, adapta ou cria agentes; prepara instruções, ferramentas e permissões mínimas.
5. **Controlo de qualidade:** executa testes unitários, de integração, regressão, segurança e critérios específicos da função.
6. **Integração e despacho:** regista a versão aprovada, prepara o posto de trabalho e encaminha o agente para o departamento de destino.
7. **Manutenção e recuperação:** recebe agentes com falhas, executa diagnóstico, conserva evidências e exige revalidação antes do regresso ao serviço.
8. **Arquivo de soluções:** conserva decisões, experiências, resultados, versões, licenças e razões para reutilizar ou rejeitar candidatos.

A fábrica deve gerir vários pedidos em paralelo, com filas, prioridades, dependências, limites de recursos, cancelamento seguro e estado persistente. Os laboratórios podem investigar sem que isso implique instalar ou executar automaticamente os projetos encontrados.

### Fluxo de fabrico e contratação
Pedido do boss → RH analisa a função → inventário de agentes existentes → investigação de opções → comparação reutilizar/adaptar/integrar/criar → aprovação quando necessária → ambiente isolado → testes e revisão → registo da identidade e proveniência → atribuição de permissões mínimas → despacho para o departamento → monitorização e avaliação.

Não é obrigatório criar um robô novo. A reutilização de um agente existente é preferível quando cumpre os requisitos, é segura e evita duplicação. A criação de um agente próprio só avança quando a evidência justifica essa escolha.

## 5. Departamento de Recursos Humanos (RH)

O RH recebe pedidos de reforço ou de novas competências e conduz um processo de recrutamento técnico, baseado em evidências.

### Responsabilidades
- Clarificar a função, o problema a resolver e os resultados esperados.
- Consultar o inventário de agentes, equipas, ferramentas e competências antes de procurar candidatos novos.
- Pesquisar repositórios e programas existentes, documentação oficial, licenças, manutenção, compatibilidade e requisitos.
- Comparar candidatos por adequação, fiabilidade, custo total, consumo de recursos, segurança, manutenção e facilidade de reversão.
- Recomendar uma de quatro opções: reutilizar um agente existente, requalificá-lo, integrar uma ferramenta/agente externo, ou construir um agente novo.
- Produzir uma ficha de recrutamento com fontes, evidências, riscos, dependências, permissões necessárias e testes de aceitação.
- Solicitar aprovação humana para custos, acessos sensíveis, execução externa, alterações persistentes ou efeitos irreversíveis.
- Enviar uma especificação validada à fábrica e acompanhar o processo até ao despacho.
- Registar a razão da decisão, incluindo quando não contratar/criar é a melhor escolha.

RH não pode considerar um README ou descrição promocional como prova suficiente de qualidade. Os candidatos devem avançar por níveis de verificação: identificado, origem/licença confirmada, revisto, testado em isolamento e aprovado para integração. Não há fallback pago silencioso, nem instalação automática só porque um repositório foi encontrado.

## 6. Departamento de Programação — prioridade estratégica

A Programação é um dos departamentos mais importantes do DGM-MAT e deve ser organizado como uma unidade de engenharia multidisciplinar, com chefia, agentes principais de projeto e especialistas por linguagem/tecnologia.

### Especialistas por linguagem
O objetivo é manter agentes especialistas para cada linguagem que seja realmente utilizada ou necessária nos projetos — por exemplo, Python, JavaScript/TypeScript, HTML/CSS, PowerShell, C#, Java, Rust, Go, SQL e outras à medida que a auditoria confirmar a necessidade. Esta lista é indicativa, não uma ordem para criar todos imediatamente.

Cada especialista deve manter conhecimento operacional atualizado sobre:
- sintaxe, semântica, tipos e características da linguagem;
- bibliotecas, frameworks, ferramentas de build e gestores de pacotes relevantes;
- convenções, padrões, arquitetura e práticas de manutenção;
- testes, depuração, profiling e análise de erros;
- segurança, dependências, compatibilidade e migrações;
- documentação oficial, versões suportadas e mudanças relevantes;
- integração com outras linguagens, APIs, protocolos e sistemas;
- limitações conhecidas e métodos para validar afirmações.

“Especialista” não significa alegar que sabe literalmente tudo. Significa ter uma área de responsabilidade clara, fontes consultáveis, capacidade de pesquisa, conhecimento versionado e um processo para reconhecer incerteza e confirmar informação atualizada.

### Programas com várias linguagens
Quando um programa envolve duas ou mais linguagens, a chefia da Programação nomeia um **agente principal de projeto** que coordena os especialistas necessários. Exemplo: frontend TypeScript, backend Python, scripts PowerShell e base de dados SQL.

O agente principal deve:
1. analisar a arquitetura e mapear componentes, linguagens, interfaces e dependências;
2. dividir o trabalho por especialidade sem perder a visão do sistema;
3. definir contratos comuns: APIs, esquemas, formatos, autenticação, erros, eventos e versões;
4. manter um plano de integração e evitar alterações incompatíveis;
5. pedir revisão cruzada aos especialistas quando uma alteração atravessa fronteiras;
6. executar ou solicitar testes unitários, de contrato, integração, regressão e end-to-end adequados;
7. consolidar os resultados e apresentar evidências, riscos residuais e estado real;
8. escalar conflitos ou incertezas para a chefia da Programação.

Os especialistas não devem trabalhar como silos independentes. Cada um é responsável pela sua área; o agente principal é responsável pela coordenação e integração do trabalho do projeto. A revisão independente continua necessária para mudanças de risco elevado.

### Segurança e preservação de trabalho
- Antes de alterar código existente, investigar callers, imports, contratos, testes, runtime, persistência e histórico Git.
- Preservar código antigo ou de função incerta até provar que pode ser substituído.
- Fazer alterações pequenas, rastreáveis e reversíveis.
- Testar localmente quando possível e evitar consumir CI/minutos desnecessários.
- Não fazer merge para `main`, deploy, push ou alterações de produção sem o gate apropriado.
- Respeitar a lista de repositórios autorizados; clones de terceiros, Labs e mirrors congelados são apenas leitura/estudo, salvo autorização explícita separada.
- Manter memória técnica do projeto atualizada após fases concluídas, com decisões e evidências, não apenas intenções.

## 7. Departamento de Design: UI, UX, experiência e sistema visual

O Design é um departamento próprio, com chefe, agente principal e especialistas que colaboram com Programação e Produto. Não deve ser tratado como uma tarefa estética de última hora.

A separação entre **back office**, **front office**, **UI** e **UX** deve ser explícita:

- **Back office:** lógica interna de trabalho, gestão de agentes e departamentos, filas, tarefas, permissões, estados, logs, memória, configurações, auditoria e ferramentas operacionais.
- **Front office:** interfaces através das quais o utilizador interage com o DGM-MAT — cockpit desktop, experiência móvel, terminal/conversa e eventuais interfaces externas.
- **UI (User Interface):** componentes visuais e interativos: navegação, painéis, tabelas, formulários, estados, tipografia, espaçamento, acessibilidade e consistência.
- **UX (User Experience):** percursos, clareza, hierarquia de informação, facilidade de aprender, prevenção de erros, feedback, acessibilidade e adequação ao contexto do utilizador.
- **Escritório virtual:** representação visual da organização real; é uma das interfaces do front office, não o back office nem a fonte da verdade.

### Responsabilidades do Design
- Pesquisar padrões, referências, soluções existentes e práticas de acessibilidade.
- Definir arquitetura de informação, navegação, fluxos e estados vazios/erro/bloqueio.
- Manter design system, componentes reutilizáveis, tokens, variantes e documentação.
- Trabalhar com ferramentas como Figma quando disponíveis e autorizadas; a integração com Figma é uma possibilidade a avaliar, não uma dependência obrigatória do core.
- Criar protótipos, testar fluxos, recolher feedback e entregar especificações claras à Programação.
- Rever a implementação real para detetar diferenças face ao desenho e problemas de usabilidade.
- Coordenar UI desktop, cockpit móvel, painéis operacionais e escritório virtual sem duplicar a lógica de negócio.
- Garantir que o modo económico é legível e funcional em hardware fraco, com navegação por listas/árvores mesmo sem gráficos avançados.

O agente principal de Design coordena especialistas de UI, UX, design system, acessibilidade, prototipagem e avaliação visual conforme a necessidade. A chefia do Design coordena-se com a chefia de Programação e com o boss para resolver prioridades e conflitos.

## 8. Back office e front office: separação arquitetural obrigatória

O core e o back office operacional devem continuar a funcionar sem depender de uma janela, navegador, renderizador 2D/3D ou aplicação móvel. As interfaces são clientes independentes.

Arquitetura conceptual:
- **Core/runtime:** estado real, orquestração, filas, tarefas, agentes, permissões, persistência, eventos e recuperação.
- **Serviços departamentais:** RH, fábrica, Programação, Design e restantes departamentos, implementados como capacidades/serviços com contratos explícitos.
- **API/contratos de observabilidade:** expõem estado e ações autorizadas de forma versionada e auditável.
- **Front office:** cockpit desktop/móvel, conversa/terminal e outras interfaces.
- **Renderizador do escritório virtual:** lê estado real e representa edifícios, departamentos, chefias, trabalhadores, tarefas e fluxos.

Fechar o cockpit ou desligar o renderizador não pode interromper tarefas do core. Se uma interface estiver indisponível, o trabalho deve continuar e o estado persistir; quando a interface regressar, volta a consultar o estado atual em vez de assumir que as suas animações anteriores são verdadeiras.

## 9. Escritório virtual adaptativo e representação de trabalho

O escritório deve representar a organização e permitir navegar por edifício, piso, departamento, equipa, agente, tarefa e evento. Cada departamento tem um chefe visível e os trabalhadores estão organizados em equipas sob agentes principais.

Modos gráficos:
- **Económico:** 2D leve, ícones ou bonecos simples, indicado para o PC atual e como modo sempre disponível.
- **Equilibrado:** 2.5D/isométrico low-poly, quando o benchmark permitir.
- **Avançado:** 3D mais elaborado apenas se houver capacidade comprovada.

A mudança de modo gráfico nunca altera permissões, lógica, estado, qualidade ou prioridades do core. Deve existir alternativa de navegação por listas e árvores. O edifício pode mostrar a fábrica e os laboratórios, RH, Programação, Design, back office, áreas de manutenção e outros departamentos. Os movimentos e indicadores são derivados de eventos verificáveis.

## 10. Descoberta autónoma: o DGM-MAT deve saber onde procurar

O DGM-MAT deve ter um **registo de capacidades e mapa de fontes** que permita encaminhar cada necessidade para o departamento, repositório, ferramenta ou fonte de conhecimento adequado.

Antes de pesquisar ou criar algo, o agente principal deve:
1. identificar o tipo de problema e a especialidade necessária;
2. consultar o catálogo de capacidades, agentes, skills, conectores, contratos e decisões anteriores;
3. consultar o mapa de repositórios e identificar a fonte de verdade de cada projeto;
4. verificar se a capacidade já existe no core, runtime, orchestrator, backend, contratos ou frontend autorizado;
5. pesquisar documentação oficial e fontes primárias; depois, quando apropriado, comparar repositórios e alternativas;
6. verificar licença, manutenção, compatibilidade, permissões, custo e requisitos de hardware;
7. registar as fontes e evidências e atualizar o catálogo quando a descoberta for relevante;
8. encaminhar o trabalho para o chefe e equipa adequados, ou pedir esclarecimento/aprovação quando necessário.

A descoberta autónoma não autoriza mutações autónomas. Encontrar código não equivale a aprová-lo; encontrar uma API não autoriza enviar-lhe dados; encontrar uma solução paga não autoriza contratá-la. Ações sensíveis têm gates de aprovação, limites de orçamento e trilho de auditoria.

## 11. Registos mínimos e estados comuns

Todos os departamentos devem usar contratos compatíveis, evitando inventários isolados e inconsistentes. Os registos devem incluir, quando aplicável:
- IDs estáveis de departamento, chefe, equipa, agente, tarefa, candidato e versão;
- origem e proveniência do agente/candidato;
- competências e limites conhecidos;
- responsável, agente principal, membros e dependências;
- estado, timestamps, tentativas, bloqueios e motivo;
- permissões, ambiente, recursos e orçamento autorizado;
- fontes, evidências, testes, decisões e aprovadores;
- resultados, riscos residuais e plano de reversão.

Estados de exemplo a formalizar no contrato: proposto, em investigação, selecionado, à espera de aprovação, em preparação, em teste, aprovado, despachado, ativo, bloqueado, em recuperação, suspenso, rejeitado e retirado. Os estados finais devem ser normalizados no contrato comum, com transições válidas e eventos auditáveis.

## 12. Segurança, recursos e governação

- Reutilizar primeiro o que já existe e é adequado.
- Priorizar soluções locais/gratuitas e compatíveis com Windows e hardware limitado.
- Nunca ativar APIs pagas ou subscrições silenciosamente.
- Isolar projetos externos e laboratórios de experiências.
- Usar permissões mínimas, credenciais protegidas e registo de ações.
- Exigir aprovação adequada para instalação persistente, acesso a contas, envio de mensagens, push, deploy, alteração de produção ou operações irreversíveis.
- Definir timeouts, limites de RAM/CPU, cancelamento, retentativas seguras e limpeza de ambientes de teste.
- Separar diagnóstico, proposta e mutação; nunca confundir uma recomendação com autorização.
- Disponibilizar cópias de segurança, reversão e recuperação testada.
- Não prometer disponibilidade literal de 100%; desenhar para isolamento de falhas, persistência, recuperação e degradação graciosa.

## 13. Fases sugeridas — requisitos primeiro, implementação após auditoria

1. **Auditoria read-only:** inventariar core/runtime/orchestrator, contratos, persistência, eventos, testes, repositórios e interfaces atuais.
2. **Modelo organizacional:** definir contratos para departamentos, chefias, equipas, agentes principais/subagentes, competências e proveniência.
3. **Mapa de capacidades e fontes:** documentar onde o DGM-MAT deve procurar antes de duplicar trabalho.
4. **RH e fábrica em modo controlado:** fluxo de recrutamento, comparação de candidatos, aprovações, testes isolados e registo de decisões.
5. **Programação multi-linguagem:** começar pelas linguagens comprovadamente usadas nos projetos autorizados; criar agentes especialistas e coordenação por projeto.
6. **Design e UI/UX:** definir fronteiras back/front office, design system, protótipos e integração opcional com Figma.
7. **API de estado e observabilidade:** garantir que interfaces leem o estado real do core.
8. **Cockpit 2D e escritório navegável:** apresentar chefias, equipas, pessoas/robôs, tarefas e estados.
9. **Modos 2.5D/3D:** apenas após benchmark e sem penalizar o core.
10. **Validação contínua:** testes de aceitação, segurança, recuperação, acessibilidade, consumo de recursos e coerência visual/operacional.

## 14. Critérios de aceitação da visão

A visão só pode ser considerada concretizada quando os testes demonstrarem que:
- cada departamento tem chefe e relações hierárquicas consultáveis;
- cada equipa tem agente principal e subagentes com tarefas e responsabilidades claras;
- um projeto multilíngue coordena especialistas e valida interfaces entre linguagens;
- RH verifica primeiro as capacidades existentes e regista a evidência da decisão;
- a fábrica testa e aprova agentes antes do despacho;
- pessoas e robôs correspondem à proveniência registada;
- o escritório apresenta estados reais, incluindo bloqueios e inatividade;
- back office/core continuam a funcionar se todas as interfaces visuais forem fechadas;
- UI/UX têm responsabilidades, design system e fluxo de revisão explícitos;
- o DGM-MAT consegue descobrir as fontes de verdade e encaminhar uma necessidade sem depender de memória implícita não documentada;
- alterações de risco são auditáveis, reversíveis e sujeitas aos gates adequados.

## 15. Relação com documentação existente

Este documento complementa, não substitui:
- [Catálogo mestre de capacidades](DGM-MAT_MASTER_CAPABILITY_CATALOG_2026-10-14.md)
- [Investigação sobre escritórios virtuais](DGM-MAT_VIRTUAL_OFFICE_RESEARCH_2026-10-14.md)
- [Requisitos de escritório adaptativo e core](DGM-MAT_ADAPTIVE_VIRTUAL_OFFICE_AND_CORE_REQUIREMENTS_2026-10-14.md)
- [Plano de independência do core e implementação do escritório](DGM-MAT_CORE_INDEPENDENCE_AND_VIRTUAL_OFFICE_IMPLEMENTATION_PLAN_2026-10-14.md)

**Limite atual:** esta é uma especificação documental. Não afirma que os departamentos, o RH, a fábrica, os agentes especialistas ou o escritório descritos já existem ou funcionam no runtime. A próxima etapa é auditar a implementação atual e mapear requisitos para capacidades comprovadas, lacunas e testes, sem duplicar módulos nem alterar repositórios não autorizados.

## 16. Proatividade soberana do DGM-MAT: investigação, propostas e melhoria controlada

### Intenção
O DGM-MAT deve ser proativo a identificar oportunidades para melhorar a qualidade, fiabilidade, eficiência e cobertura das funções que lhe foram confiadas. Proatividade significa observar evidências, reconhecer uma lacuna, investigar alternativas, formular propostas, testar hipóteses em ambientes seguros e apresentar resultados ao boss. **Não significa autoalteração irrestrita nem autorização para colocar mudanças em produção sem aprovação.**

A iniciativa pode nascer de um pedido explícito do boss (“audita este programa e vê como o podemos melhorar”) ou de uma lacuna detetada pelo próprio DGM-MAT através de métricas, testes falhados, erros recorrentes, tarefas bloqueadas, desempenho insuficiente ou funcionalidades em falta.

### Ciclo de melhoria proativa
1. **Detetar e justificar:** identificar uma lacuna com evidências observáveis e explicar o impacto real; separar factos, hipóteses e desconhecidos.
2. **Abrir uma proposta:** criar um registo de melhoria com objetivo, âmbito, critérios de sucesso, risco, recursos necessários, limitações e plano de reversão.
3. **Investigar (RH + laboratórios):** consultar o catálogo de capacidades e a memória técnica, procurar soluções internas reutilizáveis e pesquisar fontes externas, repositórios, documentação e programas relevantes. Registar proveniência, licença, manutenção, dependências, segurança e custos.
4. **Pedir trabalho à Programação:** RH ou o agente principal da melhoria pode emitir um pedido formal à chefia de Programação. A chefia designa um agente principal e os especialistas adequados, incluindo especialistas por linguagem quando necessário.
5. **Criar uma área de trabalho isolada:** antes de alterar um programa existente, identificar o repositório e a branch corretos, verificar estado Git, callers, imports, contratos, testes, dados persistentes e dependências. Criar uma branch de trabalho ou clone descartável a partir de uma base identificada, sem modificar a fonte original.
6. **Experimentar no laboratório:** implementar a alteração no ambiente isolado, guardar o diff e os artefactos, executar testes e comparar o comportamento anterior e posterior. Incluir testes de regressão, integração, segurança e recursos conforme o risco.
7. **Revisão independente:** um verificador que não seja apenas o autor avalia resultados, falhas, efeitos secundários, compatibilidade, evidências e reversão. Se falhar, corrigir no clone ou abandonar a proposta; não disfarçar falhas.
8. **Relatório ao boss:** apresentar problema, proposta, fontes, diff, testes executados, resultados comparativos, riscos residuais, custos, limitações e recomendação. Indicar claramente o que foi testado e o que não foi.
9. **Aprovação explícita:** o boss decide aprovar, pedir alterações, adiar ou rejeitar. A aprovação deve referir-se à proposta/diff/versão concreta, não ser interpretada como autorização geral para mudanças futuras.
10. **Implementação controlada:** só após aprovação, um processo de integração/implementação aplica a alteração à branch ou ambiente autorizado, com backup ou ponto de reversão, testes pós-integração e registo de auditoria.
11. **Verificação e observação:** comparar o resultado real com os critérios de sucesso; se surgirem regressões, parar a promoção e reverter de acordo com o plano aprovado.
12. **Aprendizagem documentada:** guardar decisão, evidências, lições e razão de aceitação/rejeição na memória técnica apropriada, sem incorporar como verdade uma hipótese que não foi confirmada.

### Departamento de Implementação e Integração
Fica proposta a criação de um **Departamento de Implementação e Integração**, ligado operacionalmente à fábrica e aos laboratórios, mas com responsabilidades distintas:
- gerir branches/ambientes de teste e clones de trabalho autorizados;
- preparar builds e aplicar mudanças aprovadas;
- executar pipelines de validação e testes pós-integração;
- manter backups, artefactos, diffs, versões e planos de reversão;
- confirmar que a mudança aplicada corresponde exatamente à versão aprovada;
- produzir evidências de implementação e devolver o resultado ao boss e à chefia responsável.

Este departamento não deve ser o único a validar o seu próprio trabalho: revisão independente e testes automatizados apropriados continuam necessários. Não deve poder aprovar por si só alterações de produção, permissões, custos ou efeitos externos para os quais não tenha autorização explícita.

### Regras de segurança para clones e repositórios
- Um clone de experiência é descartável e isolado; não é uma licença para modificar o upstream nem para sincronizar automaticamente com ele.
- Não tocar em clones de terceiros, Labs, mirrors congelados ou repositórios fora do âmbito autorizado.
- Não fazer merge para `main`, push, deploy ou alterações a dados persistentes apenas porque os testes locais passaram.
- Verificar licenças e obrigações antes de reutilizar código ou copiar implementações externas.
- Não utilizar credenciais reais nem dados de produção em laboratórios, salvo procedimento explicitamente autorizado e protegido.
- Se o estado da fonte original, a origem do código ou o impacto forem desconhecidos, parar e pedir esclarecimento.
- Todas as operações devem ser auditáveis e reversíveis na medida tecnicamente possível.

### Graus de autonomia
- **Autónomo:** observar métricas, consultar documentação autorizada, inventariar capacidades, detetar oportunidades, criar propostas e executar testes não destrutivos em ambientes aprovados.
- **Autonomia condicionada:** criar branches/clones, instalar dependências, executar código externo ou usar recursos adicionais apenas dentro de políticas, limites e ambientes previamente autorizados.
- **Aprovação obrigatória:** integrar em branches protegidas, alterar runtime ou dados persistentes, instalar serviços permanentes, conceder permissões, aceder a credenciais, enviar dados para serviços externos, incorrer em custos, fazer push/deploy ou executar ações irreversíveis.
- **Proibido por defeito:** contornar gates, alterar a própria política de segurança, apagar evidências, ocultar falhas, aprovar o próprio trabalho de alto risco ou usar fallback pago silencioso.

### Critérios de aceitação
A proatividade de melhoria só está demonstrada quando o DGM-MAT consegue identificar uma lacuna sustentada por evidências, formular uma proposta rastreável, investigar alternativas, testar uma alteração isoladamente, comparar resultados, apresentar o relatório ao boss e aguardar uma decisão antes da integração. Deve ser possível rejeitar uma proposta sem qualquer alteração na fonte original.

## 17. Distinção obrigatória: proatividade do DGM-MAT versus Sovereign Trader

A palavra “proatividade” não tem exatamente o mesmo significado nos dois projetos e os seus âmbitos não devem ser confundidos.

### DGM-MAT — proatividade operacional e melhoria de software controlada
O DGM-MAT pode identificar oportunidades de melhoria do seu próprio funcionamento e das ferramentas autorizadas, investigar, desenhar soluções, experimentar em clones, coordenar RH/Programação/Laboratório/Implementação e apresentar propostas ao boss. Pode desenvolver um agente novo quando o processo de RH/fábrica o justificar. **A alteração do programa original e a sua promoção para uso real continuam sujeitas a aprovação e gates.** Não se pretende autoevolução irrestrita.

### Sovereign Trader — proatividade de investigação de oportunidades financeiras
O Sovereign Trader deve ser proativo na pesquisa, análise e monitorização de oportunidades para procurar retornos financeiros: analisar mercados, instrumentos, estratégias, condições, custos, liquidez, risco, cenários e evidências; comparar hipóteses; detetar alterações relevantes; produzir oportunidades classificadas e relatórios para decisão.

O objetivo é que o sistema não fique à espera de uma pergunta para começar a investigar dentro dos parâmetros autorizados. Deve procurar oportunidades de forma disciplinada e comunicar também quando não encontra uma oportunidade suficientemente fundamentada. A proatividade **não** significa garantir lucros, aumentar risco automaticamente, negociar sem autorização, alterar estratégias de produção por conta própria ou reescrever o seu próprio código.

A pesquisa financeira deve distinguir dados observados, inferências, hipóteses e resultados históricos; considerar custos, slippage, liquidez, drawdown e risco de perda; validar estratégias em backtests e paper trading antes de qualquer utilização real; evitar sobreajuste e enviesamento de sobrevivência; e respeitar os limites do Risk Engine e do RealModeGuard. PAPER-first mantém-se como regra, e a passagem a REAL exige as aprovações e guardrails definidos para o projeto. Não há promessa de retorno nem “dinheiro garantido”.

### Separação entre os projetos
- O Sovereign Trader mantém escritório, processos, estado, contratos e ciclo de vida próprios; não depende do DGM-MAT, Mades ou de outros programas para executar a sua lógica essencial.
- Não transferir automaticamente autonomia de desenvolvimento do DGM-MAT para o Sovereign Trader.
- O DGM-MAT pode ajudar a pesquisar ou desenvolver ferramentas apenas quando explicitamente autorizado, mas isso não dá ao DGM-MAT controlo sobre decisões de trading nem elimina as barreiras de segurança do Sovereign Trader.
- Os dois projetos devem manter documentação e auditoria separadas, com integrações opcionais e explícitas em vez de dependências implícitas.
