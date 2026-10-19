# Cockpit conversacional remoto — requisito operacional
**Data:** 2026-10-19  
**Estado:** requisito de produto documentado; implementação e conectividade real ainda exigem validação.

## Contexto do proprietário
O proprietário é motorista de camião articulado e pode passar 20–30 dias consecutivos fora de casa, a viajar e trabalhar por vários países europeus. O computador de casa deve continuar a executar tarefas, enquanto o proprietário acompanha o estado e conversa com o DGM-MAT através do telemóvel, mesmo estando longe do PC.

## Missão do DGM-MAT
DGM-MAT é uma ferramenta para construir e reparar ferramentas: engenharia de software, DevOps, auditoria e reparação de programas, pesquisa técnica, scripts e integração de trabalho/conversas/respostas de várias IAs. Não é o Sovereign Trader e não deve herdar os seus dados, permissões ou lógica financeira.

## Experiência de cockpit
- Conversação em linguagem natural para criar, esclarecer, delegar, acompanhar, pausar e retomar missões.
- Estado verdadeiro e persistente: tarefas, agentes efetivamente ativos, fases, logs relevantes, resultados, falhas e bloqueios. Nunca simular atividade, agentes, progresso ou sucesso.
- Caixa de entrada durável de pedidos de aprovação/autenticação, acessível remotamente; não depender de um pop-up local que o proprietário não consegue ver.
- Notificações remotas para pedidos que exigem atenção, falhas relevantes e tarefas concluídas; com deduplicação, expiração, leitura e estado de resolução.
- Interface responsiva e utilizável num telemóvel, com texto legível, controlos grandes e conteúdo que não fique cortado. O chat é a porta conversacional; o escritório virtual continua uma projeção separada da atividade real.
- Recuperação depois de perda de rede, reinício do PC ou longos períodos offline, sem perder o estado nem repetir cegamente ações.

## Aprovação e autenticação
1. Cada pedido deve indicar a tarefa, o motivo, o sistema/alvo, o nível de risco, o que será executado e o prazo de validade.
2. Aprovação de ação e introdução de credenciais são fluxos diferentes. Uma autorização não deve ser inferida de uma mensagem vaga.
3. Passwords, tokens, códigos MFA e segredos devem ser recolhidos num formulário/canal seguro específico e encaminhados diretamente ao componente autorizado; não devem aparecer no histórico de chat, logs, notificações push ou relatórios.
4. Aprovações devem ser autenticadas, vinculadas ao utilizador/dispositivo e à ação exata, expirar, ser revogáveis e protegidas contra replay. Ações privilegiadas/destrutivas continuam a exigir confirmação explícita.
5. Se a identidade, a autorização, a conectividade ou o resultado forem ambíguos, falhar em modo fechado e pedir reconciliação.

## Conectividade e autoridade
- O PC DGM-MAT permanece a autoridade de execução e a fonte do estado real; o cockpit é uma interface remota, não um segundo cérebro.
- Preferir ligação privada autenticada (por exemplo, Tailscale) quando disponível. Qualquer rendezvous público deve ser mínimo: descoberta/estado de presença, sem execução privilegiada, credenciais ou arquivo de conversações.
- Não expor APIs locais diretamente à Internet. Antes de acesso remoto, autenticação e autorização têm de ser aplicadas de forma consistente a HTTP, WebSocket e clientes.
- O sistema deve funcionar em modo degradado quando o PC ou o telemóvel estiver offline e explicar claramente o que não pode confirmar.
- Acesso e histórico devem respeitar a identidade do proprietário e a separação entre projetos.

## Fronteiras arquiteturais
O cérebro DGM-MAT continua responsável por raciocínio, missões, agentes, execução, estado, aprovações e memória. O cockpit apresenta informação verificada e envia pedidos autenticados; não concede permissões por si, não ultrapassa os gates do cérebro e não mistura repositórios satélite.

O cockpit é uma capacidade operacional necessária para o cenário de uso do proprietário, embora a sua implementação permaneça modular e separada do núcleo.

## Critérios de aceitação
- [ ] Enviar uma ordem natural a partir de Android e receber confirmação com ID de tarefa e estado persistente.
- [ ] Ver progresso real, bloqueios, logs sanitizados e resultado, inclusive após reconectar.
- [ ] Receber remotamente uma solicitação de aprovação quando o PC está em casa e o proprietário está fora.
- [ ] Aprovar/recusar apenas a ação identificada; testar expiração, revogação, dispositivo não autorizado e replay.
- [ ] Introduzir um segredo sem o guardar no chat/logs/notificações.
- [ ] Demonstrar que a perda de rede não repete ações privilegiadas nem declara sucesso falso.
- [ ] Testar responsividade em ecrãs móveis e acessibilidade dos controlos.
- [ ] Validar o comportamento real do PC/API antes de declarar acesso remoto seguro.

## Sequência recomendada
1. Auditar autenticação, sessões, APIs HTTP/WebSocket, fila de aprovações e estado persistente existentes.
2. Testar o caminho remoto de ponta a ponta com uma tarefa inofensiva e um pedido de aprovação simulado.
3. Validar autenticação global e segurança de rede antes de disponibilizar acesso remoto.
4. Só depois consolidar UI móvel/web e notificações.
