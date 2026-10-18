# Constituição arquitetural vinculativa do DGM-MAT
**Identificador:** DGM-MAT-ARCH-CONSTITUTION-001  
**Data de aprovação da decisão pelo proprietário:** 2026-10-18  
**Estado:** NORMA ARQUITETURAL VINCULATIVA — ALTERAÇÃO APENAS POR ADITAMENTO AUTORIZADO  
**Âmbito:** DGM-MAT, todos os departamentos, agentes, repositórios satélite, interfaces, pipelines de recuperação e documentação técnica da família DGM-MAT.

> **REGRA SUPREMA:** a unificação de recuperação consolida trabalho e histórico entre o PC e o GitHub. NÃO consolida os repositórios satélite num monólito. A modularidade da organização e a separação dos departamentos são decisões de arquitetura vigentes e não podem ser revertidas implicitamente.

Este documento é a fonte de autoridade arquitetural para modularidade, hierarquia, fronteiras entre repositórios e escritório virtual. Documentos anteriores continuam a ser fontes de requisitos e contexto, subordinados a esta Constituição quando exista conflito. O código e os testes descrevem a realidade implementada; não alteram silenciosamente a decisão arquitetural.

A proteção é de governação e histórico Git, não uma alegação de imutabilidade técnica do ficheiro. Nenhuma alteração, substituição, remoção ou interpretação que reverta estas regras pode ser feita sem autorização explícita do proprietário. Uma mudança autorizada exige aditamento datado que explique motivo, impacto, migração, riscos e compatibilidade; a regra anterior permanece no histórico. Uma alteração comum ao código ou um merge de recuperação não constitui essa autorização.

## 1. Duas operações diferentes — nunca confundir

### 1.1 Unificação de recuperação
Objetivo: recuperar e comparar o trabalho feito no PC com o trabalho avançado no GitHub; integrar os dois conjuntos de alterações numa branch de unificação; preservar commits, branches, ficheiros, testes, documentação e proveniência; resolver divergências com evidência; depois validar e sincronizar.

Esta operação pode consolidar versões concorrentes de um mesmo ficheiro ou implementação. Não autoriza a mover código de uma repo satélite para DGM-MAT só para simplificar imports ou CI.

### 1.2 Arquitetura modular
Objetivo permanente: manter vários repositórios com responsabilidades explícitas, contratos estáveis e dependências dirigidas. A fronteira entre repositórios é uma fronteira real de propriedade, testes, versão e evolução — não apenas uma pasta dentro do mesmo monólito.

É proibido interpretar “unificação”, “recuperação”, “consolidação” ou “sincronização” como ordem para juntar todas as repos. É igualmente proibido apagar uma dependência modular sem verificar o seu proprietário, contrato, callers, versão, testes e histórico.

## 2. Hierarquia de autoridade e comando

1. **Proprietário humano:** autoridade final sobre objetivos, decisões irreversíveis, permissões de alto risco, publicação, credenciais e exceções à Constituição.
2. **DGM-MAT Central — Patrão/cérebro soberano:** mantém a missão global, prioridades, política, memória canónica, estado global, orçamento de recursos, autorização de departamentos/agentes, despacho, resolução de conflitos e validação final.
3. **Chefias departamentais:** têm autonomia operacional dentro do mandato e respondem pela qualidade, plano, dependências e resultados do departamento.
4. **Cérebros departamentais / agentes principais:** planeiam e executam tarefas especializadas, gerem subagentes e memória operacional delimitada, reportam progresso e pedem ajuda quando necessário.
5. **Agentes especialistas, workers, ferramentas e colaboradores externos:** executam tarefas delimitadas; não ganham autoridade central pelo facto de estarem instalados, serem mais capazes ou terem sido contratados.

“Cérebro próprio” de um departamento significa capacidade especializada, plano local, estado operacional, ferramentas e critérios de conclusão próprios. NÃO significa soberania sobre políticas globais, permissões, orçamento, memória canónica ou aceitação final. Não é obrigatório que cada departamento use um modelo de IA separado; o contrato e o isolamento lógico são obrigatórios, enquanto o processo/modelo concreto se adapta aos recursos disponíveis.

## 3. Fronteiras dos repositórios

### 3.1 Repositório central: `AndreVazao/DGM-MAT`
É o plano de controlo e cérebro soberano. Deve conter apenas o núcleo central e a integração necessária para:
- receber e classificar missões;
- manter estado global persistente, prioridades, políticas e memória canónica;
- encaminhar e coordenar trabalho entre departamentos;
- controlar permissões, aprovações, escalamento, cancelamento e limites de recursos;
- validar resultados e evidências, resolver conflitos e manter auditoria;
- descobrir capacidades/repositórios e apresentar o estado real através de API;
- recuperar de falhas sem depender do cockpit.

Não deve absorver a implementação integral de cada departamento, conectores, frontends ou runtimes especializados. O core pode conter adaptadores finos e compatibilidade temporária com plano de migração explícito; não pode tornar-se o local definitivo de todas as implementações.

### 3.2 Contratos partilhados: `DGM-Contracts`
Responsável pelos tipos, esquemas, interfaces e contratos versionados que atravessam fronteiras: missões, tarefas, agentes, departamentos, mensagens, eventos, artefactos, aprovações, resultados, capacidades e saúde. Mudanças incompatíveis exigem versionamento/migração. O código central e os satélites dependem de versões publicadas/pinadas deste contrato; não copiam definições divergentes informalmente.

### 3.3 Repositórios modulares já identificados
Os nomes abaixo são fronteiras conhecidas na documentação atual, não prova automática de que cada implementação esteja completa ou operacional:
- `DGM-MAT-Runtime`: ciclo de vida dos workers, execução, recuperação e runtime especializado.
- `DGM-MAT-Orchestrator`: mecanismo de execução/decomposição e coordenação técnica delegado pelo plano de controlo; nunca substitui a autoridade soberana do DGM-MAT.
- `DGM-MAT-Agents`: catálogo, pacotes, adaptadores e ciclo de vida dos agentes.
- `DGM-MAT-Connectors`: integrações substituíveis com providers, aplicações, ferramentas, MCP e fontes externas.
- `DGM-Cockpit-Frontend` e/ou cockpit desktop/móvel: apresentação e interação humana; nunca são fonte única do estado nem condição para o core trabalhar.
- `DGM-Contracts`: contratos comuns conforme a secção anterior.

A presença, estado, visibilidade, permissões e conteúdo real de cada repo devem ser verificados durante a auditoria. Não criar dependência de uma repo por mera suposição; também não a remover apenas porque o CI não consegue aceder-lhe.

### 3.4 Departamentos satélite
Cada departamento principal deve ter uma fronteira modular própria, com contrato, responsável, testes, versão, memória operacional delimitada e interface de missão/resultado. Quando a dimensão justificar implementação independente, essa fronteira é um repositório satélite independente, e não uma pasta permanente dentro de DGM-MAT.

Departamentos-alvo iniciais:
1. **Programação e Engenharia de Software** — requisitos, arquitetura, backend, frontend, especialistas por linguagem, integração e manutenção.
2. **Investigação e Descoberta** — pesquisa de soluções, documentação, bibliotecas, modelos, skills, repositórios e avaliação de fontes/licenças.
3. **Inteligência de Conversações e Recuperação de Dados** — recolha/importação de conversas de várias IAs, preservação de turnos e proveniência, recuperação de código e contexto.
4. **Automação Web e Scraping** — navegação, automação de browser, extração de dados e adaptadores específicos de websites; respeita autenticação, privacidade, limites e políticas dos serviços.
5. **Conhecimento, Memória e Relações de Projetos** — deduplicação, grafo de relações, ligação entre conversas/projetos/repos, histórico e reconciliação de decisões. A memória nuclear continua sob autoridade do DGM-MAT.
6. **Qualidade, Testes e Segurança** — validação independente, regressões, permissões, análise de risco e evidência.
7. **DevOps, Build e Operações** — ambiente, empacotamento, saúde, observabilidade, instalação e recuperação.
8. **Design, Produto e Escritório Virtual** — UX/UI e representação visual de estados reais.
9. **Recursos Humanos e Fábrica de Agentes** — inventário, formação, criação/proposta de contratação, avaliação e despacho de agentes sob autorização central.

Esta lista é o mapa organizacional-alvo, não uma afirmação de que todos estes satélites já existem. A criação/extração de cada repo deve ser faseada, depois do inventário, com contratos e testes. A necessidade de avançar por fases não autoriza abandonar a fronteira modular nem colocar definitivamente todas as responsabilidades no monólito.

## 4. Regras obrigatórias de dependência e comunicação

- Comunicação entre repos por contratos versionados, API/eventos ou pacotes versionados; nunca por imports relativos para pastas irmãs, caminhos locais de uma máquina ou acesso direto às tabelas internas de outro módulo.
- Dependências apontam para interfaces estáveis. O plano de controlo pode chamar um departamento; um departamento não pode reescrever nem contornar a política central.
- Usar versões/tag/commit explícitos e atualizáveis de forma controlada. Não depender de `latest` para componentes críticos.
- Testar os contratos de forma isolada e em integração; cada repo tem testes próprios e testes de contrato relevantes.
- Cada tarefa tem ID de missão-pai, origem, destino, dependências, permissões mínimas, orçamento, timeout, limite de tentativas, condição de conclusão e artefactos com proveniência.
- Proibir ciclos de delegação, ping-pong, duplicação não idempotente e reabertura silenciosa de estados terminais. Backpressure e limites de fan-out/profundidade são obrigatórios.
- Um módulo indisponível deve produzir estado de bloqueio/erro verificável e pedido de ajuda; nunca fingir sucesso nem desencadear fallback pago silencioso.
- Credenciais, tokens e permissões de CI devem ser de menor privilégio. A falha de acesso a uma repo privada é problema de configuração/acesso, não justificação para apagar a arquitetura modular.
- A CI deve restaurar dependências modulares de forma explícita, segura e reproduzível. Não usar cópias vendorizadas como substituto permanente sem decisão de arquitetura autorizada e plano de proveniência.

## 5. Cérebro sempre ativo; interfaces opcionais

- O core/back office corre como serviço independente do cockpit, browser, renderer 2D/3D ou telefone.
- Fechar, reiniciar ou perder ligação à interface não pode apagar missões, resultados confirmados ou a única cópia de um pedido.
- Tarefas, eventos, decisões, dependências e resultados são persistidos. A recuperação após falha é idempotente e não repete ações externas às cegas.
- A API expõe estado real; o renderer é uma projeção/adaptador visual. Não inventa trabalhadores, progresso, reuniões, entregas ou integrações.
- O escritório virtual é progressivo e adaptável: começar com lista/árvore e 2D económico; 2.5D/3D apenas após medição no hardware. A visualização nunca é requisito para a execução.
- Agentes externos (Claude Code, outros modelos, serviços e colaboradores) são recursos substituíveis. Podem ajudar, mas não assumem soberania sobre DGM-MAT.

## 6. Inteligência de conversações — capacidade central obrigatória

O objetivo funcional é compreender a história real dos projetos, não apenas importar texto. O sistema deve:
1. Descobrir e inventariar conversas nas fontes autorizadas (exportações e, quando permitido, interfaces web), com cobertura explícita por provider.
2. Identificar separadamente cada mensagem do utilizador e cada resposta/proposta da IA, preservando ordem temporal, IDs, timestamps e proveniência.
3. Extrair pedidos, requisitos, decisões, alternativas, código, caminhos de ficheiro, erros, testes, resultados e perguntas em aberto.
4. Ligar conversas de diferentes IAs ao mesmo projeto sem assumir equivalência apenas por títulos semelhantes.
5. Comparar propostas/respostas entre providers, identificar convergências, contradições, correções posteriores e decisões substituídas; nunca transformar proposta de IA em decisão do utilizador sem evidência.
6. Associar artefactos de código à conversa, mensagem, provider, versão, caminho, fingerprint e contexto envolvente; preservar originais antes de consolidar.
7. Gerar nomes canónicos, aliases, agrupamentos e mapa de repositórios/projetos com nível de confiança e explicação.
8. Propor renomeação/reagrupamento. Alterações a metadados internos reversíveis podem seguir política aprovada; alterações externas ou ambíguas requerem aprovação quando não forem seguras.
9. Não reprocessar integralmente fontes inalteradas sem motivo; usar fingerprints, índices persistentes, checkpoints e recuperação idempotente.
10. Expor cobertura e lacunas: “não encontrado” não significa “nunca existiu”; uma fonte inacessível não conta como revista.

A implementação pode residir inicialmente no código já existente em `core/conversation_intelligence/` para manter o sistema utilizável durante a recuperação. Isso é uma localização de transição/integração, não autorização para eliminar o departamento modular. A extração para o seu satélite deve preservar contratos, dados, testes, migrações e proveniência, e ocorrer sem duplicar duas fontes de verdade.

## 7. Memória e verdade evolutiva

- A memória canónica, políticas, decisões confirmadas e prioridades pertencem ao DGM-MAT central.
- Cada departamento pode manter memória operacional especializada com escopo, origem e versão, mas não pode contradizer silenciosamente a memória nuclear.
- Distinguir explicitamente pedido do utilizador, proposta de IA, hipótese, decisão confirmada, evidência verificada, resultado de teste e estado legado/superado.
- Decisões confirmadas não são reescritas silenciosamente. Uma decisão posterior explicitamente autorizada supersede a anterior preservando a história, motivo, data e proveniência.
- Cada fase de recuperação/engenharia regista ficheiros, repos, commits, testes executados, falhas, limitações, estado não verificado e próximo passo.
- Um chat ou um relatório de sucesso não substitui estado persistente nem evidência reproduzível.

## 8. Política de recuperação, inventário e documentação

1. Inventariar primeiro: repositórios, branches, commits, árvores, documentos, módulos, imports, callers, manifests, workflows, testes, runtime e estado da memória.
2. Comparar as versões do PC e do GitHub como linhas de trabalho; registar origem, divergência, conteúdo único, duplicados e resolução.
3. Classificar documentos: **NORMATIVO**, **ATUAL/COMPLEMENTAR**, **EVIDÊNCIA**, **PROPOSTA**, **HISTÓRICO**, **SUPERADO**, **POR REVER**.
4. Um documento antigo não é apagado só por ter data antiga. Se estiver superado, adicionar aviso e link para o sucessor; mover para arquivo apenas depois de verificar referências e preservar o histórico. Eliminação definitiva exige autorização explícita e prova de que não se perde informação única.
5. Nenhum inventário pode declarar “tudo revisto” se houver fontes, branches, ficheiros ou conversas inacessíveis.
6. O README liga esta Constituição. O registo de autoridade documental classifica os documentos existentes e liga os sucessores. Os documentos especializados permanecem válidos naquilo que não contradiz esta norma.

## 9. Ordem de implementação obrigatória

**Fase 0 — Recuperação e inventário read-only**
- Comparar PC/branch de recuperação/GitHub e identificar material único.
- Fazer inventário documental e técnico dos módulos e repos.
- Mapear imports/dependências e verificar o acesso a cada repo satélite.
- Não apagar nem mover código/documentação nesta fase.

**Fase 1 — Verdade funcional do core**
- Provar serviço headless, persistência, filas, recuperação, idempotência, segurança e estado real.
- Provar que fechar o cockpit não afeta missões.
- Isolar testes da base de dados/runtime de produção.

**Fase 2 — Contratos e integração modular**
- Verificar `DGM-Contracts`, versões, imports e APIs reais.
- Corrigir CI para instalar os satélites corretos com autenticação de menor privilégio e versões fixas.
- Testar interfaces sem depender de caminhos de diretório local.

**Fase 3 — Capacidades prioritárias do cérebro**
- Intake de missão e encaminhamento.
- Ajuda/investigação de capacidades e pedido de ajuda estruturado.
- Memória e aprendizagem com proveniência.
- Inteligência de conversações: separar papéis, recuperar contexto/código, relacionar providers/projetos, comparar e propor agrupamentos/nomes.
- Validação independente e autoevolução controlada: propor, isolar, testar, apresentar diff, pedir aprovação quando necessário; nunca autoaprovar alteração de autoridade.

**Fase 4 — Piloto departamental**
- Escolher um departamento, ligar o seu satélite através dos contratos, medir custos/recursos e validar delegação, falha e recuperação.
- Expandir um departamento de cada vez; não criar paralelismo que prejudique o PC.

**Fase 5 — Cockpit e escritório virtual**
- Primeiro lista/árvore e cockpit funcional, depois escritório 2D.
- Adicionar pisos, chefias, agentes, balcões departamentais e eventos reais.
- Só depois considerar 2.5D/3D e cidade visual.

## 10. Critérios de aceitação — não declarar concluído sem evidência

- O core arranca e trabalha sem qualquer interface aberta.
- Uma missão sobrevive a desconexão/reinício de cliente e pode ser consultada com o seu estado real.
- Um módulo satélite indisponível não corrompe o core; gera bloqueio/erro e escalamento observáveis.
- Dependências modulares são rastreáveis e reproduzíveis em ambiente limpo/CI.
- Testes demonstram autorização, idempotência, recuperação, cancelamento, limites de delegação e ausência de ciclos.
- Conversas de diferentes IAs preservam autor/turno/proveniência e podem ser ligadas ao mesmo projeto com evidência.
- Pedidos do utilizador não se confundem com respostas de IA; propostas não se confundem com decisões.
- Código recuperado tem contexto e histórico; variantes são comparadas antes de escolher uma implementação.
- Nomes canónicos, aliases e relações entre conversas/projetos/repos são persistentes e explicáveis.
- Capacidades reportadas como prontas têm testes/resultados ou são explicitamente marcadas como não verificadas.
- O escritório visual representa entidades reais e pode falhar sem interromper o cérebro.
- Não há dependência obrigatória de APIs pagas nem fallback pago silencioso.

## 11. Estado atual e limites da auditoria de 2026-10-18

Na branch de recuperação foi encontrada documentação de arquitetura de 2026-10-09 a 2026-10-17 que já descreve: core independente, cockpit opcional, departamentos, hierarquia, soberania central, governação de agentes, recuperação de conversas e montagem de projetos. Esta Constituição consolida e dá precedência a essas decisões.

A auditoria documental desta sessão confirmou a presença de, entre outros:
- `docs/DGM-MAT_DIGITAL_ORGANIZATION_ARCHITECTURE.md`
- `docs/DGM-MAT_DIGITAL_ORGANIZATION_BUILD_ORDER.md`
- `docs/DGM-MAT_CONVERSATION_RECOVERY_AND_PROJECT_ASSEMBLY.md`
- `docs/DGM-MAT_DOCUMENT_AUTHORITY_REGISTER_2026-10-10.md`
- `docs/architecture/DGM-MAT_CORE_INDEPENDENCE_AND_VIRTUAL_OFFICE_IMPLEMENTATION_PLAN_2026-10-14.md`
- `docs/architecture/DGM-MAT_ADAPTIVE_VIRTUAL_OFFICE_AND_CORE_REQUIREMENTS_2026-10-14.md`
- `docs/architecture/DGM-MAT_FACTORY_HR_DEPARTMENTAL_HIERARCHY_PROGRAMMING_AND_DESIGN_2026-10-14.md`
- `docs/architecture/DGM-MAT_MASTER_CAPABILITY_CATALOG_2026-10-14.md`
- `docs/future/DGM-MAT-DEPARTMENT-SOVEREIGNTY-AND-AGENT-GOVERNANCE-2026-10-13.md`
- `docs/architecture/CONVERSATION_KNOWLEDGE_STORE_HARDENING_2026-10-10.md`

Limite: a leitura documental e a verificação de presença no GitHub não equivalem a uma auditoria linha a linha de todos os documentos, de todos os repositórios satélite, dos conteúdos locais do PC ou da implementação/runtime. Os nomes e capacidades acima descritos como alvo não devem ser confundidos com implementação já provada. A auditoria técnica deve continuar sem apagar histórico.

## 12. Resolução de conflitos

Quando existir contradição:
1. esta Constituição governa as fronteiras arquiteturais e a modularidade;
2. a diretiva de missão/verdade evolutiva governa a prioridade operacional e a proveniência das decisões;
3. os documentos técnicos especializados detalham os seus domínios sem contrariar as duas normas anteriores;
4. código, testes, logs e runtime determinam o que está realmente implementado — não alteram a arquitetura por omissão;
5. proposta de IA, documento de pesquisa, nome de repositório ou README não constitui prova suficiente de funcionamento;
6. se a decisão não puder ser resolvida pela evidência, registar conflito e escalar ao proprietário.

**Regra final:** primeiro recuperar e provar; depois integrar; manter departamentos e repositórios separados; fazer o cérebro trabalhar sem cockpit; e só declarar capacidades quando a realidade as demonstrar.
