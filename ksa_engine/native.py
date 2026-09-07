from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def executable_path() -> Path | None:
    configured = os.environ.get("KSA_ENGINE_NATIVE")
    candidates = [Path(configured)] if configured else []
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    candidates.extend(
        [
            root / "ksa_engine_cpp.exe",
            root / "ksa_engine_cpp",
            root / "build" / "native" / "ksa_engine_cpp.exe",
            root / "build" / "native" / "ksa_engine_cpp",
            root / "build" / "native" / "Release" / "ksa_engine_cpp.exe",
        ]
    )
    return next((candidate for candidate in candidates if candidate and candidate.is_file()), None)


def run_native(description: str, seconds: float, seed: int | None, as_json: bool) -> bool:
    executable = executable_path()
    if executable is None:
        return False

    command = [str(executable), description, "--seconds", str(seconds)]
    if seed is not None:
        command.extend(["--seed", str(seed)])
    if as_json:
        command.append("--json")
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"native runtime exited with status {completed.returncode}")
    return True
