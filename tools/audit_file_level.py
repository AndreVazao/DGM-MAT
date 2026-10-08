from __future__ import annotations
import ast, json, re
from pathlib import Path
ROOT=Path(r'C:\ProgramasGodMode\DGM-MAT')
OUT=ROOT/'reports'
TOPS=['core','shared','cockpit','scripts','tools','tests','config','memory_sync','Persist-Node','legacy']
DEST={'core/agents':'DGM-MAT-Agents','core/providers':'DGM-MAT-Providers','core/connectors':'DGM-MAT-Connectors','core/memory':'DGM-MAT-Memory','core/research':'DGM-MAT-Labs','core/labs':'DGM-MAT-Labs','cockpit':'DGM-Cockpit-Frontend','shared':'DGM-Contracts','core':'DGM-Core-Backend'}
def role(rel):
 s=rel.as_posix()
 for k,v in DEST.items():
  if s==k or s.startswith(k+'/'): return v
 if s.startswith('scripts/autostart/'): return 'DGM-MAT-Deploy / DGM-MAT-OS'
 if s.startswith('scripts/'): return 'DGM-MAT-Deploy or root tooling'
 if s.startswith('tests/'): return 'tests follow destination'
 return 'DGM-MAT root/review'
def imports(p):
 try: t=p.read_text(encoding='utf-8',errors='ignore'); tree=ast.parse(t)
 except Exception: return []
 out=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.Import): out += [a.name for a in n.names]
  elif isinstance(n,ast.ImportFrom):
   if n.module: out.append(('.'*n.level)+n.module)
 return out
rows=[]
for top in TOPS:
 base=ROOT/top
 if not base.exists(): continue
 for p in base.rglob('*.py'):
  rel=p.relative_to(ROOT); im=imports(p)
  internal=[x for x in im if isinstance(x,str) and (x.startswith('core') or x.startswith('shared') or x.startswith('cockpit'))]
  paths=[]
  try:
   txt=p.read_text(encoding='utf-8',errors='ignore')
   for pat in [r'C:/[A-Za-z0-9_./\\-]+',r'C:\\\\[A-Za-z0-9_ ._-]+',r'localhost:\\d+',r'ws://[^\"\']+']: paths += re.findall(pat,txt)
  except Exception: pass
  rows.append({'file':str(rel).replace('\\','/'),'role':role(rel),'imports':internal,'path_literals':sorted(set(paths))})
summary={}
for r in rows:
 d=r['file'].split('/')[0]; summary[d]=summary.get(d,0)+1
rows.sort(key=lambda x:(-len(x['imports']),x['file']))
md=['# DGM-MAT FILE-LEVEL OWNERSHIP AUDIT','## 2026-10-06','', '> No files moved. Evidence map for migration only.','', '## Summary']
for k,v in sorted(summary.items()): md.append(f'- {k}: {v} Python files')
md += ['', '## Highest internal coupling files', '| File | Proposed owner | Internal imports | Imports | Path literals |', '|---|---|---:|---|---|']
for r in rows[:120]: md.append('| '+r['file']+' | '+r['role']+' | '+str(len(r['imports']))+' | '+', '.join(r['imports'])[:180]+' | '+', '.join(r['path_literals'])[:120]+' |')
md += ['', '## Critical boundary findings', '', '- shared.models.event.Event is imported by Core, Cockpit and tests; strong DGM-Contracts candidate.', '- shared.config.settings currently imports core.storage.storage_manager, so shared config cannot move wholesale into Contracts; split public settings/schema from Core-owned storage resolution.', '- Cockpit imports Core directly in 13 locations. These are mandatory rewrites to HTTP/WebSocket/public contracts before cockpit extraction.', '- MissionEngine registers a private callback with SafeActionQueue; this couples durable queue execution to a process-local MissionEngine instance and is the known cross-process risk.', '- runtime_api.py imports MissionEngine, Storage, Workspace, Obsidian, StateStore, Queue and ProviderRegistry directly; it is currently an orchestration boundary, not a thin API layer.', '- EventBus persists through EventStore and streams through realtime in the same publish path; durable/event-contract boundary must be separated before repo extraction.', '- Hardcoded Windows paths remain in runtime/workspace/scanning code and must be centralized before extraction.', '- start_daemon.py is a lifecycle entrypoint that starts both CognitionLoop and SafeActionQueue; it belongs to deployment/OS lifecycle, not Core business logic.', '', '## Migration rule', 'Every row must receive explicit DESTINATION, REWRITE, OWNER/AUTHORITY and TEST before physical move. No source deletion is authorized by this report.']
(OUT/'DGM-MAT_FILE_LEVEL_OWNERSHIP_AUDIT.md').write_text('\n'.join(md),encoding='utf-8')
(OUT/'dgm_mat_file_level_audit.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
print(f'audited={len(rows)}')
print('summary='+json.dumps(summary,ensure_ascii=False))