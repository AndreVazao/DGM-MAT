# Requisitos consolidados — escritório adaptável, cidade virtual e cérebro DGM-MAT
**Data:** 2026-10-14  
**Estado:** requisitos documentados em branch de trabalho; implementação não iniciada.

## 1. Prioridade arquitetural
O cérebro funcional do DGM-MAT tem prioridade sobre a visualização. A empresa deve conseguir receber pedidos, planear, delegar, executar, verificar, persistir resultados, recuperar de falhas e pedir aprovação humana mesmo que o escritório visual esteja fechado ou desativado.

O escritório é uma interface operacional ligada a eventos e estados reais do Orchestrator/Runtime; nunca é a fonte de verdade. Nenhuma animação pode inventar agentes, progresso, entregas ou resultados.

## 2. Renderização adaptável ao hardware
A visualização tem níveis de detalhe selecionáveis automaticamente com opção de controlo manual:
- **Modo económico:** mapa 2D/planta, figuras-palito ou ícones, animações mínimas, sem sombras/física/renderização contínua pesada.
- **Modo equilibrado:** isométrico 2.5D/low-poly, personagens simples, animações seletivas e deslocação por rotas.
- **Modo imersivo:** edifício 3D detalhado, personagens, elevadores, veículos e cidade empresarial, só quando o hardware suporta.

O nível de detalhe afeta apenas a apresentação, nunca a semântica, a capacidade ou a segurança do runtime. A seleção automática deve considerar RAM disponível, CPU, GPU/WebGL, taxa de frames, temperatura/pressão se acessível, número de agentes e configuração do utilizador. Não depender de sensores indisponíveis: usar medições reais e fallback conservador. Reduzir automaticamente animações/efeitos se a renderização prejudicar o uso do computador. O utilizador pode escolher um nível inferior manualmente.

No computador-alvo atualmente conhecido (2 núcleos, cerca de 3 GB RAM), iniciar com modo económico e testar antes de ativar isométrico.

## 3. Edifício navegável e identificação de pisos
- O edifício terá vista em corte/explodida: os pisos podem afastar-se verticalmente para inspeção, com scroll/roda do rato, zoom, arrastar e seleção de piso.
- Cada piso apresenta de forma persistente o nome do departamento e indicadores reais: agentes ativos, tarefas em curso, fila, bloqueios, pedidos recebidos/enviados e entregáveis.
- O utilizador pode percorrer todo o edifício, abrir qualquer piso, sala ou departamento e inspecionar os agentes e as tarefas em tempo real.
- Deve existir navegação alternativa acessível por lista/árvore de pisos, útil no modo económico e para teclado/ecrãs pequenos.
- Os pisos são departamentos lógicos configuráveis, não obrigatoriamente processos de sistema separados.

## 4. Agentes, postos de consulta e comunicação
- Cada agente visível corresponde a um agente real registado no runtime e tem identidade estável.
- Selecionar um agente abre um painel com papel, tarefa atual, estado, dependências, permissões relevantes, última ação confirmada, evidências/logs, resultado e próximo passo.
- Deve ser possível iniciar uma comunicação dirigida a um agente específico, sujeita a autorização, registo e regras do runtime.
- Cada departamento terá uma **secretária de serviço / balcão de consulta**: interface resumida para saber o que está a fazer, filas, prioridades, pedidos entre departamentos, bloqueios, métricas e entregas. A secretária representa um endpoint real de consulta/coordenação do departamento; não é apenas uma personagem.
- A comunicação visual (telefone, balão, reunião) corresponde a eventos persistentes; não substitui mensagens, pedidos e confirmações registados no backend.

## 5. Direção, receção e atendimento de pedidos
Modelo de governação proposto para validar na arquitetura:
- **Direção/Boss:** responsável pela estratégia operacional, prioridades globais, decisões de escalamento, revisão de relatórios e distribuição de ordens. Pode visitar visualmente os departamentos e emitir ordens, mas não precisa de executar cada tarefa.
- **Receção / Front Office / Triagem:** ponto de entrada para pedidos externos e clientes; recolhe contexto, classifica, deteta duplicados, estima urgência e encaminha para o departamento adequado.
- Pedidos rotineiros dentro de políticas aprovadas podem ser encaminhados automaticamente; decisões de alto impacto, ambíguas, dispendiosas ou fora da política sobem ao Boss/humano.
- O Boss deve poder falar diretamente com o cliente quando necessário, mas o atendimento não deve bloquear a empresa inteira.
- Separar claramente: cliente humano, pedido externo, agente externo, serviço de terceiro e departamento interno.
- Nenhuma ordem com efeitos externos é executada sem permissões e aprovação necessárias.

## 6. Cidade empresarial e logística externa
A expansão visual para uma mini cidade é uma fase futura:
- O edifício DGM-MAT é o núcleo central.
- Outros edifícios podem representar parceiros, fornecedores, serviços de terceiros, clusters ou agentes externos; devem estar rotulados e ligados a integrações reais.
- Pedidos e entregas externos podem ser mostrados como pacotes a viajar em carros/motas, mas o percurso é uma metáfora visual do fluxo real e tem de corresponder a pedido, destinatário, estado e confirmação verificáveis.
- Não apresentar um fornecedor ou agente como conectado se a integração não estiver ativa.
- Tráfego decorativo, se existir, deve estar explicitamente separado dos transportes operacionais e pode ser desativado em modo económico.
- Animações lúdicas (por exemplo, entrega de pizza/bebidas durante pausas) são opcionais, não operacionais, não devem interferir com prioridades nem sugerir consumo real de recursos. Desativadas por defeito no modo económico e facilmente desligáveis em todos os modos.

## 7. Cérebro DGM-MAT: capacidades prioritárias
Antes da cidade e de animações complexas, confirmar e melhorar:
1. Registo persistente de tarefas, estados, dependências e eventos.
2. Receção, classificação, planeamento e decomposição de pedidos.
3. Seleção de agentes/provedores segundo capacidade, custo, quotas, segurança e recursos locais.
4. Delegação com contratos explícitos, timeout, cancelamento, retentativas seguras e prevenção de duplicação.
5. Verificação independente de resultados e evidências, testes quando aplicável e revisão de segurança.
6. Gestão de bloqueios, pedidos de ajuda, escalamento e recuperação.
7. Memória persistente com proveniência, deduplicação e controlo de alterações.
8. Aprovação humana para operações externas, credenciais, pagamentos, push, eliminação e mudanças de produção.
9. Observabilidade: logs estruturados, métricas, trilho de auditoria e estado consultável por agente/departamento.
10. Operação local-first, degradação graciosa e ausência de fallback pago silencioso.

## 8. Arquitetura em camadas
- **Camada 1 — Core/runtime:** execução real, tarefas, eventos, contratos, memória e segurança.
- **Camada 2 — Direção e departamentos:** triagem, políticas, planeamento, filas e coordenação.
- **Camada 3 — Comunicação e logística:** pedidos, mensagens, artefactos, encomendas e confirmações.
- **Camada 4 — Adaptador de presença:** transforma eventos reais em estados/ações visuais sem controlar a execução.
- **Camada 5 — Renderer adaptável:** 2D, 2.5D ou 3D, com zoom, scroll, pisos explodidos e cidade futura.
- **Camada 6 — Cockpit de controlo:** inspeção, pesquisa, comunicação dirigida, aprovações e auditoria.

A falha das camadas visuais não deve derrubar as camadas 1–3.

## 9. Fases de implementação
- Fase A: auditar o cérebro e os contratos já existentes; não duplicar módulos nem reescrever sem evidência.
- Fase B: validar tarefas persistentes, eventos, execução, verificação e recuperação com testes locais.
- Fase C: cockpit funcional em 2D com estado real e consulta de departamentos/agentes.
- Fase D: navegação do edifício, pisos identificados, vista explodida e balcões de departamento.
- Fase E: comunicação dirigida, pedidos e logística interna com elevadores/encomendas.
- Fase F: renderização 2.5D/3D adaptável e medição de recursos.
- Fase G: integrações externas e mini cidade com transportes operacionais.
- Fase H: animações lúdicas opcionais e decoração, apenas depois da estabilidade.

## 10. Critérios de aceitação
- Core executa e persiste tarefas com a visualização desligada.
- Estados apresentados correspondem a eventos/estados confirmados.
- O utilizador consegue inspecionar todos os pisos, departamentos e agentes.
- Cada departamento tem painel/secretária de consulta funcional.
- O utilizador consegue dirigir uma mensagem/pedido a um agente ou departamento com controlo de permissões.
- O scroll/zoom/vista explodida não oculta o rótulo do departamento nem perde a seleção atual.
- A redução de qualidade não remove funcionalidades operacionais.
- Modo económico permanece utilizável em hardware fraco e não exige GPU dedicada.
- Pedidos externos e viagens visuais só aparecem como operações reais quando existem integração e estados verificáveis.
- As animações lúdicas são opcionais e nunca mascaram alertas, bloqueios ou trabalho pendente.

## 11. Limites desta decisão
Este documento é um requisito de produto/arquitetura, não prova que todas as capacidades já existam. Não autoriza instalar ferramentas externas, fazer merge na main, alterar clones de terceiros/Labs, sincronizar a cópia local ou executar ações em produção. As decisões de implementação dependem da auditoria do código e dos testes do runtime atual.
