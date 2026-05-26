import os

widgets = [
    "cockpit/workspace/task_feed_widget.py",
    "cockpit/workspace/execution_timeline_widget.py",
    "cockpit/runtime/autonomous_console.py",
    "cockpit/workspace/cognition_graph.py",
    "cockpit/workspace/memory_graph.py",
    "cockpit/approvals/patch_review_ui.py",
    "cockpit/providers/login_form.py",
    "cockpit/repositories/import_ui.py",
    "cockpit/runtime/provider_diagnostics.py"
]

for w in widgets:
    if os.path.exists(w):
        print(f"VERIFIED: {w}")
    else:
        print(f"MISSING: {w}")
