# Docker setup for RoverFlake2

Install Docker with the Compose plugin. The container uses Ubuntu 24.04 and ROS
Jazzy on every host; Fedora and macOS do not need ROS installed on the host.

From the rovercli, `rovercli docker` detects the host and starts the
matching `rover` service, then opens a shell in it. Use
`rovercli docker --rebuild` to force an image rebuild. By default, Compose reuses
an existing image and builds if it is missing. Windows, WSL, and macOS use
separate Docker Desktop configurations; Fedora uses its SELinux-aware configuration.
For local RoverFlake2 development, pass the path to a host checkout with
`rovercli docker --roverflake-path <path-to-RoverFlake2>`. The checkout is
bind-mounted at `/RoverFlake2`, so edits are visible in the container. If a
`RoverFlake2` checkout sits beside the `rovercli` checkout, the CLI uses it
automatically. Otherwise it uses the persistent named workspace volume.
Checkout-backed containers have a separate name for each checkout, so an
existing named-volume container cannot hide the bind mount.
Restart a MoveIt launch to reload changes to its robot description; rebuild the
workspace inside the container when new files or packages are added.
To immediately kill all running containers on the active Docker daemon and exit
without starting Rover, use `rovercli docker --kill-all`. This also kills
containers unrelated to Rover.
On Linux desktops with a local X11 display, `rovercli docker` uses `xhost` to
grant the container's root user display access before opening the container.

## Windows

Docker Desktop uses the Windows-specific configuration when `rovercli docker`
runs from PowerShell. It uses standard Docker networking and does not configure
GUI forwarding or USB/CAN device access. For command-line ROS tools, run:

```powershell
rovercli docker
```

For `rviz2` on Windows, use a WSL 2 distribution with WSLg and enable that
distribution under Docker Desktop's **Settings > Resources > WSL Integration**.
Install `rovercli` inside that distribution, then run `rovercli docker` from
its terminal. The WSL configuration passes the
WSLg X11 socket and `DISPLAY` to the container. Test `rviz2` on the target
machine; accelerated graphics and hardware access depend on its WSL setup.
The PowerShell configuration does not provide that GUI connection.

## Fedora

The Fedora Compose file uses the host network, `/dev`, and the X11 socket for
rover hardware and GUI access. If your desktop uses Wayland, Xwayland must be
running and `DISPLAY` must be set. `rovercli docker` grants the container's
root user X11 access automatically when `xhost` is available. For manual
Compose use, grant access on the host before starting a GUI application:

```sh
xhost +si:localuser:root
docker compose -f docker-compose.fedora.yml up -d --build rover
docker compose -f docker-compose.fedora.yml exec rover bash
```

## macOS (Intel or Apple Silicon)

Docker Desktop runs this Linux image as amd64 on Intel Macs and arm64 on Apple
Silicon. Start the container with:

```sh
docker compose -f docker-compose.macos.yml up -d --build rover
docker compose -f docker-compose.macos.yml exec rover bash
```

For Linux GUI windows on macOS, install and start XQuartz, enable **Allow
connections from network clients** in its settings, restart XQuartz, then run
`xhost +localhost` on the Mac before starting the container. The Compose file
routes `DISPLAY` through `host.docker.internal`. Docker Desktop does not pass
through the host's USB or CAN devices, so hardware nodes need a Linux host.

On the first container start, the entrypoint runs `rovercli setup` to install
ROS Jazzy and clone RoverFlake2 into its workspace volume. With
`--roverflake-path`, it uses the supplied checkout instead. The entrypoint then
sources ROS Jazzy and attempts a workspace build when no
`install/setup.bash` exists. The named volume keeps the checkout across
container restarts.
