#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
from geometry_msgs.msg import TwistStamped
from turtlebot_simulation.msg import SensorsAggregated


class LocalPerception(Node):
    """
    ROS2 node that subscribes to aggregated sensor data
    and publishes to the agent uplink topic.
    """

    def __init__(self):
        super().__init__('local_perception')

        # Private member for latest sensor data
        self._latest_sensors = None

        # Private member for latest cmd_vel
        self._latest_cmd_vel = None

        # Private member for latest goal state
        self._latest_goal_state = None

        # Subscribe to aggregated sensor data
        self.sensors_sub = self.create_subscription(
            SensorsAggregated,
            '/sensors_aggregated',
            self._on_sensors_aggregated,
            10
        )

        # Subscribe to cmd_vel
        self.cmd_vel_sub = self.create_subscription(
            TwistStamped,
            '/diffdrive_controller/cmd_vel',
            self._on_cmd_vel,
            10
        )

        # Subscribe to goal state
        self.goal_state_sub = self.create_subscription(
            Int32,
            '/goal_state',
            self._on_goal_state,
            10
        )

        # Publisher for agent uplink
        self.uplink_publisher = self.create_publisher(Int32, '/agent_uplink', 10)

        # Create 25Hz timer for publishing
        self.timer = self.create_timer(1.0 / 25.0, self._timer_callback)

        self.get_logger().info('LocalPerception node initialized')
        self.get_logger().info('Subscribed to /sensors_aggregated')
        self.get_logger().info('Publishing to /agent_uplink at 25Hz')

    def _on_sensors_aggregated(self, msg: SensorsAggregated):
        """
        Callback for aggregated sensor data.
        Stores the latest sensor data for processing.
        """
        self._latest_sensors = msg

    def _on_cmd_vel(self, msg: TwistStamped):
        """
        Callback for cmd_vel messages.
        Stores the latest command velocity.
        """
        self._latest_cmd_vel = msg

    def _on_goal_state(self, msg: Int32):
        """
        Callback for goal_state messages.
        Stores the latest goal state.
        """
        self._latest_goal_state = msg

    def _timer_callback(self):
        """
        Timer callback that runs at 25Hz.
        Publishes to agent_uplink topic.
        """
        uplink_msg = Int32()
        uplink_msg.data = 0
        self.uplink_publisher.publish(uplink_msg)


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
