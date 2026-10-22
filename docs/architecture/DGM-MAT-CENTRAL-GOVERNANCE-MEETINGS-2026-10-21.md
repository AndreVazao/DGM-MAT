# DGM-MAT — Reuniões de Governação, Decisão e Criação de Departamentos

**Data:** 2026-10-21  
**Estado:** contrato arquitetural proposto para implementação; não prova que reuniões persistidas ou animações já existam  
**Âmbito:** DGM-MAT Central, departamentos, agentes, Laboratório, cockpit PC/mobile e escritório virtual  
**Relação normativa:** subordinado à Constituição Arquitetural DGM-MAT e ao Modelo Canónico de Operação end-to-end.

## 1. Princípio fundamental

As reuniões são um mecanismo real de governação do cérebro central, não uma animação do escritório. O DGM-MAT Central decide quando uma questão precisa de reunião, identifica os participantes necessários, prepara a agenda e reúne contributos, evidências, alternativas, riscos e recomendações. O escritório virtual é apenas uma representação opcional desse processo.

A existência de uma sala desenhada, de avatares sentados ou de animação de conversa não constitui prova de reunião. Uma reunião só existe operacionalmente quando tem um registo persistido, um ID estável, participantes identificados, agenda, contributos e estado. A sala de reuniões é a projeção visual desse registo.

O proprietário humano mantém a autoridade final sobre ações que exigem a sua aprovação. O avatar do CEO representa visualmente a direção e nunca aprova por si só: uma aprovação sensível requer identidade autenticada, intenção explícita e um evento auditável.

## 2. Quando convocar uma reunião

O DGM-MAT deve avaliar a necessidade de reunião durante o planeamento e a governação da missão. Os seguintes casos exigem uma reunião formal, salvo se existir uma política explícita mais restritiva:

- **Criação, divisão, fusão ou encerramento de departamento.**
- **Criação, recrutamento, promoção, desativação ou alteração material de responsabilidades de agentes.**
- **Decisão que afete dois ou mais departamentos**, incluindo dependências, interfaces, prioridades ou recursos partilhados.
- **Mudança arquitetural relevante**, alteração de contrato público ou decisão difícil de reverter.
- **Conflito entre recomendações**, risco elevado, bloqueio recorrente ou desacordo entre responsáveis.
- **Decisão que exija autorização do proprietário** ou possa alterar permissões, credenciais, custos, dados, serviços externos ou produção.

Tarefas rotineiras, reversíveis e já autorizadas podem prosseguir sem reunião. O sistema deve explicar por que convocou uma reunião ou por que a considerou desnecessária quando isso for relevante; não deve convocar reuniões sem propósito apenas para animar o escritório.

## 3. Tipos de reunião e participantes

### 3.1 Reunião de departamento

Participantes mínimos: CEO/direção quando a decisão exigir supervisão, responsável do departamento e agentes especialistas realmente envolvidos. Outros participantes são convidados apenas se houver uma contribuição concreta a dar.

Exemplos: rever um problema de UI com Design; avaliar um bug com Engenharia e QA; rever cobertura e fontes com Pesquisa.

### 3.2 Reunião interdepartamental

O CEO/direção deve participar quando há uma decisão interdepartamental a tomar, para acompanhar o contexto global, coordenar prioridades e dar o aval dentro da sua autoridade. Os departamentos envolvidos devem estar representados por responsáveis ou delegados reais e relevantes.

Exemplo: Front Office/UI define a necessidade e os critérios de experiência; Programação avalia arquitetura, implementação e dependências; Pesquisa apresenta fontes, opções e evidências. QA pode avaliar riscos e critérios de aceitação. Cada departamento contribui com a sua especialidade, sem fingir que todos sabem tudo.

A reunião deve distinguir:
- factos e evidências verificadas;
- hipóteses ainda por confirmar;
- propostas e recomendações de cada departamento;
- riscos, contrapartidas, dependências e custos;
- desacordos e informação em falta;
- decisão tomada, responsável e condições.

### 3.3 Reunião do Laboratório para criar departamentos ou agentes

O Laboratório prepara a proposta; não se concede a si próprio autorização para alterar a organização. A proposta deve incluir, conforme aplicável:

- missão, problema e benefício esperado;
- âmbito, responsabilidades e limites explícitos;
- capacidades e competências necessárias;
- chefe, agentes e dependências propostas, sem os apresentar como já existentes;
- contratos/APIs, dados e ferramentas necessários;
- requisitos de segurança, permissões e isolamento;
- impacto estimado em CPU/RAM, armazenamento, rede, tempo e custos;
- alternativas, incluindo não criar nada ou reutilizar um departamento existente;
- plano de testes/sandbox, critérios de sucesso, manutenção e reversão.

O CEO/direção revê a proposta. Quando a decisão exige autoridade do proprietário, o DGM-MAT solicita a aprovação explícita do proprietário autenticado. Só depois da aprovação e das verificações de política é permitido iniciar a criação efetiva. A aprovação da proposta não significa que a implementação, contratação ou ativação já terminou: cada etapa tem estado e evidência próprios.

## 4. Ciclo de vida de uma reunião

Estado recomendado:

`proposed → prepared → awaiting_participants → in_progress → decision_pending → approved | rejected | needs_revision | deferred`

Após a decisão, a reunião pode passar para `actions_pending` e finalmente `closed`. Cancelamentos e falhas de persistência devem ser estados explícitos, não apagamento do histórico.

1. **Detetar:** classificar a decisão e a necessidade de reunião durante o planeamento.
2. **Convocar:** criar registo persistido com `meeting_id`, `correlation_id`, tipo, motivo, prioridade, decisor e departamentos envolvidos.
3. **Preparar:** gerar agenda, contexto relevante, perguntas, critérios de decisão e fontes de evidência.
4. **Convidar:** selecionar pessoas/agentes existentes a partir do catálogo real. Participantes indisponíveis ficam marcados como indisponíveis; não são substituídos silenciosamente por entidades fictícias.
5. **Reunir contributos:** recolher análises independentes, prós/contras, riscos, estimativas e recomendações. Registar proveniência e versão dos contributos.
6. **Debater e reconciliar:** expor contradições e lacunas; solicitar pesquisa adicional se a evidência for insuficiente. Não resolver desacordos por votação automática ou maioria de modelos sem critério explícito.
7. **Decidir:** registar resultado, fundamentação, condições, objeções relevantes e autoridade que decidiu. Se faltar aprovação necessária, manter a decisão pendente.
8. **Executar ações aprovadas:** criar tarefas vinculadas à reunião apenas após as aprovações necessárias. Cada ação usa o fluxo normal de missão, permissões, execução e validação do DGM-MAT.
9. **Verificar e fechar:** validar resultados, atualizar a reunião com evidências e manter ligação a tarefas, artefactos e decisões posteriores.

Se a reunião não puder obter dados ou participantes necessários, fica bloqueada, adiada ou marcada como incompleta. Não se inventa consenso.

## 5. Registo persistente mínimo

O modelo de dados deve permitir consultar, após reinício ou desconexão:

- `meeting_id`, `schema_version`, `correlation_id`, tipo, título, objetivo e estado;
- quem convocou, decisor, autoridade exigida e aprovações registadas;
- departamentos e participantes com IDs estáveis, papéis e disponibilidade observada;
- agenda, contexto/fonte, contributos, recomendações e timestamps;
- evidências e proveniência, factos, hipóteses, riscos, objeções e lacunas;
- opções avaliadas e critérios usados para comparar prós e contras;
- decisão, fundamentação, condições, validade/expiração se aplicável;
- ações/tarefas associadas, responsáveis, dependências, estados e resultados;
- histórico de alterações, cancelamentos, falhas e eventos de auditoria.

Não guardar segredos nem copiar conversas completas para a telemetria visual por defeito. O registo deve apontar para fontes e artefactos autorizados.

## 6. Separação entre decisão, aprovação e execução

Estes são eventos diferentes:

- **Recomendado:** um departamento apresenta uma proposta.
- **Decidido:** a autoridade competente escolhe uma opção.
- **Aprovado:** a aprovação exigida foi dada por uma identidade autorizada.
- **Despachado:** as tarefas foram criadas e atribuídas.
- **Executado:** o handler/worker realizou o trabalho e produziu evidência.
- **Validado:** os critérios de aceitação foram verificados.

Nenhum destes estados deve ser inferido a partir de uma animação, de uma mensagem textual, de um HTTP 200 ou da presença de um agente na sala. Rejeitar ou adiar uma proposta não é uma falha do sistema: é um resultado de governação válido.

Uma reunião não pode, por si só, iniciar Ollama, alterar configuração, conceder permissões, contratar/criar agentes, publicar código, executar ações destrutivas ou chamar serviços externos. Essas ações passam pelos contratos e autorizações normais, com confirmação explícita quando exigida.

## 7. Sala de reuniões e projeção visual

A sala de reuniões deve existir no mapa lógico do escritório e poder acolher reuniões de departamento, interdepartamentais e do Laboratório. A sala pode mostrar:

- título e objetivo da reunião;
- departamentos e participantes reais;
- agenda e fase atual;
- propostas, prós/contras, riscos e questões por resolver;
- decisão pendente, aprovações exigidas e ações associadas.

A apresentação é adaptativa: lista/timeline no modo económico; personagens sentadas e animações leves no modo 2D/2.5D; 3D apenas quando suportado. Movimentos e gestos são cosméticos e subordinados ao estado do registo. A interface deve permitir consultar a reunião sem animação e não deve manter um processo de reunião apenas para sustentar uma cena visual.

As reuniões e os relatórios devem ser consultáveis no cockpit PC; o mobile reutiliza a mesma fonte de verdade, permissões e IDs. Nenhum cliente cria um cérebro ou registo paralelo.

## 8. Critérios de aceitação

- Um pedido de criação de departamento ou de novos agentes produz uma proposta e uma reunião de governação antes de qualquer alteração efetiva.
- Uma decisão entre departamentos convoca os departamentos relevantes e inclui o CEO/direção quando a decisão exige coordenação ou aval.
- O exemplo Front Office + Programação + Pesquisa permite recolher contributos distintos, evidências, prós/contras, riscos e recomendações.
- Decisão e aprovação são estados/eventos separados e verificáveis.
- Não se cria nem ativa um departamento/agente antes de concluir as aprovações exigidas.
- A reunião, as decisões e as ações sobrevivem ao refresh, à perda de ligação e ao reinício suportado.
- Os participantes provêm do catálogo real; entidades ausentes ou indisponíveis são assinaladas sem serem inventadas.
- Um desacordo ou falta de evidência resulta em pedido de investigação, revisão ou adiamento, não em consenso fictício.
- A UI e o escritório refletem o registo real; desativar o renderizador não interrompe a reunião nem o core.
- Testes cobrem pelo menos: reunião interdepartamental, proposta de novo departamento, aprovação pendente, rejeição/adiamento, participante indisponível, persistência e prevenção de execução antes da aprovação.

## 9. Plano de implementação sugerido

1. **Contrato central:** modelos versionados para reunião, participante, contributo, decisão, aprovação e ação; persistência e API read-only para consulta.
2. **Orquestração:** detetor de decisões que exigem reunião; seleção de departamentos/participantes pelo catálogo; agenda e registo de contributos.
3. **Governação:** ligação às permissões e aprovações existentes; bloqueio de ações não autorizadas; trilho de auditoria.
4. **Piloto funcional em texto:** testar uma reunião interdepartamental e uma proposta de novo departamento sem animação nem efeitos externos.
5. **Cockpit:** agenda, contributos, evidências, decisão e ações pendentes com estados reais.
6. **Escritório virtual:** projetar a reunião na sala física, com movimento/animação opcional e modo económico.
7. **Validação no PC Windows:** provar o ciclo real, a persistência, a recuperação e os limites de autorização. GitHub Actions isolado não substitui esta prova.

**Estado final deste documento:** define o comportamento pretendido. A implementação de reuniões persistidas, APIs, convocação automática por política, decisão/aprovação e sala animada permanece por verificar até existir código, testes e evidência de runtime.
