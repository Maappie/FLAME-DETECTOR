# system_start.py — Windows launcher (PowerShell), runs modules so package imports work.
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional, Sequence

# --- Modules to run (module, args...) in the order you want ---
TARGETS: Sequence[Sequence[str]] = [
    ["scripts.flame_detection.main"],                 # python -m scripts.flame_detection.main
    ["scripts.system_setup.broker_start", "run"],     # python -m scripts.system_setup.broker_start run
    ["scripts.system_setup.record_mqtt"],             # python -m scripts.system_setup.record_mqtt
    ["scripts.flame_detection.stream"],               # python -m scripts.flame_detection.stream
]

LAUNCH_DELAY_SEC = 0.3  # small stagger so windows open cleanly


def find_repo_root(start: Path) -> Path:
    """Assume this file lives under .../FLAME-DETECTOR/scripts/system/... -> go up to repo root."""
    # system_start.py path examples:
    #   C:\Users\Renz\CODES\FLAME-DETECTOR\scripts\system\system_start.py
    # repo root is parents[2] from there
    return start.resolve().parents[2]


def find_repo_venv_python(start: Path) -> Optional[Path]:
    """Walk upward from start to find .venv\\Scripts\\python.exe"""
    for p in [start, *start.parents]:
        cand = p / ".venv" / "Scripts" / "python.exe"
        if cand.exists():
            return cand
    return None


def run_module_in_new_powershell(python_exe: Path, repo_root: Path, module: str, *args: str) -> None:
    """Open a new PowerShell window, cd to repo root, run 'python -m module [args...]', keep window open."""
    py = str(python_exe)
    mod = module
    arglist = " ".join(f"'{a}'" for a in args)
    cmd = f"& '{py}' -m {mod} {arglist}".rstrip()

    ps_cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-NoExit",
        "-Command",
        f"Set-Location -LiteralPath '{repo_root}'; {cmd}"
    ]
    subprocess.Popen(ps_cmd, cwd=str(repo_root))


def main() -> None:
    here = Path(__file__).resolve()
    repo_root = find_repo_root(here)
    venv_python = find_repo_venv_python(repo_root)
    python_exe = venv_python if venv_python else Path(sys.executable)

    # Sanity: require package layout
    for pkg in [repo_root / "scripts" / "__init__.py",
                repo_root / "scripts" / "flame_detection" / "__init__.py",
                repo_root / "scripts" / "system_setup" / "__init__.py"]:
        if not pkg.exists():
            print(f"[WARN] Missing {pkg}. Create empty __init__.py so package imports work.")

    for target in TARGETS:
        run_module_in_new_powershell(python_exe, repo_root, *target)
        time.sleep(LAUNCH_DELAY_SEC)

    print(f"Launched {len(TARGETS)} PowerShell windows using: {python_exe}")
    print(f"[cwd] {repo_root}")


if __name__ == "__main__":
    main()
