#!/usr/bin/env python3

import os

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
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

        # Configurable parameters
        self.declare_parameter('model_config', 'local_model.yaml')
        self.declare_parameter('model_weights', '')
        self.declare_parameter('model_device', 'cuda')

        # Private members for most recent messages
        self._latest_imu = None
        self._latest_image = None
        self._cfg = {}
        self._bridge = None
        self._device = 'cpu'

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
        self._init_cv_bridge()

        self.get_logger().info('LocalPerception node initialized')
        self.get_logger().info('Subscribed to /imu/data and /oakd/rgb/preview/image_raw')
        self.get_logger().info('Publishing to /agent_uplink at 25Hz')

    def _init_cv_bridge(self):
        try:
            from cv_bridge import CvBridge

            self._bridge = CvBridge()
        except Exception as exc:
            self.get_logger().error(f'cv_bridge initialization failed: {exc}')
            self._bridge = None

    def _initialize_model(self):
        """
        Initialize the PyTorch model using a YAML config and optional weights.
        """
        config_param = self.get_parameter('model_config').get_parameter_value().string_value
        if os.path.isabs(config_param):
            config_path = config_param
        else:
            pkg_share = get_package_share_directory('turtlebot_simulation')
            config_path = os.path.join(pkg_share, 'config', config_param)

        try:
            with open(config_path, 'r', encoding='utf-8') as handle:
                self._cfg = yaml.safe_load(handle) or {}
            self.get_logger().info(f'Loaded model config from {config_path}')
        except FileNotFoundError:
            self.get_logger().error(f'Model config not found: {config_path}')
            return
        except yaml.YAMLError as exc:
            self.get_logger().error(f'Failed to parse model config: {exc}')
            return

        weights_override = self.get_parameter('model_weights').get_parameter_value().string_value
        weights_path = weights_override or self._cfg.get('model', {}).get('weights', '')

        try:
            from models.local_perception_model import build_model
            import torch

            self._device = self._select_device(torch)

            self._model = build_model(self._cfg).to(self._device)
            if weights_path:
                self._model.load_state_dict(torch.load(weights_path, map_location=self._device))
                self.get_logger().info(f'Loaded model weights from {weights_path}')
            else:
                self.get_logger().info('No weights provided; using randomly initialized model')
            self._model.eval()
            self.get_logger().info(f'Model using device: {self._device}')
        except ImportError as exc:
            self.get_logger().error(f'PyTorch import error: {exc}')
            self._model = None
        except Exception as exc:
            self.get_logger().error(f'Failed to initialize model: {exc}')
            self._model = None

    def _select_device(self, torch_module):
        pref = self.get_parameter('model_device').get_parameter_value().string_value.lower()
        cuda_available = torch_module.cuda.is_available()
        cuda_count = torch_module.cuda.device_count() if cuda_available else 0
        self.get_logger().info(
            f'model_device preference={pref}, cuda_available={cuda_available}, cuda_count={cuda_count}'
        )
        if pref in ('cuda', 'gpu'):
            if cuda_available:
                return torch_module.device('cuda')
            self.get_logger().warn('CUDA requested but not available; falling back to CPU')
            return torch_module.device('cpu')
        if pref == 'cpu':
            return torch_module.device('cpu')
        if pref == 'auto':
            return torch_module.device('cuda') if cuda_available else torch_module.device('cpu')
        self.get_logger().warn(f'Unknown device preference {pref}; defaulting to CPU')
        return torch_module.device('cpu')

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

        if self._model is None:
            return

        image_tensor = self._preprocess_image(self._latest_image)
        imu_tensor = self._preprocess_imu(self._latest_imu)
        if image_tensor is None or imu_tensor is None:
            return

        try:
            import torch

            image_tensor = image_tensor.to(self._device, non_blocking=True)
            imu_tensor = imu_tensor.to(self._device, non_blocking=True)

            with torch.no_grad():
                output = self._model(image_tensor, imu_tensor)
            result = int(output.item())
        except Exception as exc:
            self.get_logger().error(f'Inference failed: {exc}')
            return

        # Publish result to agent_uplink topic
        msg = Int32()
        msg.data = result
        self.uplink_publisher.publish(msg)

    def _preprocess_image(self, image_msg: Image):
        """
        Preprocess image message for model input.
        This is a skeleton - actual preprocessing would go here.
        """
        if self._bridge is None:
            return None

        try:
            import torch

            cv_image = self._bridge.imgmsg_to_cv2(image_msg, desired_encoding='rgb8')
            image_tensor = torch.from_numpy(cv_image).permute(2, 0, 1).float() / 255.0
            return image_tensor.unsqueeze(0)
        except Exception as exc:
            self.get_logger().error(f'Image preprocessing failed: {exc}')
            return None

    def _preprocess_imu(self, imu_msg: Imu):
        """
        Preprocess IMU message for model input.
        This is a skeleton - actual preprocessing would go here.
        """
        try:
            import torch

            orientation = [
                imu_msg.orientation.x,
                imu_msg.orientation.y,
                imu_msg.orientation.z,
                imu_msg.orientation.w,
            ]
            angular_velocity = [
                imu_msg.angular_velocity.x,
                imu_msg.angular_velocity.y,
                imu_msg.angular_velocity.z,
            ]
            linear_acceleration = [
                imu_msg.linear_acceleration.x,
                imu_msg.linear_acceleration.y,
                imu_msg.linear_acceleration.z,
            ]
            imu_features = orientation + angular_velocity + linear_acceleration
            return torch.tensor(imu_features, dtype=torch.float32).unsqueeze(0)
        except Exception as exc:
            self.get_logger().error(f'IMU preprocessing failed: {exc}')
            return None


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
