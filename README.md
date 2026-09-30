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

## `docker`
Start the Docker Compose `rover` service using the configuration selected for
the host OS, then open a shell in the container:

```sh
rovercli docker
```

By default, an existing image is reused and Compose builds it if it is missing.
The first container start installs ROS and RoverFlake2. Pass `--rebuild` to
rebuild the image, or `--roverflake-path <path-to-RoverFlake2>` to use a local
checkout. Use `rovercli docker --container <name-or-id>` to enter an existing
container without building an image. Pass `--kill-all` to kill every running
container on the active Docker daemon; this also affects containers unrelated
to Rover. See
[DockerInstallation.md](DockerInstallation.md) for host-specific GUI setup.
