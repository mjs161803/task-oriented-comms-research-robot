#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """
    Launch file for running episodic simulation with TurtleBot4.
    
    This launch file:
    - Launches the turtlebot4_gazebo simulation
    - Launches an episode manager node to control simulation episodes
    - Runs the simulation for a configurable number of episodes
    - Each episode runs for a configurable duration (default: 60 seconds)
    - Scores are stored to a file after each episode
    """
    
    # Get package directory
    pkg_turtlebot_simulation = FindPackageShare('turtlebot_simulation')
    
    # Launch arguments
    num_episodes = LaunchConfiguration('num_episodes', default='10')
    episode_duration = LaunchConfiguration('episode_duration', default='60.0')
    output_file = LaunchConfiguration('output_file', default='episode_scores.txt')
    gui = LaunchConfiguration('gui', default='true')
    use_joystick = LaunchConfiguration('use_joystick', default='false')  # Disable joystick by default for episodic runs
    model = LaunchConfiguration('model', default='standard')
    
    declare_num_episodes_arg = DeclareLaunchArgument(
        'num_episodes',
        default_value='10',
        description='Number of episodes to run'
    )
    
    declare_episode_duration_arg = DeclareLaunchArgument(
        'episode_duration',
        default_value='60.0',
        description='Duration of each episode in seconds'
    )
    
    declare_output_file_arg = DeclareLaunchArgument(
        'output_file',
        default_value='episode_scores.txt',
        description='Path to output file for storing episode scores'
    )
    
    declare_gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='true',
        description='Set to "true" to launch Gazebo GUI'
    )
    
    declare_use_joystick_arg = DeclareLaunchArgument(
        'use_joystick',
        default_value='false',
        description='Set to "true" to enable joystick control (typically disabled for episodic runs)'
    )
    
    declare_model_arg = DeclareLaunchArgument(
        'model',
        default_value='standard',
        description='TurtleBot4 model: standard or lite'
    )
    
    # Include the main turtlebot4_gazebo launch file
    turtlebot4_gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                pkg_turtlebot_simulation,
                'launch',
                'turtlebot4_gazebo.launch.py'
            ])
        ]),
        launch_arguments={
            'gui': gui,
            'use_joystick': use_joystick,
            'use_sim_time': 'true',
            'model': model
        }.items()
    )
    
    # Episode manager node
    episode_manager_node = Node(
        package='turtlebot_simulation',
        executable='episode_manager.py',
        name='episode_manager',
        output='screen',
        parameters=[{
            'num_episodes': num_episodes,
            'episode_duration': episode_duration,
            'output_file': output_file,
            'use_sim_time': True
        }]
    )
    
    return LaunchDescription([
        declare_num_episodes_arg,
        declare_episode_duration_arg,
        declare_output_file_arg,
        declare_gui_arg,
        declare_use_joystick_arg,
        declare_model_arg,
        turtlebot4_gazebo_launch,
        episode_manager_node
    ])
