# DGM-MAT Digital Headquarters — pacote documental

**Data:** 2026-10-12  
**Estado:** documentação e pesquisa; não implementado  
**Branch:** `docs/digital-headquarters-concept-2026-10-12`

Este pacote preserva o conceito visual do escritório vivo, a investigação de agentes externos e a avaliação de bases de escritório virtual. Foi criado isoladamente para retomar o trabalho depois da auditoria/reconciliação dos branches locais e remotos.

## Documentos

1. [Conceito funcional e arquitetura futura](DGM-MAT-DIGITAL-HEADQUARTERS-CONCEPT-2026-10-12.md)
   - Interface com navegação fixa esquerda, escritório central e chat à direita.
   - Enfermaria, armazém, produção, QA, expedições, formação, contratação e remodelação.
   - Regras de segurança, eventos conceptuais e plano por fases.

2. [Integração de agentes externos e evolução autónoma](DGM-MAT-EXTERNAL-AGENTS-AND-SELF-IMPROVEMENT-RESEARCH-2026-10-12.md)
   - DeepSeek Harness como trabalhador externo, não como cérebro.
   - Arquitetura de adaptador, isolamento, compatibilidade, recursos e prova de conceito.
   - Ciclo de melhoria baseado em evidência, testes, revisão e rollback.

3. [Pesquisa comparativa de escritórios virtuais](DGM-MAT-VIRTUAL-OFFICE-TECHNOLOGY-RESEARCH-2026-10-12.md)
   - My Virtual Office, Claude Office / Pixel Agent Office, My Virtual World, DeepSeek Harness e implementação própria.
   - Comparação de arquitetura, visual, integrações, recursos e licenças.
   - Recomendação de prova de conceito e plano incremental.

4. [Runtime adaptável e agentes distribuídos](DGM-MAT-ADAPTIVE-RUNTIME-AND-DISTRIBUTED-WORKERS-2026-10-12.md)
   - Perfis de renderização 3D, 2D avançado, 2D leve, boneco mínimo e chat sem animação.
   - Adaptação ao hardware com medição, fallback, escolha manual e preservação do estado.
   - Arquitetura para usar Harness, Claude Code, Ollama e ferramentas futuras em vários computadores autorizados.
   - Gateway por nó, catálogo de capacidades, segurança da rede, política free/local-first e APIs pagas apenas com autorização.

5. [Wireframe SVG](assets/dgm-mat-digital-headquarters-wireframe.svg)
   - Desenho vetorial de referência para a composição da interface.
   - É um wireframe ilustrativo; valores e eventos desenhados não representam dados reais do sistema.

## Decisões de segurança

- DGM-MAT continua a ser o cérebro/orquestrador e fonte canónica de estado, memória, política e validação.
- Harnesses, ferramentas e computadores externos são workers substituíveis, nunca uma segunda fonte de verdade.
- O escritório é uma projeção do estado real, não uma segunda autoridade.
- A renderização adapta-se à máquina sem alterar as capacidades funcionais centrais.
- Nenhuma percentagem, expedição, colaboração, recuperação ou conclusão pode ser inventada.
- Nós remotos têm de ser inscritos e autorizados; estar na LAN não significa ser confiável.
- Preferência inicial free/local-first; APIs pagas apenas depois de configuração e autorização explícitas.
- Nenhuma instalação ou integração na máquina principal antes de medir recursos e testar isolamento.
- Nenhum merge, rebase, reset ou sincronização foi realizado como parte deste pacote.

## Próxima sequência ao regressar ao PC

1. Auditoria read-only dos branches, working trees, commits locais e remotos.
2. Preservar snapshots e reconciliar divergências conforme evidência.
3. Auditar contratos, APIs, eventos, providers, persistência e frontend atuais do DGM-MAT.
4. Medir baseline do PC e definir perfil mínimo funcional.
5. Avaliar um único Harness numa sandbox isolada, comparando-o com as ferramentas já disponíveis.
6. Prototipar UI com dados mock; depois integrar read-only.
7. Validar contrato de worker local antes de testar um segundo computador na rede privada.
8. Só depois decidir adoção, implementação e merge.

## Fontes principais

- https://github.com/deepseek-ai/deepseek-harness
- https://github.com/eliautobot/my-virtual-office
- https://github.com/paulrobello/claude-office
- https://github.com/forgeekscn/pixel-agent-office
- https://github.com/eliautobot/my-virtual-world
- https://github.com/openhands/software-agent-sdk
- https://github.com/SWE-agent/SWE-agent
