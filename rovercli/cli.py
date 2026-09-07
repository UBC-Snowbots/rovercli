import argparse
from pathlib import Path

from .commands import print_ip_table, setup_roverflake, sync, time_sync
from .commands.setup_roverflake import APT_PKG_LISTS_DIR, SETUP_SCRIPTS_DIR


def build_parser():
    parser = argparse.ArgumentParser(description="Rover Command Line Interface")
    subparsers = parser.add_subparsers(dest="command")

    sync_parser = subparsers.add_parser("sync", help="Sync files to a rover computer")
    sync_parser.add_argument("--src-root", default="RoverFlake2")
    sync_parser.add_argument("--dst-root", default="RoverFlake2")
    sync_parser.add_argument("--remote-host", default="rv@192.168.1.4")
    sync_parser.add_argument("--no-build", action="store_true")
    sync_parser.add_argument("--packages", nargs="+", default=None)
    sync_parser.add_argument("--package-list", type=str, default=None)
    sync_parser.add_argument("--no-external-pkgs", action="store_true")
    sync_parser.set_defaults(func=_run_sync)

    setup_parser = subparsers.add_parser("setup", help="Set up the RoverFlake environment on this machine")
    setup_parser.add_argument("--dst", default="RoverFlake2", help="Destination directory, relative to home")
    setup_parser.add_argument("--distro", required=True, help="ROS distro to install (e.g. jazzy)")
    setup_parser.add_argument(
        "--apt-pkg-list",
        nargs="+",
        default=["base", "perceptions"],
        help="Names (without .yaml) of apt package lists from apt_pkg_lists/ to install",
    )
    setup_parser.add_argument(
        "--setup-script",
        nargs="+",
        default=["update_submodules.sh", "install-ros2-base.sh", "install_rosdeps.sh", "install_phidgets.sh"],
        help="Names of setup scripts from setup_scripts/ to run, in order",
    )
    setup_parser.set_defaults(func=_run_setup)

    ip_parser = subparsers.add_parser("print-ip-table", help="Print rover network addresses")
    ip_parser.set_defaults(func=lambda args: print_ip_table())

    time_parser = subparsers.add_parser("time-sync", help="Synchronize time with a rover computer")
    time_parser.add_argument("--remote-host", default="rover")
    time_parser.set_defaults(func=lambda args: time_sync(remote_host=args.remote_host))

    tui_parser = subparsers.add_parser("tui", help="Open the Textual interface")
    tui_parser.set_defaults(func=lambda args: _run_tui())
    return parser


def _run_sync(args):
    sync(
        args.src_root,
        args.dst_root,
        remote_host=args.remote_host,
        build=not args.no_build,
        packages=args.packages,
        external_pkgs=not args.no_external_pkgs,
        package_list=args.package_list,
    )


def _run_setup(args):
    pkg_list_files = [APT_PKG_LISTS_DIR / f"{name}.yaml" for name in args.apt_pkg_list]
    setup_scripts = [SETUP_SCRIPTS_DIR / name for name in args.setup_script]
    setup_roverflake(Path.home() / args.dst, pkg_list_files, setup_scripts, args.distro)


def _run_tui():
    from .tui import run_tui

    run_tui()


def main():
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        _run_tui()


if __name__ == "__main__":
    main()