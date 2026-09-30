import hashlib
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


def _compose_filename() -> str:
    system = platform.system()
    if system == "Windows":
        return "docker-compose.windows.yml"
    if system == "Darwin":
        return "docker-compose.macos.yml"
    if system == "Linux":
        if os.environ.get("WSL_DISTRO_NAME") or "microsoft" in platform.release().lower():
            return "docker-compose.wsl.yml"
        os_release = Path("/etc/os-release")
        if os_release.exists():
            for line in os_release.read_text().splitlines():
                key, separator, value = line.partition("=")
                if separator and key == "ID" and value.strip('"').lower() == "fedora":
                    return "docker-compose.fedora.yml"
        return "docker-compose.yml"
    raise RuntimeError(f"Docker setup is not configured for {system}.")


def kill_all_containers():
    result = subprocess.run(
        ["docker", "ps", "--quiet"],
        check=True,
        capture_output=True,
        text=True,
    )
    container_ids = result.stdout.split()
    if not container_ids:
        print("No running Docker containers.")
        return

    subprocess.run(["docker", "kill", *container_ids], check=True)
    print(f"Killed {len(container_ids)} running Docker container(s).")


def start_docker(build: bool = False, kill_all: bool = False, roverflake_path: Optional[Path] = None):
    if kill_all:
        kill_all_containers()
        return

    package_root = Path(__file__).resolve().parents[2]
    if roverflake_path is None:
        nearby_checkout = package_root.parent / "RoverFlake2"
        if (nearby_checkout / "src").is_dir():
            roverflake_path = nearby_checkout

    env = os.environ.copy() if roverflake_path is not None else None
    if roverflake_path is not None:
        roverflake_path = roverflake_path.expanduser().resolve()
        if not roverflake_path.is_dir():
            raise NotADirectoryError(f"RoverFlake2 path is not a directory: {roverflake_path}")
        env["ROVERFLAKE_PATH"] = str(roverflake_path)
    compose_filename = _compose_filename()
    compose_file = package_root / "docker" / compose_filename
    if not compose_file.is_file():
        raise FileNotFoundError(f"Could not find {compose_filename}; run rovercli docker from the rovercli checkout.")

    compose = ["docker", "compose", "-f", str(compose_file)]
    if roverflake_path is not None:
        dev_compose_file = compose_file.parent / "docker-compose.dev.yml"
        if not dev_compose_file.is_file():
            raise FileNotFoundError(f"Could not find {dev_compose_file}.")
        compose.extend(["-f", str(dev_compose_file)])

    if compose_filename in ("docker-compose.yml", "docker-compose.fedora.yml") and os.environ.get("DISPLAY", "").startswith(":"):
        if shutil.which("xhost"):
            result = subprocess.run(["xhost", "+si:localuser:root"], check=False)
            if result.returncode != 0:
                print("Could not grant Docker access to the X11 display; GUI apps may fail.", file=sys.stderr)
        else:
            print("xhost is unavailable; GUI apps in Docker may fail.", file=sys.stderr)

    container_name = "rovercli-rover-wsl" if compose_filename == "docker-compose.wsl.yml" else "rovercli-rover"
    if roverflake_path is not None:
        checkout_id = hashlib.sha256(str(roverflake_path).encode()).hexdigest()[:10]
        container_name = f"{container_name}-local-{checkout_id}"
    existing_container = subprocess.run(
        ["docker", "inspect", container_name],
        capture_output=True,
        text=True,
    )
    if existing_container.returncode == 0:
        if build:
            subprocess.run(["docker", "rm", "--force", container_name], check=True)
        else:
            print(f"Entering existing {container_name} container...", flush=True)
            subprocess.run(
                ["docker", "start", "--attach", "--interactive", container_name],
                check=True,
            )
            return

    run_command = [*compose, "run", "--name", container_name]
    if build:
        run_command.append("--build")
    run_command.extend(["rover", "bash"])

    print(f"Starting rover with {compose_filename}...", flush=True)
    subprocess.run(run_command, cwd=compose_file.parent, check=True, env=env)
