# Relatório de Análise — DGM-MAT (.exe e APK)

**Data:** 2026-10-24  
**Autor:** Claude Code (by request do utilizador)  
**Repositórios:** `AndreVazao/DGM-MAT` e `AndreVazao/DGM-MAT-Mobile`  
**Local da instalação .exe:** `C:\ProgramasGodMode\DGM-MAT\installed\DGM-MAT.exe`

---

## 1. Disponibilidade nos GitHub Actions

### .exe do DGM-MAT — DISPONÍVEL ✅
- Workflow: `Windows Executable Build` (`.github/workflows/build-windows.yml`) no repositório `AndreVazao/DGM-MAT`.
- Compila via PyInstaller (Python 3.12) a partir de `build/dgm_mat.spec`, produzindo `DGM-MAT.exe`.
- Último **run com sucesso**: `2026-10-06T20:01:07Z` (run `37523249361`, branch `main`).
- Artifact publicado: `DGM-MAT-Windows-3.12.zip` (+ `.sha256`), não expirado.
- Runs recentes (23/10/2026) do mesmo workflow **falharam** — o artifact disponível para download é o do sucesso de 06/10.

### APK do DGM-MAT-Mobile — DISPONÍVEL ✅
- Workflow: `One-shot Android APK Build` no repositório `AndreVazao/DGM-MAT-Mobile`.
- Último **run com sucesso**: `2026-10-21T05:50:20Z` (run `39551825947`, branch `main`).
- Artifact publicado: `DGM-MAT-Mobile-debug.apk` (~4,1 MB), não expirado.
- Nota: apesar do README do mobile descrever um cockpit PWA (não APK nativo), existe sim um build de APK nos Actions. Trata-se de um build **de debug** (não assinado para distribuição de produção).

---

## 2. Download e instalação do .exe

- Download do artifact: `DGM-MAT-Windows-3.12.zip` (~70,8 MB) → `C:\Users\André Vazão\Downloads\DGM-MAT\exe\`.
- Extraído e instalado (cópia para pasta estável): `C:\ProgramasGodMode\DGM-MAT\installed\DGM-MAT.exe` (71,3 MB).
- Não há instalador clássico (MSI/setup.exe). O ficheiro é um executável PyInstaller mono-ficheiro, autossuficiente. A "instalação" consistiu em copiá-lo para uma pasta fixa, junto dos ficheiros de suporte (`config/`, `scripts/`, `health.json`, `ecosystem.json`, `README.md`, `architecture.md`).
- O script `packaging/windows/Install-DGM-MAT.ps1` existente no repo instala um **outro** executável (`DGM-MAT-BackOffice.exe`, do `DGM-MAT-Deploy`), não o `DGM-MAT.exe` dos Actions — não foi aplicado.

---

## 3. Teste de funcionamento do .exe

### Teste de fumo (modo headless)
Lançado `DGM-MAT.exe --headless`. O processo arranca, executa o `BootstrapEngine` (profile `HEADLESS`) e conclui com `Runtime: Bootstrap complete. All systems nominal.`

**O que funciona corretamente:**
- Logger persistente inicializado em `C:\DevopGodMode\runtime\logs\dgm-runtime.log`.
- `StorageManager` operacional em `C:\DevopGodMode\runtime`; base de dados SQLite iniciada/reutilizada (`DB_REUSED`, 2 tabelas).
- Todas as fases do bootstrap concluídas: validação de ambiente, inicialização de armazenamento, registo do ecossistema, governação, memória, providers, federação, kernel de runtime, camada em tempo real, ponte do cockpit, validação de saúde.
- `EventBus V2`, `Cognitive Kernel`, `Evolution Engine`, `Update Engine` (versão 0.1.0), `SafeActionQueue`, `CredentialVault` (chave mestra gerada) — todos inicializados.
- Servidor API (Uvicorn) vinculado a `http://127.0.0.1:8181`.
- `GET /health` → `200 OK` com `{"status":"healthy"}`.
- Controlador de degradação funcional: detetou CPU 91.2% / MEM 93.9% (modo degradado) e saiu de modo degradado quando normalizou.
- Perfil de baixa memória ativado (`total_ram=2.96GB`, memória ~93%) — inicialização de motores avançados diferida adequadamente ao recurso limitado.

### Interação via API (endereço já em execução na porta 8181)
| Endpoint | Resultado | Observação |
|---|---|---|
| `GET /health` | `200 OK` `{"status":"healthy"}` | ✅ Funciona |
| `GET /governance/audit/self` | `404 Not Found` | ❌ Documentado no README, não exposto nesta build |
| `GET /governance/audit/workspace` | `404 Not Found` | ❌ Idem |
| `GET /governance/repair/self/plan` | `404 Not Found` | ❌ Idem |
| `POST /governance/repair/self/apply` | não testado | Documentado, presumivelmente também ausente |

---

## 4. O que NÃO funciona / problemas encontrados

### A. Conflito de porta 8181
Quando outra instância do DGM-MAT (versão código-fonte via `pythonw.exe C:\ProgramasGodMode\DGM-MAT\main.py --headless`, PID 6100) já está a correr, o `.exe` **não consegue vincular a API** à porta 8181:
```
[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8181)
```
O bootstrap do .exe completa, mas o servidor API falha. Não é possível correr duas instâncias simultâneas na mesma porta. Isso impediu o teste inicial do .exe até que a instância de código-fonte fosse parada.

### B. Endpoints de governança documentados mas ausentes (404)
O `README.md` do DGM-MAT documenta a "Governance API":
- `GET /governance/audit/self`
- `GET /governance/audit/workspace`
- `GET /governance/repair/self/plan`
- `POST /governance/repair/self/apply`

Na build compilada todos devolvem `404 Not Found`. Ou não estão implementados nesta versão ou não são expostos pelo servidor API. É uma inconsistência entre documentação e realidade.

### C. Dependências opcionais em falta (avisos não bloqueantes)
- `core.memory.memory_manager` em falta.
- `core.providers.provider_registry` em falta.

### D. Recurso de hardware limitado
O PC tem 2,96 GB de RAM com memória a ~93% de utilização. O perfil de baixa memória é ativado e a inicialização de motores avançados é diferida. Isto limita o desempenho e a capacidade do sistema.

### E. Possível instância duplicada/zumbi
Foram observados dois processos `DGM-MAT.exe` (PIDs 8036 e 6852), mas apenas o 6852 vincula a porta 8181. O outro pode ser um resíduo/instância órfã.

---

## 5. APK — estado e limitações

- `DGM-MAT-Mobile-debug.apk` (~4,1 MB) descarregado com sucesso de `AndreVazao/DGM-MAT-Mobile` (Actions, run `39551825947`).
- **Não foi possível instalar/testar o APK num dispositivo:** `adb devices` não retornou qualquer dispositivo Android/emulador ligado. Não há forma de validar a instalação nem o funcionamento móvel neste ambiente.
- Trata-se de um build de **debug**, não assinado para distribuição de produção.

---

## 6. Conclusão

| Item | Estado |
|---|---|
| .exe disponível nos Actions | ✅ Sim (build de 06/10/2026) |
| .exe descarregado e instalado | ✅ `C:\ProgramasGodMode\DGM-MAT\installed\DGM-MAT.exe` |
| .exe arranca e faz bootstrap | ✅ Sim ("All systems nominal") |
| API `/health` responde | ✅ Sim (200 OK) |
| Endpoints de governança (`/governance/...`) | ❌ 404 Not Found (documentados, ausentes) |
| Conflito de porta 8181 com instância em execução | ❌ Impede múltiplas instâncias simultâneas |
| APK disponível nos Actions | ✅ Sim (build debug de 21/10/2026) |
| APK instalado/testado num dispositivo | ❌ Não há dispositivo Android ligado via ADB |

### O que funciona bem
O núcleo do DGM-MAT (.exe) é funcional: arranca, inicializa armazenamento, kernel, event bus, motores de evolução/atualização, cofre de credenciais e expõe um endpoint `/health` saudável. O sistema deteta e reage ao estado de degradação por recurso (CPU/memória).

### O que não funciona e porquê
1. **Endpoints de governança devolvem 404** — não estão implementados/expões nesta build, apesar de estarem documentados no README.
2. **Conflito de porta 8181** — o servidor API não sobe se outra instância DGM-MAT já ocupa a porta; não há alternativa de porta configurável nem deteção de instância existente.
3. **APK não testável** — sem dispositivo Android/emulador, não se pode validar a instalação nem o funcionamento móvel.

### O que pode ser mudado para funcionar
1. Implementar (ou expor) os endpoints `/governance/audit/self`, `/governance/audit/workspace`, `/governance/repair/self/plan` e `POST /governance/repair/self/apply`, ou removê-los do README para não criar expectativa.
2. Tornar a porta da API configurável (variável de ambiente ou argumento de linha de comando) e adicionar deteção de instância já em execução para evitar o erro `[Errno 10048]`.
3. Investigar e eliminar o segundo processo `DGM-MAT.exe` órfão/duplicado.
4. Assinar o APK para distribuição de produção (atualmente é debug).
5. Disponibilizar um dispositivo/emulador Android para validar a instalação e funcionamento do APK.
6. Considerar otimizações para o perfil de baixa memória (2,96 GB RAM), que atualmente difere motores avançados.

---

**Ficheiros produzidos nesta sessão:**
- `C:\ProgramasGodMode\DGM-MAT\installed\DGM-MAT.exe` — executável instalado
- `C:\Users\André Vazão\Downloads\DGM-MAT\exe\DGM-MAT-Windows-3.12.zip` — artifact .exe dos Actions
- `C:\Users\André Vazão\Downloads\DGM-MAT\apk\DGM-MAT-Mobile-debug.apk` — artifact APK dos Actions
- `C:\Users\André Vazão\Downloads\DGM-MAT\dgm-mat-exe.log` — log de execução do .exe
- `C:\ProgramasGodMode\DGM-MAT\RELATORIO_ANALISE_DGM-MAT_EXE_APK.md` — este relatório
