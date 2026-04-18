# Use official ROS2 Jazzy base image (Ubuntu 24.04)
FROM osrf/ros:jazzy-desktop-full

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV LD_LIBRARY_PATH=/opt/ros/jazzy/lib:${LD_LIBRARY_PATH:-}
ENV GZ_SIM_SYSTEM_PLUGIN_PATH=/opt/ros/jazzy/lib
ENV GZ_SIM_RESOURCE_PATH=/opt/ros/jazzy/share:${GZ_SIM_RESOURCE_PATH:-}

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
    python3-yaml \
    python3-rosdep \
    ros-jazzy-turtlebot4-simulator \
    ros-jazzy-irobot-create-nodes \
    ros-jazzy-turtlebot4-description \
    ros-jazzy-turtlebot4-msgs \
    ros-jazzy-ros-gz \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-ros-gz-interfaces \
    ros-jazzy-twist-mux \
    ros-jazzy-joy \
    ros-jazzy-teleop-twist-joy \
    ros-jazzy-plotjuggler-ros \
    wget \
    git \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch (CUDA 12.4 build; works on newer driver stacks including 13.0)
RUN python3 -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu124 --break-system-packages

# Install minisom for self-organizing maps
RUN python3 -m pip install --no-cache-dir minisom --break-system-packages

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
