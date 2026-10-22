# DGM-MAT — Plano Mestre de Estabilização do Cérebro e Entrega por Fases

**Data:** 2026-10-22  
**Estado:** plano de execução proposto — não é prova de implementação  
**Ramo documental:** `docs/dgm-mat-brain-first-roadmap-2026-10-22`  
**Objetivo:** deixar a arquitetura, o cérebro, a execução de missões, a governação, a memória, as interfaces e o processo de entrega estruturalmente coerentes antes da instalação e do fine-tuning local.

> **Regra de saída:** nenhuma fase é considerada concluída por existir documentação, por a API responder HTTP 200, por uma missão aparecer como RUNNING ou por um build terminar. A fase só passa quando os critérios verificáveis abaixo forem demonstrados. Quando um requisito já estiver implementado, não o reescrever: inspecionar, testar e registar a evidência.

## 1. Decisão central e ordem de prioridades

O DGM-MAT deve evoluir por esta ordem:

1. **Conhecer o estado real do código e reconciliar o que já existe.**
2. **Garantir um ciclo end-to-end de missão funcional, persistente e verificável.**
3. **Garantir segurança, permissões e aprovação humana em todos os pontos relevantes.**
4. **Estabilizar o ciclo de vida do runtime, os executores e a recuperação após falhas.**
5. **Unificar os contratos de estado/eventos consumidos por PC, APK e escritório.**
6. **Fechar a experiência mínima do cockpit PC e validar o empacotamento EXE.**
7. **Validar o APK, o emparelhamento e a ligação segura ao PC.**
8. **Só então expandir a autonomia dos departamentos e construir a visualização rica do escritório.**
9. **Fazer fine-tuning local com observações reais, sem confundir afinação com reparação estrutural.**

**Princípios inegociáveis:** estabilidade > funcionalidades; evidência > suposições; controlo manual > automação destrutiva; custo zero/local-first por defeito; nenhuma alteração irreversível sem autorização; nenhum agente declara sozinho uma entrega crítica concluída.

## 2. Âmbito e fronteiras

- **DGM-MAT Central:** cérebro soberano; mantém missões, política, memória canónica, despacho, permissões, checkpoints, eventos e verificação final.
- **Departamentos:** módulos lógicos autónomos com responsabilidades, competências, limites, filas e critérios de aceitação; começam no mesmo processo quando isso simplifica a operação.
- **Agentes:** executores de capacidades identificadas e verificadas; o nome ou prompt de um agente não prova que a competência existe.
- **Cockpit PC:** interface operacional e de conversa; não é fonte de verdade nem requisito para o cérebro continuar a executar.
- **APK:** cliente remoto do mesmo cérebro, nunca um segundo cérebro; só recebe permissões autorizadas.
- **Escritório digital:** projeção visual de telemetria real; não inventa agentes, atividade ou progresso.
- **Repositórios satélite:** permanecem separados e comunicam por contratos explícitos; não os fundir para facilitar um build.
- **VAZÃO Sovereign Trader:** sistema separado, salvo decisão arquitetural explícita em contrário.

A arquitetura deve continuar útil num PC fraco. O core tem de funcionar headless; o cockpit e o escritório não podem manter modelos pesados ou renderização 3D contínua como condição de funcionamento.

## 3. Fase 0 — Inventário, reconciliação e mapa de evidências

### Trabalho
- Registar os SHAs atuais de `main`, branches de trabalho, PRs e cópias locais quando estas estiverem acessíveis.
- Comparar o que existe em `main`, nos branches e nos documentos de estabilização; não assumir que alterações preparadas noutro branch já estão em `main`.
- Para cada requisito, atribuir um estado: `CONFIRMADO`, `IMPLEMENTADO-NÃO-VERIFICADO`, `PARCIAL`, `AUSENTE`, `BLOQUEADO` ou `OBSOLETO-CANDIDATO`.
- Mapear entrypoints, criação/inicialização/paragem de loops, consumidores de filas, executores, armazenamento, APIs, clientes e testes.
- Verificar imports, callers, compatibilidade de contratos, persistência, configuração e histórico Git antes de alterar ou remover ficheiros.
- Preservar o código antigo até ser provado que está obsoleto e não tem consumidores.

### Critério de saída
Existe um mapa de capacidades e lacunas com links para código/testes e SHAs. Não há conclusões baseadas apenas no nome do ficheiro ou em documentação.

## 4. Fase 1 — Contrato end-to-end de missão (bloqueio principal)

### Ciclo obrigatório
`received → classified → planned → approval_pending | queued → running → succeeded | failed | blocked | cancelled | unknown`

Os nomes exatos podem adaptar-se ao modelo existente, mas o significado deve ser inequívoco e consistente entre backend e clientes.

### Trabalho
- Separar explicitamente pedido do utilizador, contexto, proposta de agente, decisão, plano aprovado, ação tentada, resultado observado e resultado validado.
- Associar cada missão a IDs estáveis, timestamps, plano/versionamento, dependências, executor, critérios de aceitação e referências de evidência.
- Cada tipo de missão suportado deve estar ligado a um executor real. Se não existir executor, responder `blocked/unsupported` ou falhar explicitamente; não simular execução.
- A decomposição em subtarefas é planeamento, não execução.
- O sucesso da criação HTTP significa apenas “missão aceite/criada”, nunca “missão concluída”.
- Garantir idempotência para pedidos repetidos, correlação ponta a ponta e limites claros de timeout/retry.
- Os bloqueios de aprovação de uma missão não devem parar tarefas independentes.
- Resultados parciais e erros têm de ser preservados e apresentados ao utilizador.

### Critérios de saída
- Pelo menos um tipo de missão suportado percorre receção, execução real, verificação e entrega do resultado.
- Um tipo não suportado termina num estado explícito sem fingir sucesso.
- Repetir um pedido com a mesma chave/idempotência não cria trabalho duplicado.
- Os estados da API, armazenamento e cockpit coincidem.

## 5. Fase 2 — Persistência, checkpoints e recuperação

### Trabalho
- Definir a fonte de verdade durável para missões, subtarefas, decisões, eventos e aprovações.
- Persistir checkpoints de forma atómica e validar as janelas de falha entre gravações.
- No arranque, reconciliar filas, missões e intervenções pendentes; não ressuscitar trabalho cancelado nem perder aprovações consumidas.
- Separar estados terminais de estados recuperáveis.
- Aplicar transações, timeouts e política de concorrência adequados à base de dados existente. Não mudar de base de dados sem benchmark e justificação.
- Verificar política de cópias de segurança, migrações e compatibilidade com versões anteriores.
- Definir retenção para logs/eventos e evitar persistir segredos ou conteúdo sensível desnecessário.

### Critérios de saída
- Reiniciar o processo durante uma missão não corrompe o registo nem duplica execução.
- Reiniciar enquanto uma missão espera por André preserva o pedido de intervenção e permite retomar/rejeitar uma única vez.
- Cancelamento, rejeição e decisão consumida não podem ser repetidos para reabrir uma ação.
- Há testes de falha injetada nas fronteiras críticas de persistência.

## 6. Fase 3 — Ciclo de vida do runtime e filas

### Trabalho
- Identificar um único proprietário de cada loop/worker e um único caminho autorizado para consumir cada fila.
- Garantir startup/shutdown determinísticos, prevenção de workers duplicados e recuperação de tarefas órfãs.
- Definir limites de concorrência, timeout, cancelamento, backoff e classificação de falhas transitórias/permanentes.
- Não fazer retry automático de ações não idempotentes sem salvaguardas.
- Evitar que tarefas de investigação, providers lentos ou uma missão bloqueada prendam o loop central.
- Expor a saúde do worker separadamente da saúde HTTP da API.

### Critérios de saída
- Iniciar e parar o runtime repetidamente não duplica consumidores.
- Falha num worker não paralisa o processo de gestão de missões.
- As tarefas em fila, ativas, bloqueadas e falhadas podem ser explicadas através de estado persistido e eventos.

## 7. Fase 4 — Segurança, governação e autonomia progressiva

### Trabalho
- Inventariar todas as rotas HTTP e WebSocket, incluindo rotas antigas/compatibilidade, operações de leitura e mutações.
- Aplicar autenticação e autorização em todas as rotas que expõem dados privados ou alteram estado; exceções públicas devem ser mínimas e documentadas.
- Restringir CORS a origens explícitas; recordar que CORS não substitui autenticação.
- Proteger WebSockets durante o handshake e validar sessão, scopes, expiração e revogação.
- Manter loopback como limite por defeito até a matriz de autenticação estar testada. Não abrir LAN, Tailscale ou Internet prematuramente.
- Separar permissões para consultar, criar missão, aprovar, cancelar, gerir providers, mexer em ficheiros e executar ações.
- As decisões críticas devem estar ligadas ao hash exato do plano e às evidências analisadas. Se plano ou evidência mudar, invalidar a aprovação.
- Reuniões entre CEO e departamentos precedem alterações estruturais importantes. André mantém a aprovação final para decisões protegidas.
- Confiança progressiva exige delegação explícita, âmbito estreito, limites de risco, resultados reversíveis verificados e revogação. Aprovações repetidas não concedem autoridade automaticamente.
- CAPTCHA/MFA e passos de autenticação humana não são contornados. Segredos nunca entram em prompts, logs ou memória genérica.

### Critérios de saída
- Testes negativos provam que sessão ausente/expirada, scope insuficiente e utilizador revogado não conseguem consultar dados privados nem executar mutações.
- Os dois WebSockets e todas as rotas de mutação têm contratos de autenticação testados.
- Aprovação não executa por si só; a execução verifica novamente plano, permissão e evidência no momento da ação.
- Uma missão à espera de aprovação não bloqueia missões independentes.

## 8. Fase 5 — Memória, decisões e aprendizagem controlada

### Trabalho
- Preservar proveniência, autor, data, fonte, nível de confiança e estado das decisões.
- Distinguir pedido do proprietário, sugestão de IA, decisão aprovada, decisão substituída e hipótese experimental.
- Guardar observações de execução separadas de lições validadas.
- Uma lição só é reutilizável depois de passar avaliação reproduzível e não pode alterar automaticamente a política central.
- Permitir procurar conhecimento em conversas/documentos sem misturar dados entre projetos ou repositórios.
- Criar política de deduplicação, retenção e arquivo para reduzir ruído sem eliminar história útil.

### Critérios de saída
- Uma decisão pode ser rastreada até à sua fonte e às alterações que a substituíram.
- A memória não transforma automaticamente uma hipótese ou saída de agente em facto confirmado.
- Importações repetidas não duplicam silenciosamente o mesmo artefacto.

## 9. Fase 6 — Observabilidade e desempenho mensurável

### Trabalho
Começar com métricas locais de baixo custo; só adicionar uma stack de observabilidade se houver necessidade demonstrada.

Métricas mínimas:
- latência da receção até ao início, execução, verificação e entrega;
- duração e falhas por executor/provider/ferramenta;
- tamanho/idade das filas e número de missões bloqueadas;
- CPU, memória, disco e número de workers;
- reconexões, erros de API e eventos perdidos;
- número de retries e custo estimado/real, quando disponível.

Cada evento deve ter versão de schema, ID, timestamp, fonte, correlation ID, entidade, transição de estado e referência de evidência. Não incluir credenciais nem corpos completos de conversa por defeito.

### Critérios de saída
- Um relatório local identifica os maiores tempos e erros sem recolher conteúdo sensível.
- Antes/depois de uma otimização pode ser comparado com a mesma carga de teste.
- Não instalar serviços pesados nem manter modelos locais ativos sem benefício medido.

## 10. Fase 7 — Contratos comuns e cockpit PC

### Trabalho
- Definir uma fonte de verdade e schemas versionados para missões, agentes, departamentos, aprovações, providers, saúde e eventos.
- O cockpit consulta o backend e envia comandos autorizados; não mantém estado soberano.
- Fechar o ciclo de conversa: envio, confirmação de receção, progresso real, pergunta/aprovação quando necessária, resultado final ou erro.
- Distinguir “PC não encontrado”, “PC encontrado mas sem emparelhamento”, “sessão expirada”, “API indisponível” e “runtime degradado”.
- Implementar reconexão, atualização incremental e recuperação de eventos perdidos.
- Preferir polling moderado no início; avaliar SSE para eventos unidirecionais e reservar WebSockets para necessidades bidirecionais comprovadas.
- Tornar uploads/anexos explícitos, limitados e seguros; não aceitar caminhos locais arbitrários nem executar ficheiros enviados sem revisão.
- O backend continua a trabalhar se o cockpit fechar.

### Critérios de saída
- O cockpit não reporta sucesso com base apenas num HTTP 200 de criação.
- Ao perder/reabrir o cockpit, a missão e o histórico recuperam-se a partir do backend.
- O utilizador vê estados reais, erros legíveis e aprovações pendentes.

## 11. Fase 8 — EXE, serviço local e instalação no PC

### Trabalho
- Auditar o entrypoint, dependências, configuração, paths, permissões e armazenamento para o ambiente Windows.
- Definir startup/shutdown previsíveis, logs rotativos, diagnóstico e recuperação após reinício.
- Confirmar que o EXE não depende acidentalmente da pasta de desenvolvimento ou de uma consola aberta.
- Validar health, autenticação, execução, persistência, reinício e compatibilidade do cockpit separadamente.
- Construir a partir de um SHA identificado; registar artefacto, hash, versão e resultado de cada teste.
- Evitar múltiplas builds sem alterações relevantes; usar uma única execução manual quando o branch estiver pronto.
- Não declarar o EXE pronto apenas porque o empacotamento terminou.

### Critérios de saída
- Arranque e paragem são controlados e repetíveis.
- API, worker e armazenamento são diagnosticados separadamente.
- Um teste end-to-end local demonstra pelo menos uma missão real suportada, um bloqueio seguro e recuperação após reinício.
- Os artefactos são reproduzíveis e identificados por commit.

## 12. Fase 9 — APK e ligação segura ao PC

### Trabalho
- Validar primeiro testes de contrato, sintaxe e build do APK; a build prova empacotamento, não conectividade funcional.
- Confirmar descoberta rendezvous, endpoint, permissões de rede e compatibilidade Android/WebView.
- Implementar emparelhamento por código temporário, sessão com scopes e expiração, revogação e mensagens de estado inequívocas.
- Não confiar em `localhost` no WebView Android para chegar ao PC; usar o mecanismo de descoberta/ligação aprovado.
- A recuperação USB/ADB pode executar apenas operações reversíveis e autorizadas. Não contornar autorização de depuração, limpar dados nem reinstalar sem confirmação explícita.
- Testar interrupção de rede, PC desligado, sessão expirada, código reutilizado, dispositivo revogado e pedido repetido.
- Não expor bootstrap tokens no APK nem armazenar segredos permanentes no cliente.

### Critérios de saída
- APK instala e abre; a ligação é testada separadamente do build.
- Emparelhamento funciona uma vez, expira e não pode ser repetido/reutilizado.
- Falhas de rede não duplicam missões nem mostram sucesso falso.
- PC e APK mostram o mesmo estado de missão e as mesmas aprovações permitidas.

## 13. Fase 10 — Departamentos, contratação de agentes e autoevolução

### Trabalho
- Começar por departamentos lógicos dentro do processo central; só separar processos/máquinas quando existir necessidade mensurável e contrato claro.
- Cada departamento tem missão, responsável, capacidades comprovadas, limites, fila, memória delimitada, critérios de aceitação e resultados auditáveis.
- A investigação encontra opções; QA independente testa; engenharia implementa; DevOps empacota; segurança verifica; o cérebro integra e entrega.
- Contratação de agentes reutiliza competências verificadas e exige uma tarefa/necessidade real.
- Departamentos podem autoevoluir tarefas reversíveis dentro do mandato e orçamento concedidos.
- Alterações de arquitetura, segurança, credenciais, política, reestruturação e operações irreversíveis seguem o gate humano.
- Nunca permitir que um agente crie, avalie e aprove sozinho a própria elevação de privilégios.

### Critérios de saída
- Uma tarefa pode ser atribuída, executada, avaliada e devolvida por um departamento com evidência.
- O cérebro consegue resolver conflitos, reatribuir tarefas e continuar trabalho independente.
- Nenhum departamento pode alterar unilateralmente a política central.

## 14. Fase 11 — Escritório digital adaptativo

Só começar quando as fases de missão, segurança, contratos e cockpit estiverem aprovadas.

1. **Cockpit operacional:** missões, chat, filas, saúde, aprovação, logs e diagnóstico.
2. **Escritório 2D/isométrico:** pisos e departamentos reais; agentes e animações dependem de telemetria.
3. **3D opcional:** ativado por capacidade do equipamento, sem bloquear o backend ou a interface leve.

Estados visuais válidos: ativo (atividade observada recente), à espera (dependência explícita), inativo (telemetria válida sem trabalho), degradado, indisponível ou desconhecido. Não converter `unknown` em `active` para decoração.

### Critérios de saída
- Cada elemento visual tem uma fonte de dados rastreável.
- O escritório continua utilizável sem WebGL/3D e em PC de baixo desempenho.
- Desligar o escritório não afeta as missões.

## 15. Fase 12 — Fine-tuning e testes locais

O fine-tuning local é uma etapa de afinação, não um substituto da correção estrutural.

### Bateria mínima no PC
- Arranque a frio, paragem, segundo arranque e recuperação após reinício.
- Saúde da API, saúde do worker, autenticação e permissões.
- Missão suportada com resultado real; missão não suportada; erro de provider; tarefa bloqueada à espera de André.
- Fechar/reabrir cockpit durante execução; reconectar; verificar ausência de duplicação.
- Persistência de missões, decisões, eventos e histórico.
- Testes de CPU/memória em perfil leve e durante atividade.
- EXE: paths, logs, configuração, permissões e funcionamento sem terminal.
- APK: instalação, descoberta, emparelhamento, expiração, revogação, perda de rede e sincronização de estado.
- USB/ADB: dispositivo autorizado, offline, cabo removido e recuperação reversível; nunca testar primeiro com operações destrutivas.

Registar para cada achado: passos de reprodução, resultado esperado/observado, logs sem segredos, gravidade, causa provável, correção, regressão e commit. Corrigir uma classe de falhas de cada vez e repetir os testes afetados.

## 16. Política de CI, custos e releases

- Testes locais e suites focadas primeiro; CI apenas quando acrescenta evidência necessária.
- GitHub Actions manual para builds de EXE/APK, respeitando os minutos disponíveis.
- Um build de cada artefacto por revisão candidata, salvo falha concreta que justifique nova execução.
- Não correr suites completas por rotina após alterações documentais ou mudanças sem impacto no código; verificar sempre o alcance real.
- Providers pagos ficam desativados por defeito; nunca fazer fallback pago silencioso.
- Guardar SHAs, logs, hashes dos artefactos e relatório de validação.
- Nenhum deploy, merge ou release é considerado aprovado só por um agente o recomendar.

## 17. Gate final de prontidão estrutural

Antes de declarar o cérebro “pronto para instalação”, todos os pontos aplicáveis devem ter evidência:

- [ ] Inventário reconciliado com os branches e SHAs efetivos.
- [ ] Pelo menos um caminho de missão real end-to-end verificado.
- [ ] Tipos de missão não suportados bloqueiam honestamente.
- [ ] Idempotência, cancelamento, timeouts e recuperação testados.
- [ ] Persistência e retoma após reinício demonstradas.
- [ ] Lifecycle de workers sem duplicação demonstrado.
- [ ] Todas as rotas privadas/de mutação e WebSockets cobertos por autenticação/autorização testadas.
- [ ] Aprovação humana vinculada ao plano exato e à evidência.
- [ ] Cockpit mostra estados reais e recupera contexto.
- [ ] EXE validado por SHA com teste local documentado.
- [ ] APK validado por SHA; instalação e ligação verificadas como testes separados.
- [ ] Escritório consome telemetria real e não é requisito para execução.
- [ ] Perfil de recursos medido no hardware-alvo.
- [ ] Nenhum bug crítico aberto, nenhum segredo nos logs, nenhuma alteração destrutiva sem autorização.
- [ ] Documento de release separa explicitamente passou, falhou, bloqueado e não testado.

Um item por marcar não significa necessariamente que todo o desenvolvimento tem de parar; significa que a capacidade dependente desse item não pode ser declarada pronta nem exposta prematuramente.

## 18. Lacunas já documentadas que devem ser revalidadas

Os documentos seguintes registam observações de auditorias anteriores. Devem ser revalidados contra o SHA/branch atual antes de se assumir que continuam iguais ou que já foram resolvidos:

- [Gate de estabilização end-to-end do backend — 2026-10-17](DGM-MAT-BACKEND-END-TO-END-STABILIZATION-GATE-2026-10-17.md): execução real, ownership do runtime, correspondência entre aprovação e fila de ações, cockpit e testes end-to-end.
- [Auditoria da fronteira de segurança da API — 2026-10-09](../security/API_SECURITY_BOUNDARY_AUDIT_2026-10-09.md): autenticação consistente, WebSockets, CORS e rotas antigas.
- [Modelo canónico de operação e departamentos — 2026-10-21](DGM-MAT-CANONICAL-OPERATING-MODEL-END-TO-END-AND-DEPARTMENTS-2026-10-21.md): autoridade, responsabilidades e autonomia delimitada.
- [Esquemática do escritório virtual — 2026-10-21](DGM-MAT-VIRTUAL-OFFICE-SYSTEM-SCHEMATIC-2026-10-21.md): fonte de verdade, telemetria, estados e fronteiras entre interfaces.
- [MissionEngine — checkpoints e intervenção humana](MISSION_ENGINE_HUMAN_INTERVENTION_CHECKPOINTS.md): persistência, espera por utilizador e limites atuais de exposição remota.

## 19. Registo de execução por fase

Manter uma tabela de controlo atualizada à medida que cada fase é trabalhada:

| Fase | Estado | Evidência/commit | Bloqueios | Próxima ação |
|---|---|---|---|---|
| 0 — Inventário | A iniciar/revalidar | A preencher | A identificar | Reconciliar branches e código |
| 1 — Missão end-to-end | Não declarar concluída sem teste | A preencher | A identificar | Validar executor real |
| 2 — Persistência | A verificar | A preencher | A identificar | Testes de falha/reinício |
| 3 — Runtime/filas | A verificar | A preencher | A identificar | Confirmar ownership de loops |
| 4 — Segurança/governação | Parcial até evidência atual | A preencher | A identificar | Auditoria de todas as rotas |
| 5 — Memória/aprendizagem | A verificar | A preencher | A identificar | Proveniência e validação |
| 6 — Observabilidade | A verificar | A preencher | A identificar | Instrumentação leve |
| 7 — Cockpit PC | A verificar | A preencher | A identificar | Ciclo real de missão |
| 8 — EXE | Build ainda por confirmar para a revisão candidata | A preencher | Sessão/build/teste local | Build única + validação |
| 9 — APK | Build atualizada por confirmar para a revisão candidata | A preencher | Sessão/build/teste local | Build única + ligação segura |
| 10 — Departamentos | Incremental | A preencher | Contratos/capacidades | Autonomia delimitada |
| 11 — Escritório | Depois dos gates do cérebro | A preencher | Telemetria real | Começar 2D/isométrico |
| 12 — Fine-tuning local | Depois da instalação | A preencher | Acesso ao PC | Executar bateria local |

**Não marcar estados como concluídos por intenção ou por documentação.** Atualizar a tabela com o commit exato, os testes efetivamente executados, o resultado e a data.

## 20. Checkpoint de implementação — 2026-10-22

O desenvolvimento remoto começou em branches isolados, sem fazer merge nem substituir o código existente.

| Componente | Alteração em preparação | PR | Estado de validação |
|---|---|---|---|
| Backend — catálogo do escritório | O endpoint existente `GET /runtime/office/telemetry` acrescenta o catálogo declarado de departamentos/agentes; atividade permanece `unknown` sem evidência direta; permissões internas não são expostas. | [DGM-MAT #145](https://github.com/AndreVazao/DGM-MAT/pull/145) | Testes adicionados; ainda não executados. |
| Cockpit móvel | Nova vista de escritório com contagens observadas, atividade recente sem objetivos privados e diretório expansível quando o catálogo estiver disponível. | [DGM-MAT-Mobile #2](https://github.com/AndreVazao/DGM-MAT-Mobile/pull/2) | Sintaxe JavaScript verificada; testes de contrato e APK ainda não executados. |
| Cockpit PC | Diretório expansível de departamentos/agentes, separado dos estados em direto e construído com DOM/`textContent`. | [DGM-Cockpit-Frontend #13](https://github.com/AndreVazao/DGM-Cockpit-Frontend/pull/13) | Sintaxe JavaScript verificada; suíte Node e revisão visual local ainda não executadas. |

### Ordem de integração

1. Rever e validar primeiro o PR de backend #145.
2. Só depois integrar os PRs de interface #2 e #13; ambos mantêm fallback honesto se o catálogo ainda não existir.
3. Compilar uma única revisão candidata de APK e EXE depois de confirmar os SHAs integrados.
4. No PC, executar a suíte Python focada e o cockpit; no telemóvel, instalar o APK e validar emparelhamento, telemetria, perda de rede e expiração de sessão.
5. Só então ligar atividade de agentes a eventos reais. Não converter papéis declarados em agentes “ativos” sem heartbeat/execução verificável.

**Estado factual deste checkpoint:** os três PRs de implementação estão separados e não foram integrados. Não foi criado nenhum novo APK/EXE, não foram iniciados workflows de CI e os testes de runtime/Python não foram executados. A verificação sintática de JavaScript não equivale à execução da suíte de testes.

O PR [DGM-MAT #143](https://github.com/AndreVazao/DGM-MAT/pull/143), relativo a reuniões de governação e aprovações do proprietário, continua separado e requer a sua própria revisão/validação; não se assume que a interface já está ligada a esses controlos.

## 21. Referências técnicas externas

Estas referências são pontos de comparação, não dependências obrigatórias:

- SQLite WAL: https://www.sqlite.org/wal.html
- OpenTelemetry para Python: https://opentelemetry.io/docs/languages/python/
- Android WebView — boas práticas de segurança: https://developer.android.com/privacy-and-security/risks/insecure-webview-native-bridges
- LiteLLM (avaliar apenas se houver lacuna real no gateway atual): https://docs.litellm.ai/
- OpenWOP (comparação de padrões de orquestração durável): https://github.com/openwop/openwop

---

**Resultado pretendido:** quando o DGM-MAT for instalado, o núcleo funcional e a governação já devem estar estruturalmente bem organizados. Os testes locais servirão para descobrir diferenças de hardware, falhas de integração e pequenos ajustes de interface — não para descobrir pela primeira vez se o cérebro consegue executar, persistir, distribuir, proteger e verificar uma missão.
