#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32


class LocalActuator(Node):
    """
    ROS2 node that subscribes to /agent_downlink.
    """

    def __init__(self):
        super().__init__('local_actuator')

        # Private member for latest downlink message
        self._latest_downlink = None

        # Subscribe to agent downlink
        self.downlink_sub = self.create_subscription(
            Int32,
            '/agent_downlink',
            self._on_downlink,
            10
        )

        self.get_logger().info('LocalActuator node initialized')
        self.get_logger().info('Subscribed to /agent_downlink')

    def _on_downlink(self, msg: Int32):
        """
        Callback for agent_downlink messages.
        Stores the latest downlink message.
        """
        self._latest_downlink = msg


def main(args=None):
    rclpy.init(args=args)
    node = LocalActuator()
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
