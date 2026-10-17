# DGM-MAT — Plano de implementação do cérebro independente e do escritório virtual
**Data:** 2026-10-14  
**Branch:** `docs/tooling-capability-audit-2026-10-14`  
**Estado:** plano técnico; ainda sem implementação de código  
**Prioridade:** estabilidade e continuidade do core antes da visualização.

## 1. Decisão de arquitetura

O DGM-MAT deve ser tratado como um serviço/empresa digital que funciona em background. O escritório virtual, o cockpit web e o cockpit móvel são clientes independentes que consultam e controlam o sistema através de contratos explícitos. Nenhuma dessas interfaces é proprietária do estado ou do ciclo de vida das tarefas.

**Regra inegociável:** fechar, reiniciar, perder a ligação ou bloquear o renderer não pode parar o core, apagar pedidos, perder resultados confirmados nem deixar tarefas sem estado recuperável.

Não prometer disponibilidade literal de 100%: energia, hardware, disco, sistema operativo, providers e rede continuam a ser dependências. O objetivo é continuidade isolada, persistência, degradação graciosa, diagnóstico e recuperação testável.

## 2. Estado conhecido e limite da evidência

- O README de `AndreVazao/DGM-MAT` descreve funções de auditoria de repositórios, self-repair controlado, APIs de governação e a intenção de tornar a API uma entrada de cockpit.
- Existem repositórios separados `DGM-MAT-Runtime`, `DGM-MAT-Orchestrator` e `DGM-Cockpit-Frontend`. Os READMEs consultados de Runtime e Orchestrator contêm apenas uma descrição genérica de módulo. A tentativa de ler o README do Cockpit devolveu 404 porque o repositório está vazio.
- Os requisitos detalhados de escritório adaptável já estão documentados em `DGM-MAT_ADAPTIVE_VIRTUAL_OFFICE_AND_CORE_REQUIREMENTS_2026-10-14.md`.

Isto **não prova** que todos os contratos, workers, persistência, filas ou APIs estejam completos. A primeira implementação deve começar por uma auditoria read-only das implementações e testes reais, em vez de assumir capacidades pelo nome dos módulos.

## 3. Camadas propostas

### A. Core / Back office
- Serviço de background com ciclo de vida independente das interfaces.
- Fonte de verdade para tarefas, dependências, estados, eventos e resultados.
- Intake de pedidos, validação, deduplicação/idempotência, classificação e encaminhamento.
- Scheduler/orquestrador com limites de concorrência, timeouts, cancelamento e retries seguros.
- Registo persistente e recuperação após reinício; distinguir tarefas em curso, recuperáveis, bloqueadas e com resultado desconhecido.
- Gestão de permissões e aprovação humana para efeitos externos ou operações sensíveis.
- Logs estruturados, métricas, health checks e diagnóstico.
- Operação local-first; sem fallback pago silencioso.

### B. API e contratos
- API autenticada para criar pedidos, consultar estado, comunicar com agentes/departamentos e receber eventos.
- Separar endpoints de consulta dos comandos que alteram estado.
- Contratos versionados para tarefas, agentes, departamentos, mensagens, eventos, artefactos, aprovações e saúde.
- Cada evento inclui timestamp, origem, correlation/task ID e resultado; mensagens inválidas ou antigas não podem sobrescrever estado mais recente.
- Paginação e limites de resposta; o cockpit não deve carregar todos os logs de uma vez.
- A API não deve executar lógica de renderização nem depender de um cliente ligado.

### C. Cockpit de trabalho 2D
- Visão global: saúde do core, pedidos, filas, tarefas, bloqueios e aprovações pendentes.
- Detalhe de tarefa: objetivo, estado, dependências, tentativas, resultado, evidência, logs e próximo passo.
- Detalhe de agente/worker: identidade real, capacidades, tarefa atual, últimas ações e permissões relevantes.
- Mensagens dirigidas a um agente ou departamento com autorização e registo.
- Histórico pesquisável, filtros, timeline e indicação clara de estado desatualizado/desconhecido.
- Interface responsiva para PC e telefone, sem exigir renderização 3D.

### D. Escritório virtual como adaptador visual
- Renderer separado do processo core e, idealmente, isolado do processo da API.
- Consome uma projeção read-only de estados/eventos reais.
- Mapeia departamentos e agentes registados para pisos, salas e bonecos; sem inventar entidades.
- Clicar num boneco abre o painel funcional do cockpit.
- A representação visual de chamadas, reuniões, pacotes e deslocações corresponde a eventos identificáveis; caso contrário, é explicitamente decorativa.
- Se o renderer falhar, a API, as tarefas e os workers continuam operacionais.

### E. Cockpit móvel
- Cliente separado que pode desligar-se sem afetar o core.
- Criar pedidos, consultar resultados, ver alertas e aprovar operações permitidas.
- Sincronizar estado com o backend; não guardar a única cópia de um pedido no telefone.
- Autenticação, permissões, confirmação e auditoria para comandos.

## 4. Estratégia gráfica recomendada

1. **Económico (default):** 2D/SVG ou canvas leve, figuras-palito/ícones, atualizações por evento, animação reduzida e sem efeitos pesados.
2. **Equilibrado:** vista isométrica 2.5D/low-poly com animações seletivas.
3. **Avançado:** 3D apenas após benchmark em hardware real e demonstração de que não prejudica o core.

A tecnologia concreta deve ser escolhida após auditar o frontend existente e o hardware. Não adicionar uma framework ou motor 3D só por preferência estética. Se não houver frontend funcional, construir primeiro uma prova 2D mínima e isolada, com dependências pequenas e contrato de dados testável.

A adaptação de qualidade deve usar métricas observadas (FPS, carga de CPU, memória, capacidades gráficas disponíveis) e fallback conservador. A visualização pode baixar de qualidade ou encerrar-se; o core nunca deve aguardar por frames, animações ou resposta do renderer.

## 5. Plano de trabalho, gates e entregáveis

### Fase 0 — Auditoria read-only
Inventariar os repositórios autorizados da família DGM-MAT, branches, entry points, processos, APIs, persistência, tarefas, eventos, contratos, testes, workflows e dependências. Inspecionar callers/imports e confirmar quais componentes estão realmente ativos. Não modificar clones de terceiros, Labs protegidos ou o mirror congelado.

**Entregável:** matriz de realidade: capacidade, localização, evidência, testes, lacuna, risco e recomendação.

### Fase 1 — Provar a independência do core
Criar/fortalecer testes que executam o core sem frontend; submetem um pedido; persistem estado/eventos; interrompem/reiniciam o processo em ambiente de teste; verificam recuperação, idempotência e estado de resultado desconhecido. Testar renderer indisponível e cliente desligado.

**Gate:** nenhuma fase gráfica avança se tarefas confirmadas puderem desaparecer, duplicar-se ou depender da UI.

### Fase 2 — Contratos de observabilidade
Definir DTOs/esquemas versionados para status, tarefas, agentes, departamentos, mensagens, aprovações e eventos. Expor consultas autenticadas read-only e comandos separados. Testar autorização, limites, dados antigos e campos ausentes.

### Fase 3 — Cockpit 2D funcional
Criar vista de tarefas e agentes, detalhe, timeline, pesquisa e submissão de pedidos. Primeiro validar a utilidade operacional; a estética vem depois. O frontend do cockpit está vazio segundo a resposta 404 observada, por isso deve ser tratado como projeto a iniciar, não como UI existente a preservar.

### Fase 4 — Escritório navegável
Adicionar planta 2D, pisos e departamentos, vista explodida, seleção de agente e balcões de consulta ligados aos mesmos dados do cockpit. A lista/árvore permanece disponível como alternativa.

### Fase 5 — 2.5D e 3D adaptáveis
Só após benchmarks e testes de isolamento. Manter o renderer opcional, reduzir automaticamente efeitos sob carga e assegurar que falhas da camada gráfica não propagam exceções nem bloqueios ao core.

### Fase 6 — Comunicação visual e logística
Representar mensagens, pedidos, entregáveis e movimentos com correlation IDs e confirmação real. Parceiros externos só aparecem como conectados quando a integração estiver ativa. Animações de pausa/decorativas são opcionais e desligadas por defeito em modo económico.

## 6. Testes de aceitação obrigatórios

- Iniciar o core sem abrir o cockpit.
- Submeter um pedido via API/terminal e consultar o estado após fechar o cliente.
- Encerrar abruptamente o renderer durante trabalho e confirmar que o core não é afetado.
- Reiniciar o frontend e recuperar a vista a partir do backend, sem duplicar pedidos.
- Simular restart do core em testes e verificar recuperação idempotente.
- Simular provider lento/indisponível, timeout, mensagem inválida, armazenamento indisponível e estado desconhecido.
- Confirmar que falhas não se apresentam como sucesso e que operações externas exigem permissões/aprovações adequadas.
- Medir CPU/RAM com modo económico no PC-alvo antes de experimentar renderização avançada.
- Validar que cada agente, estado e comunicação mostrados têm proveniência real.
- Executar testes localmente sempre que possível; workflows de GitHub Actions devem manter o padrão manual quando não forem essenciais.

## 7. Política de alterações

- Branch dedicada, alterações pequenas e documentadas.
- Investigar antes de decidir; preservar código existente sem evidência de substituição.
- Não fazer merge para `main`, push de código operacional, deploy, instalação de ferramentas ou alterações ao runtime em produção como consequência desta nota.
- Não tocar em clones de terceiros, Labs ou `DGM-MAT-FULL-MIRROR`.
- Após cada fase, atualizar documentação e memória central apenas depois de verificar os resultados.
- Qualquer alteração com efeitos externos ou autoridade elevada exige revisão e aprovação explícitas.

## 8. Recomendação imediata

O próximo trabalho técnico é a **Fase 0 — auditoria read-only do core/runtime/orquestração e das fronteiras do cockpit**, usando o código e testes existentes. Só depois devemos selecionar o primeiro módulo a alterar. O objetivo não é criar já bonecos; é tornar a atividade real observável e provar que a empresa continua a trabalhar quando a janela fecha.
