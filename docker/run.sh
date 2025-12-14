#!/bin/bash

# Docker run script for TurtleBot simulation
# This script handles X11 forwarding for Gazebo GUI support

# Allow X11 forwarding
xhost +local:docker 2>/dev/null || echo "Note: xhost command not available. GUI may not work."

# Run the container
docker run -it --rm \
  --name turtlebot-sim \
  --network host \
  -e DISPLAY=${DISPLAY} \
  -e QT_X11_NO_MITSHM=1 \
  -e TURTLEBOT3_MODEL=burger \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $(pwd)/src:/root/workspace/src:rw \
  task-oriented-comms-robot:latest \
  "$@"
