# DGM-MAT Windows update — V1

## Preferred update path

Do not manually delete the installed executable or uninstall the application before a verified package is ready. The supported update script performs a controlled in-place replacement and preserves the existing data directories. This is safer than removing the current installation first.

The Windows build artifact contains:

- \`DGM-MAT.exe\` and its SHA-256 sidecar;
- \`scripts/install_windows_update.ps1\`, the governed update engine;
- \`scripts/install_dgm_mat_update.ps1\`, the elevation/checksum wrapper;
- \`Install-DGM-MAT-Update.bat\`, the double-click launcher;
- \`scripts/rollback_windows_update.ps1\`;
- the browser extension and its installer.

## Operator procedure

1. Download the ZIP and the separate \`.zip.sha256\` artifact from the successful GitHub Actions Windows Executable Build run.
2. Verify the ZIP SHA-256 against the separately downloaded checksum before extracting or running anything.
3. Extract the ZIP to a normal writable folder. Do not extract over the installed DGM-MAT directory.
4. Close the DGM-MAT Chat cockpit window. Leave the installation files and local data untouched.
5. Double-click \`Install-DGM-MAT-Update.bat\`. Approve the Windows UAC prompt only after confirming the package ZIP checksum.
6. The updater verifies the packaged executable digest, checks the API listener belongs to the expected DGM-MAT executable, requests graceful shutdown and waits. It never force-kills processes.
7. The updater backs up the previous executable, service launcher, runtime/recovery/report folders and the full local Vault under the update-backups directory. It does not delete the old backup or local user data.
8. The updater replaces only managed runtime files and writes an \`INSTALL-MANIFEST.json\` with hashes and backup locations. It deliberately leaves credentials, worktrees and persistent memory untouched.
9. The runtime remains stopped. Launch DGM-MAT using the normal shortcut and verify \`/health\`, authenticated session, cockpit and core workflows.

If any precondition or checksum fails, the update aborts before replacing the executable. If a process is not the expected DGM-MAT owner or does not shut down gracefully, the updater refuses to stop it.

## Rollback

Use the packaged \`scripts/rollback_windows_update.ps1\` with the exact backup directory created by the installer. The rollback validates manifest hashes and stages the previous executable and launcher before replacing either. Do not delete the backup until the new installation has passed local acceptance.

## Important boundaries

- This is an update, not an uninstall/reinstall. It preserves the Vault and existing project/worktree data.
- Never run an unverified ZIP or a package whose independent ZIP checksum does not match.
- Never copy the private Vault, credentials, browser profiles or local archives into GitHub.
- A successful Windows CI build is not proof of successful operation on the target PC. Complete local smoke and acceptance tests after the update.
