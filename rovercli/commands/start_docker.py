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


def _container_state(container: str) -> Optional[str]:
    result = subprocess.run(
        ["docker", "container", "inspect", "--format", "{{.State.Running}}", container],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _enter_container(container: str, running: bool):
    print(f"Entering existing {container} container...", flush=True)
    if running:
        subprocess.run(["docker", "exec", "--interactive", "--tty", container, "bash"], check=True)
    else:
        subprocess.run(["docker", "start", "--attach", "--interactive", container], check=True)


def _allow_local_x11_root():
    if platform.system() != "Linux" or not os.environ.get("DISPLAY", "").startswith(":"):
        return
    if os.environ.get("WSL_DISTRO_NAME") or "microsoft" in platform.release().lower():
        return
    if shutil.which("xhost"):
        result = subprocess.run(["xhost", "+si:localuser:root"], check=False)
        if result.returncode != 0:
            print("Could not grant Docker access to the X11 display; GUI apps may fail.", file=sys.stderr)
    else:
        print("xhost is unavailable; GUI apps in Docker may fail.", file=sys.stderr)


def start_docker(build: bool = False, kill_all: bool = False, roverflake_path: Optional[Path] = None, container: Optional[str] = None):
    if container is not None and (kill_all or build or roverflake_path is not None):
        raise ValueError("--container cannot be combined with --kill-all, --rebuild, or --roverflake-path")
    if kill_all:
        kill_all_containers()
        return
    if container is not None:
        state = _container_state(container)
        if state is None:
            raise ValueError(f"Docker container {container!r} does not exist")
        _allow_local_x11_root()
        _enter_container(container, running=state == "true")
        return

    env = os.environ.copy() if roverflake_path is not None else None
    if roverflake_path is not None:
        roverflake_path = roverflake_path.expanduser().resolve()
        if not roverflake_path.is_dir():
            raise NotADirectoryError(f"RoverFlake2 path is not a directory: {roverflake_path}")
        env["ROVERFLAKE_PATH"] = str(roverflake_path)
    compose_filename = _compose_filename()
    package_root = Path(__file__).resolve().parents[2]
    compose_file = package_root / "docker" / compose_filename
    if not compose_file.is_file():
        raise FileNotFoundError(f"Could not find {compose_filename}; run rovercli docker from the rovercli checkout.")

    compose = ["docker", "compose", "-f", str(compose_file)]
    if roverflake_path is not None:
        dev_compose_file = compose_file.parent / "docker-compose.dev.yml"
        if not dev_compose_file.is_file():
            raise FileNotFoundError(f"Could not find {dev_compose_file}.")
        compose.extend(["-f", str(dev_compose_file)])

    _allow_local_x11_root()

    container_name = "rovercli-rover-wsl" if compose_filename == "docker-compose.wsl.yml" else "rovercli-rover"
    state = _container_state(container_name)
    if state is not None:
        if build:
            subprocess.run(["docker", "rm", "--force", container_name], check=True)
        else:
            _enter_container(container_name, running=state == "true")
            return

    run_command = [*compose, "run", "--name", container_name]
    if build:
        run_command.append("--build")
    run_command.extend(["rover", "bash"])

    print(f"Starting rover with {compose_filename}...", flush=True)
    subprocess.run(run_command, cwd=compose_file.parent, check=True, env=env)
