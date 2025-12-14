#!/bin/bash
set -e

# Source ROS2 setup
source /opt/ros/humble/setup.bash

# Install TurtleBot3 packages if not already installed
if ! dpkg -s ros-humble-turtlebot3-gazebo >/dev/null 2>&1; then
    echo "Installing TurtleBot3 packages..."
    apt-get update
    apt-get install -y \
        ros-humble-turtlebot3 \
        ros-humble-turtlebot3-gazebo \
        ros-humble-turtlebot3-description \
        2>/dev/null || echo "Note: TurtleBot3 packages may need manual installation"
    rm -rf /var/lib/apt/lists/*
fi

# Source workspace setup if it exists
if [ -f /root/workspace/install/setup.bash ]; then
    source /root/workspace/install/setup.bash
fi

# Execute the command passed to docker run
exec "$@"
