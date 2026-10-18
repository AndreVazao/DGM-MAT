# DGM-MAT Digital Headquarters — índice de integração documental

**Data da auditoria:** 2026-10-17  
**Repositório de referência:** `AndreVazao/DGM-MAT`, branch `main`  
**Estado:** documentação integrada no repositório; escritório visual ainda não implementado nem validado em runtime.

## Objetivo

Este índice liga a visão original do escritório digital DGM-MAT aos requisitos de arquitetura e ao plano de implementação posterior. Evita tratar o wireframe ou a documentação conceptual como funcionalidades já construídas.

## Pacote conceptual principal

Os documentos de pesquisa abaixo permanecem em `docs/future/`. O conceito principal e o índice do pacote documental têm uma única cópia canónica em `docs/architecture/`; os caminhos antigos em `docs/future/` são apenas pontes de compatibilidade.

- [Conceito canónico do Digital Headquarters](DGM-MAT-DIGITAL-HEADQUARTERS-CONCEPT-2026-10-12.md)
- [Runtime adaptável e trabalhadores distribuídos](../future/DGM-MAT-ADAPTIVE-RUNTIME-AND-DISTRIBUTED-WORKERS-2026-10-12.md)
- [Ferramentas, skills e roteiro de autonomia](../future/DGM-MAT-ADAPTIVE-TOOLS-SKILLS-AND-AUTONOMY-ROADMAP-2026-10-13.md)
- [Soberania dos departamentos e governação de agentes](../future/DGM-MAT-DEPARTMENT-SOVEREIGNTY-AND-AGENT-GOVERNANCE-2026-10-13.md)
- [Agentes externos e autoaperfeiçoamento](../future/DGM-MAT-EXTERNAL-AGENTS-AND-SELF-IMPROVEMENT-RESEARCH-2026-10-12.md)
- [Pesquisa de tecnologias para escritório virtual](../future/DGM-MAT-VIRTUAL-OFFICE-TECHNOLOGY-RESEARCH-2026-10-12.md)
- [Índice canónico do pacote de investigação](README-DIGITAL-HEADQUARTERS-RESEARCH-PACKAGE.md)
- [Wireframe SVG](../future/assets/dgm-mat-digital-headquarters-wireframe.svg)

## Requisitos e plano complementar

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

## Resultado da auditoria documental de 2026-10-17

A auditoria documental de 2026-10-17 confirmou a presença dos materiais conceptuais. Na revisão de 2026-10-18, as duas cópias exatas foram identificadas por blob SHA e os caminhos duplicados em `docs/future/` foram substituídos por ponteiros de compatibilidade para as versões canónicas em `docs/architecture/`. O wireframe e os documentos de pesquisa continuam nos seus caminhos próprios. O histórico Git conserva o conteúdo anterior.

**Limite da validação:** esta é uma confirmação de presença e ligação documental no GitHub. Não equivale a uma comparação semântica linha a linha de todas as versões históricas, nem a testes de software, build ou validação visual/runtime.


## Autoridade arquitetural vinculativa — 2026-10-18

A modularidade e a distinção entre recuperação PC + GitHub e fusão de repositórios são regidas pela [Constituição arquitetural do DGM-MAT](DGM-MAT-ARCHITECTURE-CONSTITUTION-MODULAR-DEPARTMENTS-2026-10-18.md). O inventário da revisão está em [DGM-MAT Recovery & Unification Inventory](DGM-MAT-RECOVERY-UNIFICATION-INVENTORY-2026-10-18.md).
