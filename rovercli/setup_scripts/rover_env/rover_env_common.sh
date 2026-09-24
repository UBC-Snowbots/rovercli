source ${ROVERCLI_ROOT}/setup_scripts/rover_env/rover_aliases_common.sh #Aliases like rosbuild, rosclean etc
source ${ROVERCLI_ROOT}/setup_scripts/rover_env/rover_env_vars.sh
# Guarded for docker: a fresh container/clean workspace has no install/ yet
if [ -f ${ROVERFLAKE_ROOT}/install/setup.bash ]; then
  source ${ROVERFLAKE_ROOT}/install/setup.bash # Default to sourcing the repo (May mess up if you have multiple ROS2 or ROS repos)
fi