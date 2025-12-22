#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from gazebo_msgs.srv import GetEntityState
from std_msgs.msg import Float64
import math
import threading
import time


class BlockObserver(Node):
    """
    ROS2 node that observes the four blocks in the Gazebo simulation and publishes
    the sum total of the pairwise distances between them at 30 Hz.
    
    With 4 blocks, there are C(4,2) = 6 pairwise distances calculated:
    - block_1 <-> block_2
    - block_1 <-> block_3
    - block_1 <-> block_4
    - block_2 <-> block_3
    - block_2 <-> block_4
    - block_3 <-> block_4
    
    Note: Requires that Gazebo server is running and /gazebo/get_entity_state
    service is available. Uses a multi-threaded executor to handle service calls
    within the timer callback.
    """

    def __init__(self):
        super().__init__('block_observer')
        
        # Create a Reentrant Callback Group to allow concurrent callback execution
        # This is essential for making service calls within a timer callback
        self.callback_group = ReentrantCallbackGroup()
        
        # Block names in the simulation
        self.block_names = ['block_1', 'block_2', 'block_3', 'block_4']
        
        # Create publisher for the block distances
        self.distances_publisher = self.create_publisher(
            Float64,
            'block_distances',
            10
        )
        
        # Service discovery and client (created lazily once resolved)
        self.service_name = None
        self.get_entity_state_client = None
        
        # Track service availability
        self.service_available = False
        self.service_check_count = 0
        
        self.get_logger().info('BlockObserver initialized. Resolving Gazebo GetEntityState service...')
        
        # State tracking for asynchronous operations (protected by lock)
        self._state_lock = threading.RLock()  # Reentrant lock for nested access
        self.iteration_count = 0
        self.block_positions = {}   # Maps block_name -> (x, y, z) or None
        self.request_in_flight = {} # Tracks if a request is currently in flight for a block
        
        self.request_timeout_sec = 2.0  # Timeout for individual service calls
        
        # Create timer to trigger observation at 30 Hz (1/30 = 0.0333... seconds)
        # Assign to callback group to allow concurrent execution with service calls
        self.timer = self.create_timer(
            1.0 / 30.0,  # 30 Hz
            self.observe_and_publish,
            callback_group=self.callback_group
        )

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
            # Create client with reentrant callback group for async operations
            self.get_entity_state_client = self.create_client(
                GetEntityState, 
                self.service_name,
                callback_group=self.callback_group
            )
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
        
        self.get_logger().debug('Service check: service_available is False')
        
        # Resolve service name and create client if needed
        if self.get_entity_state_client is None:
            self.get_logger().debug('Service check: client is None, resolving')
            if not self.resolve_service_name():
                # Service not resolved yet
                if self.service_check_count % 30 == 0:  # Log once per second at 30 Hz
                    self.get_logger().warn("GetEntityState service not found yet. Retrying discovery...")
                self.service_check_count += 1
                return False

        # Check if service is ready (non-blocking with 0 timeout)
        self.get_logger().debug('Service check: checking if service is ready')
        try:
            if self.get_entity_state_client.wait_for_service(timeout_sec=0.0):
                self.service_available = True
                self.get_logger().info(f"✓ {self.service_name} is now available!")
                return True
        except Exception as e:
            self.get_logger().warn(f"Error checking service availability: {e}")
            return False
        
        # Log progress every 30 iterations (~1 second at 30 Hz)
        if self.service_check_count % 30 == 0:
            svc = self.service_name or '<resolving>'
            self.get_logger().warn(f"Service {svc} not yet available. Retrying...")
        self.service_check_count += 1
        
        return False
    
    def request_block_position_async(self, block_name):
        """
        Asynchronously request the position of a block from Gazebo.
        Must be called from within the lock.
        
        Args:
            block_name: Name of the block entity in Gazebo
        """
        # Skip if already requesting this block
        if self.request_in_flight.get(block_name, False):
            return
        
        # Mark that a request is in flight
        self.request_in_flight[block_name] = True
        
        # Release lock and initiate request (will be re-acquired by caller)
        request = GetEntityState.Request()
        request.name = block_name
        request.reference_frame = 'world'
        
        try:
            # Initiate async call with callback
            future = self.get_entity_state_client.call_async(request)
            
            # Add callback to handle the response
            future.add_done_callback(
                lambda f: self._on_block_position_response(block_name, f)
            )
            
        except Exception as e:
            self.get_logger().error(f'Exception initiating call for {block_name}: {type(e).__name__}: {str(e)}')
            self.request_in_flight[block_name] = False
            self.block_positions[block_name] = None
    
    def _on_block_position_response(self, block_name, future):
        """
        Callback invoked when a block position service response is received.
        Runs in the context of the callback group.
        
        Args:
            block_name: Name of the block entity
            future: The completed future object
        """
        try:
            result = future.result()
            
            position = None
            if result is not None and result.success:
                # Extract position
                pos = result.state.pose.position
                position = (pos.x, pos.y, pos.z)
            
        except Exception as e:
            self.get_logger().error(f'Exception in response callback for {block_name}: {type(e).__name__}: {str(e)}')
            position = None
        
        # Update shared state under lock
        with self._state_lock:
            self.block_positions[block_name] = position
            self.request_in_flight[block_name] = False
    
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
    
    def observe_and_publish(self):
        """
        Main timer callback at 30 Hz. Initiates async requests for block positions,
        collects results, calculates sum of pairwise distances, and publishes to
        'block_distances' topic.
        """
        # Check if service is available (non-blocking)
        if not self.ensure_service_available():
            return
        
        # Log first time service becomes available
        if not hasattr(self, '_first_publish_logged'):
            self.get_logger().info('Service available, starting block observation...')
            self._first_publish_logged = True
        
        try:
            # Initiate async requests - keep lock time minimal
            with self._state_lock:
                # Initiate async requests for all blocks that don't have one in flight
                for block_name in self.block_names:
                    self.request_block_position_async(block_name)
                
                # Collect currently available positions (don't wait)
                positions = []
                failed_blocks = []
                for block_name in self.block_names:
                    pos = self.block_positions.get(block_name)
                    if pos is not None:
                        positions.append(pos)
                    else:
                        failed_blocks.append(block_name)
            
            # Only publish if we have all block positions
            if len(positions) != len(self.block_names):
                self.iteration_count += 1
                return
            
            # Calculate sum of all pairwise distances (6 pairs for 4 blocks)
            total_distance = 0.0
            num_blocks = len(positions)
            
            for i in range(num_blocks):
                for j in range(i + 1, num_blocks):
                    distance = self.calculate_pairwise_distance(positions[i], positions[j])
                    total_distance += distance
            
            # Publish the sum of pairwise distances
            msg = Float64()
            msg.data = total_distance
            self.distances_publisher.publish(msg)
            
            # # Log occasionally (every 30 iterations = every 1 second at 30 Hz)
            # self.iteration_count += 1
            # if self.iteration_count % 30 == 0:
            #     self.get_logger().info(f'Block distances sum: {total_distance:.4f}')
        
        except Exception as e:
            self.get_logger().error(f'Exception in observe_and_publish: {type(e).__name__}: {str(e)}', exc_info=True)


def main(args=None):
    rclpy.init(args=args)
    node = BlockObserver()

    try:
        # Use MultiThreadedExecutor to allow service calls within timer callback
        executor = rclpy.executors.MultiThreadedExecutor()
        executor.add_node(node)
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
