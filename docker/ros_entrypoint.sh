#!/bin/bash
set -e

# Source ROS2 setup
source /opt/ros/jazzy/setup.bash

# Install required ROS2 Jazzy packages if not already installed
echo "Checking and installing required ROS2 Jazzy packages..."
apt-get update || { echo "Failed to update package lists"; exit 1; }

# Install Gazebo Harmonic and ROS-Gazebo bridge packages
if ! dpkg -s ros-jazzy-ros-gz-sim >/dev/null 2>&1; then
    echo "Installing ros_gz packages..."
    apt-get install -y \
        ros-jazzy-ros-gz \
        ros-jazzy-ros-gz-sim \
        ros-jazzy-ros-gz-bridge \
        ros-jazzy-ros-gz-interfaces \
        2>/dev/null || echo "Warning: ros_gz package installation had issues"
fi

# Install robot state publisher and xacro
if ! dpkg -s ros-jazzy-robot-state-publisher >/dev/null 2>&1; then
    echo "Installing robot-state-publisher and xacro..."
    apt-get install -y \
        ros-jazzy-robot-state-publisher \
        ros-jazzy-xacro \
        2>/dev/null || echo "Warning: robot-state-publisher/xacro installation had issues"
fi

# Install control packages
if ! dpkg -s ros-jazzy-twist-mux >/dev/null 2>&1; then
    echo "Installing control packages..."
    apt-get install -y \
        ros-jazzy-twist-mux \
        ros-jazzy-joy \
        ros-jazzy-teleop-twist-joy \
        2>/dev/null || echo "Warning: control package installation had issues"
fi

# Install TurtleBot3 packages if not already installed
if ! dpkg -s ros-jazzy-turtlebot3-gazebo >/dev/null 2>&1; then
    echo "Installing TurtleBot3 packages..."
    apt-get install -y \
        ros-jazzy-turtlebot3 \
        ros-jazzy-turtlebot3-gazebo \
        ros-jazzy-turtlebot3-description \
        2>/dev/null || echo "Warning: TurtleBot3 package installation failed, manual installation may be required"
fi

rm -rf /var/lib/apt/lists/*

# Source workspace setup if it exists
if [ -f /root/workspace/install/setup.bash ]; then
    source /root/workspace/install/setup.bash
fi

# Execute the command passed to docker run
exec "$@"
