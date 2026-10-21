# Path: C:\ProgramasGodMode\DGM-MAT\core\operator\usb_recovery.py
"""Conservative USB/ADB recovery for the Android DGM-MAT cockpit.

Only allowlisted ADB operations are exposed. The service never clears app data,
changes device authorization, or executes arbitrary shell commands on Android.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PACKAGE_ID = "com.andrevazao.dgmmatmobile"
ADB_TIMEOUT_SECONDS = 12


def _candidate_adb_paths() -> list[Path]:
    candidates: list[Path] = []
    if os.getenv("DGM_ADB_PATH"):
        candidates.append(Path(os.environ["DGM_ADB_PATH"]))
    found = shutil.which("adb")
    if found:
        candidates.append(Path(found))
    local = os.getenv("LOCALAPPDATA")
    home = os.getenv("USERPROFILE")
    if local:
        candidates.extend([
            Path(local) / "Android" / "Sdk" / "platform-tools" / "adb.exe",
            Path(local) / "Programs" / "Android" / "platform-tools" / "adb.exe",
        ])
    if home:
        candidates.append(Path(home) / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "adb.exe")
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path).casefold()
        if key not in seen and path.is_file():
            unique.append(path)
            seen.add(key)
    return unique


class UsbRecoveryService:
    """Detect ADB/device state and perform narrowly scoped, reversible repairs."""

    def __init__(self, *, runner=subprocess.run, clock=time.time):
        self._runner = runner
        self._clock = clock

    def _run(self, adb: Path, *args: str, timeout: int = ADB_TIMEOUT_SECONDS) -> dict[str, Any]:
        try:
            result = self._runner(
                [str(adb), *args],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
            )
            return {
                "ok": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": (result.stdout or "")[-12000:],
                "stderr": (result.stderr or "")[-4000:],
            }
        except subprocess.TimeoutExpired:
            return {"ok": False, "returncode": None, "stdout": "", "stderr": "ADB command timed out"}
        except OSError as exc:
            return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}

    @staticmethod
    def _parse_devices(output: str) -> list[dict[str, str]]:
        devices: list[dict[str, str]] = []
        for line in output.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices attached"):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1] in {"device", "offline", "unauthorized", "no permissions", "recovery", "sideload", "bootloader"}:
                devices.append({"serial": parts[0], "state": parts[1], "details": " ".join(parts[2:])})
        return devices

    def diagnose(self) -> dict[str, Any]:
        started = self._clock()
        adb_paths = _candidate_adb_paths()
        report: dict[str, Any] = {
            "schema": "dgm-mat.usb-recovery.v1",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "adb_found": bool(adb_paths),
            "adb_path": str(adb_paths[0]) if adb_paths else None,
            "devices": [],
            "checks": [],
            "safe_repairs_available": ["restart-adb-server", "reconnect-offline"],
            "destructive_actions_performed": [],
        }
        if not adb_paths:
            report["checks"].append({
                "id": "adb-installed", "status": "failed",
                "detail": "ADB não encontrado. Instalar Android platform-tools ou definir DGM_ADB_PATH.",
            })
            report["elapsed_ms"] = int((self._clock() - started) * 1000)
            return report

        adb = adb_paths[0]
        version = self._run(adb, "version")
        report["adb_version"] = version["stdout"].strip() or version["stderr"].strip()
        report["checks"].append({
            "id": "adb-server", "status": "ok" if version["ok"] else "warning",
            "detail": report["adb_version"] or version["stderr"],
        })

        devices_result = self._run(adb, "devices", "-l")
        report["devices"] = self._parse_devices(devices_result["stdout"])
        report["checks"].append({
            "id": "usb-device", "status": "ok" if any(d["state"] == "device" for d in report["devices"]) else "warning",
            "detail": "Dispositivo autorizado detetado." if any(d["state"] == "device" for d in report["devices"]) else "Sem dispositivo ADB autorizado; confirmar cabo, depuração USB e autorização no ecrã do telemóvel.",
        })

        for device in report["devices"]:
            if device["state"] != "device":
                continue
            serial = device["serial"]
            package = self._run(adb, "-s", serial, "shell", "pm", "path", PACKAGE_ID)
            device["app_installed"] = package["ok"] and "package:" in package["stdout"]
            device["package_id"] = PACKAGE_ID
            report["checks"].append({
                "id": "mobile-app:" + serial,
                "status": "ok" if device["app_installed"] else "warning",
                "detail": "APK instalado." if device["app_installed"] else "DGM-MAT não parece estar instalado neste dispositivo.",
            })
        report["elapsed_ms"] = int((self._clock() - started) * 1000)
        return report

    def repair(self, action: str, *, confirm_install: bool = False) -> dict[str, Any]:
        """Run one explicit allowlisted repair; never wipe app or device data."""
        adb_paths = _candidate_adb_paths()
        if not adb_paths:
            return {"status": "blocked", "action": action, "reason": "ADB não encontrado."}
        adb = adb_paths[0]
        if action == "restart-adb-server":
            stop = self._run(adb, "kill-server")
            time.sleep(0.5)
            start = self._run(adb, "start-server")
            return {
                "status": "success" if start["ok"] else "failed",
                "action": action,
                "steps": [
                    {"step": "stop-server", "ok": stop["ok"], "detail": stop["stderr"] or stop["stdout"]},
                    {"step": "start-server", "ok": start["ok"], "detail": start["stderr"] or start["stdout"]},
                ],
                "data_preserved": True,
            }
        if action == "reconnect-offline":
            result = self._run(adb, "reconnect", "offline")
            return {
                "status": "success" if result["ok"] else "failed",
                "action": action,
                "detail": result["stdout"] or result["stderr"],
                "data_preserved": True,
            }
        if action == "install-apk":
            if not confirm_install:
                return {"status": "confirmation_required", "action": action, "reason": "A reinstalação substitui a aplicação; é necessária confirmação explícita. Os dados da aplicação serão preservados com -r."}
            candidates = []
            if os.getenv("DGM_MOBILE_APK_PATH"):
                candidates.append(Path(os.environ["DGM_MOBILE_APK_PATH"]))
            root = Path(__file__).resolve().parents[2]
            candidates.extend([
                root.parent / "DGM-MAT-Mobile" / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk",
                root / "artifacts" / "DGM-MAT-Mobile-debug.apk",
            ])
            apk = next((p.resolve() for p in candidates if p.is_file() and p.suffix.casefold() == ".apk"), None)
            if apk is None:
                return {"status": "blocked", "action": action, "reason": "Não foi encontrado um APK de diagnóstico/reparação. Gerar primeiro o APK validado.", "data_preserved": True}
            devices = self._parse_devices(self._run(adb, "devices", "-l")["stdout"])
            targets = [d for d in devices if d["state"] == "device"]
            if len(targets) != 1:
                return {"status": "blocked", "action": action, "reason": "É necessário exatamente um dispositivo ADB autorizado para evitar instalar no dispositivo errado.", "device_count": len(targets), "data_preserved": True}
            result = self._run(adb, "-s", targets[0]["serial"], "install", "-r", str(apk), timeout=180)
            return {
                "status": "success" if result["ok"] and "success" in result["stdout"].casefold() else "failed",
                "action": action,
                "device": targets[0]["serial"],
                "detail": result["stdout"] or result["stderr"],
                "data_preserved": True,
                "apk": str(apk),
            }
        return {"status": "blocked", "action": action, "reason": "Ação não permitida."}


usb_recovery_service = UsbRecoveryService()
