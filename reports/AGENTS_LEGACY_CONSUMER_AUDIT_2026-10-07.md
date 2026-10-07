# DGM-MAT Agents Legacy Consumer Audit — 2026-10-07

## Objective

Close the post-extraction audit gate for `core/agents` without deleting the compatibility surface prematurely.

## Findings

- Production/runtime consumer found: `core/runtime/runtime.py`, now correctly consumes `core.agents.boundary.create_runtime_agents()`.
- Test consumer found: `tests/contracts/test_agent_boundary.py`, intentionally validates the public composition boundary.
- No remaining production/test imports outside the Agents package itself, the boundary, or legacy content were found.
- `legacy/` still contains historical `core.agents` imports. These are retained as legacy/archive material and are not active runtime consumers.
- The standalone `DGM-MAT-Agents` package contains the extracted implementations for the current agent family and specialization modules.

## Compatibility decision

The implementation authority is now `DGM-MAT-Agents`.

The active `DGM-MAT/core/agents` implementation files were converted to compatibility shims that resolve the standalone package locally. This preserves old import paths for compatibility while eliminating duplicate agent implementations from Core.

A small `core/agents/_compat.py` loader supports:

1. installed `dgm_mat_agents`;
2. explicit `DGM_AGENTS_PATH`;
3. the sibling repository `C:\\ProgramasGodMode\\DGM-MAT-Agents\\src`.

`boundary.py` and `service_adapters.py` remain in Core because they are composition infrastructure, not agent implementations.

## Validation

- Direct legacy import of `core.agents.base_agent.BaseAgent`: resolves to `dgm_mat_agents.base_agent`.
- Direct legacy specialization import remains available.
- Runtime boundary returns `RepoAgent`, `ProviderAgent`, and `AutonomyAgent` from `dgm_mat_agents`.
- `python -m compileall -q core tests`: passed.
- Focused contracts/autonomy/runtime suite: **9 passed**.
- Full DGM-MAT suite: **100% passed**, exit code 0, ~69.77 s.
- DGM-MAT-Agents standalone suite: **2 passed**.
- No GitHub Actions were triggered.
- FULL-MIRROR was not touched.

## Safety boundary

The old implementation files are not deleted yet. They now act as compatibility shims, so rollback remains straightforward and no consumer is forced to migrate in one destructive step.

The remaining `legacy/` imports are explicitly excluded from production extraction and should only be revisited if legacy recovery/testing is intentionally activated.

## Next gate

Proceed to the next Core extraction candidate only after reviewing its real consumers and preserving public contracts. Do not treat `core/agents` as an implementation authority anymore.
