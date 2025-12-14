#!/bin/bash
set -e

# Source ROS2 setup
source /opt/ros/humble/setup.bash

# Source workspace setup if it exists
if [ -f /root/workspace/install/setup.bash ]; then
    source /root/workspace/install/setup.bash
fi

# Execute the command passed to docker run
exec "$@"
