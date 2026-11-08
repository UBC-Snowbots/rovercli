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
bash ./add-rovercli-to-path.sh
```

To update the current shell immediately, source the script instead:

```sh
source ./add-rovercli-to-path.sh
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

## `moteus-save-config`
Save the connected moteus configuration as one file per CAN ID in the
`motor_config` directory:

```sh
rovercli moteus-save-config --name <name>
```

The `--name` option is optional; when omitted, saved files use `unnamed` in
their filenames.

## `moteus-calibrate`

Calibrate the moteus controllers configured in a YAML file. When omitted, the
command uses `motor_config/calibration.yaml`. The YAML maps each CAN ID to a
list of calibration parameters. Before calibrating, the command discovers
connected controllers with `moteus_tool --info` and skips configured IDs that
are not available.

```sh
rovercli moteus-calibrate
rovercli moteus-calibrate path/to/calibration.yaml
```

For example:

```yaml
1:
  - "--cal-force-kv 339"
```

Each attempted calibration updates `motor_config/calibration_log.yaml` with
the latest run for that CAN ID: UTC start/finish timestamps, parameters,
success/failure/interruption status, exit code (when available), and the contents
of the JSON report announced by `REPORT:` (stored as nested data in `output`,
not an escaped string). The original
report file is deleted only after its contents have been saved in the calibration
log. Console output is still shown live but is not stored. Entries for other
IDs, including skipped controllers, are preserved. A failed calibration is
logged and stops the command.

## `docker`
Start the Docker Compose `rover` service using the configuration selected for
the host OS, then open a shell in the container:

```sh
rovercli docker
```

By default, an existing image is reused and Compose builds it if it is missing.
Pass `--rebuild` to rebuild the image, or
`--roverflake-path <path-to-RoverFlake2>` to build from and mount a local
checkout. Containers persist after you exit, so later launches reuse the same
container. Use `--container-name <name>` to maintain multiple independent
containers. If multiple named RoverCLI containers exist and no name is
provided, the CLI prompts you to choose one. Pass `--kill-all` to kill every
running container on the active Docker daemon; this also affects containers
unrelated to Rover. See
[DockerInstallation.md](DockerInstallation.md) for host-specific GUI setup.
