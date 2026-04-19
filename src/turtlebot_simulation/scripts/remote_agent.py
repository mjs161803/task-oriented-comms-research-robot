#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32


class RemoteAgent(Node):
    """
    ROS2 node that subscribes to /agent_uplink and publishes to /agent_downlink.
    """

    def __init__(self):
        super().__init__('remote_agent')

        # Private member for latest uplink message
        self._latest_uplink = None

        # Subscribe to agent uplink
        self.uplink_sub = self.create_subscription(
            Int32,
            '/agent_uplink',
            self._on_uplink,
            10
        )

        # Publisher for agent downlink
        self.downlink_publisher = self.create_publisher(Int32, '/agent_downlink', 10)

        # Create 25Hz timer for publishing
        self.timer = self.create_timer(1.0 / 25.0, self._timer_callback)

        self.get_logger().info('RemoteAgent node initialized')
        self.get_logger().info('Subscribed to /agent_uplink')
        self.get_logger().info('Publishing to /agent_downlink at 25Hz')

    def _on_uplink(self, msg: Int32):
        """
        Callback for agent_uplink messages.
        Stores the latest uplink message.
        """
        self._latest_uplink = msg

    def _timer_callback(self):
        """
        Timer callback that runs at 25Hz.
        Publishes dummy variable to agent_downlink topic.
        """
        downlink_msg = Int32()
        downlink_msg.data = 0
        self.downlink_publisher.publish(downlink_msg)


def main(args=None):
    rclpy.init(args=args)
    node = RemoteAgent()
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
