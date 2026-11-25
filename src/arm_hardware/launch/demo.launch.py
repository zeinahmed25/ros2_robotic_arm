"""Full pipeline: Gazebo + RViz2 + slider GUI + hardware bridge."""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    gazebo_launch = os.path.join(
        get_package_share_directory('arm_gazebo'), 'launch', 'gazebo.launch.py')
    port = DeclareLaunchArgument(
        'port', default_value='/dev/ttyACM0',
        description='Serial port of the Arduino')
    return LaunchDescription([
        port,
        IncludeLaunchDescription(PythonLaunchDescriptionSource(gazebo_launch)),
        Node(
            package='arm_hardware', executable='hardware_bridge',
            name='hardware_bridge', output='screen',
            parameters=[{'port': LaunchConfiguration('port')}]),
        Node(
            package='arm_control', executable='slider_gui',
            name='slider_gui', output='screen'),
    ])
