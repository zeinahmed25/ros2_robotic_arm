import tkinter as tk

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

JOINTS = ['joint1', 'joint2', 'joint3', 'joint4']
LIMITS = [(-1.57, 1.57), (-1.57, 1.57), (-1.57, 1.57), (-1.57, 1.57)]


class SliderGui(Node):
    def __init__(self):
        super().__init__('slider_gui')
        self.pub = self.create_publisher(
            JointTrajectory, '/arm_controller/joint_trajectory', 10)

        self.root = tk.Tk()
        self.root.title('Arm Control')
        self.vars = []
        for name, (lo, hi) in zip(JOINTS, LIMITS):
            var = tk.DoubleVar(value=0.0)
            tk.Scale(self.root, label=name, from_=lo, to=hi,
                     resolution=0.01, orient=tk.HORIZONTAL, length=350,
                     variable=var, command=self.on_change).pack(padx=10)
            self.vars.append(var)
        tk.Button(self.root, text='Center', command=self.center).pack(pady=8)
        self.root.after(200, self.keepalive)

    def keepalive(self):
        """Resend the current slider values 5 times per second.

        This guarantees the final slider position always reaches the
        controller, even if one message was missed.
        """
        self.on_change()
        self.root.after(200, self.keepalive)

    def on_change(self, _=None):
        msg = JointTrajectory()
        msg.joint_names = JOINTS
        point = JointTrajectoryPoint()
        point.positions = [v.get() for v in self.vars]
        point.time_from_start = Duration(sec=0, nanosec=300000000)
        msg.points = [point]
        self.pub.publish(msg)

    def center(self):
        for v in self.vars:
            v.set(0.0)
        self.on_change()

    def spin(self):
        def tick():
            rclpy.spin_once(self, timeout_sec=0)
            self.root.after(20, tick)
        tick()
        self.root.mainloop()


def main():
    rclpy.init()
    gui = SliderGui()
    gui.spin()
    gui.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
