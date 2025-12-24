# Migration Notes: ROS2 Humble → ROS2 Jazzy with Gazebo Harmonic → TurtleBot4

This document describes the migrations:
1. ROS2 Humble with Gazebo Classic to ROS2 Jazzy with Gazebo Harmonic
2. TurtleBot3 to TurtleBot4

## Summary of Changes

### Docker Environment
- **Base Image**: Updated from `osrf/ros:humble-desktop-full` to `osrf/ros:jazzy-desktop-full`
- **OS Version**: Ubuntu 22.04 → Ubuntu 24.04
- **Gazebo Version**: Gazebo Classic (Gazebo 11) → Gazebo Harmonic (Gazebo Sim)
- **Robot Platform**: TurtleBot3 Waffle Pi → TurtleBot 4

### Key Package Changes

#### TurtleBot Platform Migration
| Previous Package (TurtleBot3) | New Package (TurtleBot4) |
|-------------------------------|--------------------------|
| `ros-jazzy-turtlebot3` | `ros-jazzy-turtlebot4-simulator` |
| `ros-jazzy-turtlebot3-gazebo` | `ros-jazzy-turtlebot4-description` |
| `ros-jazzy-turtlebot3-description` | `ros-jazzy-turtlebot4-msgs` |

### Key Package Changes

#### Replaced Packages
| ROS2 Humble Package | ROS2 Jazzy Package |
|---------------------|-------------------|
| `ros-humble-gazebo-ros-pkgs` | `ros-jazzy-ros-gz-sim` |
| `ros-humble-gazebo-msgs` | `ros-jazzy-ros-gz-interfaces` |
| `ros-humble-gazebo-plugins` | `ros-jazzy-ros-gz-bridge` |

#### New Dependencies
- `ros-jazzy-robot-state-publisher` - For publishing robot transforms
- `ros-jazzy-xacro` - For processing URDF/xacro files
- `ros-jazzy-ros-gz` - Core ROS-Gazebo bridge package

### Launch File Changes

#### Before (TurtleBot3 with Gazebo Classic)
```python
pkg_turtlebot3_description = FindPackageShare('turtlebot3_description')
pkg_turtlebot3_gazebo = FindPackageShare('turtlebot3_gazebo')
spawn_entity = Node(package='ros_gz_sim', executable='create', 
                   arguments=['-file', robot_sdf_file, ...])
```

#### After (TurtleBot4 with Gazebo Harmonic)
```python
pkg_turtlebot4_description = FindPackageShare('turtlebot4_description')
robot_description_content = Command([FindExecutable(name='xacro'), ' ', robot_description_file])
spawn_entity = Node(package='ros_gz_sim', executable='create', 
                   arguments=['-topic', '/robot_description', ...])
```

### World File Changes

#### SDF Version
- **Before**: SDF 1.6
- **After**: SDF 1.8

#### Model URIs
- **Before**: `model://sun`, `model://ground_plane`
- **After**: `https://fuel.gazebosim.org/1.0/OpenRobotics/models/Sun`, `https://fuel.gazebosim.org/1.0/OpenRobotics/models/Ground Plane`

#### Plugins
- Removed Gazebo Classic ROS plugins from world file
- ROS-Gazebo bridge handled by `ros_gz_bridge` node in launch file

### Installation Strategy

To handle potential package availability issues:
1. **Build-time**: Install core tools and TurtleBot4 packages from ROS Jazzy repositories
2. **Runtime**: Verify and install missing packages via entrypoint script
   - This provides flexibility if packages are not yet in repositories
   - Allows graceful degradation if specific packages are unavailable

### GPG Key Configuration

The Dockerfile now includes proper GPG key configuration to ensure package repositories are trusted:
```dockerfile
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    lsb-release \
    && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && rm -rf /var/lib/apt/lists/*
```

## Known Issues and Considerations

### 1. Package Availability
TurtleBot4 packages are available in ROS2 Jazzy repositories. The pre-built `ros-jazzy-turtlebot4-simulator` package is used as specified.

### 2. TurtleBot4 Compatibility
TurtleBot4 uses a different robot description format compared to TurtleBot3:
- Uses xacro files for robot description
- Different sensor configuration
- Different dimensions and capabilities

### 3. Environment Variables
TurtleBot4 does not require a MODEL environment variable like TurtleBot3 did (TURTLEBOT3_MODEL). The robot model is specified directly in the URDF/xacro files.

### 3. Gazebo Harmonic vs Classic
Gazebo Harmonic has different:
- Plugin architecture
- Service names and interfaces
- Launch mechanisms
- Model database (now uses Fuel instead of local models)

### 4. ros_gz_bridge Topics
The bridge needs explicit topic mappings. Currently configured:
- `/cmd_vel` - Velocity commands to robot
- `/clock` - Simulation clock

Additional topics may need to be added for:
- Camera streams
- Sensor data
- Other ROS2-Gazebo communications

### 5. Entity State Services
The `block_observer.py` node queries Gazebo for entity states. This functionality needs to be verified with Gazebo Harmonic's service interface.

## Testing Recommendations

1. **Build Test**: Verify Docker image builds successfully
   ```bash
   docker-compose build
   ```

2. **Launch Test**: Start simulation and verify Gazebo Harmonic launches
   ```bash
   docker-compose up -d
   docker-compose exec ros2-simulation bash
   ros2 launch turtlebot_simulation turtlebot_gazebo.launch.py
   ```

3. **Robot Spawn Test**: Verify TurtleBot4 spawns correctly in simulation

4. **Control Test**: Verify robot responds to velocity commands

5. **Sensor Test**: Verify camera and other sensors publish data

6. **Block Observer Test**: Verify block distance calculations work

## Rollback Plan

If issues arise, rollback to TurtleBot3:
1. Checkout the commit before TurtleBot4 migration
2. Rebuild Docker images
3. TurtleBot3 packages are available in Jazzy

## Future Improvements

1. **Custom Gazebo Models**: Optimize block models for TurtleBot4 interaction
2. **Advanced Sensors**: Take advantage of TurtleBot4's sensor suite
3. **Performance**: Optimize ros_gz_bridge topic mappings
4. **Testing**: Add automated tests for TurtleBot4 integration

## References

- [ROS2 Jazzy Documentation](https://docs.ros.org/en/jazzy/)
- [Gazebo Harmonic Documentation](https://gazebosim.org/docs/harmonic)
- [TurtleBot4 Documentation](https://turtlebot.github.io/turtlebot4-user-manual/)
- [ros_gz Documentation](https://github.com/gazebosim/ros_gz)
- [ROS2 Jazzy Migration Guide](https://docs.ros.org/en/jazzy/Releases/Release-Jazzy-Jalisco.html)
