cd "$ROVERFLAKE_ROOT"
sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r --skip-keys="serial moteus_msgs" -y --rosdistro $ROS_DISTRO --skip-keys="rviz rviz2 "