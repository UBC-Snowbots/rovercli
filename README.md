# `rovercli`
A command line interface and Textual TUI for UBC Rover operations.

# Installation
From the repository root, install the package:

```sh
python -m pip install -e . --break-system-packages
```

This installs Textual and creates the `rovercli` terminal command. Running
`rovercli` without arguments opens the TUI.

If `rovercli` is not already on your PATH, run the setup script after
installation. It detects whether zsh or bash is being used and updates the
corresponding shell configuration file:

```sh
bash rovercli/setup_scripts/add-rovercli-to-path.sh
```

To update the current shell immediately, source the script instead:

```sh
source rovercli/setup_scripts/add-rovercli-to-path.sh
```


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