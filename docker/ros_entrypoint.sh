#!/bin/bash
set -e

# Source ROS2 setup
source /opt/ros/jazzy/setup.bash

# Install TurtleBot3 packages if not already installed
if ! dpkg -s ros-jazzy-turtlebot3-gazebo >/dev/null 2>&1; then
    echo "Installing TurtleBot3 packages..."
    apt-get update
    apt-get install -y \
        ros-jazzy-turtlebot3 \
        ros-jazzy-turtlebot3-gazebo \
        ros-jazzy-turtlebot3-description \
        2>/dev/null || echo "Warning: TurtleBot3 package installation failed, manual installation may be required"
    rm -rf /var/lib/apt/lists/*
fi

# Source workspace setup if it exists
if [ -f /root/workspace/install/setup.bash ]; then
    source /root/workspace/install/setup.bash
fi

# Execute the command passed to docker run
exec "$@"
