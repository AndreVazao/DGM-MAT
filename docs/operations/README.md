# DGM-MAT Operational Agent Guides

These documents specify intended behaviour for shell execution, Git, AI engine lifecycle, browser automation and secrets. Documentation is not proof of implementation.

- AGENT_SHELL_GIT_POLICY.md
- POWERSHELL_CMD_GIT_PLAYBOOK.md
- AI_ENGINE_LIFECYCLE.md
- WEB_AUTOMATION_VAULT_AND_AUTH.md

Implementation order: command executor with audit and safety gates; AI engine lifecycle manager; isolated self-repair; read-only browser inventory and human authentication handoff; encrypted vault; cockpit integration.

No paid API is required by this design. Do not silently incur costs.