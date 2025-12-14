# Use official ROS2 Humble base image
FROM osrf/ros:humble-desktop-full

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TURTLEBOT3_MODEL=burger

# Install additional dependencies
# Note: TurtleBot3 packages may need to be installed when running the container
# if they are not available in package repos during build
RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create workspace
WORKDIR /root/workspace

# Copy the source code
COPY src ./src

# Build the workspace
RUN . /opt/ros/humble/setup.sh && \
    colcon build --symlink-install

# Setup entrypoint
COPY docker/ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod +x /ros_entrypoint.sh

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
