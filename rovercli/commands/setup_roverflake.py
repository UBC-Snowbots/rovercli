from pathlib import Path
import subprocess, os
import yaml
from string import Template

ROVERFLAKE_GIT = "https://github.com/UBC-Snowbots/RoverFlake2.git"

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
APT_PKG_LISTS_DIR = PACKAGE_ROOT / "apt_pkg_lists"
SETUP_SCRIPTS_DIR = PACKAGE_ROOT / "setup_scripts"
ROVER_ENV_DIR = SETUP_SCRIPTS_DIR / "rover_env"
ROS_INSTALL = SETUP_SCRIPTS_DIR / "install-ros2.sh"

class ShellTemplate(Template):
    delimiter = "@@"  # unlikely to collide with bash's own $VAR / ${VAR} syntax

def input_loop(prompt: str, valid_responses: list[str]) -> str:
    while True:
        response = input(prompt)
        if response in valid_responses:
            return response
        print(f"Invalid response. Please enter one of: {', '.join(valid_responses)}")

def setup_roverflake(dst: Path, pkg_list_files: list[Path], setup_scripts: list[Path], distro: str):
    """
    Sets up the Roverflake environment.
    """

    os.environ["ROS_DISTRO"] = distro
    print("Setting up Ros and RoverFlake!\n")
    r = input_loop("Would you like to install 1: ros base (no rviz, etc) or 2: ros desktop?: ", ["1", "2"])
    if r == "1":
        os.environ["ROS_INSTALL"] = f"ros-{distro}-ros-base"
    elif r == "2":
        os.environ["ROS_INSTALL"] = f"ros-{distro}-desktop"

    print(f"Selected ROS installation: {os.environ['ROS_INSTALL']}")

    r = input_loop("Would you like to cd into RoverFlake directory on startup? (useful for onboard computers) [y/n]: ", ["y", "n"])
    cd_roverflake = True if r == "y" else False

    install_apt_pkgs(pkg_list_files, distro, "pkgs_start")
    if dst.exists():
        print(f"Destination {dst} already exists.")
    else:
        input(f"Destination {dst} does not exist. Press Enter to create and clone RoverFlake into it.")
        dst.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(["git", "clone", ROVERFLAKE_GIT, str(dst)], check=True)
        check_result(result, "Failed to clone RoverFlake repository.")

    os.environ["ROVERFLAKE_ROOT"] = str(dst)
    setup_scripts = [ROS_INSTALL, *setup_scripts]
    for script in setup_scripts:
        result = subprocess.run(["bash", str(script)], check=True)
        check_result(result, f"Failed to run setup script: {script}")

    install_apt_pkgs(pkg_list_files, distro, "pkgs_after_ros")

    render_roverrc(dst, distro, ROVER_ENV_DIR / ".roverrc.template", Path.home() / ".roverrc", cd_to_roverflake=cd_roverflake)
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

def install_apt_pkgs(pkg_list_files: list[Path], distro: str, key: str):
    all_pkgs = []
    for file in pkg_list_files:
        with open(file, "r") as f:
            data = yaml.safe_load(f)
            all_pkgs.extend(data.get(key, []))

    if all_pkgs:
        result = subprocess.run(["sudo", "-v"], check=True)
        check_result(result, "Failed to obtain sudo privileges.")
        result = subprocess.run(["sudo", "apt", "update"], check=True)
        check_result(result, "Failed to update APT package list.")
        all_pkgs = [str(s).replace("${ROS_DISTRO}", distro) for s in all_pkgs]
        result = subprocess.run(["sudo", "apt", "install", "-y", *all_pkgs], check=True)
        check_result(result, "Failed to install APT packages.")

def check_result(result: subprocess.CompletedProcess, error_message: str):
    if result.returncode != 0:
        raise RuntimeError(error_message)

def render_roverrc(dst_root: Path, ros_distro: str, template_path: Path, out_path: Path, cd_to_roverflake: bool = False):
    text = template_path.read_text()
    cd_to_roverflake = "cd $ROVERFLAKE_ROOT" if cd_to_roverflake else "" 
    rendered = ShellTemplate(text).substitute(
        ROVERFLAKE_ROOT=str(dst_root), 
        ROVERCLI_ROOT=str(PACKAGE_ROOT), 
        ROS_DISTRO=ros_distro,
        CD_TO_RF=cd_to_roverflake
    )
    out_path.write_text(rendered)
    out_path.chmod(0o644)
