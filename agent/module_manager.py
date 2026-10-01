import json
import shutil
import subprocess
from pathlib import Path


REPO = Path("/opt/iot-platform")
MODULES = Path("/opt/iot/modules")
STATE = Path("/opt/iot-agent/current.json")


def sh(*args):
    return subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
    )


def load_current():
    if not STATE.exists():
        return {}

    return json.loads(STATE.read_text())


def save_current(current):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(
        json.dumps(current, indent=2)
    )


def install(name, version):
    # 1. Daftarkan HANYA modul spesifik ini agar diunduh oleh Git
    sh(
        "git",
        "-C",
        str(REPO),
        "sparse-checkout",
        "add",
        f"modules/{name}",
    )

    # 2. Tarik kode modul spesifik tersebut
    sh(
        "git",
        "-C",
        str(REPO),
        "pull",
        "--ff-only",
    )

    src = REPO / "modules" / name
    dst = MODULES / name

    if not src.exists():
        raise RuntimeError(
            f"Module '{name}' does not exist in repository"
        )

    dst.parent.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        src,
        dst,
        dirs_exist_ok=True,
    )

    sh(
        "python3",
        "-m",
        "venv",
        str(dst / "venv"),
    )

    req = dst / "requirements.txt"

    if req.exists():
        sh(
            str(dst / "venv/bin/pip"),
            "install",
            "-r",
            str(req),
        )

    sh(
        "systemctl",
        "enable",
        "--now",
        f"iot-module@{name}",
    )


def remove(name):
    subprocess.run(
        [
            "systemctl",
            "disable",
            "--now",
            f"iot-module@{name}",
        ],
        check=False,
    )

    shutil.rmtree(
        MODULES / name,
        ignore_errors=True,
    )

    # Bersihkan checkout modul dari /opt/iot-platform agar hemat disk
    try:
        current_modules = list(load_current().keys())
        # Susun ulang daftar folder yang di-checkout
        allowed_paths = ["agent", "scripts", "systemd"] + [f"modules/{m}" for m in current_modules if m != name]
        sh("git", "-C", str(REPO), "sparse-checkout", "set", *allowed_paths)
    except Exception:
        pass


def reconcile(desired, report):
    current = load_current()

    wanted = {
        module["name"]: module
        for module in desired.get("modules", [])
        if module.get("enabled", True)
    }

    # Install / update modules
    for name, module in wanted.items():
        version = module["version"]

        if current.get(name) == version:
            continue

        report(
            name,
            version,
            "installing",
        )

        try:
            install(name, version)

            current[name] = version
            save_current(current)

            report(
                name,
                version,
                "success",
            )

        except Exception as exc:
            report(
                name,
                version,
                "failed",
                str(exc),
            )

    # Remove modules no longer in desired state
    for name in list(current):
        if name not in wanted:
            remove(name)

            del current[name]
            save_current(current)

            report(
                name,
                "-",
                "removed",
            )
