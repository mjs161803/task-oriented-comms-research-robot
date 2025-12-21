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
    
    Note: Requires that Gazebo server is running and /gazebo/get_entity_state
    service is available. The node will retry connecting asynchronously.
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
        
        # Service discovery and client (created lazily once resolved)
        self.service_name = None
        self.get_entity_state_client = None
        
        # Track service availability
        self.service_available = False
        self.service_check_count = 0
        
        self.get_logger().info('Initialized. Resolving Gazebo GetEntityState service...')
        
        # State variable for tracking iterations
        self.iteration_count = 0
        
        # Create timer to publish at 100 Hz (0.01 seconds)
        self.timer = self.create_timer(0.01, self.calculate_and_publish_metric)

    def resolve_service_name(self):
        """
        Discover the correct GetEntityState service name exposed by Gazebo.
        Tries to find any service ending with 'get_entity_state' of type gazebo_msgs/srv/GetEntityState.
        Prefers '/gazebo/get_entity_state' when available.
        """
        names_and_types = self.get_service_names_and_types()
        candidates = []
        for name, types in names_and_types:
            # Match by suffix to handle namespaced setups
            if name.endswith('get_entity_state'):
                for t in types:
                    if 'gazebo_msgs/srv/GetEntityState' in t:
                        candidates.append(name)
                        break

        if not candidates:
            return False

        # Prefer '/gazebo/get_entity_state' if present
        candidates.sort(key=lambda n: (0 if n.startswith('/gazebo/') else 1, len(n)))
        chosen = candidates[0]

        if self.service_name != chosen:
            self.service_name = chosen
            self.get_entity_state_client = self.create_client(GetEntityState, self.service_name)
            self.service_available = False
            self.get_logger().info(f"Using service '{self.service_name}' for GetEntityState")

        return True
    
    def ensure_service_available(self):
        """
        Check if service is available. Non-blocking, call this before using the service.
        Logs occasionally to avoid spam.
        """
        if self.service_available:
            return True
        
        # Resolve service name and create client if needed
        if self.get_entity_state_client is None:
            self.resolve_service_name()

        # If still no client, keep retrying
        if self.get_entity_state_client is None:
            if self.service_check_count % 100 == 0:
                self.get_logger().warn("GetEntityState service not found yet. Retrying discovery...")
            self.service_check_count += 1
            return False

        # Check if service is ready (non-blocking)
        if self.get_entity_state_client.wait_for_service(timeout_sec=0.0):
            self.service_available = True
            self.get_logger().info(f"✓ {self.service_name} is now available!")
            return True
        
        # Log progress every 100 iterations (~1 second at 100 Hz)
        if self.service_check_count % 100 == 0:
            svc = self.service_name or '<resolving>'
            self.get_logger().warn(f"Service {svc} not yet available. Retrying...")
        self.service_check_count += 1
        
        return False
    
    def get_block_position_sync(self, block_name):
        """
        Get the position of a block from Gazebo synchronously.
        
        Args:
            block_name: Name of the block entity in Gazebo
            
        Returns:
            tuple: (x, y, z) position or None if failed
        """
        request = GetEntityState.Request()
        request.name = block_name
        request.reference_frame = 'world'
        
        try:
            # Use the service client for synchronous calls
            future = self.get_entity_state_client.call_async(request)
            rclpy.spin_until_future_complete(self, future, timeout_sec=1.0)
            
            if future.result() is None:
                self.get_logger().debug(f'Service call for {block_name} returned None (timeout or no response)')
                return None
            
            result = future.result()
            if not result.success:
                self.get_logger().debug(f'Service call for {block_name} succeeded=False. Response: {result}')
                return None
            
            pos = result.state.pose.position
            return (pos.x, pos.y, pos.z)
        except Exception as e:
            self.get_logger().error(f'Exception getting state for {block_name}: {type(e).__name__}: {str(e)}')
            import traceback
            self.get_logger().error(f'Traceback: {traceback.format_exc()}')
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
        # Check if service is available (non-blocking)
        if not self.ensure_service_available():
            return
        
        # Get positions of all blocks
        positions = []
        failed_blocks = []
        for block_name in self.block_names:
            pos = self.get_block_position_sync(block_name)
            if pos is not None:
                positions.append(pos)
            else:
                failed_blocks.append(block_name)
        
        # Only publish if we have all block positions
        if len(positions) != len(self.block_names):
            if self.iteration_count % 100 == 0:  # Log once per second
                self.get_logger().warn(f'Failed to retrieve positions for: {", ".join(failed_blocks)}')
            self.iteration_count += 1
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
        self.iteration_count += 1
        if self.iteration_count % 100 == 0:
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
