import os
import subprocess
from pathlib import Path
from typing import Optional

import yaml


def sync(
    src: str,
    dst: str,
    remote_host: str,
    packages: Optional[list[str]] = None,
    build: bool = True,
    external_pkgs: bool = True,
    package_list: Optional[str] = None,
):
    src_path = Path.home() / src
    dst_root = Path("~") / dst
    dst_path = dst_root / "src" if packages else dst_root
    print(f"Syncing from {src_path} to {remote_host}:{dst_path} with build={build} and packages={packages}")

    src_dir = src_path / "src"
    if not src_dir.exists():
        raise ValueError(f"Source directory '{src_dir}' does not exist.")

    rsync_cmd = ["rsync", "-azc", "--stats"]
    if packages or package_list:
        if external_pkgs:
            external_packages = src_dir / "external_pkgs"
            if external_packages.exists():
                rsync_cmd.append(str(external_packages))
        if package_list:
            with open(package_list) as package_file:
                listed_packages = yaml.safe_load(package_file)["packages"]
            packages = (packages or []) + listed_packages
        for package in packages or []:
            package_path = src_dir / package
            if not package_path.exists():
                raise ValueError(f"Package directory '{package}' does not exist.")
            rsync_cmd.append(str(package_path))
    else:
        rsync_cmd.extend(["--delete", str(src_dir)])

    rsync_cmd.append(f"{remote_host}:{dst_path}")
    print(f"Running rsync command: {' '.join(rsync_cmd)}")
    if subprocess.run(rsync_cmd).returncode != 0:
        raise RuntimeError("Rsync src transfer failed")

    metadata_command = ["rsync", "-azc", "--stats"]
    for filename in ("colcon.defaults.yaml", "colcon.meta"):
        metadata_file = src_path / filename
        if metadata_file.exists():
            metadata_command.append(str(metadata_file))
    metadata_command.append(f"{remote_host}:{dst_root}")
    if len(metadata_command) > 4 and subprocess.run(metadata_command).returncode != 0:
        raise RuntimeError("Rsync meta transfer failed")

    print("Source transfer complete!")
    if not build:
        return

    ros_distro = os.environ.get("ROS_DISTRO")
    if not ros_distro:
        raise ValueError("ROS_DISTRO environment variable is not set.")

    env = os.environ.copy()
    env["MAKEFLAGS"] = "-j3"
    remote_command = (
        f"cd {dst_root}; source /opt/ros/{ros_distro}/setup.bash && colcon build "
        f"--base-paths {dst_root / 'src'} --build-base {dst_root / 'build'} "
        f"--install-base {dst_root / 'install'} --symlink-install"
    )
    if packages:
        remote_command += f" --packages-select {' '.join(packages)}"
    if subprocess.run(["ssh", remote_host, remote_command], env=env).returncode != 0:
        raise RuntimeError("Remote build failed")