import platform
import subprocess
from pathlib import Path


def _compose_filename() -> str:
    system = platform.system()
    if system == "Windows":
        return "docker-compose.windows.yml"
    if system == "Darwin":
        return "docker-compose.macos.yml"
    if system == "Linux":
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


def start_docker(build: bool = False, kill_all: bool = False):
    if kill_all:
        kill_all_containers()
        return

    compose_filename = _compose_filename()
    package_root = Path(__file__).resolve().parents[2]
    compose_file = package_root / compose_filename
    if not compose_file.is_file():
        compose_file = Path.cwd() / compose_filename
    if not compose_file.is_file():
        raise FileNotFoundError(f"Could not find {compose_filename}; run rovercli docker from the rovercli checkout.")

    compose = ["docker", "compose", "-f", str(compose_file)]
    up_command = [*compose, "up", "-d"]
    if build:
        up_command.append("--build")
    up_command.append("rover")

    print(f"Starting rover with {compose_filename}...", flush=True)
    subprocess.run(up_command, cwd=compose_file.parent, check=True)
    subprocess.run([*compose, "exec", "rover", "bash"], cwd=compose_file.parent, check=True)