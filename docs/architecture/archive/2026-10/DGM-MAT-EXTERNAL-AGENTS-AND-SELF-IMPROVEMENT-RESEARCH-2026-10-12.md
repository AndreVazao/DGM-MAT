# DGM-MAT — Política de integração de agentes externos e evolução autónoma
## Investigação técnica e proposta de arquitetura
**Data de referência:** 2026-10-12  
**Estado:** investigação documental; não implementado; não autoriza merges nem instalação  
**Branch documental:** `docs/digital-headquarters-concept-2026-10-12`

## 1. Decisão executiva

**Recomendação:** avaliar o DeepSeek Harness (`dsh`) como um runtime/ferramenta de agente externo, não como cérebro nem como fonte de verdade do DGM-MAT. Integrá-lo apenas atrás de um adaptador isolado e substituível, depois de um teste de compatibilidade, recursos e segurança.

O DGM-MAT deve continuar a ser responsável por:
- receber e classificar pedidos;
- manter memória e registos próprios;
- decidir prioridades e delegação;
- definir permissões e limites;
- selecionar e supervisionar ferramentas/provedores;
- validar resultados, testes e diffs;
- decidir se uma aprendizagem ou alteração de código é aceite;
- conservar histórico, auditoria, rollback e estado do trabalho.

O agente externo pode produzir propostas, pesquisa, relatórios, patches e resultados de testes. Não deve poder modificar autonomamente a política do DGM-MAT, os seus próprios controlos de segurança ou o repositório principal sem revisão.

## 2. O que é o DeepSeek Harness

Fontes oficiais consultadas:
- Repositório: https://github.com/deepseek-ai/deepseek-harness
- Documentação: https://deepseek-harness.github.io/deepseek-harness/
- Arquitetura: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md
- Segurança: https://github.com/deepseek-ai/deepseek-harness/blob/master/SAFETY.md
- Apresentação oficial: https://www.deepseek.com/harness/en/

O projeto descreve-se como um *agent harness* open-source, desenvolvido pela DeepSeek AI e licenciado sob MIT. A arquitetura é baseada em Cordis e na ideia “everything is a plugin”: modelos, ferramentas, skills, sessões, armazenamento, loops, sandbox, agendamento e UI podem ser compostos e substituídos através de plugins/perfis.

O repositório documenta superfícies de execução `web`, `headless`, `sdk`, `sdk-minimal` e `acp`, além de plugins. O comando documentado para abrir a UI local é `npx @deepseek-ai/dsh web`; o padrão indicado é `http://127.0.0.1:3080`. Também existe execução a partir do código-fonte com pnpm.

**Distinção importante:** o Harness não é simplesmente “um modelo DeepSeek” nem uma cópia literal do Claude Code. É uma infraestrutura para construir/executar agentes. A experiência de programação depende do modelo configurado, das ferramentas, do perfil, das permissões e da configuração. A existência de UI/CLI não prova que todas as funcionalidades e todos os fluxos do Claude Code sejam equivalentes.

### Estado e estabilidade
A página oficial identifica o projeto como *developer preview* e avisa que podem ocorrer alterações incompatíveis. As APIs públicas ainda não devem ser tratadas como contratos estáveis sem fixar uma versão e executar testes de integração.

## 3. Pode funcionar como um trabalhador do DGM-MAT?

**Em princípio, sim — sujeito a um teste real.** A melhor relação é “DGM-MAT → adaptador → sessão isolada do DSH → artefactos/resultados → validação pelo DGM-MAT”.

Usos potenciais:
- investigação de código e documentação;
- revisão de arquitetura;
- geração de patches numa cópia de trabalho;
- correção de bugs em branches isoladas;
- criação de testes e análise de falhas;
- comparação de alternativas técnicas;
- produção de relatórios de auditoria;
- desenvolvimento de capacidades solicitadas pelo DGM-MAT.

Não assumir antes do teste:
- compatibilidade direta com o Ollama instalado;
- compatibilidade com cada modelo local ou endpoint OpenAI-compatible;
- compatibilidade direta com todos os MCPs atuais;
- equivalência funcional com Claude Code;
- consumo aceitável de CPU/RAM no PC de 2 núcleos e cerca de 3 GB;
- que a UI do DSH seja a UI principal do DGM-MAT.

A interface própria do DSH pode ser útil para uso manual/diagnóstico. Para integração automatizada, testar primeiro os perfis headless/SDK/ACP e os contratos públicos da versão escolhida, em vez de controlar a UI por cliques/OCR.

## 4. Modelo de integração recomendado

```text
Utilizador
   |
DGM-MAT (orquestração, política, memória e estado canónico)
   |
Router de capacidades / política de delegação
   |
External Agent Adapter (contrato interno estável do DGM-MAT)
   |             |                 |
DSH isolado   Claude Code       Outros agentes
   |             |                 |
Artefactos, logs, diff, testes, relatório e estado de saída
   |
Validador DGM-MAT: política + testes + revisão + aprovação
   |
Memória de aprendizagem / proposta de alteração / entrega
```

O adaptador interno deve desacoplar o DGM-MAT dos detalhes e mudanças do DSH. A mudança de versão ou a remoção do DSH não pode obrigar a reescrever a orquestração nem a memória.

### Contrato interno proposto (conceitual; não assumir que já existe)
Cada execução delegada deve incluir:
- `task_id`, `correlation_id`, `agent_id`, `provider_id`, versão do adaptador;
- objetivo, contexto mínimo necessário, critérios de aceitação e limites;
- repositório/worktree de destino explicitamente autorizado;
- política de rede, filesystem, shell e credenciais;
- timeout, limite de tentativas e limite de recursos;
- estado: queued / starting / running / waiting / blocked / succeeded / failed / cancelled;
- logs/eventos e timestamps;
- lista de artefactos, diff, testes executados e códigos de saída;
- resultado estruturado e limitações conhecidas;
- indicação de validação humana ou automática.

O esquema deve ser alinhado com os contratos já existentes no DGM-MAT após auditoria local. Não criar um segundo sistema de tarefas só para acomodar o DSH.

## 5. Isolamento e segurança — condição de entrada

A própria documentação de segurança do DSH declara que é experimental, não auditado e capaz de executar código/comandos gerados por modelos, carregar plugins e aceder à rede, processos, credenciais e ficheiros disponibilizados. O sandbox e os pedidos de aprovação reduzem o risco, mas não garantem isolamento.

Política inicial obrigatória:
1. Não executar com privilégios de administrador.
2. Não montar o diretório inteiro do utilizador, `C:\DevopGodMode`, todos os repositórios ou as pastas de memória.
3. Criar um workspace descartável por tarefa, com cópia/snapshot ou worktree dedicado.
4. Começar com acesso read-only à documentação necessária e sem credenciais.
5. Não disponibilizar tokens de GitHub, chaves de API, cookies, ficheiros .env ou credenciais do Windows ao agente.
6. Desativar plugins não necessários; inspecionar cada plugin e a sua origem.
7. Restringir rede de saída; nunca assumir que um prompt é uma fronteira de segurança.
8. Exigir aprovação explícita para escrita fora do workspace, operações Git remotas, instalação de dependências, acesso a rede sensível ou alterações de configuração.
9. Registar comando, diretório de trabalho, processo, ficheiros alterados e resultado.
10. Limpar processos filhos e sessões no fim; testar que não deixa janelas ou processos órfãos.
11. Fixar versão e dependências durante a avaliação; evitar atualização automática em produção.
12. Manter backups e poder terminar o processo sem perder o estado canónico.

Não usar o DSH como única fronteira de segurança. Se o PC não suportar container/VM de forma aceitável, usar primeiro um workspace dedicado com permissões de Windows reduzidas e ficheiros descartáveis; documentar que isso é isolamento mais fraco.

## 6. Recursos e compatibilidade com o PC

A máquina de destino tem aproximadamente 2 núcleos e 3 GB de RAM disponíveis segundo o contexto do projeto; os modelos locais utilizáveis são pequenos. O DSH é uma aplicação Node/TypeScript com UI e serviços de agente, pelo que a pegada de memória real tem de ser medida. A UI Web pode ter custo adicional. Não assumir que o Harness executa um modelo local sem custo ou que a infraestrutura é leve só por ser open-source.

Plano de medição:
- baseline de RAM/CPU antes de arrancar;
- arranque sem tarefa e memória após estabilizar;
- execução de tarefa pequena com modelo local e, separadamente, provedor externo já disponível;
- pico de RAM, CPU, tempo, erros e processos filhos;
- comparação UI vs headless/SDK;
- teste de shutdown/restart e verificação de processos residuais;
- repetir 3 vezes, registar mediana e pior caso;
- abortar se prejudicar o DGM-MAT ou o uso normal do PC.

O primeiro teste não deve instalar simultaneamente múltiplos runtimes nem modelos grandes.

## 7. Evolução própria: aprendizagem sem dependência

A expressão “aprender e evoluir” deve ser implementada inicialmente como melhoria de software e de processos baseada em evidência, não como alteração espontânea e opaca dos pesos de um modelo.

### Ciclo proposto
1. O DGM-MAT deteta uma limitação, falha recorrente ou oportunidade.
2. Regista evidência reproduzível: tarefa, contexto relevante, saída, erro, testes e versão.
3. Formula uma hipótese e critérios de sucesso.
4. Delega pesquisa ou patch a um ou mais trabalhadores (por exemplo, DSH ou Claude Code).
5. Recebe artefactos num branch/worktree isolado.
6. Executa testes locais, linters, validações de contrato e regressões.
7. Compara com baseline e mede custo/benefício.
8. Solicita revisão humana para mudanças críticas.
9. Só depois incorpora a solução e escreve uma memória de aprendizagem com evidência, decisão e possibilidade de rollback.
10. Monitoriza se a melhoria continua válida.

### O que a memória deve guardar
- problema e condições de reprodução;
- tentativa(s) efetuadas e agente/ferramenta usada;
- diffs e commits associados;
- testes, resultados e métricas;
- o que foi aceite/rejeitado e porquê;
- limitações e data de revisão;
- nível de confiança e ligações aos artefactos.

Não guardar cegamente todas as saídas como “verdade”. Distinguir factos verificados, hipóteses, conselhos de agentes externos e decisões aprovadas.

### Auto-modificação permitida por níveis
- **Nível 0 — observar:** leitura e relatório.
- **Nível 1 — propor:** criar patch num workspace isolado.
- **Nível 2 — validar:** executar testes permitidos e produzir evidência.
- **Nível 3 — preparar entrega:** abrir branch/PR ou pacote para revisão.
- **Nível 4 — integrar:** apenas com políticas de aprovação existentes; não conceder automaticamente ao agente externo.
- **Nível 5 — alterar o próprio mecanismo de segurança/orquestração:** sempre revisão humana explícita, testes de regressão e plano de rollback.

Não permitir que um agente reescreva o validador, eleve as próprias permissões ou altere a política de aprovação para aprovar o seu próprio trabalho.

## 8. Como medir se o DGM-MAT está a aprender

Indicadores úteis:
- taxa de testes aprovados antes/depois;
- regressões introduzidas;
- tarefas concluídas sem intervenção;
- qualidade da saída avaliada por critérios reproduzíveis;
- tempo até diagnóstico e recuperação;
- repetição de erros já resolvidos;
- custo de CPU/RAM/tempo e eventuais chamadas externas;
- taxa de rejeição de patches;
- rollback após integração;
- proporção de memórias com evidência e ligação a teste/commit.

O progresso não é “o agente disse que aprendeu”. É a melhoria mensurável e persistente de uma tarefa repetível.

## 9. Plano de prova de conceito (sem mexer no projeto principal)

### P0 — pré-requisitos
- Auditar branches/working trees e confirmar que o PC tem um workspace descartável.
- Ler a versão exata do DSH, licença e documentação de segurança.
- Confirmar runtime Node suportado e espaço em disco.
- Definir limites de CPU/RAM, rede e ficheiros.
- Nenhuma instalação global ou mudança de startup ainda.

### P1 — avaliação isolada
- Instalar numa pasta temporária ou perfil isolado.
- Iniciar a UI local apenas se necessário; não expor na LAN.
- Confirmar comando de encerramento e ausência de processos residuais.
- Medir recursos sem modelo/tarefa.

### P2 — tarefa read-only
- Pedir para resumir uma pasta pequena de documentação sintética.
- Confirmar que não altera ficheiros.
- Verificar logs, formato de resultado e cancelamento.

### P3 — tarefa de código descartável
- Criar um pequeno repositório de teste com teste que falha.
- Pedir diagnóstico e patch.
- Guardar diff; executar testes separadamente fora do agente.
- Rejeitar se o agente alterar ficheiros fora do workspace ou tentar aceder a credenciais.

### P4 — adapter spike
- Criar apenas num branch de protótipo um adaptador mínimo com timeout, cancelamento, captura de logs, workspace allowlist e saída estruturada.
- Comparar o contrato com os providers já existentes.
- Não alterar contratos centrais antes de documentar compatibilidade.

### P5 — decisão
Classificar: adotar como provider experimental, manter como ferramenta manual externa, ou rejeitar por custo/segurança/compatibilidade. A decisão deve ser reversível.

## 10. Critérios de aceitação

O DSH só pode avançar para integração experimental se:
- iniciar e terminar de forma controlada;
- não exigir privilégios de administrador;
- executar apenas dentro do workspace permitido;
- respeitar timeout/cancelamento;
- produzir saída e artefactos auditáveis;
- passar tarefa de teste sem alterar ficheiros proibidos;
- não expor credenciais;
- ter consumo de recursos aceitável;
- ter versão fixada e método de rollback;
- o adaptador não acoplar a orquestração aos detalhes internos do DSH.

## 11. Alternativas a manter na matriz

- **Claude Code Free:** trabalhador de programação existente; usar conforme disponibilidade, limites e controlo de acesso já configurados.
- **Ollama/modelos locais:** inferência local para tarefas adequadas; não são substitutos automáticos de um agente de ferramentas.
- **OpenHands Agent Server/SDK:** alternativa de runtime de agente com API HTTP/WebSocket; investigar custo de recursos e isolamento antes de considerar.
- **SWE-agent/Mini-SWE-agent:** alternativas orientadas para tarefas de engenharia de software; validar requisitos de execução e dependências.
- **Agentes via CLI/API já presentes:** podem ser mais simples de adaptar que introduzir um runtime completo.

Não adotar vários agentes novos ao mesmo tempo. Escolher um único candidato e comparar com baseline.

## 12. Conclusão

O DSH parece tecnicamente plausível como funcionário externo e substituível. A sua arquitetura de plugins é interessante, mas o seu estado de developer preview e as capacidades de execução exigem isolamento forte. O valor estratégico não está em substituir o DGM-MAT; está em permitir que o DGM-MAT delegue trabalho a ferramentas mais maduras, valide os resultados e converta sucessos verificados em melhorias documentadas.

**Decisão proposta:** aprovar apenas investigação e prova de conceito isolada. Não instalar na máquina principal nem integrar em runtime de produção antes de recuperar a consistência dos repositórios e validar os critérios acima.


## 13. Workers distribuídos em vários computadores

A arquitetura deve permitir que um DGM-MAT central delegue tarefas a ferramentas instaladas em máquinas distintas e autorizadas — por exemplo, Harness num PC, Claude Code noutro e, futuramente, ferramentas locais, web ou API noutros nós. Não se deve ligar diretamente a lógica central às interfaces internas de cada ferramenta.

Modelo proposto:

```text
DGM-MAT central (política, memória, despacho e validação)
    -> catálogo de capacidades e estado dos nós
    -> transporte privado autenticado e encriptado
    -> gateway do nó / adaptador local
    -> Harness | Claude Code | Ollama | outras ferramentas
    -> artefactos, logs permitidos, diffs e resultados
    -> validação central DGM-MAT
```

Cada nó é inscrito explicitamente e anuncia apenas capacidades aprovadas. O catálogo mantém versão, disponibilidade, recursos medidos, permissões e último heartbeat. Quando o heartbeat expira, o nó passa a indisponível/desconhecido; não se pode apresentar o seu estado antigo como disponibilidade atual.

A rede local, por si só, não cria confiança. O primeiro protótipo deve usar um registo manual de nós, tarefas read-only e workspaces descartáveis. Exigir identidade individual por nó, transporte encriptado, autorização por tarefa, timeout/cancelamento, logs de auditoria, limites de recursos e revogação. Não expor agentes diretamente à Internet nem transmitir segredos ou toda a memória central. Resultados remotos são não confiáveis até serem validados pelo DGM-MAT.

## 14. Renderização adaptável não altera o cérebro

A renderização 3D/2D/mínima do escritório é uma preocupação separada do runtime de agentes. Um computador modesto deve continuar a poder usar o chat e uma personagem mínima mesmo sem capacidade para animação avançada. A adaptação visual não deve obrigar a instalar outro modelo, runtime de agente ou motor de jogo. O perfil de renderização e a seleção do worker são decisões distintas, com medições e limites próprios.

## 15. Seleção free/local-first e APIs futuras

O dispatcher deve aplicar uma política explícita e configurável: preferir ferramentas locais gratuitas adequadas; depois serviços gratuitos já autorizados e nós aprovados; usar ferramentas web gratuitas quando forem adequadas; e permitir APIs pagas apenas quando o utilizador configurar e autorizar o provedor e os limites de despesa. O sistema deve ponderar qualidade, confidencialidade, latência, disponibilidade, limites e recursos — não apenas preço. Se não houver opção gratuita apropriada, deve esperar, explicar a limitação ou pedir autorização; nunca gerar custos silenciosamente.

Esta capacidade futura deve ser acrescentada através de adaptadores e contratos estáveis, preservando memória, política e estado canónico do DGM-MAT. A especificação complementar está em [Runtime adaptável e agentes distribuídos](DGM-MAT-ADAPTIVE-RUNTIME-AND-DISTRIBUTED-WORKERS-2026-10-12.md).
