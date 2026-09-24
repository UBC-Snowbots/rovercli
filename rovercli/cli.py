import argparse

from .commands import print_ip_table, sync, time_sync


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