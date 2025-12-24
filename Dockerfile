# Use official ROS2 Jazzy base image (Ubuntu 24.04)
FROM osrf/ros:jazzy-desktop-full

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Add GPG keys for additional repositories
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    lsb-release \
    && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && rm -rf /var/lib/apt/lists/*

# Install additional dependencies
# Core build tools and utilities
RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-pip \
    python3-rosdep \
    ros-jazzy-turtlebot4-simulator \
    ros-jazzy-turtlebot4-description \
    ros-jazzy-turtlebot4-msgs \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-ros-gz-interfaces \
    ros-jazzy-twist-mux \
    ros-jazzy-joy \
    ros-jazzy-teleop-twist-joy \
    wget \
    git \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Create workspace
WORKDIR /root/workspace

# Copy the source code
COPY src ./src

# Build the workspace
RUN . /opt/ros/jazzy/setup.sh && \
    colcon build --symlink-install

# Configure .bashrc to source ROS and workspace setup in interactive shells
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "if [ -f /root/workspace/install/setup.bash ]; then source /root/workspace/install/setup.bash; fi" >> /root/.bashrc

# Setup entrypoint
COPY docker/ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod +x /ros_entrypoint.sh

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
