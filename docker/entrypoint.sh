#!/bin/bash
set -e

if [ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]; then
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
fi

# build
if [ ! -f "$ROVERFLAKE_ROOT/install/setup.bash" ]; then
  if ! colcon build --symlink-install; then
    echo "WARNING: initial colcon build failed. Container stays up so you can debug." >&2
    if [ ! -f "$ROVERFLAKE_ROOT/src/external_pkgs/moteus/CMakeLists.txt" ]; then
      echo "HINT: git submodules look uninitialized. On the host run: git submodule update --init --recursive" >&2
    fi
  fi
fi
echo "Finished initial setup."
if [ -f "$ROVERFLAKE_ROOT/install/setup.bash" ]; then
  source "$ROVERFLAKE_ROOT/install/setup.bash"
fi

exec "$@"
