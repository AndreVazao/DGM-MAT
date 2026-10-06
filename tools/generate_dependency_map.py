from __future__ import annotations
import ast, json, re
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"C:\ProgramasGodMode\DGM-MAT")
OUT = ROOT / "reports"
OUT.mkdir(exist_ok=True)
EXCLUDE = {".git",".pytest_cache","__pycache__",".runtime","legacy","build","node_modules",".venv"}
PY = [p for p in ROOT.rglob("*.py") if not any(x in EXCLUDE for x in p.parts)]

def rel(p): return p.relative_to(ROOT).as_posix()

mods = {}
for p in PY:
    if p.name == "__init__.py":
        mod = ".".join(p.relative_to(ROOT).parent.parts)
    else:
        mod = ".".join(p.relative_to(ROOT).with_suffix("").parts)
    mods[mod] = rel(p)

edges=[]; external=defaultdict(set); file_refs=[]; symbols=defaultdict(list)
for p in PY:
    src=rel(p)
    try: tree=ast.parse(p.read_text(encoding="utf-8",errors="ignore"))
    except Exception as e:
        file_refs.append({"file":src,"kind":"parse_error","value":str(e)}); continue
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):
            for a in n.names:
                target=a.name
                if target in mods or any(target.startswith(m+".") for m in mods):
                    edges.append({"from":src,"to_module":target,"kind":"import"})
                else: external[target.split(".")[0]].add(src)
        elif isinstance(n,ast.ImportFrom):
            target=n.module or ""
            if target and (target in mods or any(target.startswith(m+".") for m in mods)):
                edges.append({"from":src,"to_module":target,"kind":"from_import"})
            elif target: external[target.split(".")[0]].add(src)
        elif isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            symbols[src].append({"type":type(n).__name__,"name":n.name,"line":n.lineno})
    text=p.read_text(encoding="utf-8",errors="ignore")
    for m in re.finditer(r'(?:[A-Za-z]:\\[^"\r\n]+)',text):
        file_refs.append({"file":src,"kind":"path_literal","value":m.group(0)[:300]})

resolved=[]
for e in edges:
    target=e["to_module"]; candidates=[]
    if target in mods: candidates.append(mods[target])
    for m,r in mods.items():
        if m.startswith(target+"."): candidates.append(r)
    resolved.append({**e,"resolved":sorted(set(candidates))[:20]})

dir_edges=defaultdict(set)
for e in resolved:
    if not e["resolved"]: continue
    a=e["from"].split("/")[0]
    for r in e["resolved"]:
        b=r.split("/")[0]
        if a!=b: dir_edges[a].add(b)

repo_dirs=[p.name for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("DGM-")]
report={"generated":"2026-10-06","root":str(ROOT),"python_files":len(PY),"modules":len(mods),"internal_import_edges":len(resolved),"embedded_dgm_dirs":sorted(repo_dirs),"edges":resolved,"directory_edges":{k:sorted(v) for k,v in sorted(dir_edges.items())},"external_dependencies":{k:sorted(v) for k,v in sorted(external.items())},"symbols":symbols,"file_references":file_refs}
(OUT/"dgm_mat_dependency_graph.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")

md=["# DGM-MAT — MAPA REAL DE INTERLIGAÇÕES","","Gerado automaticamente a partir do código atual.","","## Estado analisado","Este é o mapa factual ANTES de qualquer migração física. Não é a arquitetura desejada.","",f"- Ficheiros Python analisados: **{len(PY)}**",f"- Módulos detectados: **{len(mods)}**",f"- Ligações internas de import: **{len(resolved)}**",f"- Diretórios DGM-* embutidos: **{len(repo_dirs)}**",""]
md += ["## Topologia por diretório",""]
for a,bs in sorted(dir_edges.items()):
    md.append("### "+a)
    md += ["- -> "+b for b in sorted(bs)]
    md.append("")
md += ["## Interligações ficheiro -> módulo",""]
for e in sorted(resolved,key=lambda x:(x["from"],x["to_module"])):
    if e["resolved"]: md.append("- "+e["from"]+" -> "+e["to_module"]+" ("+e["kind"]+")")
md += ["","## Dependências externas",""]
for k,v in sorted(external.items()): md.append("- "+k+" — "+str(len(v))+" ficheiros")
md += ["","## Regras de migração","",
"1. Não mover core, shared, config, cockpit ou entrypoints antes de fechar o grafo.",
"2. Cada ficheiro será classificado por função e destino real.",
"3. DGM-MAT-* embutidos serão comparados com os repos satélite antes da extração.",
"4. legacy fica fora da primeira migração.",
"5. DGM-MAT-FULL-MIRROR permanece intocado.",
"6. Cada movimento implica reescrita de imports/configuração, testes e validação antes do commit.",
"7. O nome da pasta nunca será usado como única razão para decidir o destino.",""]
(OUT/"DGM-MAT_INTERCONNECTION_MAP.md").write_text("\n".join(md),encoding="utf-8")
print(json.dumps({"python_files":len(PY),"modules":len(mods),"edges":len(resolved),"dgm_dirs":sorted(repo_dirs)}))
