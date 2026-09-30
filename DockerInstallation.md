# Docker setup for RoverFlake2

Install Docker with the Compose plugin. The container uses Ubuntu 24.04 and ROS
Jazzy on every host; Fedora and macOS do not need ROS installed on the host.

From the rovercli, `rovercli docker` detects the host and starts the
matching `rover` service, then opens a shell in it. Use
`rovercli docker --rebuild` to force an image rebuild. By default, Compose reuses
an existing image and builds if it is missing. Windows and macOS use Docker
Desktop configurations; Fedora uses its SELinux-aware configuration.
For local RoverFlake2 development, pass the path to a host checkout with
`rovercli docker --roverflake-path <path-to-RoverFlake2>`. The checkout is
bind-mounted at `/RoverFlake2`, so edits are visible in the container. Without
this option, Docker continues to use its persistent named workspace volume.
To immediately kill all running containers on the active Docker daemon and exit
without starting Rover, use `rovercli docker --kill-all`. This also kills
containers unrelated to Rover.
On Linux desktops with a local X11 display, `rovercli docker` uses `xhost` to
grant the container's root user display access before opening the container.

## Windows

Docker Desktop uses the Windows-specific configuration automatically. It uses
standard Docker networking and does not configure GUI forwarding or USB/CAN
device access. Use a Linux host for rover hardware access or ROS discovery that
depends on host networking. For example, in PowerShell:

```powershell
rovercli docker --roverflake-path C:\Users\you\Github\Rover\RoverFlake2
```

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

The image runs `rovercli setup` during the build to install ROS Jazzy and clone
RoverFlake2. Compose stores that workspace in a named volume so it is not
masked by the rovercli checkout and changes persist across container restarts.
The entrypoint sources ROS Jazzy and attempts a workspace build when no
`install/setup.bash` exists. To discard the persisted workspace and seed a fresh
clone from a rebuilt image, run `docker compose down -v` before bringing it up.
