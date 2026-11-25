import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

JOINTS = ['joint1', 'joint2', 'joint3', 'joint4']


class TrajectoryPublisher(Node):
    def __init__(self):
        super().__init__('trajectory_publisher')
        self.pub = self.create_publisher(
            JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.poses = [
            [0.0, 0.0, 0.0, 0.0],
            [1.0, 0.5, 0.3, 0.0],
            [-1.0, -0.5, 0.5, 0.3],
        ]
        self.i = 0
        self.timer = self.create_timer(3.0, self.send)

    def send(self):
        msg = JointTrajectory()
        msg.joint_names = JOINTS
        point = JointTrajectoryPoint()
        point.positions = self.poses[self.i % len(self.poses)]
        point.time_from_start = Duration(sec=2, nanosec=0)
        msg.points = [point]
        self.pub.publish(msg)
        self.get_logger().info(f'Sent pose {self.i % len(self.poses)}')
        self.i += 1


def main():
    rclpy.init()
    node = TrajectoryPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
