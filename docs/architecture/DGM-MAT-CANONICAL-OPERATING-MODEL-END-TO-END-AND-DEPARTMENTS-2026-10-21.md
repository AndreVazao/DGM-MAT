# DGM-MAT — Modelo Canónico de Operação, Departamentos, Multi-Agent e Ciclo End-to-End
**Identificador:** DGM-MAT-CANONICAL-OPERATING-MODEL-001  
**Data:** 2026-10-21  
**Estado:** ADITAMENTO CANÓNICO DE EXECUÇÃO — subordinado à Constituição Arquitetural de 2026-10-18  
**Autoridade:** diretivas explícitas do proprietário. A Constituição mantém autoridade normativa sobre modularidade, hierarquia e fronteiras de repositórios.  
**Âmbito:** DGM-MAT, AndreOS-Memory, contratos, runtime, departamentos, repositórios satélite, cockpit PC/móvel, recuperação de conversas, pesquisa, engenharia e futuras máquinas departamentais.

> **Regra principal:** DGM-MAT é o cérebro e sede central. A empresa digital tem de funcionar como uma organização multi-agent real, com departamentos responsáveis, agentes especializados, execução verificável e estado persistente. O escritório virtual apenas espelha essa realidade. A documentação não prova implementação: uma capacidade só é entregue quando o percurso funcional e os testes o demonstram.

## 1. Autoridade e princípios inegociáveis

1. O proprietário humano mantém autoridade final sobre objetivos, decisões irreversíveis, credenciais, permissões de alto risco, publicação e exceções à arquitetura.
2. DGM-MAT Central é o cérebro soberano: recebe pedidos, mantém a missão global e a memória canónica, planeia, distribui trabalho, resolve conflitos, governa permissões, supervisiona resultados e apresenta a resposta final.
3. Chefias departamentais têm autonomia operacional delimitada. Nenhum departamento ou agente pode alterar a política central, aprovar a própria elevação de privilégios ou declarar sozinho concluído trabalho crítico.
4. **Estabilidade > funcionalidades; evidência > suposições; controlo manual > automação destrutiva.**
5. Local-first e custo zero por defeito. Ferramentas e providers pagos nunca são escolhidos por fallback silencioso; custos e limites são observáveis.
6. A organização começa modular dentro de um único PC e pode distribuir departamentos por máquinas autorizadas sem reescrever o cérebro.
7. Repositórios satélite continuam separados. Recuperar/unificar trabalho do PC e GitHub não significa fundir departamentos num monólito.
8. Nunca confundir pedido do utilizador, proposta de IA, decisão confirmada, plano, ação tentada, resultado observado e resultado validado.
9. Se uma capacidade não existe, está indisponível ou não foi testada, regista-se o bloqueio e comunica-se honestamente; não se simula conclusão.

## 2. Organização empresarial virtual

### 2.1 DGM-MAT Central / Headquarters — cérebro e direção
Responsabilidades exclusivas:
- entrada e correlação de pedidos, prioridade global e gestão de missões;
- memória canónica, verdade evolutiva e reconciliação de fontes;
- catálogo de departamentos, agentes, capacidades, ferramentas, permissões e nós;
- planeamento, despacho, dependências, limites de concorrência e coordenação entre departamentos;
- aprovações/escalamento, cancelamento, idempotência e recuperação;
- integração de entregáveis, verificação final e resposta ao proprietário;
- auditoria e publicação do estado real para APIs e cockpits.

O core tem de funcionar headless. Fechar, reiniciar ou perder o cockpit não pode perder uma missão nem interromper indevidamente o trabalho do cérebro.

### 2.2 Agente de ligação ao proprietário — Chief of Staff / Front Office
Manter um agente lógico dedicado, de serviço contínuo quando runtime e recursos o permitirem, responsável por:
- conversar com o proprietário, incluindo voz quando suportada;
- transformar linguagem natural em objetivo, contexto, restrições e critérios de aceitação;
- manter o significado do pedido durante a execução e perguntar apenas quando a ambiguidade bloqueia uma decisão segura;
- comunicar com o Boss, transmitir progresso real, recolher decisões e devolver a resposta final;
- distinguir o que foi pedido pelo utilizador do que foi sugerido por agentes internos;
- nunca esconder bloqueios nem inventar que uma tarefa foi feita.

É um serviço lógico prioritário, não uma exigência de manter um modelo pesado ativo no PC fraco. Pode usar sessão leve, fila e notificações, recuperando contexto persistido após reinício.

### 2.3 Departamentos iniciais
Cada departamento tem ID estável, missão, chefe lógico, catálogo de capacidades, orçamento/limites, agentes, memória operacional delimitada, fila, eventos, critérios de aceitação, testes, auditoria e contrato de entrada/saída. Cada departamento tem o seu escritório/balcão virtual próprio, mesmo quando partilha fisicamente o PC.

1. **Programação e Engenharia de Software** — implementação e manutenção; coordena especialistas por linguagem, arquitetura, integração e revisão.
2. **Qualidade, Testes e Bug Hunting** — independente dos autores; reproduz falhas, testa regressões, integração, API/UI e end-to-end, verifica imports/callers/runtime/persistência e pode bloquear uma entrega sem evidência.
3. **Investigação e Web Research** — fontes públicas/técnicas, documentação oficial, soluções, benchmarks, licenças, bibliotecas, ferramentas e providers. Regista fontes, data, confiança e limitações; pesquisar não autoriza alterar produção.
4. **Laboratório de Respostas e Avaliação** — testa respostas, hipóteses, prompts, modelos e estratégias em experiências reproduzíveis. É distinto do departamento que procura informação: recebe hipóteses e devolve resultados avaliados.
5. **Inteligência de Conversações e Recuperação de Conhecimento** — descobre, importa, transcreve, classifica, relaciona e preserva conversas e artefactos de múltiplas IAs; mantém proveniência e memória de projetos.
6. **DevOps, Runtime e Releases** — builds, empacotamento, Git, CI, configuração, deploy, saúde, logs, rollback e validação de ambientes; respeita limites de Actions e prefere testes locais.
7. **Segurança e Governação** — autenticação, autorização, segredos, políticas, sandbox, revisão de risco, auditoria e incidentes.
8. **Dados, Memória e Documentação** — armazenamento durável, índices, migrações, registo de decisões, documentação canónica, pesquisa interna e proveniência.
9. **Providers, Conectores e Integrações** — adaptadores normalizados para IAs, APIs, MCP, browser e ferramentas externas; observa disponibilidade, limites, custos e permissões.
10. **Produto, UX e Cockpit** — cockpit PC/móvel e escritório virtual; consulta APIs/eventos reais, oferece ações autorizadas e estados honestos. Não contém a fonte de verdade.
11. **Integrações de Hardware/Dispositivos** — USB/ADB, diagnóstico e recuperação segura quando necessário; exige autorização, preservação de dados e testes específicos.

Os departamentos começam como módulos lógicos dentro do DGM-MAT, sem exigir novos processos ou repositórios imediatamente. Separar em repositório/processo/máquina só quando existir contrato claro, consumidor real, testes, observabilidade e motivo operacional. Não criar departamentos fictícios para preencher o escritório.

### 2.4 Especialistas de programação prioritários
A especialização é por competência demonstrada, não apenas pelo nome ou prompt. No PC fraco, um agente pode cobrir várias competências, mantendo papéis e resultados separados.

**Núcleo prioritário**
- **Python:** backend, automação, APIs, agentes, scripts, testes e integração do DGM-MAT.
- **JavaScript / TypeScript:** lógica web, cockpit, serviços Node.js, contratos cliente e integração.
- **HTML:** estrutura semântica de interfaces web.
- **CSS:** layout responsivo, acessibilidade, design system e desempenho visual.
- **SQL / bases de dados:** SQLite, PostgreSQL, migrações, integridade, índices, concorrência e persistência.
- **PowerShell / Windows scripting:** instalação, diagnóstico, serviços, processos, paths, permissões, packaging e automação segura no Windows.
- **Shell / Bash:** automação Linux, containers e CI.
- **YAML / JSON / TOML:** configuração, workflows e contratos; são competências de configuração, não linguagens de programação equivalentes às anteriores.
- **Java / Kotlin e Android:** aplicação móvel, Capacitor/Android, integração de dispositivo e APK.
- **Git / GitHub / CI:** controlo de versões, revisão, branches, builds e releases; competência transversal.

**Especialistas condicionais ao portefólio**
- **C/C++ e firmware:** quando trabalho EVSE, microcontroladores ou drivers o exigir.
- **Rust / Go:** workers, ferramentas de sistema ou serviços distribuídos apenas quando houver caso de uso medido.
- **Java adicional, C#/.NET ou outras linguagens:** ativar com base nos repositórios reais, dependências e pedidos, não por catálogo abstrato.

HTML/CSS não são linguagens de programação no mesmo sentido de Python, mas exigem especialização própria. O especialista de arquitetura e integração coordena os limites entre linguagens; QA valida independentemente. Não criar todos os agentes em simultâneo: começar pelos papéis mínimos e expandir com evidência de carga e benefício.

### 2.5 Chefias, agentes e comunicação
Hierarquia: proprietário → DGM-MAT Central → chefe de departamento → agente principal/lead → especialistas/subagentes → ferramentas/serviços. O agente principal mantém plano e dependências; não se limita a encaminhar mensagens. Cada tarefa regista mission/task ID, departamento, executor, dependências, inputs, outputs, permissões, critérios de aceitação, evidências, tentativas, estado e timestamps.

Mensagens interdepartamentais são estruturadas, correlacionadas, auditáveis e limitadas. Proibir ciclos sem progresso, delegação ilimitada, tarefas duplicadas e dois agentes a alterar simultaneamente o mesmo artefacto sem coordenação. A falta de capacidade gera pedido estruturado de ajuda ao HQ; nunca concede permissões implicitamente.

## 3. Escritórios virtuais como espelho fiel
- Cada departamento tem escritório/sala e balcão de consulta próprios, identificados pelo departamento real.
- Cada agente mostrado corresponde a registo real do catálogo/runtime. Agentes indisponíveis, simulados ou não implementados não podem ser apresentados como trabalhadores ativos.
- **Convenção visual obrigatória:** pessoas/agentes existentes são personagens humanos; agentes criados pelo DGM-MAT são representados como robôs em todas as interfaces e departamentos. O CEO usa avatar humano baseado na fotografia canónica com cabelo. A forma visual não altera permissões nem estado operacional.
- Animações de conversa, reuniões, movimento, execução, enfermaria, produção, controlo de qualidade ou expedição só são emitidas a partir de eventos/estados reais.
- Estado desconhecido aparece como desconhecido; ausência de evento não significa inatividade nem sucesso.
- A UI é uma projeção substituível. Primeiro lista/chat/2D económico; 2D avançado/3D apenas quando o hardware medido suporta. O perfil visual não altera permissões ou capacidades.
- O PC atual é limitado: começar leve, medir CPU/RAM e concorrência, manter inferência local pesada em standby quando necessário. O cérebro e as tarefas essenciais têm prioridade sobre animações.
- O cockpit móvel é cliente autenticado para enviar pedidos, consultar estado, anexar ficheiros quando o endpoint existir, ouvir/falar quando suportado e aprovar ações. O cockpit nunca é pré-requisito para o core executar.

## 4. Ciclo end-to-end obrigatório de cada pedido
1. **Receção:** gerar ID/correlation ID; persistir texto original, origem, data, anexos referenciados, utilizador e contexto disponível.
2. **Compreensão:** identificar objetivo, projeto, restrições, prioridade, riscos, idioma, dependências e critério de conclusão. Preservar o pedido literal.
3. **Contexto e memória:** procurar decisões, documentação, conversas, artefactos e tarefas anteriores. Distinguir informação confirmada, proposta, histórica, contraditória e não verificada.
4. **Plano executável:** decompor em tarefas com dono, inputs/outputs, dependências, ferramentas/capacidades, política de retries e critérios de aceitação. Plano sem executor é bloqueio, não execução.
5. **Decisão de política:** classificar efeitos e riscos. Ações rotineiras, limitadas e allowlisted podem seguir autonomia previamente aprovada; ações destrutivas, externas, sensíveis, financeiras, de credenciais ou alto impacto exigem aprovação adequada.
6. **Despacho e execução real:** enviar tarefas para workers registados; verificar heartbeat, capacidade, autorização e disponibilidade. Capturar logs, artefactos, versões, eventos e erros. Não marcar progresso por inferência.
7. **Coordenação:** aguardar dependências, gerir concorrência, encaminhar pedidos de ajuda e consolidar resultados. Limitar tentativas, tempo, custo e ciclos. Cancelamento propaga-se e deixa estado claro.
8. **Validação independente:** testes adequados ao risco: sintaxe, imports/callers, testes unitários, integração, API/UI, E2E, segurança, persistência, reinício e inspeção do resultado real. Quem implementa não é o único juiz.
9. **Persistência e recuperação:** gravar estados, decisões, outputs e evidências de forma durável e idempotente. Em crash, reconciliar armazenamentos; nunca repetir cegamente efeitos externos com resultado desconhecido.
10. **Finalização:** verificar critérios de aceitação um a um; distinguir sucesso completo, parcial, falhado, cancelado, bloqueado e resultado desconhecido.
11. **Resposta final:** o agente de ligação apresenta o resultado em linguagem clara: pedido, trabalho feito, evidências/testes, artefactos/caminhos, limitações, decisões pendentes e próximo passo. Não afirmar alteração/teste/publicação sem prova.
12. **Aprendizagem e memória:** registar lições e atualizar resumos canónicos sem substituir silenciosamente decisões anteriores. Alteração de intenção exige proveniência, data e relação de supersessão.

Estados semânticos mínimos: RECEIVED, UNDERSTANDING, PLANNED, AWAITING_APPROVAL, QUEUED, RUNNING, WAITING_DEPENDENCY, VALIDATING, COMPLETED, PARTIAL, FAILED, CANCELLED e UNKNOWN_NEEDS_REVIEW. Nomes internos podem mapear para estes estados por contratos versionados, sem perder as distinções.

## 5. Recuperação autónoma de conversas de várias IAs — missão prioritária
A recuperação é capacidade central, não uma tarefa pontual nem um resumo superficial.

### 5.1 Descobrir e inventariar
- Inventariar providers disponíveis/autorizados (por exemplo, ChatGPT, Claude, Gemini, Grok, DeepSeek e qualquer fonte nova explicitamente indicada, incluindo nomes como “QN” quando confirmado).
- Usar primeiro exportação oficial; depois browser autenticado dedicado; automação visual/OCR apenas quando DOM/exportação não bastem. Login, MFA e CAPTCHA são concluídos pelo utilizador; nunca copiar tokens/cookies do perfil pessoal nem contornar controlos.
- Guardar cobertura por provider, IDs/títulos/URLs/datas, contagem de mensagens quando disponível, método, fingerprint, checkpoint e falhas. Fonte inacessível = lacuna explícita, nunca “revista”.
- Quando o utilizador disser “vai buscar as conversas ao [provider]”, iniciar/retomar esse provider sem perder inventário global nem reimportar conversas inalteradas.

### 5.2 Importar e separar turnos
- Preservar transcript bruto e mensagens normalizadas, ordem, autor, timestamps e proveniência.
- Separar mensagens do utilizador de respostas da IA; papéis desconhecidos permanecem desconhecidos.
- Extrair pedidos, correções, decisões, propostas de IA, código, paths, erros, testes, resultados e questões em aberto.
- Preservar código com contexto adjacente, conversa/mensagem de origem, versão, hash/fingerprint, linguagem e path referido. Não executar artefactos importados automaticamente.
- Usar checkpoints, hashes e processamento incremental idempotente. Não reler tudo quando a fonte não mudou, salvo falha, nova evidência ou pedido explícito.

### 5.3 Renomear dentro da própria IA
- Produzir nomes canónicos com projeto + tema + finalidade/etapa e guardar título original, título proposto, provider e ID.
- Antes de alterar título no provider, confirmar que sessão e ação são suportadas, reversíveis e autorizadas. Se não forem seguras ou a interface mudar, registar sugestão e pedir intervenção, sem fingir que renomeou.
- Nunca eliminar conversas originais para as organizar.

### 5.4 Resumo de pedidos e verdade evolutiva
- Construir resumo consolidado dos pedidos reais do utilizador, agrupado por projeto, requisitos, prioridades e cronologia.
- Comparar respostas de várias IAs com os pedidos, mas não decidir por maioria de modelos. Confrontar as respostas com evidência e decisões explícitas.
- Identificar convergências, contradições, propostas nunca aceites, pedidos corrigidos, decisões substituídas, código antigo versus atual e requisitos sem implementação.
- Atualizar incrementalmente o resumo quando chegam novas conversas ou decisões; manter histórico e referências para as mensagens que justificam cada afirmação.
- Classificar como pedido do utilizador, proposta de IA, decisão confirmada, realidade verificada, superado, conflito ou por verificar. Não misturar categorias.
- Ligar conversas de diferentes providers ao mesmo projeto com evidência e confiança; títulos parecidos não bastam.
- A memória é arquivo útil, não fila infinita de tarefas: tarefas concluídas não reabrem sem nova evidência ou pedido.

## 6. Modularidade e expansão multi-PC
Inicialmente os módulos podem correr num PC, mas comunicam como serviços separados através de contratos versionados, IDs estáveis, APIs/eventos e limites explícitos. Evitar acoplamento a paths locais ou imports privados de outro módulo.

Expansão possível quando justificada:
- **PC HQ/cérebro:** política, memória canónica, estado global, despacho, auditoria e resposta final.
- **PC Programação:** workers de engenharia, workspaces isolados, builds e testes.
- **PC Pesquisa/Laboratório:** browser/research, experiências e avaliação de respostas.
- **PC QA/CI:** testes independentes e validação se a carga justificar.
- **Outros nós:** Conversation Intelligence, integrações ou domínios dedicados conforme medição real.

Cada nó é inscrito explicitamente, autenticado, autorizado e identificado por capacidade/versão/saúde. A rede local não implica confiança. Mensagens autenticadas, limitadas, correlacionadas, idempotentes e auditáveis; acesso revogável. Perda de nó produz tarefas bloqueadas/recuperáveis sem corromper o HQ. Não é necessário manter todos os computadores desde já.

## 7. Sequência de implementação
**P0 — Inventário e verdade documental:** ler documentos canónicos/complementares, confirmar caminhos, versões, referências e divergências PC/GitHub; preservar histórico e marcar o que não foi inspecionado.

**P1 — E2E mínimo do cérebro:** provar API → missão persistente → fila → autorização → worker/handler real → resultado → validação → estado terminal → resposta final. Identificar handlers existentes, distinguir execução de planeamento e preencher lacunas prioritárias. Testar reinício, falha, cancelamento, duplicação e ação interrompida.

**P2 — Contratos e observabilidade:** contrato comum de departamentos/agentes/tarefas/eventos/artefactos; heartbeat, filas, estado, logs e evidência consultáveis. Sem sistema de tarefas paralelo.

**P3 — Piloto multi-agent mínimo:** HQ + ligação ao proprietário + Python + QA/bug hunter + Research + Conversation Intelligence. Expandir quando os papéis piloto funcionarem e forem mensuráveis.

**P4 — Recuperação de conversações:** inventário por provider, ingestão com papéis/proveniência, resumo de pedidos, relações e evolução de intenção, renomeação autorizada e sincronização de memória.

**P5 — Departamento de software ampliado e laboratórios:** especialistas adicionais de frontend/SQL/PowerShell/Android conforme portefólio; pesquisa separada de avaliação de respostas; QA independente.

**P6 — Cockpit PC e móvel:** expor missões reais e ações autorizadas, com respostas/anexos apenas quando suportados. Não simular providers, upload, execução ou aprovação.

**P7 — Escritórios virtuais fiéis:** cada departamento/agente mapeado a estado real; começar com UI económica e adicionar 2D/3D progressivamente.

**P8 — Distribuição multi-PC:** separar um módulo de cada vez depois de contratos, testes, autenticação, health checks e recuperação passarem.

## 8. Critérios obrigatórios de aceitação
- Pedido real rastreável por ID do início à resposta final.
- Plano contém executor/capacidade identificados ou assinala bloqueio.
- Execução, aprovação e validação são eventos distintos, persistentes e auditáveis.
- Estado sobrevive ao fecho do cockpit, desconexão e reinício suportado.
- Não há falsos sucessos; resultado desconhecido não é tratado como sucesso.
- Testes independentes provam caminhos críticos, erros e recuperação.
- Sistema distingue mensagens do utilizador e da IA e mantém proveniência de cada resumo/decisão.
- Importação de novo provider é retomável, incremental e mostra cobertura/lacunas.
- Renomeações externas são confirmadas pela plataforma ou declaradas não realizadas.
- Escritório reflete estados reais e pode ser desligado sem interromper o core.
- Um departamento pode falhar sem corromper o cérebro ou os outros departamentos.
- Nenhuma capacidade é declarada concluída apenas por documentação, mocks, HTTP 200 ou um plano.
- Custos, limites, permissões e recursos são visíveis; sem API paga ou ação destrutiva silenciosa.

## 9. Resumo da revisão documental inicial — 2026-10-21
Revisão dirigida, não exaustiva de todo o histórico do PC/GitHub nem de todas as repos satélite. Foram abertos e revistos nesta passagem:

- **Constituição Arquitetural 2026-10-18:** norma superior para cérebro central, departamentos, contratos, fronteiras modulares, recuperação de conversações e sequência.
- **Digital Headquarters Concept 2026-10-12:** requisitos visuais para receção, gabinetes, departamentos, agentes, armazém, QA, enfermaria e expedição; visualização não é realidade operacional.
- **Adaptive Runtime and Distributed Workers 2026-10-12:** perfis adaptáveis ao hardware e workers distribuídos; proposta até validação.
- **Department Sovereignty and Agent Governance 2026-10-13:** autonomia departamental limitada, escalamento, anti-loop e aprovação central.
- **Adaptive Tools, Skills and Autonomy Roadmap 2026-10-13:** núcleo próprio separado de adaptadores substituíveis, autonomia governada e perfis de hardware.
- **External Agents and Self-Improvement Research 2026-10-12:** runtimes externos são workers substituíveis; DGM-MAT mantém política, memória e aceitação final.
- **Virtual Office Technology Research 2026-10-12:** UI independente/adaptável, com revisão de licenças antes de reutilizar software.
- **Digital Organization Architecture:** HQ, Engineering, QA, Bug Hunters, DevOps, Research, Conversation Intelligence e Provider Liaison; tarefas atribuíveis e auditáveis.
- **Digital Organization Build Order:** kernel → integração runtime → governação → ciclo de vida de workers → pilotos → Conversation Intelligence → avaliação → escala. Estados documentais não provam execução atual.
- **Conversation Recovery and Project Assembly Protocol:** inventário, vault, relações, nomes canónicos, extração contextual, staging e descoberta de repositórios.
- **Primary Mission and Evolving Truth:** recuperação de conversas como prioridade, distinção entre intenção, resposta IA, decisão e realidade verificada.
- **Conversation Intelligence Evidence Model v1:** proveniência de turnos, fingerprints, progress store e knowledge history; não prova importação autenticada ou E2E concluído.
- **AI Provider History Recovery and Script Archive:** exportação oficial primeiro, browser dedicado depois, OCR como último recurso, sem roubo de cookies nem execução automática de scripts recuperados.
- **Digital Headquarters Integration Index e Recovery & Unification Inventory:** ligam fontes e limites; inventários anteriores são dirigidos/parciais, não prova de auditoria completa.
- **Adaptive Virtual Office Requirements e Factory/HR/Departmental Hierarchy:** requisitos para salas, balcões, RH, especialistas e hierarquia; não declarados implementados.

### Síntese dos documentos
As decisões de base já estavam espalhadas: DGM-MAT como cérebro, organização por departamentos, especialização de agentes, QA independente, pesquisa, Conversation Intelligence, escritório como projeção, adaptação ao PC fraco, memória com proveniência e expansão multi-PC. Este documento não apaga nem substitui os originais: reúne a direção operacional e acrescenta o contrato end-to-end e o modelo explícito de departamentos. A Constituição de 2026-10-18 continua normativa para modularidade; a Diretiva Primária continua normativa para intenção/proveniência; documentos de pesquisa continuam propostas até implementação/testes.

**Limite importante:** esta revisão cobre os documentos identificados e acessíveis nesta passagem, não todos os ficheiros, branches locais, históricos completos, satélites ou dados privados de providers. O inventário tem de continuar até cada fonte ter estado explícito. Não declarar “todos os documentos revistos” antes dessa conclusão.

## 10. Regra permanente de progresso e relatório
Cada etapa regista pedido/ID; documento/código consultado; branch/commit/path; decisão; alteração; testes e resultados reais; limitações; fontes não acessíveis; próximo passo. O relatório separa **feito e verificado**, **feito mas não testado**, **proposto**, **bloqueado** e **não feito**. Nunca esconder falhas nem repetir verificações antigas sem motivo; retestar quando muda o caminho afetado ou há risco plausível de regressão.

**Regra final:** construir primeiro o cérebro end-to-end; organizar trabalho real por departamentos; recuperar a intenção histórica com proveniência; manter módulos independentes; e só considerar o DGM-MAT completo quando os critérios funcionais e as provas correspondentes passarem.
