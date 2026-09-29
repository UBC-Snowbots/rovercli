# Ubuntu runs inside the image on every host. The CLI setup installs ROS Jazzy
# and the RoverFlake dependencies into this container.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    ROVERFLAKE_ROOT=/RoverFlake2 \
    ROS_DISTRO=jazzy \
    RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
    ROS_DOMAIN_ID=101 \
    PATH=/opt/rovercli-venv/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    python3 \
    python3-venv \
    sudo \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /opt/rovercli/
COPY rovercli/ /opt/rovercli/rovercli/
COPY docker/entrypoint.sh /usr/local/bin/rover-entrypoint.sh

RUN find /opt/rovercli/rovercli/setup_scripts -type f -name '*.sh' \
        -exec sed -i 's/\r$//' {} + \
    && sed -i 's/\r$//' /usr/local/bin/rover-entrypoint.sh \
    && python3 -m venv --system-site-packages /opt/rovercli-venv \
    && /opt/rovercli-venv/bin/pip install --no-cache-dir -e /opt/rovercli \
    && chmod +x /usr/local/bin/rover-entrypoint.sh \
    && rovercli setup \
        --dst /RoverFlake2 \
        --distro jazzy \
        --apt-pkg-list base perceptions \
        --setup-script update_submodules.sh install_rosdeps.sh install_phidgets.sh \
        --ros-version desktop \
        --git-protocol https \
        --cd-roverflake n \
    && rm -rf /root/.cache/pip

WORKDIR $ROVERFLAKE_ROOT

ENTRYPOINT ["/usr/local/bin/rover-entrypoint.sh"]
CMD ["/bin/bash"]
