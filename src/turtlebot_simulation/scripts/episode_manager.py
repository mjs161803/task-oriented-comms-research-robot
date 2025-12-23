#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from std_srvs.srv import Empty
import time
import os
from datetime import datetime


class EpisodeManager(Node):
    """
    ROS2 node that manages episodic simulation runs in Gazebo.
    
    This node:
    - Subscribes to /block_distances topic to track the latest score
    - Runs the simulation for 60 seconds per episode
    - Stores the final score to a file at the end of each episode
    - Resets the simulation between episodes using Gazebo reset service
    - Shuts down after a configured number of episodes
    """

    def __init__(self):
        super().__init__('episode_manager')
        
        # Declare parameters
        self.declare_parameter('num_episodes', 10)
        self.declare_parameter('episode_duration', 60.0)  # seconds
        self.declare_parameter('output_file', 'episode_scores.txt')
        
        # Get parameters
        self.num_episodes = self.get_parameter('num_episodes').value
        self.episode_duration = self.get_parameter('episode_duration').value
        self.output_file = self.get_parameter('output_file').value
        
        # State tracking
        self.current_episode = 0
        self.latest_score = None
        self.episode_start_time = None
        self.is_running = False
        self.waiting_for_reset = False
        self.reset_wait_start = None
        self.should_shutdown = False  # Flag for clean shutdown
        
        # Subscribe to block distances
        self.score_subscriber = self.create_subscription(
            Float64,
            'block_distances',
            self.score_callback,
            10
        )
        
        # Create service client for resetting simulation
        self.reset_world_client = self.create_client(Empty, '/reset_world')
        
        # Timer to check episode completion (check at 10 Hz)
        self.check_timer = self.create_timer(0.1, self.check_episode_timer)
        
        self.get_logger().info(f'Episode Manager initialized')
        self.get_logger().info(f'  Number of episodes: {self.num_episodes}')
        self.get_logger().info(f'  Episode duration: {self.episode_duration} seconds')
        self.get_logger().info(f'  Output file: {self.output_file}')
        
        # Initialize output file with header
        self.initialize_output_file()
        
        # Wait for reset service to be available
        self.get_logger().info('Waiting for /reset_world service...')
        if not self.reset_world_client.wait_for_service(timeout_sec=30.0):
            self.get_logger().warn('/reset_world service not available after 30 seconds, continuing anyway')
        else:
            self.get_logger().info('/reset_world service is available')
        
        # Start first episode
        self.start_episode()
    
    def initialize_output_file(self):
        """Initialize the output file with a header."""
        try:
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(self.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(self.output_file, 'w') as f:
                f.write(f"# Episode Scores - Generated at {datetime.now().isoformat()}\n")
                f.write(f"# Total episodes: {self.num_episodes}\n")
                f.write(f"# Episode duration: {self.episode_duration} seconds\n")
                f.write("# Format: episode_number,score\n")
            
            self.get_logger().info(f'Initialized output file: {self.output_file}')
        except Exception as e:
            self.get_logger().error(f'Failed to initialize output file: {e}')
    
    def score_callback(self, msg):
        """Callback for /block_distances topic."""
        self.latest_score = msg.data
    
    def start_episode(self):
        """Start a new episode."""
        self.current_episode += 1
        self.latest_score = None  # Reset score for new episode
        self.episode_start_time = time.time()
        self.is_running = True
        
        self.get_logger().info(f'=' * 60)
        self.get_logger().info(f'Starting Episode {self.current_episode}/{self.num_episodes}')
        self.get_logger().info(f'=' * 60)
    
    def check_episode_timer(self):
        """Timer callback to check if episode should end or if waiting after reset."""
        # Check if shutdown was requested
        if self.should_shutdown:
            raise SystemExit  # This will trigger clean shutdown in the main function
        
        # Check if we're waiting after a reset
        if self.waiting_for_reset:
            elapsed_wait = time.time() - self.reset_wait_start
            if elapsed_wait >= 1.0:  # Wait 1 second after reset
                self.waiting_for_reset = False
                self.start_episode()
            return
        
        if not self.is_running:
            return
        
        elapsed_time = time.time() - self.episode_start_time
        
        # Check if episode duration has been reached
        if elapsed_time >= self.episode_duration:
            self.end_episode()
    
    def end_episode(self):
        """End the current episode and store the score."""
        self.is_running = False
        
        # Get final score
        final_score = self.latest_score if self.latest_score is not None else 0.0
        
        self.get_logger().info(f'Episode {self.current_episode} completed')
        self.get_logger().info(f'Final score: {final_score:.4f}')
        
        # Store score to file
        self.store_score(self.current_episode, final_score)
        
        # Check if we should continue or shutdown
        if self.current_episode >= self.num_episodes:
            self.get_logger().info('=' * 60)
            self.get_logger().info(f'All {self.num_episodes} episodes completed!')
            self.get_logger().info(f'Scores saved to: {self.output_file}')
            self.get_logger().info('=' * 60)
            self.get_logger().info('Shutting down...')
            # Set flag to trigger shutdown from main thread
            self.should_shutdown = True
        else:
            # Reset simulation and start next episode
            self.reset_simulation()
    
    def store_score(self, episode_number, score):
        """Store the episode score to the output file."""
        try:
            with open(self.output_file, 'a') as f:
                f.write(f"{episode_number},{score:.6f}\n")
            self.get_logger().info(f'Stored score for episode {episode_number}: {score:.6f}')
        except Exception as e:
            self.get_logger().error(f'Failed to store score: {e}')
    
    def reset_simulation(self):
        """Reset the Gazebo simulation."""
        self.get_logger().info('Resetting simulation...')
        
        # Create reset request
        request = Empty.Request()
        
        # Call reset service asynchronously
        future = self.reset_world_client.call_async(request)
        future.add_done_callback(self.reset_callback)
    
    def reset_callback(self, future):
        """Callback for reset service response."""
        try:
            response = future.result()
            self.get_logger().info('Simulation reset successful')
        except Exception as e:
            self.get_logger().error(f'Failed to reset simulation: {e}')
        
        # Set state to wait for simulation to stabilize
        self.waiting_for_reset = True
        self.reset_wait_start = time.time()


def main(args=None):
    rclpy.init(args=args)
    node = EpisodeManager()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except SystemExit:
        # Normal shutdown initiated by the node
        pass
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
