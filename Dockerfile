# Ubuntu runs inside the image on every host. The CLI setup installs ROS Jazzy
# and the RoverFlake dependencies into this container.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    ROVERFLAKE_ROOT=/RoverFlake2 \
    ROS_DISTRO=jazzy \
    RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
    ROS_DOMAIN_ID=101 \
    ROVERCLI_ROOT=/opt/rovercli/rovercli \
    PATH=/opt/rovercli-venv/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    python3 \
    python3-pip \
    sudo \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /opt/rovercli/
COPY rovercli/ /opt/rovercli/rovercli/
COPY docker/entrypoint.sh /usr/local/bin/rover-entrypoint.sh

RUN python3 -m pip install -e /opt/rovercli --break-system-packages \
    && chmod +x /usr/local/bin/rover-entrypoint.sh \
    && rm -rf /root/.cache/pip

WORKDIR $ROVERFLAKE_ROOT

ENTRYPOINT ["/usr/local/bin/rover-entrypoint.sh"]
CMD ["/bin/bash"]
