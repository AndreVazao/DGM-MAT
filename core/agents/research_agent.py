"""Compatibility shim; implementation lives in DGM-MAT-Agents."""
from ._compat import load
_impl = load("dgm_mat_agents.research_agent")
for _name in dir(_impl):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_impl, _name)
