# `rovercli`
A command line interface and Textual TUI for UBC Rover operations.

# Installation
From the repository root, install the package:

```sh
python -m pip install -e . --break-system-packages
```

This installs Textual and creates the `rovercli` terminal command. Running
`rovercli` without arguments opens the TUI.


# Commands
## `setup`

This command sets up the RoverFlake2 repo.

```sh
rovercli setup --distro jazzy
```

## `tui`

```sh
rovercli
rovercli tui
```

## `sync`
Sync files between devices on the UBC Rover network, without unecessary copying of files that haven't changed.

```
rovercli sync --src-root RoverFlake2 --dst-root RoverFlake2 --remote-host rv@192.168.1.4
```

Other commands are `rovercli print-ip-table` and `rovercli time-sync`.