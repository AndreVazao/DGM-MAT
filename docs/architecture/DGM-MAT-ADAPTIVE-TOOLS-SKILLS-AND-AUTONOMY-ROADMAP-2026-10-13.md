# DGM-MAT — matriz evolutiva de ferramentas, agentes e autonomia

**Data:** 2026-10-13  
**Estado:** pesquisa e proposta arquitetural; não implementado nem aprovado para instalação  
**Branch:** `docs/digital-headquarters-concept-2026-10-12`

## 1. Objetivo estratégico

DGM-MAT deve evoluir de um orquestrador local assistido para uma empresa digital capaz de executar trabalho contínuo em várias áreas, mantendo controlo central, memória fiável, especialização departamental, auditoria e capacidade de operar em máquinas diferentes.

A ambição de autonomia total é um objetivo de longo prazo, não uma capacidade que se possa declarar antecipadamente. “Trabalhar sozinho” significa concluir missões dentro de limites verificáveis, reconhecer incerteza, recuperar de falhas, pedir autorização quando necessário e provar resultados. Não significa acesso ilimitado, autoalteração sem controlo ou ausência de revisão para ações de alto risco.

## 2. O que é próprio do DGM-MAT e o que é substituível

**Núcleo próprio e duradouro:**
- autoridade, hierarquia e política;
- contratos de tarefas, eventos e estados;
- memória nuclear, proveniência e reconciliação;
- registo de capacidades, permissões e recursos;
- deduplicação, limites de delegação, cancelamento e prevenção de ciclos;
- validação independente, auditoria, aprovação e rollback;
- identidade visual e projeção do estado real do escritório.

**Adaptadores substituíveis:**
- modelos locais ou remotos;
- runtimes/harnesses de programação;
- agentes de investigação, browser, terminal e documentação;
- ferramentas MCP;
- motores de workflow, indexação e avaliação;
- renderização do escritório 3D/2D/chat;
- workers noutros computadores.

O DGM-MAT não deve depender de um único fornecedor nem delegar a uma ferramenta externa a propriedade da memória, política ou autoridade central. Um worker externo recebe uma tarefa delimitada e devolve artefactos e evidências.

## 3. Perfis por hardware

As classes seguintes são perfis de planeamento, não requisitos rígidos. A classificação real deve ser medida pelo agente de diagnóstico local.

### Perfil A — PC antigo e limitado

Contexto conhecido do projeto: máquina com cerca de 2 núcleos e aproximadamente 3 GB de RAM utilizável pelo sistema; modelos locais muito pequenos (até cerca de 4B, segundo a experiência reportada pelo utilizador). Não tentar manter vários modelos nem vários agentes de inferência pesados ativos ao mesmo tempo.

- Um processo de orquestração leve e persistente; SQLite/JSONL para estado local quando adequado.
- Uma única tarefa de inferência local de cada vez, com fila e limite de memória.
- Modelo local pequeno para classificação, extração, resumos curtos, rotulagem e tarefas estritamente delimitadas; não assumir qualidade de programação complexa.
- Usar ferramentas já instaladas e trabalhadores remotos autorizados apenas quando disponíveis e autorizados.
- Preferir execução sequencial, contexto compacto, caches, timeout, checkpoint e retomada.
- UI em chat ou 2D leve; sem 3D obrigatório nem serviços de fundo duplicados.
- Evitar Docker/containers pesados, múltiplos servidores de modelos, embeddings constantes e grandes indexações até serem medidos.
- Se a máquina estiver saturada, pausar a inferência e manter apenas monitorização/filas.

### Perfil B — PC intermédio

- Um modelo local principal quantizado e, se a medição permitir, um pequeno modelo auxiliar.
- Workers isolados por tarefa; concorrência baixa e ajustável.
- Indexação incremental, testes locais e observabilidade.
- Interface 2D/isométrica; 3D apenas se os testes de frame time, RAM e GPU o justificarem.
- Agentes externos em modo de preparação/revisão, com permissões separadas.

### Perfil C — PC novo e forte

- Modelos locais maiores, quantização adequada à VRAM/RAM e possível servidor de inferência dedicado.
- Paralelismo controlado entre tarefas independentes, com quotas por agente.
- Workers locais separados por domínio, sandboxes descartáveis e execução de testes em paralelo.
- Índices de código/documentos maiores e avaliação de qualidade automatizada.
- Renderização 3D/efeitos avançados se medidos como estáveis; interface e estado não dependem do renderer.
- Possibilidade de nó central e workers em máquinas adicionais na rede privada.

### Perfil D — corporação distribuída

- DGM-MAT central como plano de controlo, vários nós inscritos e revogáveis, gateways por máquina e catálogo de capacidades.
- Fila de trabalho durável, leases/heartbeats, retry com limites, idempotência, checkpoints e armazenamento de artefactos.
- Identidade e autorização por nó/agente, comunicação autenticada e cifrada; sem portas administrativas expostas diretamente à Internet.
- Alocação por custo, latência, especialidade, privacidade, capacidade e disponibilidade.
- Workers externos podem desaparecer sem perda da memória canónica ou do controlo do sistema.

## 4. Catálogo de ferramentas para avaliar

Nenhuma ferramenta desta secção está aprovada para instalação automática. A seleção final exige inspeção de licença, maturidade, dependências, segurança, custo, recursos e compatibilidade com contratos DGM-MAT. As referências abaixo são pontos de investigação, não garantias de qualidade.

### 4.1 Runtimes e harnesses locais

**LocalHarness** — https://github.com/ahwurm/localharness  
- Descreve agentes configurados em YAML, endpoints compatíveis com OpenAI, ferramentas, memória, permissões deny-first e hierarquia de subagentes.
- Hipótese de valor: estudar o modelo de configuração e permissões sem ligar imediatamente ao runtime central.
- Verificar primeiro: maturidade, dependências, testes, comportamento de execução de ferramentas e consumo real. Não adotar só porque o conceito encaixa.

**Forge** — https://github.com/andreglegg/forge  
- Harness de programação local-first, direcionado a modelos pequenos/locais; o projeto declara estado public alpha.
- Hipótese de valor: candidato a worker experimental em sandbox no PC antigo, caso os requisitos de Node e recursos sejam compatíveis.
- Precaução: o repositório descreve atualização automática em determinadas instalações globais; avaliar/pinar versão e desativar qualquer comportamento de atualização não desejado antes de confiar-lhe código.

**Felix** — https://github.com/sausheong/felix  
- Gateway de agentes autoalojado, binário Go, memória persistente, MCP, políticas de ferramentas e subagentes.
- Hipótese de valor: estudar a simplicidade operacional e o desenho de memória/ferramentas.
- Precaução: validar o uso real de RAM, superfície HTTP, execução de comandos, armazenamento de segredos e modelo de permissões. Não o transformar no cérebro alternativo do DGM-MAT.

**DeepSeek Harness** — https://github.com/deepseek-ai/deepseek-harness  
- Já registado no pacote de pesquisa anterior; candidato experimental de interface/workers.
- Precaução: isolamento forte, workspace autorizado, versão fixada e nenhuma credencial valiosa no ambiente. Não executar diretamente sobre a pasta principal sem sandbox e backup.

### 4.2 Orquestração e workflows

**LangGraph** — https://github.com/langchain-ai/langgraph  
- Avaliar se for necessária uma máquina de estados explícita, checkpoints, pausa/retoma e aprovação humana.
- Usar apenas se resolver uma lacuna real; não reconstruir por cima dos contratos existentes sem auditoria.

**CrewAI** — https://github.com/crewAIInc/crewAI  
- Útil como referência de papéis e equipas para protótipos.
- Não permitir conversação aberta entre agentes sem limites; a orquestração do DGM-MAT continua a decidir estado, prioridade e orçamento.

**Microsoft Agent Framework** — https://github.com/microsoft/agent-framework  
- Candidato a avaliar para integrações Python/.NET e workflows no ecossistema Microsoft.
- Verificar requisitos, maturidade e se duplica capacidades existentes.

**OpenAI Agents SDK** — https://github.com/openai/openai-agents-python  
- Referência de handoffs, ferramentas e guardrails; uso de serviços/modelos remotos pode implicar envio de dados e custo.
- Só usar providers remotos com configuração e autorização explícitas.

**LlamaIndex Workflows** — https://github.com/run-llama/llama_index  
- Candidato para fluxos centrados em documentos, ingestão e transformação de conhecimento.
- Manter proveniência e validação no DGM-MAT, não num índice secundário opaco.

### 4.3 Programação e engenharia

**Aider** — https://github.com/Aider-AI/aider  
- Agente de programação orientado a Git e alterações rastreáveis; candidato a worker que prepara diffs.
- Avaliar modelos compatíveis, tamanho de contexto e disciplina de alterações.

**Continue** — https://github.com/continuedev/continue  
- Integração de assistência no editor, com modelos configuráveis e ecossistema de extensões.
- Bom candidato para o posto humano de programação, mas a sua extensão/serviço não deve receber permissões globais por defeito.

**OpenHands** — https://github.com/All-Hands-AI/OpenHands  
- Mais orientado a tarefas de engenharia multi-etapa e ambientes isolados.
- Pode ser pesado para o PC antigo; priorizar um PC forte ou sandbox remota autorizada.

**SWE-agent** — https://github.com/SWE-agent/SWE-agent  
- Referência e candidato para tarefas de resolução de issues com avaliação reproduzível.
- Não assumir que um benchmark garante correção no nosso repositório; exigir testes e revisão.

**Claude Code / Claude Code Free, Codex, ferramentas existentes do utilizador**  
- Tratar cada uma como worker/adaptador cuja disponibilidade, quotas, licença e acesso podem mudar.
- Nunca depender de uma única ferramenta ou presumir que uma conta gratuita oferece automação ilimitada.
- O DGM-MAT deve manter o estado e os artefactos para retomar com outro worker se uma quota acabar.

### 4.4 Ferramentas de protocolo e capacidades

**MCP** — https://modelcontextprotocol.io/  
- Interface para expor ferramentas e recursos a agentes; não é, por si só, um sistema de autorização central.
- Cada servidor MCP precisa de identidade, allowlist de ferramentas, escopo de dados, timeout, registo de chamadas e política de aprovação.
- Não conceder a todos os agentes todos os servidores MCP.

**Ollama** — https://ollama.com/  
- Opção para inferência local e modelos substituíveis; o modelo escolhido tem de caber no hardware real.
- Medir memória, latência e qualidade no nosso conjunto de tarefas antes de atribuir funções.

**llama.cpp** — https://github.com/ggml-org/llama.cpp  
- Motor de inferência local com foco em execução eficiente em hardware diverso.
- Avaliar apenas se oferecer uma vantagem mensurável sobre a instalação existente.

**Playwright** — https://github.com/microsoft/playwright  
- Automação de browser e testes de interface; manter browser em perfil isolado, sem cookies pessoais ou sessões privilegiadas partilhadas com workers.
- Captchas, login e ações sensíveis continuam a exigir fluxo autorizado e intervenção humana quando aplicável.

### 4.5 Observabilidade, testes e memória

- **OpenTelemetry** — https://opentelemetry.io/ : rastreio de tarefas, chamadas, latências e falhas; não incluir segredos em traces.
- **pytest** — https://github.com/pytest-dev/pytest : testes automatizados do backend Python quando aplicável.
- **Vitest** — https://github.com/vitest-dev/vitest : testes de componentes e lógica JavaScript/TypeScript quando aplicável.
- **Playwright** — testes de ponta a ponta da UI em ambiente de teste.
- **SQLite** — persistência local de estado e eventos quando a carga e o padrão de escrita o permitirem; definir backups e migrações.
- **Git** — diffs, branches e reversibilidade; cada worker deve trabalhar em branch/worktree/sandbox atribuída e nunca fazer merge para a branch principal sem a política de aprovação aplicável.

Não instalar todos estes componentes. São candidatos para comparar com os mecanismos já existentes no DGM-MAT.

## 5. Skills: biblioteca interna e portabilidade

As skills devem ser instruções modulares, versionadas e auditáveis, e não permissões escondidas. Cada skill terá:
- identificador e versão;
- objetivo e condições de ativação;
- entradas, saídas e artefactos;
- ferramentas necessárias e escopo mínimo;
- riscos, proibições e aprovações;
- critérios de sucesso e testes;
- proveniência/licença das fontes;
- compatibilidade de runtime;
- histórico de alterações e avaliação.

Biblioteca inicial proposta:
1. auditoria read-only de repositório/branches/working tree;
2. preservação de snapshots e deteção de divergências;
3. pesquisa documental com fontes e nível de confiança;
4. decomposição de tarefas e dependências;
5. implementação backend/API por contrato;
6. implementação frontend/UI/UX por contrato;
7. revisão independente de diff;
8. testes, regressões e relatório de evidências;
9. diagnóstico de bugs e causa-raiz;
10. análise de permissões/segredos/MCP;
11. comparação de scripts e consolidação com backup;
12. documentação de decisões/memórias;
13. avaliação de capacidade de hardware e perfil adaptativo;
14. gestão de incidentes, pausa e rollback;
15. avaliação de novos agentes e contratação controlada.

As skills são portáveis entre workers apenas na medida em que o runtime e as ferramentas suportem os contratos. Adaptadores traduzem a skill para cada runtime; não assumir compatibilidade automática de formatos. Uma skill não pode conceder acesso que o agente não possui.

## 6. Aprendizagem e autoevolução como empresa

O ciclo de melhoria deve ser fechado por evidência:

1. Observar uma falha, desperdício ou oportunidade com métricas/relatório.
2. Registar hipótese e impacto esperado.
3. Consultar a memória e o histórico para evitar repetir experiências.
4. Propor alteração isolada a uma skill, workflow, contrato ou adaptador.
5. Testar em sandbox e comparar com baseline.
6. Verificar qualidade, segurança, recursos e regressões.
7. Obter aprovação conforme o risco.
8. Publicar em branch/versão identificada, monitorizar e reverter se necessário.
9. Atualizar memória com o resultado real, incluindo tentativas falhadas.

**Autonomia graduada:**
- Nível 0: observação e recomendação.
- Nível 1: executar tarefas read-only.
- Nível 2: preparar alterações em sandbox/branch e testar.
- Nível 3: executar operações reversíveis pré-autorizadas dentro de quotas.
- Nível 4: gerir missões de baixo risco de ponta a ponta com auditoria e possibilidade de interrupção.
- Nível 5: coordenar departamentos e workers distribuídos; operações de alto impacto continuam sujeitas a política e aprovação humana.

A passagem de nível depende de evidência e avaliação por tipo de tarefa, não de tempo de funcionamento ou confiança verbal. O sistema deve continuar útil se um agente, modelo, nó ou serviço ficar indisponível.

## 7. Contratos mínimos para ambiente adaptativo

Cada nó anuncia capacidades verificadas: CPU, RAM disponível, GPU/VRAM, espaço livre, sistema operativo, ferramentas e versões, modelos disponíveis, conectividade, concorrência máxima e estado de saúde. Não confiar apenas naquilo que a máquina declara: validar com probes limitados.

Cada tarefa tem requisitos mínimos e limites máximos. O dispatcher escolhe um worker elegível com base em:
- capacidade medida e carga atual;
- especialidade e resultados anteriores;
- custo e disponibilidade;
- privacidade e classificação de dados;
- latência, deadline e dependências;
- permissões e compatibilidade do artefacto.

Se nenhum worker satisfizer os requisitos, o sistema espera, divide a tarefa, reduz o escopo, pede ajuda autorizada ou escala ao Patrão. Nunca deve contornar silenciosamente os limites.

## 8. Segurança e continuidade

- Workers com workspace dedicado e permissões mínimas; nunca usar privilégios de administrador como padrão.
- Segredos fora de prompts, logs, artefactos e memória de longo prazo.
- Aprovação humana para publicar, apagar, comprar, enviar mensagens externas, alterar credenciais, mexer em produção ou modificar política de segurança, salvo política futura específica e explicitamente autorizada.
- Limites de duração, tentativas, mensagens, fan-out, RAM/CPU e custo.
- Timeouts, circuit breakers, cancelamento, idempotência e filas limitadas.
- Snapshots, backups e rollback testado.
- Nós remotos inscritos explicitamente, autenticados, cifrados e revogáveis.
- Sem acesso remoto público direto; usar rede privada e gateway controlado.
- Licenças de código, skills, modelos e assets verificadas antes de adoção comercial.
- Reavaliar periodicamente dependências, versões e permissões; atualizações não são automaticamente seguras.

## 9. Plano de investigação e implementação

### Fase 1 — Auditoria sem alterações
- Reconciliar estado local/remoto e preservar snapshots.
- Mapear contratos, filas, eventos, memória, providers, SafeActionQueue, governance, UI e testes existentes.
- Medir baseline de hardware, processos, RAM, CPU, armazenamento e tempos de tarefa.
- Identificar capacidades duplicadas antes de escolher frameworks.

### Fase 2 — Matriz comparativa
Para cada candidato, registar: versão/commit, licença, dependências, memória em idle e pico, permissões, ferramentas, persistência, retomada, testes, manutenção, modelo de custo, compatibilidade e resultado da prova de conceito.

### Fase 3 — Um worker
- Selecionar um único candidato de baixo custo e risco.
- Usar repositório descartável, dados sintéticos e sem credenciais.
- Testar pedido de acesso, delegação, loop A→B→A, duplicação, timeout, cancelamento, restart, falha de modelo e limite de memória.
- Comparar artefactos e testes com execução sem agente.

### Fase 4 — Skills e departamentos
- Introduzir contratos versionados e skills auditadas.
- Começar com um departamento, um coordenador e poucas especialidades lógicas.
- Adicionar QA independente e avaliação de segurança nos trabalhos críticos.
- Não aumentar concorrência sem medir.

### Fase 5 — Hardware novo e nós distribuídos
- Repetir benchmark no PC forte, definir perfis e comparar qualidade/latência/custo.
- Adicionar um nó de cada vez com gateway, autenticação, heartbeat, permissões e revogação.
- Testar falha de rede e indisponibilidade de nó.

### Fase 6 — Autonomia gradual
- Libertar apenas tarefas reversíveis e de baixo risco com critérios objetivos.
- Medir taxa de sucesso, regressões, tempo de intervenção humana, custo/energia, recuperação e incidentes.
- Expandir escopo apenas depois de várias execuções reproduzíveis e rollback demonstrado.

## 10. Critério de decisão

Uma ferramenta só entra na arquitetura se melhorar uma capacidade mensurável sem duplicar o núcleo, ultrapassar recursos, comprometer a segurança ou impor dependência desnecessária. Se um componente existente já cumprir o contrato, preservar e testar antes de substituir.

## 11. Fontes de investigação

Fontes de projeto/documentação para verificar durante a auditoria; as descrições e maturidade podem mudar:
- LocalHarness: https://github.com/ahwurm/localharness
- Forge: https://github.com/andreglegg/forge
- Felix: https://github.com/sausheong/felix
- DeepSeek Harness: https://github.com/deepseek-ai/deepseek-harness
- LangGraph: https://github.com/langchain-ai/langgraph
- CrewAI: https://github.com/crewAIInc/crewAI
- Microsoft Agent Framework: https://github.com/microsoft/agent-framework
- OpenAI Agents SDK: https://github.com/openai/openai-agents-python
- LlamaIndex: https://github.com/run-llama/llama_index
- Aider: https://github.com/Aider-AI/aider
- Continue: https://github.com/continuedev/continue
- OpenHands: https://github.com/All-Hands-AI/OpenHands
- SWE-agent: https://github.com/SWE-agent/SWE-agent
- Model Context Protocol: https://modelcontextprotocol.io/
- Ollama: https://ollama.com/
- llama.cpp: https://github.com/ggml-org/llama.cpp
- Playwright: https://github.com/microsoft/playwright
- OpenTelemetry: https://opentelemetry.io/
- pytest: https://github.com/pytest-dev/pytest
- Vitest: https://github.com/vitest-dev/vitest
- Artigo de investigação sobre arquitetura de coding harnesses (2026): https://arxiv.org/abs/2609.00006

**Limitação:** esta é uma shortlist documental, não uma auditoria de segurança nem uma medição prática. Nenhum candidato deve ser instalado ou receber acesso ao ambiente principal antes da prova de conceito e da comparação com a arquitetura existente.

## 12. Recuperação assistida, aprendizagem com ajuda externa e prevenção de dependência

### 12.1 Princípio obrigatório

Quando o DGM-MAT não conseguir concluir uma tarefa com evidência suficiente, deve reconhecer o bloqueio, pedir ajuda ao recurso adequado e transformar a solução validada em conhecimento reutilizável. Pedir ajuda não é uma falha; repetir indefinidamente o mesmo erro sem aprender é uma falha de arquitetura.

O ciclo esperado é:

1. **Tentar:** consultar contratos, memória, ferramentas disponíveis e tentativas anteriores; executar apenas ações autorizadas.
2. **Diagnosticar:** classificar o bloqueio (conhecimento, erro técnico, ferramenta em falta, permissão, limite externo, recursos de hardware, dependência ou ambiguidade).
3. **Preparar o pedido:** reunir objetivo, contexto mínimo, evidências, erros completos relevantes, tentativas já feitas, restrições, critérios de aceitação e o que continua por descobrir.
4. **Escolher ajuda:** selecionar documentação oficial, agente interno especializado, modelo alternativo, ferramenta externa aprovada ou pessoa responsável, segundo competência, privacidade, custo, latência e permissões.
5. **Delegar com limites:** entregar uma tarefa delimitada, com entradas e saídas explícitas, prazo/limite de tentativas e sem conceder acesso amplo por conveniência. Não transmitir credenciais, tokens ou dados privados desnecessários.
6. **Validar independentemente:** testar a resposta contra os critérios originais, reproduzir quando possível, verificar regressões e segurança e distinguir afirmações do ajudante de factos confirmados.
7. **Aprender:** guardar a causa confirmada (ou marcar a hipótese como não confirmada), a solução, os testes, limitações, fonte/proveniência, versão e condições em que a solução é válida.
8. **Reutilizar e avaliar:** procurar essa aprendizagem em tarefas futuras, confirmar que continua válida e medir se reduziu erros, tempo ou necessidade de assistência.

### 12.2 Pedido de ajuda normalizado

Cada pedido deve conter, quando aplicável:

- identificador da tarefa e departamento responsável;
- resultado pretendido e critérios de aceitação;
- resumo curto do contexto e referências para artefactos, em vez de despejar todo o histórico;
- evidências, logs e passos de reprodução;
- tentativas anteriores e respetivos resultados;
- questão concreta que o ajudante deve resolver;
- restrições de segurança, privacidade, hardware, custo e dependências;
- permissões estritamente necessárias;
- formato esperado da resposta e testes para a validar.

A resposta externa deve regressar como uma proposta identificável e auditável, não como uma ordem que substitui a governação do DGM-MAT.

### 12.3 Memória de aprendizagem com proveniência

Guardar a aprendizagem em camadas:

- **Memória de incidente:** o que aconteceu, quando, evidências, impacto e resolução.
- **Conhecimento reutilizável:** padrão do problema, diagnóstico, solução validada, alternativas rejeitadas e condições de aplicabilidade.
- **Skill versionada:** apenas quando o procedimento for suficientemente repetível; deve incluir objetivo, gatilhos de ativação, entradas/saídas, ferramentas autorizadas, limites, testes e versão.
- **Memória de fonte externa:** nome/identificador do agente ou fonte, data, versão/modelo quando conhecido, ligações e partes ainda não verificadas.

Não converter automaticamente uma resposta externa em facto permanente. Classificar cada elemento como observado, confirmado por teste, inferido, sugerido externamente ou ainda por validar. Em caso de conflito, preservar a proveniência e pedir reconciliação; não apagar silenciosamente conhecimento anterior.

### 12.4 Aprendizagem sem autoalteração perigosa

O sistema pode propor uma melhoria de memória, skill, teste ou ferramenta. A alteração deve passar por revisão de diferenças, testes isolados, avaliação de permissões e comparação com a linha de base. A autonomia para aprender não concede automaticamente autorização para instalar software, ampliar acessos, alterar políticas, publicar código, apagar dados, gastar dinheiro ou modificar produção.

Mudanças de alto impacto continuam sujeitas à autorização humana ou a uma política explícita previamente aprovada. Toda a alteração deve ser versionada, auditável e reversível.

### 12.5 Evitar ciclos de ajuda e dependência infinita

- Não repetir o mesmo pedido sem acrescentar novas evidências ou alterar a hipótese.
- Registar tentativas e resultados para evitar recomeçar do zero.
- Aplicar deduplicação, limite de tentativas, prazo, orçamento de mensagens e limite de delegações.
- Detetar ciclos entre agentes e encaminhamentos repetidos; cancelar ou escalar quando não há progresso.
- Se duas tentativas independentes falharem, ou se o risco/permissão ultrapassar o mandato, parar e pedir decisão humana em vez de improvisar.
- Se não houver ajuda externa disponível, guardar o estado, indicar o bloqueio e retomar quando existir um recurso autorizado, sem simular sucesso.
- Se a solução depender de uma versão, modelo, credencial ou ambiente específico, documentar essa dependência e criar um teste de validade futura.

### 12.6 Métricas para demonstrar aprendizagem real

Medir por tipo de tarefa, e não apenas pelo número de respostas recebidas:

- taxa de sucesso após assistência;
- percentagem de soluções externas que passam os testes independentes;
- repetição do mesmo incidente depois de a aprendizagem ter sido registada;
- número médio de tentativas e delegações por tarefa;
- tempo até desbloqueio;
- regressões e incidentes de segurança;
- percentagem de aprendizagens com fonte, versão, teste e condições de validade;
- redução, ao longo do tempo, da assistência necessária para problemas já conhecidos.

**Critério de aceitação:** a aprendizagem só é considerada eficaz quando a memória ou skill fica registada com proveniência e uma tarefa posterior comparável demonstra, através de teste ou evidência, que o sistema consegue reutilizá-la corretamente. Uma resposta recebida, por si só, não prova aprendizagem.

