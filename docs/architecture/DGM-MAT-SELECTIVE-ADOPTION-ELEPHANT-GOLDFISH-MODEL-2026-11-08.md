# Adoção seletiva do Elephant-Goldfish Model no DGM-MAT

- Data: 2026-11-08
- Estado: proposta técnica documentada; não ativa no runtime
- Upstream: https://github.com/google/elephant-goldfish-model
- Licença upstream declarada: Apache-2.0
- Branch de trabalho: feat/egm-independent-design-review-2026-11-08

## Decisão

Adotar seletivamente o método Elephant-Goldfish Model (EGM) como protocolo de engenharia e revisão independente do DGM-MAT. Não incorporar o plugin completo, não criar um segundo motor de missões e não alterar o backend de conversação, APK ou dashboard nesta fase.

O EGM encaixa no DGM-MAT porque complementa capacidades existentes: memória/contexto profundo, tarefas duráveis, especialistas, recibos, aprovação humana, validação e documentação persistente. O seu valor distintivo é separar quem concebe de quem critica, reduzindo viés de confirmação e cascatas de pressupostos.

A adoção segue a regra do próprio DGM-MAT:
UPSTREAM -> STUDY -> CLASSIFY -> EXTRACT CONCEPT -> ADAPT -> VALIDATE -> PRODUCT

Não é necessário clonar o upstream para uma lab apenas para o estudar: o projeto serve diretamente como referência metodológica e a licença permite reutilização compatível. Qualquer cópia futura de ficheiros/código deverá ser seletiva, rastreada e acompanhada da licença/notices aplicáveis.

## Mapeamento de responsabilidades

| EGM | Adaptação DGM-MAT | Limite |
|---|---|---|
| Elephant | DGM-MAT cérebro + memória AndreOS + contexto do projeto | Não pode tratar hipóteses como factos |
| Goldfish | Revisores independentes com contexto novo e pacote de evidências limitado | Sem acesso à conversa privada completa nem às conclusões do Elephant |
| Synthesizer | Agregação de findings com deduplicação e proveniência | Não pode apagar divergências relevantes |
| Human owner | André, autoridade final sobre decisões estruturais | Aprovação explícita quando exigida pela constituição |
| Living specifications | docs/designs + mapa de arquitetura + relatório de drift | Documentação não substitui testes nem runtime |
| Bootstrap | Inventário bottom-up de diretórios, módulos e interfaces | Read-only; não gerar centenas de READMEs sem necessidade |

## Fluxo proposto para alterações com impacto arquitetural

1. **Contexto (Elephant):** recuperar missão, requisitos, decisões atuais/supersedidas, árvore do projeto, consumidores, contratos, testes e estado Git.
2. **Brief:** registar problema, objetivo, não-objetivos, restrições, critérios de aceitação, riscos e ficheiros potencialmente afetados.
3. **Revisão Goldfish independente:** criar contextos de revisão realmente novos, cada um recebendo apenas o brief, documentos citados e fontes de código necessárias. Se o runtime não suportar isolamento real, declarar a revisão indisponível; não simular independência na mesma conversa.
4. **Lentes mínimas:** compreensão/autossuficiência; simplicidade e reutilização (YAGNI); arquitetura e modos de falha; compatibilidade/segurança; prontidão de implementação e testes.
5. **Síntese:** findings classificados por severidade, evidência, ficheiro/linha, impacto, recomendação e confiança. Manter findings discordantes e marcar afirmações sem evidência.
6. **Resolução:** o Elephant propõe resposta a cada finding; André decide trade-offs e aprova quando a constituição exige.
7. **Implementação:** só após gate aplicável; respeitar fronteiras e lista de ficheiros aprovados.
8. **Validação:** testes focados, regressões, CI relevante, inspeção do diff e verificação dos contratos/runtime.
9. **Registo:** guardar brief, revisão, decisões, resultados e relação com missão/task IDs; atualizar AndreOS Memory quando a conclusão for duradoura.
10. **Drift:** comparar periodicamente especificações e documentação com código real; reportar divergências, nunca alterar automaticamente para as esconder.

## Integração com capacidades existentes

- Reutilizar OrganizationTaskManager/MissionEngine e recibos duráveis já existentes; não criar fila paralela.
- Reutilizar especialistas read-only já registados quando as suas capacidades e isolamento forem comprovados.
- Relacionar cada revisão com task_id/mission_id e preservar os outputs brutos.
- Usar os scopes existentes e princípio least privilege; revisores não recebem credenciais, cookies, tokens ou permissões de execução.
- Consultas externas a modelos/fornecedores são evidência não confiável e nunca contam como Goldfish independente se partilharem o mesmo contexto.
- A consulta ao browser/IA externa não substitui testes nem revisão humana.
- O cockpit/dashboard apenas apresenta estado e artefactos verificados; não passa a ser autoridade de aprovação.

## Política de aplicação

**Obrigatório** para alterações de arquitetura, segurança, persistência, contratos públicos, autoridade/autonomia, migrações, remoção de módulos ou mudanças multi-repositório.

**Leve/opcional** para correções locais, documentação simples, testes isolados e tarefas de baixo risco. Não impor o processo completo a cada alteração.

**Bloqueio:** se não houver subagentes/contextos independentes disponíveis, o sistema pode executar uma revisão sequencial claramente identificada como não independente, mas não pode rotulá-la como Goldfish nem declarar a gate independente aprovada.

## O que NÃO importar

- Não instalar o plugin EGM globalmente no runtime de produção.
- Não adicionar dependências de execução apenas para reproduzir o plugin.
- Não duplicar MissionEngine, task manager, aprovação, armazenamento ou orquestração.
- Não permitir que agentes aprovem as próprias propostas.
- Não deixar revisores executar comandos, alterar código ou aceder a segredos.
- Não exigir revisão multiagente para tarefas triviais.
- Não copiar o repositório inteiro para DGM-MAT-Labs sem uma necessidade concreta de auditoria de código.

## Plano incremental

### Fase 0 — concluída nesta branch
- Estudar README, arquitetura e guia de workflow upstream.
- Registar decisão, mapeamento, limites e plano de adoção.

### Fase 1 — integração documental
- Criar templates curtos para brief, findings e decisão.
- Ligar templates ao sistema de missões/recibos sem novo armazenamento.
- Definir critérios de risco que determinam quando a revisão é obrigatória.

### Fase 2 — piloto read-only
- Executar o fluxo num módulo não crítico.
- Confirmar isolamento real dos revisores, proveniência e reprodutibilidade.
- Medir falsos positivos, findings úteis, custo/latência e carga de contexto.

### Fase 3 — integração gradual
- Expor estado e artefactos no dashboard como projeção read-only.
- Ativar gates apenas após testes e aceitação.
- Não alterar o backend de chat/APK nesta iniciativa.

## Critérios de aceitação

- Nenhum segundo motor de tarefas ou armazenamento paralelo.
- Revisores independentes não recebem o histórico/conclusão do agente autor.
- Cada finding é rastreável a evidência ou explicitamente marcado como hipótese.
- Nenhuma revisão pode aprovar ou executar a própria alteração.
- As operações de escrita continuam sujeitas às regras de aprovação atuais.
- Testes provam que a ausência de subagentes independentes não é mascarada.
- Relatório final distingue revisão documental, revisão de código e testes executados.

## Fontes upstream consultadas

- README: https://github.com/google/elephant-goldfish-model
- Arquitetura: https://github.com/google/elephant-goldfish-model/blob/main/docs/designs/architecture.md
- Workflow: https://github.com/google/elephant-goldfish-model/blob/main/docs/getting_started.md
- Licença: https://github.com/google/elephant-goldfish-model/blob/main/LICENSE

## Estado de implementação

Esta alteração é apenas documental. Não modifica código de produção, dependências, workflows, flags, credenciais, runtime, APK, dashboard, branches existentes ou configurações de autonomia. A integração executável fica condicionada ao piloto e aos testes acima.
