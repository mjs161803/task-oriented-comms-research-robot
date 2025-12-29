#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from tf2_msgs.msg import TFMessage
import math
import subprocess
import re


class BlockObserver(Node):
    """
    ROS2 node that subscribes to the bridged Gazebo pose stream
    (/world/turtlebot_world/pose/info) and publishes the sum of the
    pairwise distances among the four blocks to /block_distances at ~30 Hz.
    """

    def __init__(self):
        super().__init__('block_observer')

        # Block names in the simulation
        self.block_names = ['block_1', 'block_2', 'block_3', 'block_4']

        # Map name -> pose index in the bridged TFMessage (fallback when child_frame_id is empty)
        self.pose_index_by_name = self._discover_pose_indices()

        # Publisher for the sum of pairwise distances
        self.distances_publisher = self.create_publisher(Float64, '/block_distances', 10)

        # Latest positions per block_name -> (x, y, z)
        self.block_positions = {name: None for name in self.block_names}

        # Subscribe to the pose stream bridged to ROS
        self.pose_sub = self.create_subscription(
            TFMessage,
            '/world/turtlebot_world/pose/info',
            self.on_pose_info,
            10
        )

        # Compute and publish at ~30 Hz (independent of pose publish rate)
        self.timer = self.create_timer(1.0 / 30.0, self.observe_and_publish)

        # Log throttling for published distance values
        self._publish_count = 0
        self._log_every_n = 60  # ~2 seconds at 30 Hz

        self.get_logger().info('BlockObserver: subscribed to /world/turtlebot_world/pose/info')

    def on_pose_info(self, msg: TFMessage):
        """
        Update cached positions from a TFMessage created by the bridge
        mapping gz.msgs.Pose_V -> tf2_msgs/TFMessage. Each transform is
        assumed to be relative to the world frame and uses the entity name
        as child_frame_id (e.g., block_1 .. block_4).
        """
        try:
            # First try using child_frame_id if present
            used_child_ids = False
            for t in msg.transforms:
                name = t.child_frame_id
                if name in self.block_names:
                    p = t.transform.translation
                    self.block_positions[name] = (p.x, p.y, p.z)
                    used_child_ids = True

            if used_child_ids:
                return

            # Fallback: use index mapping captured from raw Gazebo message
            if not self.pose_index_by_name:
                return

            for idx, t in enumerate(msg.transforms):
                for block_name, pose_idx in self.pose_index_by_name.items():
                    if idx == pose_idx:
                        p = t.transform.translation
                        self.block_positions[block_name] = (p.x, p.y, p.z)
                        break
        except Exception as e:
            self.get_logger().warn(f'Failed to parse TFMessage: {type(e).__name__}: {str(e)}')

    def _discover_pose_indices(self):
        """Sample one raw Gazebo pose/info message to map name -> index."""
        try:
            raw = subprocess.check_output(
                ['gz', 'topic', '-e', '-t', '/world/turtlebot_world/pose/info', '-n', '1'],
                text=True,
                timeout=5.0
            )
        except Exception as e:
            self.get_logger().warn(f'Could not sample pose/info for name mapping: {type(e).__name__}: {e}')
            return {}

        names = []
        for line in raw.splitlines():
            m = re.search(r'name:\s*"([^"]+)"', line)
            if m:
                names.append(m.group(1))

        pose_index_by_name = {name: idx for idx, name in enumerate(names)}

        missing = [n for n in self.block_names if n not in pose_index_by_name]
        if missing:
            self.get_logger().warn(f'Pose index mapping missing names: {missing} (found: {list(pose_index_by_name.keys())})')

        return pose_index_by_name

    def calculate_pairwise_distance(self, pos1, pos2):
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        dz = pos2[2] - pos1[2]
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def observe_and_publish(self):
        # Collect positions; only publish when all four are available
        positions = []
        for name in self.block_names:
            pos = self.block_positions.get(name)
            if pos is None:
                return
            positions.append(pos)

        # Calculate sum of all pairwise distances (6 pairs for 4 blocks)
        total_distance = 0.0
        n = len(positions)
        for i in range(n):
            for j in range(i + 1, n):
                total_distance += self.calculate_pairwise_distance(positions[i], positions[j])

        msg = Float64()
        msg.data = total_distance
        self.distances_publisher.publish(msg)

        # Lightweight periodic log
        self._publish_count += 1
        if self._publish_count % self._log_every_n == 0:
            self.get_logger().info(f'/block_distances = {total_distance:.4f}')


def main(args=None):
    rclpy.init(args=args)
    node = BlockObserver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
