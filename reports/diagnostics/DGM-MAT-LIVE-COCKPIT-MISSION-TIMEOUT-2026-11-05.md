# Relatório de diagnóstico — primeira missão no cockpit local
Data: 2026-11-05  
Evidência operacional: fotografia fornecida pelo operador após iniciar o DGM-MAT Chat no PC  
Missão observada: `mission_b55c3887`

## Evidência visível na fotografia

- A janela `DGM-MAT — Chat` indica ligação ao backend local.
- O operador enviou: `faz uma pesquisa nas repos Barbuidos e reporta os seus estados`.
- A interface confirmou: `Missão registada: mission_b55c3887 | estado: QUEUED`.
- Cinco segundos depois, a interface apresentou: `O pedido HTTP excedeu o tempo limite. O resultado pode ser desconhecido; consulta a missão antes de voltar a enviá-la.`.

Isto confirma o percurso PC → cockpit → API local → criação/checkpoint da missão. Não prova que a missão tenha sido executada ou concluída. Não se deve reenviar o mesmo pedido sem consultar o checkpoint original.

## Causas encontradas por inspeção do código

1. `_RuntimeRequestWorker._mission()` consultava `GET /runtime/missions` para localizar uma missão individual. Esse endpoint percorre a cache de missões ativas e recarrega cada checkpoint; o custo aumenta com o histórico.
2. Já existia `GET /runtime/missions/{mission_id}`, que lê apenas o checkpoint pretendido e devolve estado, ação associada e resultado.
3. O intent router reconhecia pesquisa local com o termo singular `repo`, mas não reconhecia a formulação plural `repos` quando combinada com `pesquisa` e `estados`. O pedido era classificado como não suportado e, por isso, a ação ficava em `QUEUED`, à espera de aprovação, em vez de usar o scanner read-only.

## Correção proposta em PR #223

- O cockpit consulta diretamente o checkpoint individual por ID.
- Leituras temporariamente lentas são repetidas apenas como GET; nunca é feito novo POST para criar outra missão.
- O ciclo de polling aguarda o prazo real e não transforma um timeout de leitura numa falha da missão.
- A frase de inventário/estado de repositórios é encaminhada para o handler existente `list_repositories`, que só faz descoberta limitada e comandos Git read-only.
- Foi extraído `cockpit/mission_status_client.py`, sem dependência de Qt, para testes determinísticos.
- Testes provam o encaminhamento, a aprovação automática apenas da ação read-only, a consulta direta do checkpoint, a validação do ID devolvido e o tratamento de 404/HTTP 503.

## Validação

- Focused PR Validation #362, commit `e2bbfaeaa6364237d2662eb1adbfdf692bebe805`: **SUCCESS**.
- Python compileall: passou.
- Regressões selecionadas: `tests/autonomy/test_mission_intent_router.py`, `tests/autonomy/test_mission_system.py`, `tests/cockpit/test_mission_status_client.py`: passaram.
- CodeRabbit foi novamente chamado a rever o head atual; revisão ainda pendente.
- PR #223 continua draft, sem merge e sem auto-merge.

## Limites e próximos passos

- O executável instalado no PC ainda não contém esta correção; só a receberá depois de revisão, merge deliberado, build Windows e instalação validada.
- O estado atual da missão `mission_b55c3887` no PC não foi consultado remotamente nesta sessão. A fotografia só permite afirmar o estado apresentado naquele momento.
- Depois da atualização, a aceitação local deve consultar primeiro `mission_b55c3887` e só criar nova missão se for realmente necessário.
- A execução genérica de alterações de código continua bloqueada por #212/#220; esta correção apenas torna fiável o fluxo de missão read-only de inventário.
- A captura real de conversas continua dependente da extensão Chrome e aceitação local; consulta de IA externa gratuita continua separada em #211.

## Decisão

O cockpit já provou que consegue registar uma missão no backend local. O timeout foi diagnosticado e corrigido no código em PR #223, com CI verde no head atual. Ainda não se declara o PC corrigido nem o DGM-MAT autónomo até a PR passar revisão, ser integrada e a nova versão ser instalada e testada localmente.
