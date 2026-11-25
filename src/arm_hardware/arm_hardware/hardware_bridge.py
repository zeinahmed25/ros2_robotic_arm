"""ROS 2 -> Arduino bridge for the servo arm.

Subscribes to /arm_controller/joint_trajectory, converts the joint angles
(radians) of the configured joints to servo angles (degrees) and streams
them to the Arduino over USB serial as "<servo1>,<servo2>\\n".

The arm moves smoothly: the node interpolates from the current servo angles
to the final trajectory point over that point's time_from_start.
"""
import time

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory

from arm_hardware.conversion import format_command, interpolate, rad_to_servo_deg

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


class HardwareBridge(Node):
    def __init__(self):
        super().__init__('hardware_bridge')

        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baud', 115200)
        self.declare_parameter('joint_names', ['joint1', 'joint2'])
        self.declare_parameter('center_deg', [90.0, 90.0])
        self.declare_parameter('invert', [False, False])
        self.declare_parameter('rate_hz', 50.0)
        self.declare_parameter('dry_run', False)  # log only, no serial port

        self.joints = list(self.get_parameter('joint_names').value)
        self.center = [float(c) for c in self.get_parameter('center_deg').value]
        self.invert = [bool(i) for i in self.get_parameter('invert').value]
        if not (len(self.joints) == len(self.center) == len(self.invert)):
            raise ValueError(
                'joint_names, center_deg and invert must have the same length')

        self.dry_run = bool(self.get_parameter('dry_run').value)
        self.ser = None
        if not self.dry_run:
            self._open_serial()

        # Current / target / start servo angles, in degrees.
        self.current = list(self.center)
        self.start = list(self.center)
        self.target = list(self.center)
        self.move_start = time.monotonic()
        self.move_duration = 0.0
        self.last_sent = None

        self.create_subscription(
            JointTrajectory, '/arm_controller/joint_trajectory',
            self.on_trajectory, 10)
        period = 1.0 / float(self.get_parameter('rate_hz').value)
        self.create_timer(period, self.tick)

        self.get_logger().info(
            f'Bridge ready. Servo joints: {self.joints}'
            f'{" (dry run, no serial)" if self.dry_run else ""}')

    def _open_serial(self):
        if serial is None:
            raise RuntimeError(
                'pyserial is missing: sudo apt install python3-serial')
        port = self.get_parameter('port').value
        baud = int(self.get_parameter('baud').value)
        self.ser = serial.Serial(port, baud, timeout=0)
        # The Uno resets when the port is opened; give the bootloader time.
        time.sleep(2.0)
        self.ser.reset_input_buffer()
        self.get_logger().info(f'Opened {port} at {baud} baud')

    def on_trajectory(self, msg):
        if not msg.points:
            return
        point = msg.points[-1]  # final target of the trajectory
        indices = {n: i for i, n in enumerate(msg.joint_names)}
        new_target = list(self.target)
        for k, name in enumerate(self.joints):
            idx = indices.get(name)
            if idx is None or idx >= len(point.positions):
                continue  # joint not in this message: keep its target
            new_target[k] = rad_to_servo_deg(
                point.positions[idx], self.center[k], self.invert[k])
        self.start = list(self.current)
        self.target = new_target
        self.move_start = time.monotonic()
        t = point.time_from_start
        self.move_duration = t.sec + t.nanosec * 1e-9

    def tick(self):
        if self.move_duration > 0.0:
            fraction = (time.monotonic() - self.move_start) / self.move_duration
        else:
            fraction = 1.0
        self.current = interpolate(self.start, self.target, fraction)

        line = format_command(self.current)
        if line != self.last_sent:  # only send when the integer angles change
            self.last_sent = line
            if self.ser is not None:
                try:
                    self.ser.write(line)
                except serial.SerialException as exc:
                    self.get_logger().error(f'Serial write failed: {exc}')
            else:
                self.get_logger().info(f'[dry run] would send {line!r}')

        if self.ser is not None:
            self._drain_input()

    def _drain_input(self):
        try:
            data = self.ser.read(256)
        except serial.SerialException:
            return
        for text in data.decode('ascii', errors='ignore').splitlines():
            text = text.strip()
            if text == 'ERR':
                self.get_logger().warn('Firmware reported a bad command line')
            elif text:
                self.get_logger().info(f'Arduino: {text}')

    def destroy_node(self):
        if self.ser is not None:
            self.ser.close()
        super().destroy_node()


def main():
    rclpy.init()
    node = HardwareBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
