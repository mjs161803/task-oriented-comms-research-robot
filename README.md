# task-oriented-comms-research-robot
Simulation to explore task-oriented communication schemes to enable robot task completion.

## Overview
This repository contains a ROS2 Humble workspace with a Gazebo simulation featuring a TurtleBot3 robot and interactive blocks that the robot can push around.

## Prerequisites

### Option 1: Docker (Recommended)
- Docker
- Docker Compose
- X11 server (for Gazebo GUI)

### Option 2: Native Installation
- ROS2 Humble
- Gazebo (installed with ROS2)
- TurtleBot3 packages

## Installation

### Option 1: Using Docker (Recommended)

Docker provides an isolated environment with all dependencies pre-installed, making it the easiest way to get started.

#### Prerequisites for Docker
1. Install Docker and Docker Compose:
   - Follow the official Docker installation guide: https://docs.docker.com/get-docker/
   - Install Docker Compose: https://docs.docker.com/compose/install/

2. Allow X11 forwarding (for Gazebo GUI):
   ```bash
   xhost +local:docker
   ```

#### Build and Run with Docker Compose
1. Clone this repository:
   ```bash
   git clone https://github.com/mjs161803/task-oriented-comms-research-robot.git
   cd task-oriented-comms-research-robot
   ```

2. Build the Docker image:
   ```bash
   docker-compose build
   ```

3. Start the container:
   ```bash
   docker-compose up -d
   ```

4. Access the container shell:
   ```bash
   docker-compose exec ros2-simulation bash
   ```

5. Inside the container, launch the simulation:
   ```bash
   ros2 launch turtlebot_simulation turtlebot_gazebo.launch.py
   ```

#### Alternative: Using Docker directly

You can also use the provided helper script to run the container:
```bash
# Build the image
docker build -t task-oriented-comms-robot:latest .

# Run using the helper script
./docker/run.sh
```

Or run Docker commands manually:
```bash
# Allow X11 forwarding
xhost +local:docker

# Run the container with GUI support
docker run -it --rm \
  --name turtlebot-sim \
  --network host \
  --privileged \
  -e DISPLAY=$DISPLAY \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  task-oriented-comms-robot:latest
```

#### Installing TurtleBot3 Packages in Container

When you first run the container, TurtleBot3 packages will be automatically installed if not already present. However, if you need to install them manually, run:
```bash
apt-get update
apt-get install -y ros-humble-turtlebot3 ros-humble-turtlebot3-gazebo ros-humble-turtlebot3-description
```

### Option 2: Native Installation

### Install ROS2 Humble
Follow the official ROS2 Humble installation guide: https://docs.ros.org/en/humble/Installation.html

### Install TurtleBot3 Packages
```bash
sudo apt update
sudo apt install ros-humble-turtlebot3* ros-humble-gazebo-ros-pkgs
```

### Set TurtleBot3 Model
Add this to your `~/.bashrc`:
```bash
export TURTLEBOT3_MODEL=burger
```

Then source it:
```bash
source ~/.bashrc
```

## Building the Workspace (Native Installation Only)

If you're using Docker, the workspace is automatically built during image creation. For native installations:

1. Clone this repository (if not already done):
```bash
git clone https://github.com/mjs161803/task-oriented-comms-research-robot.git
cd task-oriented-comms-research-robot
```

2. Build the workspace:
```bash
colcon build
```

3. Source the workspace:
```bash
source install/setup.bash
```

## Running the Simulation

Launch the Gazebo simulation with TurtleBot3 and blocks:
```bash
ros2 launch turtlebot_simulation turtlebot_gazebo.launch.py
```

This will:
- Start Gazebo with a custom world
- Spawn a TurtleBot3 robot at the origin
- Place four colored blocks (red, green, blue, yellow) in the world that the robot can push

### Launch Arguments
You can customize the launch with these arguments:

- `gui:=true/false` - Enable/disable Gazebo GUI (default: true)
- `use_sim_time:=true/false` - Use simulation time (default: true)
- `world:=/path/to/world` - Path to custom world file

Example:
```bash
ros2 launch turtlebot_simulation turtlebot_gazebo.launch.py gui:=false
```

## Controlling the TurtleBot

In a new terminal, you can control the TurtleBot using keyboard teleop:
```bash
source install/setup.bash
ros2 run turtlebot3_teleop teleop_keyboard
```

## World Description
The simulation world includes:
- Ground plane
- Four colored blocks (0.5m x 0.5m x 0.5m) positioned around the TurtleBot
  - Red block at (1.0, 0.5)
  - Green block at (-1.0, 1.0)
  - Blue block at (0.5, -1.5)
  - Yellow block at (-1.5, -0.5)
- The blocks have realistic physics and can be pushed by the TurtleBot

## Package Structure
```
task-oriented-comms-research-robot/
├── docker/
│   └── ros_entrypoint.sh         # Docker entrypoint script
├── src/
│   └── turtlebot_simulation/
│       ├── launch/
│       │   └── turtlebot_gazebo.launch.py
│       ├── worlds/
│       │   └── turtlebot_blocks.world
│       ├── CMakeLists.txt
│       └── package.xml
├── .dockerignore                  # Docker build exclusions
├── docker-compose.yml             # Docker Compose configuration
├── Dockerfile                     # Docker image definition
└── README.md
```

## Docker Notes

- The Docker image is based on `osrf/ros:humble-desktop-full` and includes all necessary dependencies
- Gazebo GUI support is enabled through X11 forwarding
- The workspace is automatically built during image creation
- Source code changes can be made on the host and will be reflected in the container (when using docker-compose with volume mounts)
- To rebuild the workspace inside a running container:
  ```bash
  cd /root/workspace
  colcon build
  source install/setup.bash
  ```
