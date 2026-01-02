#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command, FindExecutable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Get package directories
    pkg_ros_gz_sim = FindPackageShare('ros_gz_sim')
    pkg_turtlebot_simulation = FindPackageShare('turtlebot_simulation')
    pkg_turtlebot4_description = FindPackageShare('turtlebot4_description')
    pkg_irobot_create_control = FindPackageShare('irobot_create_control')
    
    # Paths to world file
    world_file = PathJoinSubstitution([
        pkg_turtlebot_simulation,
        'worlds',
        'turtlebot_blocks.world'
    ])
    
    # Path to twist_mux config
    twist_mux_config = PathJoinSubstitution([
        pkg_turtlebot_simulation,
        'config',
        'twist_mux.yaml'
    ])
    
    # Path to joystick config
    joystick_config = PathJoinSubstitution([
        pkg_turtlebot_simulation,
        'config',
        'joystick.yaml'
    ])

    # PlotJuggler layout file
    plot_layout = PathJoinSubstitution([
        pkg_turtlebot_simulation,
        'config',
        'imu_plot_config.xml'
    ])
    
    # Get URDF for TurtleBot4
    robot_description_file = PathJoinSubstitution([
        pkg_turtlebot_simulation,
        'urdf',
        'standard',
        'turtlebot4.urdf.xacro'
    ])
    
    robot_description_content = Command([
        FindExecutable(name='xacro'), ' ',
        robot_description_file,
        ' gazebo:=ignition'
    ])
    
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    gui = LaunchConfiguration('gui', default='true')
    world = LaunchConfiguration('world', default=world_file)
    use_joystick = LaunchConfiguration('use_joystick', default='true')
    use_plotjuggler = LaunchConfiguration('use_plotjuggler', default='true')
    use_local_perception = LaunchConfiguration('use_local_perception', default='false')
    
    declare_use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    
    declare_gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='true',
        description='Set to "true" to launch Gazebo GUI'
    )
    
    declare_world_arg = DeclareLaunchArgument(
        'world',
        default_value=world_file,
        description='Path to world file'
    )
    
    declare_use_joystick_arg = DeclareLaunchArgument(
        'use_joystick',
        default_value='true',
        description='Set to "true" to enable joystick control'
    )
    
    declare_use_plotjuggler_arg = DeclareLaunchArgument(
        'use_plotjuggler',
        default_value='true',
        description='Set to "true" to launch PlotJuggler for data visualization'
    )
    
    declare_use_local_perception_arg = DeclareLaunchArgument(
        'use_local_perception',
        default_value='false',
        description='Set to "true" to launch local_perception node for ML inference'
    )
    
    # Gazebo Harmonic (using ros_gz_sim)
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                pkg_ros_gz_sim,
                'launch',
                'gz_sim.launch.py'
            ])
        ]),
        launch_arguments={
            'gz_args': [world, ' -r -v 4'],
            'on_exit_shutdown': 'true'
        }.items()
    )
    
    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description_content,
            'use_sim_time': use_sim_time
        }],
        output='screen'
    )
    
    # Spawn TurtleBot4 using ros_gz_sim create
    spawn_turtlebot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', '/robot_description',
            '-name', 'turtlebot4',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.01',
            '-Y', '0.0'
        ],
        output='screen'
    )
    
    # ROS-Gazebo bridge for clock and other topics
    # Note: cmd_vel is handled by ros2_control, so we don't bridge it here
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/world/turtlebot_world/model/turtlebot4/link/oakd_rgb_camera_frame/sensor/rgbd_camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/world/turtlebot_world/model/turtlebot4/link/oakd_rgb_camera_frame/sensor/rgbd_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/model/turtlebot4/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/model/turtlebot4/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/world/turtlebot_world/pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
        ],
        remappings=[
            ('/world/turtlebot_world/model/turtlebot4/link/oakd_rgb_camera_frame/sensor/rgbd_camera/image', '/oakd/rgb/preview/image_raw'),
            ('/world/turtlebot_world/model/turtlebot4/link/oakd_rgb_camera_frame/sensor/rgbd_camera/camera_info', '/oakd/rgb/preview/camera_info'),
            ('/imu', '/imu/data'),
        ],
        output='screen'
    )
    # Path to control config
    control_config = PathJoinSubstitution([
        pkg_irobot_create_control,
        'config',
        'control.yaml'
    ])

    # Spawn controllers
    start_joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--param-file', control_config],
        output='screen'
    )

    start_diff_drive_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diffdrive_controller', '--param-file', control_config],
        output='screen'
    )
    
    # twist_mux node - multiplexes velocity commands from multiple sources
    twist_mux_node = Node(
        package='twist_mux',
        executable='twist_mux',
        parameters=[twist_mux_config, {'use_sim_time': use_sim_time}],
        remappings=[('/cmd_vel_out', '/diffdrive_controller/cmd_vel')],
        output='screen'
    )
    
    # Joy node - reads joystick input
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_joystick),
        output='screen'
    )
    
    # Teleop twist joy - converts joystick messages to Twist messages
    teleop_twist_joy_node = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',
        parameters=[joystick_config, {'use_sim_time': use_sim_time, 'publish_stamped_twist': True}],
        remappings=[('/cmd_vel', '/cmd_vel_joy')],
        condition=IfCondition(use_joystick),
        output='screen'
    )
    
    # Block observer node - subscribes to pose stream and publishes distances
    block_observer = Node(
        package='turtlebot_simulation',
        executable='block_observer.py',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )
    
    # PlotJuggler node - visualizes ROS2 topics in real-time
    plotjuggler_node = Node(
        package='plotjuggler',
        executable='plotjuggler',
        name='plotjuggler',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=['--layout', plot_layout],
        condition=IfCondition(use_plotjuggler),
        output='screen'
    )
    
    # Local perception node - runs ML inference on sensor data
    local_perception_node = Node(
        package='turtlebot_simulation',
        executable='local_perception.py',
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_local_perception),
        output='screen'
    )
    
    return LaunchDescription([
        declare_use_sim_time_arg,
        declare_gui_arg,
        declare_world_arg,
        declare_use_joystick_arg,
        declare_use_plotjuggler_arg,
        declare_use_local_perception_arg,
        gz_sim,
        robot_state_publisher,
        spawn_turtlebot,
        bridge,
        start_joint_state_broadcaster,
        start_diff_drive_controller,
        twist_mux_node,
        joy_node,
        teleop_twist_joy_node,
        block_observer,
        plotjuggler_node,
        local_perception_node
    ])

