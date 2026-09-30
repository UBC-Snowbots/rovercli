#!/bin/bash
set -e

if [ ! -f "$HOME/.rovercli-setup-complete" ]; then
  rovercli setup \
    --dst "$ROVERFLAKE_ROOT" \
    --distro "$ROS_DISTRO" \
    --apt-pkg-list base perceptions \
    --setup-script update_submodules.sh install_rosdeps.sh install_phidgets.sh \
    --ros-version desktop \
    --git-protocol https \
    --cd-roverflake n
  touch "$HOME/.rovercli-setup-complete"
fi
if [ -f "$HOME/.roverrc" ]; then
  source "$HOME/.roverrc"
fi

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
if [ -f "$HOME/.roverrc" ]; then
  source "$HOME/.roverrc"
fi

exec "$@"
