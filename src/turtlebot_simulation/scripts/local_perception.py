#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, Image
from std_msgs.msg import Int32


class LocalPerception(Node):
    """
    ROS2 node that subscribes to IMU data and camera images,
    runs a PyTorch model on them at 25Hz, and publishes the result.
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

        # Create 25Hz timer for model inference
        self.timer = self.create_timer(1.0 / 25.0, self._inference_callback)

        # Initialize PyTorch model (skeleton)
        self._model = None
        self._initialize_model()

        self.get_logger().info('LocalPerception node initialized')
        self.get_logger().info('Subscribed to /imu/data and /oakd/rgb/preview/image_raw')
        self.get_logger().info('Publishing to /agent_uplink at 25Hz')

    def _initialize_model(self):
        """
        Initialize the PyTorch model.
        This is a skeleton - actual model implementation would go here.
        """
        # TODO: Initialize PyTorch model
        # Example:
        # import torch
        # self._model = YourModelClass()
        # self._model.load_state_dict(torch.load('path/to/weights.pth'))
        # self._model.eval()
        
        self.get_logger().info('Model initialization (skeleton) - ready for implementation')

    def _on_imu_data(self, msg: Imu):
        """Callback for IMU data - stores the most recent message."""
        self._latest_imu = msg

    def _on_image(self, msg: Image):
        """Callback for camera images - stores the most recent message."""
        self._latest_image = msg

    def _inference_callback(self):
        """
        Timer callback that runs at 25Hz.
        Performs model inference on the latest image and IMU data.
        """
        # Check if we have received data from both topics
        if self._latest_imu is None or self._latest_image is None:
            return

        # TODO: Preprocess data and run model inference
        # Example:
        # image_tensor = self._preprocess_image(self._latest_image)
        # imu_tensor = self._preprocess_imu(self._latest_imu)
        # 
        # with torch.no_grad():
        #     output = self._model(image_tensor, imu_tensor)
        #     result = int(output.item())

        # For now, just publish a dummy value
        result = 0  # Placeholder - replace with actual model output

        # Publish result to agent_uplink topic
        msg = Int32()
        msg.data = result
        self.uplink_publisher.publish(msg)

    def _preprocess_image(self, image_msg: Image):
        """
        Preprocess image message for model input.
        This is a skeleton - actual preprocessing would go here.
        """
        # TODO: Convert ROS Image message to PyTorch tensor
        # Example:
        # import numpy as np
        # import torch
        # from cv_bridge import CvBridge
        # 
        # bridge = CvBridge()
        # cv_image = bridge.imgmsg_to_cv2(image_msg, desired_encoding='rgb8')
        # image_tensor = torch.from_numpy(cv_image).permute(2, 0, 1).float()
        # image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension
        # return image_tensor
        pass

    def _preprocess_imu(self, imu_msg: Imu):
        """
        Preprocess IMU message for model input.
        This is a skeleton - actual preprocessing would go here.
        """
        # TODO: Extract IMU data and convert to PyTorch tensor
        # Example:
        # import torch
        # 
        # # Extract orientation quaternion
        # orientation = [
        #     imu_msg.orientation.x,
        #     imu_msg.orientation.y,
        #     imu_msg.orientation.z,
        #     imu_msg.orientation.w
        # ]
        # 
        # # Extract angular velocity
        # angular_velocity = [
        #     imu_msg.angular_velocity.x,
        #     imu_msg.angular_velocity.y,
        #     imu_msg.angular_velocity.z
        # ]
        # 
        # # Extract linear acceleration
        # linear_acceleration = [
        #     imu_msg.linear_acceleration.x,
        #     imu_msg.linear_acceleration.y,
        #     imu_msg.linear_acceleration.z
        # ]
        # 
        # # Combine all features
        # imu_features = orientation + angular_velocity + linear_acceleration
        # imu_tensor = torch.tensor(imu_features).float().unsqueeze(0)
        # return imu_tensor
        pass


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
