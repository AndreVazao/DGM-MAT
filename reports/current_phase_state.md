# Current Phase State Report (PHASE 1)

This report establishes the initial baseline for the repository extraction from `DGM-MAT` into the satellite repositories.

## 1. Repository Totals
* **Total Files:** 987 files
* **Python Files (.py):** 819
* **JSON Files (.json):** 69
* **Markdown Files (.md):** 54
* **No Extension:** 17
* **YAML/YML Files (.yml / .yaml):** 13
* **Text Files (.txt):** 9
* **Shell Scripts (.sh):** 1
* **TOML config (.toml):** 1
* **Ini config (.ini):** 1
* **Log files (.log):** 1
* **Spec files (.spec):** 1
* **Stylesheets (.qss):** 1

## 2. Satellite Mapping Coverage
Based on `reports/extraction_plan.md`:
* **DGM-Core-Backend:** 144 files
* **DGM-Cockpit-Frontend:** 65 files
* **DGM-Experimental:** 85 files
* **DGM-Docs:** 20 files
* **Total Covered:** 314 files

## 3. UNASSIGNED File Count
* **UNASSIGNED Files:** 673 files (approx. 68.2% of the repository)
* **Description of Unassigned Files:** 
  * Sub-repository folders residing in root (e.g., `DGM-MAT-Agents`, `DGM-MAT-Assets`, `DGM-MAT-Cluster`, etc.).
  * CI/CD workflows under `.github/workflows/`.
  * Runtime trace logs, database sessions, and execution journals in `.runtime/`.
  * Various configuration and auxiliary testing tools in the repository root.

## 4. Extraction Blockers
* **Cross-Process State desync:** The Cockpit UI (Frontend) communicates with the backend via websockets, but the backend relies on an in-memory `state_store` and a separate daemon process for the `CognitionLoop`. Isolation of backend vs. frontend will require clean API interface separation.
* **Shared schemas & DTOs:** No centralized `contracts` folder or module exists. API models are imported ad-hoc from internal backend modules, creating coupling.
* **Hardcoded Absolute Paths:** Subsystems (e.g., `MissionEngine`, `StorageManager`) contain hardcoded Windows file system paths (`C:\ProgramasGodMode`, `C:\DevopGodMode\runtime`), which will block platform-independent runs until environment variables or configs are generalized.
* **Aggressive Resource Governance:** The `GovernanceEngine` actively throttles processes when memory spikes, which might trigger state degradation during testing of isolated components.
