# Frozen Windows runtime ? external module dependencies

The Windows PyInstaller package includes the standalone source trees required by the runtime. The CI build pins each public repository to a known commit and copies only its `src` package into the frozen bundle.

| Repository | Pinned commit | Runtime package |
|---|---|---|
| `AndreVazao/DGM-Contracts` | `4d65419e17195d046607cbf68539e7cd556e1da2` | `dgm_contracts` |
| `AndreVazao/DGM-MAT-Agents` | `50f98db5cf845b03280df7d978ae1129abe14419` | `dgm_mat_agents` |
| `AndreVazao/DGM-MAT-Connectors` | `d339de22258e16d808b97360b47339c9b208f457` | `dgm_mat_connectors` |

`DGM-MAT-Agents` and `DGM-MAT-Connectors` are bundled as source data under `_MEIPASS` and resolved by their explicit composition boundaries. The boundaries retain the existing `DGM_AGENTS_PATH` and `DGM_CONNECTORS_PATH` overrides for source/developer deployments. They do not depend on a temporary sibling checkout outside the executable bundle.

`RuntimeStorageManager` independently resolves persistent state from the installed executable location, so bundling these modules does not redirect the runtime vault into `_MEIPASS`.

The build workflow installs the pinned repositories before PyInstaller, and the regression tests simulate frozen mode to verify the bundled source paths.
