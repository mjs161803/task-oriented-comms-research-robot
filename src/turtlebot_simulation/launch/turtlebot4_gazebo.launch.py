#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from pathlib import Path


def generate_launch_description():
    # Get package directories
    pkg_turtlebot_simulation = FindPackageShare('turtlebot_simulation')
    pkg_turtlebot4_gz_bringup = FindPackageShare('turtlebot4_gz_bringup')
    pkg_turtlebot4_description = FindPackageShare('turtlebot4_description')
    pkg_irobot_create_description = FindPackageShare('irobot_create_description')
    pkg_irobot_create_gz_bringup = FindPackageShare('irobot_create_gz_bringup')
    pkg_irobot_create_gz_plugins = FindPackageShare('irobot_create_gz_plugins')
    pkg_turtlebot4_gz_gui_plugins = FindPackageShare('turtlebot4_gz_gui_plugins')
    pkg_ros_gz_sim = FindPackageShare('ros_gz_sim')
    
    # Paths to world file
    world_file = PathJoinSubstitution([
        pkg_turtlebot_simulation,
        'worlds',
        'turtlebot4_blocks.sdf'
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
    
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    gui = LaunchConfiguration('gui', default='true')
    world = LaunchConfiguration('world', default=world_file)
    use_joystick = LaunchConfiguration('use_joystick', default='true')
    model = LaunchConfiguration('model', default='standard')
    
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
    
    declare_model_arg = DeclareLaunchArgument(
        'model',
        default_value='standard',
        description='TurtleBot4 model: standard or lite'
    )
    
    # Set Gazebo resource path
    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=':'.join([
            os.path.join(pkg_turtlebot4_gz_bringup.perform(None), 'worlds'),
            os.path.join(pkg_irobot_create_gz_bringup.perform(None), 'worlds'),
            os.path.join(pkg_turtlebot_simulation.perform(None), 'worlds'),
            str(Path(pkg_turtlebot4_description.perform(None)).parent.resolve()),
            str(Path(pkg_irobot_create_description.perform(None)).parent.resolve())
        ])
    )

    gz_gui_plugin_path = SetEnvironmentVariable(
        name='GZ_GUI_PLUGIN_PATH',
        value=':'.join([
            os.path.join(pkg_turtlebot4_gz_gui_plugins.perform(None), 'lib'),
            os.path.join(pkg_irobot_create_gz_plugins.perform(None), 'lib')
        ])
    )
    
    # Gazebo Harmonic
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
    
    # Clock bridge
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        output='screen',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
        ]
    )
    
    # Spawn TurtleBot4
    turtlebot4_spawn_launch = PathJoinSubstitution(
        [pkg_turtlebot4_gz_bringup, 'launch', 'turtlebot4_spawn.launch.py'])

    robot_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([turtlebot4_spawn_launch]),
        launch_arguments=[
            ('namespace', ''),
            ('rviz', 'false'),
            ('model', model),
            ('x', '0.0'),
            ('y', '0.0'),
            ('z', '0.0'),
            ('yaw', '0.0'),
            ('use_sim_time', use_sim_time)
        ]
    )
    
    # twist_mux node - multiplexes velocity commands from multiple sources
    twist_mux_node = Node(
        package='twist_mux',
        executable='twist_mux',
        parameters=[twist_mux_config, {'use_sim_time': use_sim_time}],
        remappings=[('/cmd_vel_out', '/cmd_vel')],
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
        parameters=[joystick_config, {'use_sim_time': use_sim_time}],
        remappings=[('/cmd_vel', '/cmd_vel_joy')],
        condition=IfCondition(use_joystick),
        output='screen'
    )
    
    # Block observer node - observes blocks and publishes sum of pairwise distances
    block_observer = Node(
        package='turtlebot_simulation',
        executable='block_observer.py',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )
    
    return LaunchDescription([
        declare_use_sim_time_arg,
        declare_gui_arg,
        declare_world_arg,
        declare_use_joystick_arg,
        declare_model_arg,
        gz_resource_path,
        gz_gui_plugin_path,
        gz_sim,
        clock_bridge,
        robot_spawn,
        twist_mux_node,
        joy_node,
        teleop_twist_joy_node,
        block_observer
    ])
