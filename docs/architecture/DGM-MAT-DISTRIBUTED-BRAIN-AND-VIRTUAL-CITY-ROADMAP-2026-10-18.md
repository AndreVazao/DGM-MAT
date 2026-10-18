# DGM-MAT — Arquitetura distribuída, cérebro headless e cidade virtual

**Data:** 2026-10-18  
**Estado:** decisão arquitetural aprovada pelo proprietário; visão futura obrigatória, implementação faseada.  
**Âmbito:** cérebro DGM-MAT, departamentos, nós/PCs satélite, cockpit/Headquarters e evolução visual.

## 1. Princípio soberano

**O cérebro DGM-MAT é a autoridade. O Headquarters é uma projeção visual.** O cérebro deve iniciar, raciocinar, planear, coordenar, executar, persistir estado e recuperar trabalho sem precisar de abrir qualquer interface gráfica. Nenhum cockpit, browser, telemóvel, renderizador 2D/3D ou serviço de descoberta pode ser requisito para a operação do cérebro.

O Headquarters não é o cérebro, não define a verdade do sistema, não agenda nem autoriza trabalho por conta própria e não pode ser o único local onde exista estado operacional. Apresenta o estado real recebido de APIs/eventos autenticados do runtime. Animações, agentes, filas, laboratórios, armazéns e progresso visual devem corresponder a entidades e eventos reais; nunca fabricar atividade.

## 2. Visão de evolução: de edifício para cidade

### Fase A — edifício único
Na instalação inicial, o cérebro e vários departamentos podem correr no mesmo PC, como módulos isolados de um edifício com diferentes andares. O cockpit atual é deliberadamente simples: serve para o proprietário conversar com o DGM-MAT e dar ordens enquanto o cérebro é estabilizado.

### Fase B — departamentos desacoplados
Os departamentos passam a ter contratos, interfaces, estado e limites de recursos explícitos. Mesmo quando correm no mesmo computador, devem poder ser iniciados, parados, testados e substituídos de forma independente. A comunicação entre módulos não deve depender de caminhos locais absolutos, memória partilhada acidental ou acesso direto a bases de dados privadas de outro módulo.

### Fase C — departamentos em PCs satélite
Quando houver hardware disponível, departamentos adequados podem ser instalados em PCs diferentes na rede local. O cérebro central continua soberano e delega trabalho através de contratos versionados, identidade de nó, permissões mínimas, relatórios de capacidade/saúde, filas duráveis e resultados auditáveis. Um nó satélite pode falhar ou ficar offline sem corromper o cérebro nem perder trabalho confirmado; a tarefa deve poder ficar em fila, ser retomada ou ser reatribuída conforme as garantias de execução.

### Fase D — cidade virtual distribuída
O escritório visual poderá representar o cérebro como edifício central e os departamentos distribuídos como edifícios próprios. A cidade cresce apenas quando existirem serviços/nós reais que justifiquem a representação. A adição de novos PCs, aceleradores, armazenamento ou departamentos deve permitir ampliar a organização sem reconstruir a arquitetura de raiz.

Estas fases descrevem a direção arquitetural; não afirmam que a distribuição multi-PC já está implementada.

## 3. Cockpit/Headquarters independente e multiplataforma

- O frontend pode correr no PC principal, num PC separado, num browser remoto ou num telemóvel.
- O frontend comunica com APIs/eventos autenticados; não acede diretamente à base de dados interna nem executa lógica soberana.
- A perda do frontend, do browser, da ligação do telemóvel ou do renderizador não pode parar nem bloquear o cérebro e os departamentos.
- O frontend pode ser substituído por outro cliente compatível sem migrar o estado operacional.
- A descoberta/conectividade remota é um plano de acesso, não o plano de execução. Uma falha de Vercel, Tailscale, DNS ou internet não deve ser confundida com falha do cérebro local.
- O cockpit atual mantém-se simples nesta fase. Não iniciar a cidade 2D/3D antes de o percurso cérebro → tarefa → execução → resultado → persistência → recuperação estar validado.

## 4. Contratos necessários antes da distribuição física

Projetar e evoluir gradualmente contratos explícitos para:

1. **Identidade e confiança do nó:** ID estável, identidade autenticada, versão, capacidades anunciadas e política de confiança.
2. **Relatório de capacidade/saúde:** sistema operativo, CPU, RAM disponível, GPU/VRAM quando aplicável, espaço, ferramentas/modelos instalados, carga, estado e limites de concorrência.
3. **Envelope da tarefa:** ID idempotente, origem, objetivo, entradas referenciadas, permissões, limites, critérios de aceitação e versão do contrato.
4. **Fila durável e lease:** tarefa persistida antes de ser reconhecida; lease/heartbeat com limites claros; reentrega segura; política explícita para tarefas não idempotentes.
5. **Envelope do resultado:** resultado, artefactos, logs essenciais, evidência de validação, versões, duração, erros e proveniência.
6. **Eventos/observabilidade:** eventos de estado com timestamp e correlação, consumíveis pelo cockpit sem lhe transferir autoridade.
7. **Compatibilidade de versões:** negociação de versões, migrações controladas e rejeição explícita de contratos incompatíveis.
8. **Segurança:** autenticação entre nós, autorização por tarefa, princípio do menor privilégio, segredos fora do repositório/logs e auditoria.
9. **Offline/recuperação:** comportamento definido quando o cérebro, um satélite, a rede ou o cockpit fica indisponível; persistência local e sincronização sem duplicação destrutiva.
10. **Agendamento adaptado a recursos:** encaminhar tarefas conforme capacidades e pressão real de recursos; evitar sobrecarregar o PC antigo.

Não implementar tudo de uma vez sem necessidade. Primeiro auditar contratos, filas, persistência e runtime já existentes e reutilizar o que for comprovadamente correto.

## 5. Adaptação ao hardware

O runtime deve medir as capacidades reais em vez de presumir um PC ideal. No hardware fraco, reduzir concorrência, limitar modelos, usar chat/listas e evitar renderização pesada. Em hardware mais forte, permitir mais workers, modelos maiores, aceleração e representação visual mais rica, sempre através de perfis de capacidade e testes. A mesma instalação lógica deve poder migrar para um PC novo usando manifestos de ambiente e recuperação documentada, sem depender do hardware antigo.

Ferramentas em falta devem ser pesquisadas e comparadas; qualquer instalação que altere o ambiente requer aprovação do proprietário. Não introduzir dependências pagas por defeito. A Virtual Factory pode propor componentes novos, mas devem ser construídos e testados isoladamente antes de produção.

## 6. Ordem de implementação e prioridade imediata

**Prioridade atual: reparar e validar o cérebro de ponta a ponta.** O desenho distribuído deve evitar bloqueios arquiteturais, mas não deve atrasar a estabilização.

1. Inventariar o runtime atual, imports/callers, contratos, persistência, filas, permissões, processos e testes; identificar as falhas reais.
2. Validar o ciclo completo: ordem do utilizador → planeamento → tarefa durável → execução real → pedido de ajuda/pesquisa quando necessário → resultado → verificação → persistência → apresentação no cockpit.
3. Validar reinício e recuperação, erros de providers/ferramentas, indisponibilidade da rede e capacidade reduzida.
4. Corrigir defeitos em alterações pequenas, reversíveis e com testes focados e regressão.
5. Manter o cockpit atual simples, como cliente do cérebro, e provar que o cérebro continua a trabalhar com o cockpit fechado.
6. Só depois evoluir para contratos de distribuição física e, mais tarde, cidade visual avançada.

Programação/revisão de código e Investigação/Inovação são departamentos de prioridade elevada: exigem evidência, fontes, revisão independente, testes e comunicação honesta do que está ou não validado.

## 7. Regra de não regressão

Nenhuma melhoria é aceite apenas porque adiciona uma funcionalidade. Deve preservar o comportamento existente e ser validada contra critérios de aceitação. Antes de editar, inspecionar dependências, histórico e alterações não integradas. Não apagar código ou branches não compreendidos. Testes falhados ou bloqueados devem ser declarados; não se pode apresentar um merge como concluído nem o sistema como ponta a ponta funcional sem evidência.

Gates mínimos para alterações ao cérebro:
- sintaxe/imports e testes focados;
- contratos e permissões;
- persistência/filas e reinício quando aplicável;
- percurso de integração e resultado real;
- regressões relevantes;
- build/arranque Windows quando o ambiente permitir;
- registo do que passou, falhou, ficou bloqueado e não foi testado.

## 8. Limites e não objetivos atuais

- Não transformar o Headquarters no controlador central.
- Não exigir que todos os departamentos estejam no mesmo PC para sempre.
- Não assumir que a distribuição multi-PC, a cidade virtual, o frontend remoto ou o failover total já existem.
- Não implementar 2D/3D ou instalar novas ferramentas antes de o cérebro estar estável.
- Não clonar automaticamente repositórios satélite ou privados para a pasta de trabalho local. Código externo só entra no DGM-MAT-Labs através de importação aprovada, análise de licença/segurança e decisão explícita de reutilização.
- Não confundir o repositório de recuperação DGM-MAT-Memory com a memória de governação andreos-memory.

## 9. Relação com a documentação existente

Esta decisão complementa:
- [Índice de integração do Digital Headquarters](DGM-MAT-DIGITAL-HEADQUARTERS-INTEGRATION-INDEX-2026-10-17.md)
- [Plano de runtime adaptável e trabalhadores distribuídos](../future/DGM-MAT-ADAPTIVE-RUNTIME-AND-DISTRIBUTED-WORKERS-2026-10-12.md)
- [Requisitos do escritório virtual e cérebro adaptável](DGM-MAT_ADAPTIVE_VIRTUAL_OFFICE_AND_CORE_REQUIREMENTS_2026-10-14.md)
- [Plano de independência do cérebro e escritório virtual](DGM-MAT_CORE_INDEPENDENCE_AND_VIRTUAL_OFFICE_IMPLEMENTATION_PLAN_2026-10-14.md)

**Critério de sucesso:** hoje, um cérebro estável, headless e testável com cockpit simples; amanhã, o mesmo cérebro soberano a delegar a departamentos em máquinas distintas e a expor o estado real a clientes independentes; mais tarde, uma cidade virtual que representa fielmente essa organização distribuída.
