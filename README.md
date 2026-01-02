# task-oriented-comms-research-robot
Simulation to explore task-oriented communication schemes to enable robot task completion.

## Overview
This repository contains a ROS2 Jazzy workspace with a Gazebo Harmonic simulation featuring a TurtleBot 4 robot with interactive blocks that the robot can push around.

## Prerequisites

### Option 1: Docker (Recommended)
- Docker
- Docker Compose
- X11 server (for Gazebo GUI)

### Option 2: Native Installation
- ROS2 Jazzy
- Gazebo Harmonic (installed with ROS2)
- TurtleBot4 packages

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

**Important**: All docker-compose commands must be run from the repository root directory.

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

   **Note**: The Docker container has access to USB joystick devices connected to the host. The joystick nodes are launched automatically. If no joystick is connected, the nodes will report an error but the simulation will still run normally.

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

# Run the container with GUI and joystick support
docker run -it --rm \
  --name turtlebot-sim \
  --network host \
  --device /dev/input:/dev/input \
  -e DISPLAY=$DISPLAY \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v /dev/input:/dev/input:ro \
  task-oriented-comms-robot:latest
```

#### Installing TurtleBot4 Packages in Container

When you first run the container, TurtleBot4 packages will be automatically installed if not already present. However, if you need to install them manually, run:
```bash
apt-get update
apt-get install -y ros-jazzy-turtlebot4-simulator ros-jazzy-turtlebot4-description ros-jazzy-turtlebot4-msgs
```

### Option 2: Native Installation

### Install ROS2 Jazzy
Follow the official ROS2 Jazzy installation guide: https://docs.ros.org/en/jazzy/Installation.html

### Install TurtleBot4 Packages
```bash
sudo apt update
sudo apt install ros-jazzy-turtlebot4-simulator ros-jazzy-ros-gz
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

### Standard Simulation Mode

Launch the Gazebo simulation with TurtleBot4 and blocks:
```bash
ros2 launch turtlebot_simulation turtlebot_gazebo.launch.py
```

This will:
- Start Gazebo with a custom world
- Spawn a TurtleBot 4 robot at the origin
- Place four colored blocks (red, green, blue, yellow) in the world that the robot can push
- Enable camera streaming to ROS2 topics

### Launch Arguments
You can customize the launch with these arguments:

- `gui:=true/false` - Enable/disable Gazebo GUI (default: true)
- `use_sim_time:=true/false` - Use simulation time (default: true)
- `world:=/path/to/world` - Path to custom world file
- `use_plotjuggler:=true/false` - Enable/disable PlotJuggler for real-time data visualization (default: false)
- `use_local_perception:=true/false` - Enable/disable local_perception node for ML inference (default: false)

Example:
```bash
ros2 launch turtlebot_simulation turtlebot_gazebo.launch.py gui:=false
```

### Local Perception Node

The local_perception node is an optional component that demonstrates how to integrate machine learning models with ROS2 sensor data. When enabled, it:

- Subscribes to `/imu/data` (IMU sensor data)
- Subscribes to `/oakd/rgb/preview/image_raw` (camera images)
- Runs inference at 25Hz using a PyTorch model (skeleton provided)
- Publishes integer results to `/agent_uplink` topic

To enable the local_perception node:
```bash
ros2 launch turtlebot_simulation turtlebot_gazebo.launch.py use_local_perception:=true
```

**Note**: The node includes a PyTorch model skeleton. To use it with an actual model:
1. Implement the `_initialize_model()` method to load your model
2. Implement the `_preprocess_image()` and `_preprocess_imu()` methods to prepare sensor data
3. Update the `_inference_callback()` method to run your model and process outputs

You can also run the node standalone:
```bash
ros2 run turtlebot_simulation local_perception.py
```

### PlotJuggler Integration

PlotJuggler is a tool for visualizing time-series data from ROS2 topics in real-time. It can be launched automatically with the simulation:

```bash
ros2 launch turtlebot_simulation turtlebot_gazebo.launch.py use_plotjuggler:=true
```

When PlotJuggler is enabled, it will start with the simulation and you can:
- Subscribe to any ROS2 topic (e.g., `/cmd_vel`, `/imu`, `/block_distances`, `/odom`)
- Visualize sensor data in real-time plots
- Monitor robot behavior and performance metrics
- Export data for offline analysis

**Note**: PlotJuggler requires X11 forwarding which is already configured in the Docker setup.

### Episodic Simulation Mode

For automated testing and data collection, you can run the simulation in episodic mode. This will:
- Run the simulation for a specified number of episodes
- Each episode runs for 60 seconds (configurable)
- At the end of each episode, the latest score from the `/block_distances` topic is stored to a file
- The simulation automatically resets between episodes
- After all episodes complete, the system shuts down automatically

Launch the episodic simulation:
```bash
ros2 launch turtlebot_simulation episodic_simulation.launch.py
```

#### Episodic Launch Arguments

- `num_episodes:=N` - Number of episodes to run (default: 10)
- `episode_duration:=SECONDS` - Duration of each episode in seconds (default: 60.0)
- `output_file:=PATH` - Path to output file for storing episode scores (default: episode_scores.txt)
- `gui:=true/false` - Enable/disable Gazebo GUI (default: true)
- `use_joystick:=true/false` - Enable joystick control (default: false for episodic mode)
- `use_plotjuggler:=true/false` - Enable PlotJuggler for data visualization (default: false for episodic mode)

Examples:
```bash
# Run 20 episodes with default settings
ros2 launch turtlebot_simulation episodic_simulation.launch.py num_episodes:=20

# Run 5 episodes of 30 seconds each without GUI
ros2 launch turtlebot_simulation episodic_simulation.launch.py num_episodes:=5 episode_duration:=30.0 gui:=false

# Custom output file
ros2 launch turtlebot_simulation episodic_simulation.launch.py output_file:=/tmp/my_scores.txt

# Enable PlotJuggler for episodic runs to visualize data
ros2 launch turtlebot_simulation episodic_simulation.launch.py use_plotjuggler:=true
```

The output file will contain one score per episode in CSV format:
```
# Episode Scores - Generated at 2024-12-23T12:00:00.000000
# Total episodes: 10
# Episode duration: 60.0 seconds
# Format: episode_number,score
1,15.234567
2,14.876543
3,16.123456
...
```

## Controlling the TurtleBot

The simulation includes **twist_mux** for managing multiple velocity command sources with priorities. The robot can be controlled via joystick or keyboard.

### Joystick Control (Recommended)

The simulation now supports USB joystick/gamepad control out of the box when running with Docker.

#### Prerequisites for Joystick
1. Connect a USB joystick/gamepad to your host computer
2. Verify the joystick is detected:
   ```bash
   ls -l /dev/input/js*
   ```

#### Using Joystick with Docker
The Docker container is configured to access USB joystick devices automatically:
- The `/dev/input` directory is mounted in the container
- Joystick nodes are launched by default with the simulation

#### Joystick Button Mapping
Default button mapping (may vary by device):
- **Left Stick Vertical**: Forward/Backward movement
- **Left Stick Horizontal**: Turn left/right
- **Button 4**: Enable movement (deadman switch - must be held)
- **Button 5**: Turbo mode (higher speed)

**Note**: Button and axis numbers vary between joystick models. To determine the correct mappings for your device:

1. List available joystick devices:
   ```bash
   ros2 run joy joy_enumerate_devices
   ```

2. View live joystick data (press buttons/move sticks to see which numbers appear):
   ```bash
   ros2 topic echo /joy
   ```

3. Update the configuration file with the correct button/axis numbers for your device.

#### Customizing Joystick Configuration
Edit the joystick configuration file to customize button mappings:
```bash
src/turtlebot_simulation/config/joystick.yaml
```

#### Disabling Joystick
To launch without joystick support:
```bash
ros2 launch turtlebot_simulation turtlebot_gazebo.launch.py use_joystick:=false
```

### Keyboard Control

For keyboard control, publish to the keyboard velocity topic in a new terminal:
```bash
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args --remap /cmd_vel:=/cmd_vel_keyboard
```

### Velocity Command Topics

The simulation uses **twist_mux** to manage multiple velocity sources with priorities:
- `/cmd_vel_joy` - Joystick commands (Priority: 10 - Highest)
- `/cmd_vel_keyboard` - Keyboard commands (Priority: 5 - Medium)
- `/cmd_vel_nav` - Navigation commands (Priority: 1 - Lowest)
- `/cmd_vel` - Final output sent to robot (from twist_mux)

Higher priority sources override lower priority sources when active.

## Sensor Information

The TurtleBot 4 includes several sensors that publish data to ROS2 topics:

### Camera

- **Image Topic**: `/oakd/rgb/preview/image_raw` - Raw RGB camera images
- **Depth Topic**: `/oakd/rgb/preview/depth` - Depth images
- **Point Cloud Topic**: `/oakd/rgb/preview/depth/points` - 3D point cloud data
- **Camera Info Topic**: `/oakd/rgb/preview/camera_info` - Camera calibration and metadata

You can view the camera feed using:
```bash
ros2 run rqt_image_view rqt_image_view
```

Or list all available camera topics:
```bash
ros2 topic list | grep camera
```

### IMU (Inertial Measurement Unit)

- **IMU Topic**: `/imu/data` - IMU sensor data (orientation, angular velocity, linear acceleration)

You can view IMU data using:
```bash
ros2 topic echo /imu/data
```

### Agent Uplink

- **Agent Uplink Topic**: `/agent_uplink` - Integer output from local_perception node (when enabled)

This topic publishes the output of the ML model inference performed by the local_perception node. You can monitor it using:
```bash
ros2 topic echo /agent_uplink
```

## World Description
The simulation world includes:
- Ground plane
- Four colored blocks (0.075m x 0.075m x 0.075m, or 75mm x 75mm x 75mm) positioned around the TurtleBot
  - Red block at (1.0, 0.5)
  - Green block at (-1.0, 1.0)
  - Blue block at (0.5, -1.5)
  - Yellow block at (-1.5, -0.5)
- The blocks have realistic physics and can be pushed by the robot

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

- The Docker image is based on `osrf/ros:jazzy-desktop-full` (Ubuntu 24.04) and includes all necessary dependencies
- Gazebo Harmonic GUI support is enabled through X11 forwarding
- The workspace is automatically built during image creation
- Source code changes can be made on the host and will be reflected in the container (when using docker-compose with volume mounts)
- To rebuild the workspace inside a running container:
  ```bash
  cd /root/workspace
  colcon build
  source install/setup.bash
  ```

## Gazebo GetEntity Service

The Docker image installs Gazebo ROS packages that provide the ROS2 API plugin for Gazebo Harmonic, including support for `gazebo_msgs` services related to entities (e.g., `GetEntityState`).

### Verify inside the container

1. Build the image:
   ```bash
   docker compose build
   ```
2. Start the container and launch the sim:
   ```bash
   docker compose up -d
   docker compose exec ros2-simulation bash
   ros2 launch turtlebot_simulation turtlebot_gazebo.launch.py
   ```
3. Check available interfaces/services:
   ```bash
   ros2 interface show gazebo_msgs/srv/GetEntityState
   ros2 service list | grep -i entity
   ```

Note: The plugin must be loaded at runtime by Gazebo (typically via your launch/world). This repo ensures the plugin libraries are installed in the image; loading is controlled by the launch/world configuration.
