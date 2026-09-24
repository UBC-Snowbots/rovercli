# `rovercli`
A command line interface and Textual TUI for UBC Rover operations.

# Installation
From the repository root, install the package in a virtual environment:

```sh
python -m pip install -e .
```

This installs Textual and creates the `rovercli` terminal command. Running
`rovercli` without arguments opens the TUI.

# Commands
## TUI

```sh
rovercli
rovercli tui
```

## `sync`
Sync files between devices on the UBC Rover network, without unecessary copying of files that haven't changed.

### Usage

```
rovercli sync --src-root RoverFlake2 --dst-root RoverFlake2 --remote-host rv@192.168.1.4
```

Other commands are `rovercli print-ip-table` and `rovercli time-sync`.