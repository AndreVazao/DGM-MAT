# Auditoria urgente: autocorreção e controlo web do DGM-MAT

Data: 2026-10-16
Base examinada: branch publicada `main` de `AndreVazao/DGM-MAT`.
Estado: auditoria do código remoto; a instalação local ainda requer testes no PC.

## 1. Autocorreção — capacidade observada

Ficheiros examinados:
- `core/api/governance_api.py`
- `core/self_healing/self_repair_engine.py`

Endpoints expostos:
- `GET /governance/audit/self` — executa diagnóstico de repositório em modo de leitura.
- `GET /governance/repair/self/plan` — devolve o diagnóstico/plano, sem mutação.
- `POST /governance/repair/self/apply` — exige `confirm=true`; por omissão `dry_run=true`.

O motor `SelfRepairEngine._plan()` só cria a ação automática `SELF-001` quando o repositório auditado tem o nome `DGM-MAT`. Essa ação executa um smoke test limitado do BootstrapEngine. As outras ações presentes no código (por exemplo, árvore Git suja, README ausente ou origin ausente) exigem aprovação. O executor só implementa `SELF-001`; não existe neste motor um ciclo geral que gere patches de código, aplique-os em worktree isolada, execute a suíte de testes e reverta falhas.

**Conclusão:** existe diagnóstico e uma reparação/teste automática muito estreita, não autocorreção geral de bugs.

## 2. Controlo web — capacidade observada

A pesquisa do código publicado por referências a browser control, Playwright, CDP e automação de browser não encontrou um motor operacional integrado que permita ao DGM-MAT controlar sessões web autenticadas. Não foi encontrado endpoint de controlo web nem um fluxo completo de browser worker com estado, permissões e auditoria.

Há código de inteligência de conversas e uma rota de análise de conversa em `core/api/governance_api.py`, mas analisar conteúdo fornecido ao backend não é o mesmo que abrir ChatGPT, Grok ou Gemini, navegar pelas conversas e exportar/inventariar o histórico.

**Conclusão:** não se deve apresentar controlo web como funcional até ser implementado e testado.

## 3. Plano de implementação proposto

### Fase A — motor de autocorreção com limites
1. Criar workspace temporário/worktree por tarefa e registar branch/commit de base.
2. Recolher falha reproduzível (logs, traceback e teste que falha).
3. Gerar patch limitado aos caminhos autorizados; rejeitar alterações a segredos, autenticação, políticas de segurança ou ficheiros fora do workspace.
4. Executar testes focados e depois smoke/regressão com limites de tempo/recursos.
5. Se algum teste falhar, descartar a worktree de reparação e produzir relatório; nunca aplicar parcialmente.
6. Se todos passarem, guardar patch e relatório para revisão/merge. Push, merge e alterações destrutivas continuam a ser decisões separadas.
7. Adicionar testes para falha de teste, timeout, patch inválido, árvore suja, cancelamento e recuperação.

### Fase B — controlo web assistido e auditável
1. Implementar um adaptador de browser local (Playwright ou CDP, após verificar dependências e compatibilidade da máquina).
2. Separar browser worker do processo API e limitar concorrência/recursos.
3. Utilizar perfis de browser locais já autenticados; nunca pedir nem guardar passwords em texto.
4. Começar em modo só de leitura: abrir páginas, recolher títulos/URLs/datas e conteúdo visível autorizado.
5. Adicionar exportação/inventário por fornecedor, com deduplicação, checkpoints e registo de origem.
6. Não contornar CAPTCHA, MFA, limites de acesso ou mecanismos antiabuso. Se for necessária interação humana, pausar e pedir que o utilizador conclua no browser.
7. Para cada fornecedor, validar manualmente a estrutura e limites atuais antes de automatizar; preferir exportação oficial quando disponível.
8. Guardar resultados em ficheiros/artefactos revisáveis antes de mover conversas para a memória AndreOS.

## 4. Ordem de prioridade para a entrega imediata

1. Cockpit PC com LEDs de estado de endpoints e envio de prompts.
2. Confirmar o runtime local e se a API de conversas responde.
3. Implementar e testar autocorreção isolada com relatório verificável.
4. Só depois integrar browser control e inventário de conversas; é uma capacidade maior e não deve ser simulada por um LED verde falso.

## 5. Critérios de aceitação

- O dashboard distingue API acessível de motor realmente funcional.
- A autocorreção apresenta: problema, evidência, patch, testes antes/depois e resultado.
- Nenhuma correção é aplicada à árvore principal sem passar pelos testes e pela política de aprovação.
- Browser control só aparece verde quando um teste real abre uma página de teste e devolve título/URL; a simples existência de uma dependência não conta.
- O inventário das conversas tem checkpoint, deduplicação, origem e relatório de erros, sem apagar ou modificar conversas no fornecedor.

## Limitações desta auditoria

Esta auditoria é baseada no código publicado em `main`. Não confirma o estado de branches locais não publicadas nem a configuração do PC. A instalação local e os testes end-to-end continuam necessários.
