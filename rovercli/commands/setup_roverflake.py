from pathlib import Path
import subprocess, os
import yaml
from string import Template

ROVERFLAKE_GIT = "https://github.com/UBC-Snowbots/RoverFlake2.git"

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
APT_PKG_LISTS_DIR = PACKAGE_ROOT / "apt_pkg_lists"
SETUP_SCRIPTS_DIR = PACKAGE_ROOT / "setup_scripts"
ROVER_ENV_DIR = SETUP_SCRIPTS_DIR / "rover_env"

class ShellTemplate(Template):
    delimiter = "@@"  # unlikely to collide with bash's own $VAR / ${VAR} syntax

def setup_roverflake(dst: Path, pkg_list_files: list[Path], setup_scripts: list[Path], distro: str):
    """
    Sets up the Roverflake environment.
    """

    os.environ["ROS_DISTRO"] = distro

    input("Installing apt packages... Press Enter to continue.")
    install_apt_pkgs(pkg_list_files)

    if dst.exists():
        print(f"Destination {dst} already exists.")
    else:
        input(f"Destination {dst} does not exist. Press Enter to create and clone RoverFlake into it.")
        dst.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(["git", "clone", ROVERFLAKE_GIT, str(dst)], check=True)
        check_result(result, "Failed to clone RoverFlake repository.")

    os.environ["ROVERFLAKE_ROOT"] = str(dst)

    input("Running setup scripts... Press Enter to continue.")
    for script in setup_scripts:
        result = subprocess.run(["bash", str(script)], check=True)
        check_result(result, f"Failed to run setup script: {script}")

    render_roverrc(dst, distro, ROVER_ENV_DIR / ".roverrc.template", Path.home() / ".roverrc")
    ensure_bashrc_sources_roverrc(Path.home() / ".bashrc", Path.home() / ".roverrc")

    print("RoverFlake setup complete.")
    print("Make sure to resource your .bashrc or open a new terminal session.")
    print("source ~/.bashrc")

def ensure_bashrc_sources_roverrc(bashrc_path: Path, roverrc_path: Path):
    source_line = f"source {roverrc_path}"
    existing = bashrc_path.read_text() if bashrc_path.exists() else ""
    if source_line in existing.splitlines():
        return
    with open(bashrc_path, "a") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write(f"{source_line}\n")

def install_apt_pkgs(pkg_list_files: list[Path]):
    all_pkgs = []
    for file in pkg_list_files:
        with open(file, "r") as f:
            data = yaml.safe_load(f)
            all_pkgs.extend(data.get("pkgs", []))

    if all_pkgs:
        result = subprocess.run(["sudo", "-v"], check=True)
        check_result(result, "Failed to obtain sudo privileges.")
        result = subprocess.run(["sudo", "apt", "update"], check=True)
        check_result(result, "Failed to update APT package list.")
        result = subprocess.run(["sudo", "apt", "install", "-y", *all_pkgs], check=True)
        check_result(result, "Failed to install APT packages.")

def check_result(result: subprocess.CompletedProcess, error_message: str):
    if result.returncode != 0:
        raise RuntimeError(error_message)

def render_roverrc(dst_root: Path, ros_distro: str, template_path: Path, out_path: Path):
    text = template_path.read_text()
    rendered = ShellTemplate(text).substitute(ROVERFLAKE_ROOT=str(dst_root), ROVERCLI_ROOT=str(PACKAGE_ROOT), ROS_DISTRO=ros_distro)
    out_path.write_text(rendered)
    out_path.chmod(0o644)
