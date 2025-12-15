#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Get package directories
    pkg_gazebo_ros = FindPackageShare('gazebo_ros')
    pkg_turtlebot_simulation = FindPackageShare('turtlebot_simulation')
    
    # Paths to world file
    world_file = PathJoinSubstitution([
        pkg_turtlebot_simulation,
        'worlds',
        'turtlebot_blocks.world'
    ])
    
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    gui = LaunchConfiguration('gui', default='true')
    world = LaunchConfiguration('world', default=world_file)
    
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
    
    # Gazebo server
    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                pkg_gazebo_ros,
                'launch',
                'gzserver.launch.py'
            ])
        ]),
        launch_arguments={
            'world': world,
            'verbose': 'false'
        }.items()
    )
    
    # Gazebo client
    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                pkg_gazebo_ros,
                'launch',
                'gzclient.launch.py'
            ])
        ]),
        condition=IfCondition(gui)
    )
    
    # Spawn Turtlebot3 model using gazebo model database
    # The TurtleBot3 waffle_pi model should be available if turtlebot3_gazebo is installed
    spawn_turtlebot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'turtlebot3_waffle_pi',
            '-database', 'turtlebot3_waffle_pi',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.01',
            '-Y', '0.0'
        ],
        output='screen',
    )
    
    return LaunchDescription([
        declare_use_sim_time_arg,
        declare_gui_arg,
        declare_world_arg,
        gzserver,
        gzclient,
        spawn_turtlebot
    ])

