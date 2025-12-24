#!/bin/bash

# Docker run script for TurtleBot simulation
# This script handles X11 forwarding for Gazebo GUI support
# NOTE: This script must be run from the repository root directory

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Check if we're in the repository root by verifying src directory exists
if [ ! -d "$REPO_ROOT/src" ]; then
    echo "Error: Repository root not found or src directory missing."
    echo "Please run this script from the repository root directory or check your installation."
    exit 1
fi

# Allow X11 forwarding
xhost +local:docker 2>/dev/null || echo "Note: xhost command not available. GUI may not work."

# Run the container
docker run -it --rm \
  --name turtlebot-sim \
  --network host \
  --gpus all \
  --device /dev/input:/dev/input \
  -e DISPLAY=${DISPLAY} \
  -e QT_X11_NO_MITSHM=1 \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v /dev/input:/dev/input:ro \
  -v "$REPO_ROOT/src:/root/workspace/src:rw" \
  task-oriented-comms-robot:latest \
  "$@"
