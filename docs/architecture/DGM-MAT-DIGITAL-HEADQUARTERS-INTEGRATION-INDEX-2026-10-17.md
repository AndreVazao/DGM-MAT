# DGM-MAT Digital Headquarters — índice de integração documental

**Data da auditoria:** 2026-10-17  
**Repositório de referência:** `AndreVazao/DGM-MAT`, branch `main`  
**Estado:** documentação integrada no repositório; escritório visual ainda não implementado nem validado em runtime.

## Objetivo

Este índice liga a visão original do escritório digital DGM-MAT aos requisitos de arquitetura e ao plano de implementação posterior. Evita tratar o wireframe ou a documentação conceptual como funcionalidades já construídas.

## Pacote conceptual principal

Os documentos abaixo estão presentes em `docs/future/`:

- [Conceito do Digital Headquarters](../future/DGM-MAT-DIGITAL-HEADQUARTERS-CONCEPT-2026-10-12.md)
- [Runtime adaptável e trabalhadores distribuídos](../future/DGM-MAT-ADAPTIVE-RUNTIME-AND-DISTRIBUTED-WORKERS-2026-10-12.md)
- [Ferramentas, skills e roteiro de autonomia](../future/DGM-MAT-ADAPTIVE-TOOLS-SKILLS-AND-AUTONOMY-ROADMAP-2026-10-13.md)
- [Soberania dos departamentos e governação de agentes](../future/DGM-MAT-DEPARTMENT-SOVEREIGNTY-AND-AGENT-GOVERNANCE-2026-10-13.md)
- [Agentes externos e autoaperfeiçoamento](../future/DGM-MAT-EXTERNAL-AGENTS-AND-SELF-IMPROVEMENT-RESEARCH-2026-10-12.md)
- [Pesquisa de tecnologias para escritório virtual](../future/DGM-MAT-VIRTUAL-OFFICE-TECHNOLOGY-RESEARCH-2026-10-12.md)
- [Índice do pacote de investigação](../future/README-DIGITAL-HEADQUARTERS-RESEARCH-PACKAGE.md)
- [Wireframe SVG](../future/assets/dgm-mat-digital-headquarters-wireframe.svg)

## Requisitos e plano complementar

- [Arquitetura distribuída, cérebro headless e roteiro da cidade virtual](DGM-MAT-DISTRIBUTED-BRAIN-AND-VIRTUAL-CITY-ROADMAP-2026-10-18.md)
- [Requisitos consolidados do cérebro e escritório adaptável](DGM-MAT_ADAPTIVE_VIRTUAL_OFFICE_AND_CORE_REQUIREMENTS_2026-10-14.md)
- [Plano de implementação do cérebro independente e escritório virtual](DGM-MAT_CORE_INDEPENDENCE_AND_VIRTUAL_OFFICE_IMPLEMENTATION_PLAN_2026-10-14.md)
- [Conceito arquitetural em `docs/architecture`](DGM-MAT-DIGITAL-HEADQUARTERS-CONCEPT-2026-10-12.md)
- [Pacote de investigação em `docs/architecture`](README-DIGITAL-HEADQUARTERS-RESEARCH-PACKAGE.md)

## Decisões que a implementação deve preservar

1. **O cérebro é o produto principal.** O escritório é uma camada de observabilidade e controlo sobre serviços reais; nunca deve ser requisito para executar o backend.
2. **Degradação progressiva.** A experiência deve funcionar em chat/listas num computador fraco, evoluindo para 2D e, opcionalmente, 3D quando o hardware permitir.
3. **Soberania DGM-MAT.** Memória, planeamento, governação, permissões e validação permanecem no DGM-MAT. Claude Code, harnesses e outros agentes são trabalhadores substituíveis, não autoridades.
4. **Local-first e custo zero por defeito.** Priorizar ferramentas locais e opções gratuitas; serviços pagos são opcionais e nunca pressupostos.
5. **Segurança e controlo humano.** Permissões explícitas, auditoria, execução limitada e aprovação humana para operações destrutivas ou de elevado impacto.
6. **Implementação por fases.** Primeiro contratos/backend, estado e eventos reais; depois cockpit 2D acessível; só depois visualização avançada. O cockpit móvel vem depois de o cérebro e o painel de PC estarem estáveis.
7. **Sem alegações de conclusão prematuras.** O wireframe é uma referência visual. A documentação, por si só, não comprova integração funcional, testes, build Windows ou execução.

## Decisão arquitetural confirmada em 2026-10-18

O cérebro funciona headless e permanece a autoridade soberana. Os departamentos devem ser modulares para começarem num único PC e poderem migrar para PCs satélite na mesma rede; o Headquarters pode correr noutro PC, browser ou telemóvel e apenas observa eventos/estado reais. A evolução visual poderá representar primeiro um edifício com vários andares e, à medida que existam máquinas e serviços reais, uma cidade de edifícios departamentais. A fase atual continua centrada na estabilidade e validação ponta a ponta do cérebro com cockpit simples; a distribuição multi-PC e a cidade são direção arquitetural futura, não capacidades aqui declaradas como implementadas. Ver o roteiro detalhado ligado acima.

## Resultado da auditoria documental de 2026-10-17

A auditoria da árvore recursiva de `main` confirmou a presença do pacote conceptual, do wireframe e dos documentos complementares de arquitetura. Foram encontrados materiais relacionados tanto em `docs/future/` como em `docs/architecture/`; este índice torna explícita a relação entre eles sem apagar ou substituir conteúdo histórico.

**Limite da validação:** esta é uma confirmação de presença e ligação documental no GitHub. Não equivale a uma comparação semântica linha a linha de todas as versões históricas, nem a testes de software, build ou validação visual/runtime.
