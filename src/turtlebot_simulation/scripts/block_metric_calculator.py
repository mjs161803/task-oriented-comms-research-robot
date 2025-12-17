#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import GetEntityState
from std_msgs.msg import Float64
import math


class BlockMetricCalculator(Node):
    """
    ROS2 node that calculates the sum of pairwise distances between blocks
    in the Gazebo simulation and publishes the metric at 100 Hz.
    """

    def __init__(self):
        super().__init__('block_metric_calculator')
        
        # Block names in the simulation
        self.block_names = ['block_1', 'block_2', 'block_3', 'block_4']
        
        # Create publisher for the distance metric
        self.metric_publisher = self.create_publisher(
            Float64,
            '/block_distance_metric',
            10
        )
        
        # Create service client for getting entity states from Gazebo
        self.get_entity_state_client = self.create_client(
            GetEntityState,
            '/gazebo/get_entity_state'
        )
        
        # Wait for the service to be available
        while not self.get_entity_state_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /gazebo/get_entity_state service...')
        
        self.get_logger().info('Service available. Starting metric calculation.')
        
        # Create timer to publish at 100 Hz (0.01 seconds)
        self.timer = self.create_timer(0.01, self.calculate_and_publish_metric)
    
    def get_block_position(self, block_name):
        """
        Get the position of a block from Gazebo.
        
        Args:
            block_name: Name of the block entity in Gazebo
            
        Returns:
            tuple: (x, y, z) position or None if failed
        """
        request = GetEntityState.Request()
        request.name = block_name
        request.reference_frame = 'world'
        
        try:
            future = self.get_entity_state_client.call_async(request)
            rclpy.spin_until_future_complete(self, future, timeout_sec=0.1)
            
            if future.result() is not None and future.result().success:
                pos = future.result().state.pose.position
                return (pos.x, pos.y, pos.z)
            else:
                self.get_logger().warn(f'Failed to get state for {block_name}')
                return None
        except Exception as e:
            self.get_logger().error(f'Error getting state for {block_name}: {str(e)}')
            return None
    
    def calculate_pairwise_distance(self, pos1, pos2):
        """
        Calculate Euclidean distance between two 3D positions.
        
        Args:
            pos1: tuple (x, y, z) of first position
            pos2: tuple (x, y, z) of second position
            
        Returns:
            float: Euclidean distance
        """
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        dz = pos2[2] - pos1[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def calculate_and_publish_metric(self):
        """
        Calculate sum of all pairwise distances between blocks and publish it.
        """
        # Get positions of all blocks
        positions = []
        for block_name in self.block_names:
            pos = self.get_block_position(block_name)
            if pos is not None:
                positions.append(pos)
            else:
                # If we can't get position for any block, skip this iteration
                return
        
        # Calculate sum of all pairwise distances
        total_distance = 0.0
        num_blocks = len(positions)
        
        for i in range(num_blocks):
            for j in range(i + 1, num_blocks):
                distance = self.calculate_pairwise_distance(positions[i], positions[j])
                total_distance += distance
        
        # Publish the metric
        msg = Float64()
        msg.data = total_distance
        self.metric_publisher.publish(msg)
        
        # Log occasionally (every 100 iterations = every 1 second at 100 Hz)
        if not hasattr(self, '_iteration_count'):
            self._iteration_count = 0
        self._iteration_count += 1
        
        if self._iteration_count % 100 == 0:
            self.get_logger().info(f'Block distance metric: {total_distance:.4f}')


def main(args=None):
    rclpy.init(args=args)
    node = BlockMetricCalculator()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
