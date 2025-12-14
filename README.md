# task-oriented-comms-research-robot
Simulation to explore task-oriented communication schemes to enable robot task completion.

## Overview
This repository contains a ROS2 Humble workspace with a Gazebo simulation featuring a TurtleBot3 robot and interactive blocks that the robot can push around.

## Prerequisites
- ROS2 Humble
- Gazebo (installed with ROS2)
- TurtleBot3 packages

## Installation

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

## Building the Workspace

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
├── src/
│   └── turtlebot_simulation/
│       ├── launch/
│       │   └── turtlebot_gazebo.launch.py
│       ├── worlds/
│       │   └── turtlebot_blocks.world
│       ├── CMakeLists.txt
│       └── package.xml
└── README.md
```
