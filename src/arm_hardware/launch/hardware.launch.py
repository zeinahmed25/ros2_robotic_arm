from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    port = DeclareLaunchArgument(
        'port', default_value='/dev/ttyACM0',
        description='Serial port of the Arduino')
    return LaunchDescription([
        port,
        Node(
            package='arm_hardware', executable='hardware_bridge',
            name='hardware_bridge', output='screen',
            parameters=[{'port': LaunchConfiguration('port')}]),
    ])
