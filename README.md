# ROS 2 Robotic Arm: URDF, Simulation and Hardware Control

A 4-joint robotic arm modelled in URDF, simulated in Gazebo (`gz sim`) and
RViz2, and driven from the same ROS 2 command on real servo motors through an
Arduino Uno.

```
slider_gui / trajectory_publisher
        |  trajectory_msgs/JointTrajectory
        v
/arm_controller/joint_trajectory ---> Gazebo (gz_ros2_control) --> /joint_states --> RViz2
        |
        v
hardware_bridge (ROS 2 node) --USB serial--> Arduino Uno --PWM--> 2x SG90 servos
```

## Repository layout

| Path | Contents |
|---|---|
| `src/arm_description` | URDF/Xacro model, RViz config, `display.launch.py` |
| `src/arm_gazebo` | Gazebo launch file and `ros2_control` controller config |
| `src/arm_control` | `trajectory_publisher` (demo poses) and `slider_gui` (manual control) |
| `src/arm_hardware` | `hardware_bridge` node and launch files for the real arm |
| `firmware/arm_servos` | Arduino sketch (`arm_servos.ino`) |

## The arm

Dimensions follow the assignment: base 8 cm, L1 12 cm, L2 15 cm, L3 9 cm,
end effector 6 cm. Kinematic chain:

`base_link -> joint1 -> l1 -> joint2 -> l2 -> joint3 -> l3 -> joint4 -> end_effector`

All four joints are revolute. Every link has `visual`, `collision` and
`inertial` elements. The URDF joint limits are +-1.7 rad; the slider GUI and the
servo mapping use +-1.57 rad (+-90 degrees), so the simulated joints never
press against their hard limit.

| Joint | Axis | Real servo |
|---|---|---|
| `joint1` (base rotation) | z | Servo 1 |
| `joint2` (shoulder) | y | Servo 2 |
| `joint3`, `joint4` | y | simulation only |

## Requirements

Developed with **ROS 2 Lyrical Luth** (Ubuntu 26.04) and **Gazebo Jetty**
(`gz sim`).

```bash
sudo apt install ros-lyrical-ros-gz ros-lyrical-gz-ros2-control \
  ros-lyrical-ros2-control ros-lyrical-ros2-controllers ros-lyrical-xacro \
  ros-lyrical-joint-state-publisher-gui python3-tk python3-serial
```

For the Arduino: the Arduino IDE (the `Servo` library is included with it).

## Build

```bash
cd <workspace>            # the folder that contains src/
colcon build
source install/setup.bash
```

## Run

### 1. View the model only (RViz2)

```bash
ros2 launch arm_description display.launch.py
```

### 2. Simulation (Gazebo + RViz2)

```bash
ros2 launch arm_gazebo gazebo.launch.py
```

In a second terminal (remember to `source install/setup.bash`):

```bash
ros2 run arm_control slider_gui            # sliders for every joint
# or
ros2 run arm_control trajectory_publisher  # cycles through 3 poses
```

One command on `/arm_controller/joint_trajectory` moves the arm in Gazebo and
in RViz2 (RViz2 follows `/joint_states` from the simulation).

### 3. Real servos only

1. Wire the circuit (see *Hardware* below).
2. Upload `firmware/arm_servos/arm_servos.ino` to the Arduino Uno
   (Board: *Arduino Uno*), then close the Arduino IDE and its Serial Monitor
   so the serial port is free.
3. Give your user access to the serial port (once, then log out and in):
   `sudo usermod -aG dialout $USER`
4. Start the bridge (find the port with `ls /dev/ttyACM*`):

```bash
ros2 launch arm_hardware hardware.launch.py port:=/dev/ttyACM0
```

5. Send a test command:

```bash
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \
  "{joint_names: ['joint1','joint2'], points: [{positions: [0.5, -0.3], time_from_start: {sec: 2}}]}"
```

### 4. Full pipeline demo

Gazebo, RViz2, slider GUI and the hardware bridge together:

```bash
ros2 launch arm_hardware demo.launch.py port:=/dev/ttyACM0
```

Moving a slider moves the arm in Gazebo and RViz2 and the two real servos
(`joint1` and `joint2`).

To try the bridge without an Arduino, use dry-run mode (it prints the serial
lines it would send):

```bash
ros2 run arm_hardware hardware_bridge --ros-args -p dry_run:=true
```

## Hardware

Parts: Arduino Uno with USB-B cable, 2x SG90 servo, breadboard, jumper wires,
5 V 2 A wall adapter with a female DC barrel jack, 1000 uF 16 V electrolytic
capacitor.

### Wiring

| Board pin | Connects to |
|---|---|
| D9 | Servo 1 signal wire (orange): base rotation, `joint1` |
| D10 | Servo 2 signal wire (orange): shoulder, `joint2` |
| GND | Common ground rail (shared with the external 5 V supply) |

| Servo wire | Connects to |
|---|---|
| Red (VCC) | External 5 V rail |
| Brown (GND) | Common ground rail |

### Power

* The servos are powered from the **5 V 2 A wall adapter** through the DC
  jack, not from the Arduino's 5 V pin. Servos draw more current than a USB
  port can supply, especially when starting or stalled. The Arduino's 5 V pin
  stays unconnected.
* The adapter's GND, the servos' GND and the Arduino GND are connected
  together (**common ground**). Without it the signal wires have no reference
  and the servos jitter or do not move.
* A **1000 uF, 16 V electrolytic capacitor** sits across the 5 V and GND rails
  next to the servos to absorb current spikes. Observe polarity: the stripe
  marks the negative leg and goes to the ground rail.
* The Arduino is powered over USB only.
* Check the polarity of the adapter before connecting it (centre pin positive
  is the usual case).

### Testing the firmware alone

Open the Arduino IDE Serial Monitor (115200 baud, line ending *New Line*). It
prints `READY` after a reset and both servos go to 90 degrees. Type
`<servo1>,<servo2>` (for example `45,135`) and press Enter.

## Transport and message format

* **Transport:** USB serial (Arduino Uno virtual COM port), 115200 baud, 8N1,
  using `pyserial` on the PC.
* **ROS side:** `hardware_bridge` subscribes to
  `/arm_controller/joint_trajectory`. It uses the final point of each message
  and moves smoothly from the current angles to it over `time_from_start`
  (interpolated at 50 Hz). Joints not listed in a message keep their last
  target.
* **Angle conversion:** `servo_deg = 90 + degrees(joint_rad)`, clamped to
  0..180 and rounded to whole degrees. 0 rad is the servo centre (90 degrees).
  The direction can be flipped per joint with the `invert` parameter.
* **Serial message (PC -> Arduino):** one ASCII line per update:

  ```
  <servo1_deg>,<servo2_deg>\n        e.g.  90,45\n
  ```

  The firmware clamps values to 0..180. A line it cannot parse is answered
  with `ERR`. The Arduino sends `READY` once after reset.

Bridge parameters: `port`, `baud`, `joint_names` (default `[joint1, joint2]`),
`center_deg`, `invert`, `rate_hz`, `dry_run`.

## Troubleshooting

* **`Permission denied` on `/dev/ttyACM0`:** add your user to the `dialout`
  group (see above) and log in again.
* **Port busy or no data:** close the Arduino IDE and its Serial Monitor;
  only one program can use the serial port.
* **`ERR` in the Serial Monitor:** the line must be two plain integers
  separated by a comma, for example `90,90`, typed with an English keyboard
  layout.

## Tests

The angle conversion has unit tests that need no ROS or hardware:

```bash
cd src/arm_hardware && python3 -m pytest test/test_conversion.py
```
