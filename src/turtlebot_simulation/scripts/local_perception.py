#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, Image
from std_msgs.msg import Int32
from turtlebot_simulation.msg import SensorsAggregated


class LocalPerception(Node):
    """
    ROS2 node that subscribes to IMU data and camera images
    and publishes to the agent uplink topic.
    """

    def __init__(self):
        super().__init__('local_perception')

        # Private members for most recent messages
        self._latest_imu = None
        self._latest_image = None

        # Subscribe to IMU data
        self.imu_sub = self.create_subscription(
            Imu,
            '/imu/data',
            self._on_imu_data,
            10
        )

        # Subscribe to camera image
        self.image_sub = self.create_subscription(
            Image,
            '/oakd/rgb/preview/image_raw',
            self._on_image,
            10
        )

        # Publisher for agent uplink
        self.uplink_publisher = self.create_publisher(Int32, '/agent_uplink', 10)

        # Publisher for aggregated sensor data
        self.sensors_publisher = self.create_publisher(SensorsAggregated, '/sensors_aggregated', 10)

        # Create 25Hz timer for processing
        self.timer = self.create_timer(1.0 / 25.0, self._timer_callback)

        self.get_logger().info('LocalPerception node initialized')
        self.get_logger().info('Subscribed to /imu/data and /oakd/rgb/preview/image_raw')
        self.get_logger().info('Publishing to /agent_uplink and /sensors_aggregated at 25Hz')

    def _on_imu_data(self, msg: Imu):
        """Callback for IMU data - stores the most recent message."""
        self._latest_imu = msg

    def _on_image(self, msg: Image):
        """Callback for camera images - stores the most recent message."""
        self._latest_image = msg

    def _timer_callback(self):
        """
        Timer callback that runs at 25Hz.
        """
        # Check if we have received data from both topics
        if self._latest_imu is None or self._latest_image is None:
            return

        # Publish aggregated sensor data
        sensors_msg = SensorsAggregated()
        sensors_msg.header.stamp = self.get_clock().now().to_msg()
        sensors_msg.header.frame_id = 'base_link'
        sensors_msg.image = self._latest_image
        sensors_msg.imu = self._latest_imu
        self.sensors_publisher.publish(sensors_msg)

        # Publish to agent_uplink topic
        msg = Int32()
        msg.data = 0
        self.uplink_publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = LocalPerception()
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
