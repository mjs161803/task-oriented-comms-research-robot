# Migration Notes: ROS2 Humble → ROS2 Jazzy with Gazebo Harmonic

This document describes the migration from ROS2 Humble with Gazebo Classic to ROS2 Jazzy with Gazebo Harmonic.

## Summary of Changes

### Docker Environment
- **Base Image**: Updated from `osrf/ros:humble-desktop-full` to `osrf/ros:jazzy-desktop-full`
- **OS Version**: Ubuntu 22.04 → Ubuntu 24.04
- **Gazebo Version**: Gazebo Classic (Gazebo 11) → Gazebo Harmonic (Gazebo Sim)

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

#### Before (Gazebo Classic)
```python
pkg_gazebo_ros = FindPackageShare('gazebo_ros')
gzserver = IncludeLaunchDescription(...)
gzclient = IncludeLaunchDescription(...)
spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py', ...)
```

#### After (Gazebo Harmonic)
```python
pkg_ros_gz_sim = FindPackageShare('ros_gz_sim')
gz_sim = IncludeLaunchDescription(...)
robot_state_publisher = Node(...)  # NEW: Required for robot description
spawn_entity = Node(package='ros_gz_sim', executable='create', ...)
bridge = Node(package='ros_gz_bridge', ...)  # NEW: Bridge for ROS2-Gazebo communication
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
1. **Build-time**: Install only core tools (colcon, git, wget, rosdep)
2. **Runtime**: Install ROS2 Jazzy packages via entrypoint script
   - This provides flexibility if packages are not yet in repositories
   - Allows graceful degradation if specific packages are unavailable

## Known Issues and Considerations

### 1. Package Availability
Some ROS2 Jazzy packages may not be immediately available in all package repositories. The entrypoint script (`docker/ros_entrypoint.sh`) handles installation at runtime to work around this.

### 2. TurtleBot3 Compatibility
TurtleBot3 packages (`ros-jazzy-turtlebot3-*`) may need manual installation or building from source if not available in Jazzy repositories. The system is designed to gracefully handle this.

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

3. **Robot Spawn Test**: Verify TurtleBot3 spawns correctly in simulation

4. **Control Test**: Verify robot responds to velocity commands

5. **Sensor Test**: Verify camera and other sensors publish data

6. **Block Observer Test**: Verify block distance calculations work

## Rollback Plan

If issues arise, rollback to ROS2 Humble:
1. Checkout the previous commit before this migration
2. Rebuild Docker images
3. TurtleBot3 packages have better support in Humble

## Future Improvements

1. **Custom Gazebo Models**: Migrate to Gazebo Harmonic model format
2. **Advanced Sensors**: Take advantage of Gazebo Harmonic's improved sensor models
3. **Performance**: Optimize ros_gz_bridge topic mappings
4. **Testing**: Add automated tests for Gazebo Harmonic integration

## References

- [ROS2 Jazzy Documentation](https://docs.ros.org/en/jazzy/)
- [Gazebo Harmonic Documentation](https://gazebosim.org/docs/harmonic)
- [ros_gz Documentation](https://github.com/gazebosim/ros_gz)
- [ROS2 Jazzy Migration Guide](https://docs.ros.org/en/jazzy/Releases/Release-Jazzy-Jalisco.html)
