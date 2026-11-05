# Frozen Windows runtime — external module dependencies

The current Windows build resolves external DGM packages from pinned source revisions and bundles their importable Python modules with PyInstaller.

## Pinned build inputs

| Repository | Pinned commit | Runtime package |
|---|---|---|
| AndreVazao/DGM-Contracts | 4d65419e17195d046607cbf68539e7cd556e1da2 | dgm_contracts |
| AndreVazao/DGM-MAT-Agents | 50f98db5cf845b03280df7d978ae1129abe14419 | dgm_mat_agents |
| AndreVazao/DGM-MAT-Connectors | d339de22258e16d808b97360b47339c9b208f457 | dgm_mat_connectors |

## Packaging contract

- The Windows build workflow checks out the pinned repositories and installs their packages before running PyInstaller.
- build/dgm_mat.spec adds the three source roots to Analysis.pathex.
- The spec uses PyInstaller collect_submodules for dgm_mat_agents and dgm_mat_connectors and includes their package roots in hiddenimports.
- Frozen agent composition imports dgm_mat_agents directly. It does not depend on a sibling checkout beside the executable or on locating source files under _MEIPASS.
- Frozen connector composition first imports dgm_mat_connectors directly. The configured DGM_CONNECTORS_PATH and sibling source checkout remain development fallbacks, not required deployment dependencies.
- RuntimeStorageManager resolves persistent state independently from the PyInstaller bundle, so packaged imports do not redirect the runtime vault into temporary extraction storage.

## Validation requirements

1. Build the Windows executable from the pinned dependency commits.
2. Run the deep executable validation against the produced EXE.
3. Test the frozen agent and connector composition boundaries without requiring developer checkouts.
4. Confirm the installed executable can start with persistent state outside the PyInstaller temporary directory.
5. Record artifact SHA-256 values and preserve the previous installed executable before an update.

Do not replace the current module-collection approach with copying raw source directories into the bundle unless a failing packaged-runtime test demonstrates that it is necessary.
