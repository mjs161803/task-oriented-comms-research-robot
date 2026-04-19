#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, Int32


class Teacher(Node):
    """
    ROS2 node that subscribes to /block_distances and publishes to goal_state.
    Publishes 1 if the received distance is below threshold, 0 otherwise.
    """

    DISTANCE_THRESHOLD = 1.0

    def __init__(self):
        super().__init__('teacher')

        # Publisher for goal state (1 = goal reached, 0 = not reached)
        self.goal_publisher = self.create_publisher(Int32, 'goal_state', 10)

        # Subscribe to block distances
        self.distance_sub = self.create_subscription(
            Float64,
            '/block_distances',
            self.on_block_distance,
            10
        )

        self.get_logger().info(
            f'Teacher: subscribed to /block_distances, publishing to goal_state '
            f'(threshold={self.DISTANCE_THRESHOLD})'
        )

    def on_block_distance(self, msg: Float64):
        """
        Callback for /block_distances messages.
        Publishes 1 if distance < threshold, 0 otherwise.
        """
        goal_msg = Int32()
        if msg.data < self.DISTANCE_THRESHOLD:
            goal_msg.data = 1
        else:
            goal_msg.data = 0

        self.goal_publisher.publish(goal_msg)


def main(args=None):
    rclpy.init(args=args)
    node = Teacher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
