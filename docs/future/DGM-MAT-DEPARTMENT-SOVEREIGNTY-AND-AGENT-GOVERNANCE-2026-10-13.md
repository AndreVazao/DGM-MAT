# DGM-MAT — soberania dos departamentos, delegação e prevenção de ciclos

**Data:** 2026-10-13  
**Estado:** decisão de arquitetura documentada; não implementada  
**Branch:** `docs/digital-headquarters-concept-2026-10-12`

## 1. Princípio de comando

DGM-MAT é o Patrão e cérebro central: mantém a missão global, hierarquia, políticas, memória canónica, orçamento de recursos, autorização de contratação/criação de agentes e validação final. Os departamentos são soberanos na execução do seu domínio, mas respondem ao DGM-MAT e não podem substituir nem alterar unilateralmente a autoridade central.

A soberania departamental significa autonomia operacional dentro de um mandato, não independência da governação.

- DGM-MAT atribui missão, prioridade, limites, orçamento de recursos, prazo e critérios de aceitação.
- Cada departamento escolhe como executar dentro desse mandato e gere os seus agentes autorizados.
- Só DGM-MAT autoriza a criação/contratação de novos agentes, novos departamentos, novas ferramentas privilegiadas ou alterações aos limites de segurança.
- Um departamento pode propor a contratação/criação de um especialista e justificar a necessidade; a proposta não se executa até receber autorização.
- Nenhum agente pode aprovar a própria alteração de permissões, validar sozinho trabalho crítico ou reescrever a política central.

## 2. Pedido de acesso ou ajuda entre departamentos

Um agente não deve ficar bloqueado nem tentar contornar permissões quando lhe falta uma ferramenta, dado ou capacidade. Deve emitir um pedido estruturado ao coordenador do seu departamento, que decide se pode resolver localmente ou encaminha para o departamento competente. O pedido interdepartamental passa pelo encaminhador central de tarefas/políticas, não por uma cadeia informal ilimitada de mensagens diretas.

Cada pedido contém, no mínimo:

- identificador único e identificador da missão-pai;
- departamento/agente requerente e departamento destinatário;
- resultado necessário e motivo;
- recurso ou capacidade pedidos, com o âmbito mínimo;
- classificação de risco e duração pretendida do acesso;
- prazo, estado, tentativas e referência para o artefacto/contexto relevante;
- condição explícita de conclusão e de cancelamento.

O departamento destinatário pode devolver um artefacto, uma resposta tipada, uma capacidade limitada ou uma recusa justificada. A falta de acesso nunca concede acesso implícito. O acesso temporário, se aprovado, é limitado ao recurso e tempo necessários, auditável e revogável.

## 3. Anti-entupimento e anti-loop

A comunicação deve transportar resultados e referências, não repetir indefinidamente o histórico completo.

Regras obrigatórias para a futura implementação:

1. **Uma fonte canónica:** estado da tarefa e memória partilhada são mantidos pelo núcleo; cópias locais são caches/projeções com origem e versão.
2. **Deduplicação idempotente:** pedidos equivalentes na mesma missão são associados a um pedido existente em vez de criarem uma cascata de pedidos.
3. **Grafo de delegação:** cada subtarefa regista pai, origem, destino e dependências; impedir ciclos no grafo antes de aceitar nova delegação.
4. **Limites de profundidade e fan-out:** cada missão tem máximo configurável de níveis de delegação, subtarefas simultâneas e reencaminhamentos.
5. **Orçamento de mensagens/tentativas:** número máximo de tentativas, tamanho de contexto e tempo de espera; depois disso, suspender, devolver erro estruturado ou escalar ao DGM-MAT.
6. **Estados terminais claros:** concluída, recusada, bloqueada, expirada ou cancelada; um pedido terminal não volta a abrir por resposta duplicada.
7. **Sem ping-pong:** se A pede a B, e B pede a A o mesmo recurso sem progresso novo, o núcleo deteta repetição, congela a cadeia e pede uma decisão ao coordenador/DGM-MAT.
8. **Fila com prioridades e backpressure:** urgência, dependências, custo e capacidade disponível regulam despacho; se o destino estiver saturado, o pedido espera, é reatribuído ou é escalado, sem criar workers automaticamente.
9. **Resumo + referência:** transmitir apenas contexto necessário, decisão anterior e links/IDs de artefactos, não todo o chat.
10. **Escalonamento humano:** bloqueios que exigem decisão humana entram numa fila deduplicada; uma missão bloqueada não deve bloquear missões independentes.
11. **Auditoria:** registar quem pediu, quem autorizou, o que foi disponibilizado, quando expirou e qual o resultado, sem gravar segredos desnecessários.
12. **Cancelamento propagado:** cancelar uma missão invalida as subtarefas dependentes ainda não concluídas e revoga acessos temporários associados.

## 4. Memória: partilhada, mas governada

- A memória nuclear e as políticas pertencem ao DGM-MAT.
- Departamentos podem manter memória operacional especializada e caches de trabalho, com escopo claro.
- Agentes propõem novas memórias, correções ou conclusões; o mecanismo central valida proveniência, conflito, confiança, data e âmbito antes de atualizar memória canónica.
- Distinguir factos verificados, hipóteses, decisões, preferências, resultados de teste e dados temporários.
- As memórias departamentais não podem contradizer silenciosamente a memória nuclear; conflitos geram um evento de reconciliação.
- Minimizar retenção de credenciais, dados pessoais e conteúdo irrelevante. A partilha de memória não implica acesso universal aos dados subjacentes.

## 5. Contratação e criação de agentes

Cada departamento mantém um catálogo de funções necessárias, agentes autorizados, capacidades, ferramentas, custos/consumo, desempenho medido e substitutos disponíveis.

Fluxo proposto:

1. Departamento identifica lacuna comprovada e apresenta pedido ao DGM-MAT.
2. DGM-MAT verifica se uma ferramenta ou agente existente pode resolver o problema.
3. Se necessário, autoriza a criação/contratação de um agente dedicado com função, fronteiras, permissões, recursos e critérios de avaliação.
4. O agente começa em ambiente isolado e com acesso mínimo, usando tarefas de teste.
5. O responsável departamental avalia resultados; validação independente verifica segurança e qualidade.
6. DGM-MAT aprova, rejeita, restringe, suspende ou retira o agente.
7. Toda a decisão fica registada; nenhum agente novo recebe autoridade por existir ou por ter sido criado por outro agente.

## 6. Departamento de Programação — estrutura especializada

O departamento de Programação deve cobrir o ciclo completo de engenharia sem depender de um único agente generalista. A composição concreta é dinâmica: iniciar com poucas funções ou agentes disponíveis e aumentar apenas quando o hardware, carga e benefício o justificarem.

Funções especializadas propostas:

- **Mentor Full-Stack / líder técnico:** recebe a missão de programação, decompõe trabalho, combina backend e frontend, acompanha capacidade/desempenho, revê integrações e comunica ao DGM-MAT. Coordena; não é autoridade para ultrapassar a política central.
- **Analista de requisitos e arquitetura:** clarifica requisitos, contratos, dependências, compatibilidade e decisões arquiteturais.
- **Backend/API:** serviços, lógica de domínio, endpoints, autenticação/autorização e contratos.
- **Frontend/UI:** componentes, estados de interface, integração com APIs e acessibilidade.
- **UI/UX e design system:** fluxos, ergonomia, consistência visual, responsividade e testes de usabilidade.
- **Dados e persistência:** modelos, migrações, transações, backups e integridade.
- **Integrações e conectores:** MCP, providers, ferramentas externas e adaptadores substituíveis.
- **Testes e QA:** testes unitários, integração, regressão, cenários-limite e reprodução de bugs.
- **Segurança e permissões:** revisão independente de fronteiras, segredos, dependências e operações perigosas.
- **DevOps/build/release:** empacotamento, builds, CI controlada, configuração, observabilidade e rollback.
- **Performance e compatibilidade:** medições de CPU/RAM/latência, perfil de hardware e compatibilidade Windows/ambientes-alvo.
- **Documentação e memória técnica:** atualiza contratos, decisões, instruções operacionais e evidências de teste.
- **Investigação de bugs e manutenção:** reproduz problemas, recolhe evidências, identifica causa-raiz e preserva comportamento não relacionado.

Uma mesma pessoa/agente pode desempenhar mais de uma função no protótipo inicial; os papéis são contratos de responsabilidade, não uma exigência de executar muitos modelos em simultâneo. O Mentor Full-Stack pode propor a alocação, mas DGM-MAT conserva a atribuição da missão, a política e a validação de alto risco. O QA e a revisão de segurança devem ser independentes do autor sempre que a criticidade o justificar.

## 7. Contrato mínimo de tarefa

Cada tarefa futura deve definir: objetivo, âmbito incluído/excluído, responsável, dependências, artefactos de entrada/saída, permissões, limite de recursos, prazo, critérios de aceitação, testes exigidos, riscos, estado, proveniência e condição de escalonamento.

O resultado do agente é uma proposta até passar as validações aplicáveis. Para alterações críticas: inspeção independente, testes, diff legível, backup/rollback e autorização humana quando exigida pela política.

## 8. Aplicação incremental

Esta especificação não declara que estas capacidades já existem no runtime. Antes de implementar:

1. Auditar o Mission/Autonomy, Governance, SafeActionQueue, Execution Fabric, eventos, memória e fila de intervenção humana já existentes.
2. Mapear contratos atuais para evitar criar um segundo sistema de filas ou memória.
3. Definir testes de deduplicação, ciclo A→B→A, expiração, cancelamento, saturação, permissões negadas e recuperação após reinício.
4. Prototipar com um único departamento e um trabalhador, sem paralelismo agressivo no PC de recursos limitados.
5. Medir; só depois distribuir tarefas por outros computadores autorizados.
6. Documentar evidências, limitações e decisões antes de integrar em `main`.

**Princípio final:** autonomia dentro do mandato, colaboração por contratos, memória com proveniência, autoridade central clara e nenhum ciclo de delegação sem limite.

## 9. Criação, formação e contratação dinâmica de agentes por mandato do Patrão

### 9.1 Princípio

O DGM-MAT não deve ficar limitado ao conjunto de agentes existente no momento da sua instalação. Quando uma missão exige uma capacidade para a qual a organização não foi originalmente desenhada, deve identificar a lacuna, investigar alternativas e propor a forma mais segura e económica de a preencher. Pode formar um agente existente, criar um agente interno especializado, contratar/usar um agente externo autorizado ou propor um novo departamento.

Esta capacidade não confere soberania independente ao agente nem altera a hierarquia: o **Patrão (DGM-MAT central)** mantém a autoridade sobre missão, prioridades, políticas, orçamento, permissões, aceitação e desativação. Os departamentos podem propor e executar dentro do mandato; não podem atribuir a si próprios novos poderes.

### 9.2 Escolher a resposta mínima adequada

Antes de criar algo novo, o coordenador deve verificar nesta ordem, ajustável com evidência:

1. A capacidade já existe num agente, skill, conector ou ferramenta registada?
2. Uma skill versionada ou formação de um agente existente resolve a lacuna?
3. É necessária uma instância especializada temporária para uma única missão?
4. Justifica-se um agente interno persistente, com responsabilidade e testes próprios?
5. É mais adequado recorrer a um agente externo, serviço ou especialista aprovado?
6. A necessidade é suficientemente contínua e abrangente para justificar um departamento?

A decisão deve comparar qualidade esperada, fiabilidade, privacidade, custo, latência, consumo de recursos, manutenção, dependências, permissões e possibilidade de substituir o componente. Evitar criar agentes redundantes para resolver uma necessidade que uma skill ou integração mais simples já cobre.

### 9.3 Proposta de criação/contratação

Cada proposta deve declarar:

- lacuna concreta e evidências de que os agentes atuais não a cobrem;
- missão, âmbito, resultados esperados e critérios mensuráveis de aceitação;
- se o agente é temporário ou persistente e quem é o responsável;
- competências e ferramentas necessárias, com permissões mínimas;
- modelo/runtime e requisitos de hardware, memória, concorrência e disponibilidade;
- custo máximo, limites de chamadas/tentativas e condições de paragem;
- dados que poderá consultar, retenção e regras de privacidade;
- testes, avaliação independente, riscos conhecidos e plano de reversão;
- condição de renovação, revisão, suspensão ou desativação;
- aprendizagem que deve regressar à memória central e ao departamento requisitante.

A decisão é registada como aprovada, recusada, adiada ou aprovada com condições. Se a política aplicável já tiver delegado autorização para uma classe de ações reversíveis e de baixo risco, o sistema pode atuar dentro desse limite e registar a decisão; fora dele, pede autorização ao Patrão/humano responsável.

### 9.4 Agente temporário versus agente permanente

- **Temporário:** escopo e prazo definidos, ambiente isolado, acesso mínimo e expiração automática. Os resultados úteis são avaliados e incorporados na memória ou numa skill aprovada antes do encerramento.
- **Permanente:** exige prova de valor repetido, contrato de função, responsável, versão, testes, orçamento, monitorização, revisão periódica e procedimento de substituição/desativação.
- **Externo/contratado:** acesso revogável e limitado à tarefa; não recebe automaticamente acesso ao repositório completo, memória privada, credenciais, rede interna ou ferramentas de execução. A contratação pode significar delegar trabalho através de uma API, MCP ou interface autorizada, não necessariamente instalar software.
- **Novo departamento:** só quando há uma linha de trabalho persistente com responsabilidades e coordenação próprias. O departamento continua subordinado ao núcleo de governação e não pode criar subdepartamentos ou contratar agentes ilimitadamente.

### 9.5 Contrato e ciclo de vida

Todo o agente deve ter identidade estável, versão, mandato, responsável, entradas/saídas, competências declaradas, ferramentas permitidas, limites de recursos, política de dados, critérios de qualidade, registo de execução e estado de ciclo de vida.

Estados recomendados: proposto → em avaliação → autorizado → em teste isolado → ativo com limites → suspenso/renovação pendente → desativado. Transições relevantes são auditadas; o agente não pode alterar unilateralmente o seu mandato, permissões ou estado.

### 9.6 Aprendizagem organizacional

Quando um novo agente resolve uma tarefa desconhecida:

1. validar a solução e o seu impacto;
2. guardar a proveniência, limitações, versões e evidências;
3. identificar o conhecimento reutilizável e decidir se deve tornar-se uma skill;
4. testar a skill separadamente do agente original, quando possível;
5. disponibilizar a competência aos departamentos autorizados através do registo central;
6. medir se reduz erros e dependência de assistência externa em tarefas posteriores.

Não copiar cegamente prompts, código, dados ou materiais de agentes externos. Rever licenças, direitos de uso, privacidade e segurança antes de integrar artefactos. A resposta externa não pode modificar diretamente políticas centrais nem tornar-se autoridade por si mesma.

### 9.7 Proteções contra expansão descontrolada

- Limites globais e por departamento para agentes, subagentes, profundidade, fan-out, mensagens, tempo, memória e despesa.
- Deteção de duplicados, ciclos de contratação/delegação e criação recursiva de agentes.
- Uma proposta de agente não pode aprovar a própria criação nem autorizar o seu sucessor.
- Requisitos de capacidade, orçamento e permissões são verificados antes da ativação.
- Indisponibilidade de aprovação implica aguardar, usar uma alternativa já autorizada ou declarar o bloqueio; nunca contornar a governação.
- Todos os agentes e acessos devem poder ser suspensos ou revogados centralmente, incluindo nos trabalhadores distribuídos.
- A criação automática só é permitida em classes de risco previamente aprovadas e dentro de limites verificáveis; contratação paga, acesso a dados sensíveis, publicação, produção e alterações de segurança seguem a política de autorização explícita.

### 9.8 Testes de aceitação

Antes de ativar esta capacidade, testar pelo menos:

- necessidade resolvida por skill existente sem criar agente redundante;
- agente novo rejeitado por orçamento, permissões ou política;
- agente temporário expirado e acessos revogados;
- tentativa de agente criar/autorizar outro agente sem mandato;
- ciclo de delegação/contratação detetado e interrompido;
- agente externo com resposta incorreta ou maliciosa rejeitado pela validação;
- reinício do runtime sem perder o registo de decisão nem duplicar a criação;
- resultado bem-sucedido transformado em conhecimento com proveniência e reutilizado numa tarefa posterior;
- desativação e reversão sem perda de memória ou artefactos necessários.

**Critério de sucesso:** o DGM-MAT demonstra que consegue identificar uma lacuna, escolher a opção proporcional, obter a autorização necessária, testar o novo recurso, revogá-lo quando necessário e preservar a aprendizagem útil sem permitir expansão ilimitada da sua própria autoridade.

