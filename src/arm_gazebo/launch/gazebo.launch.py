import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    desc_pkg = get_package_share_directory('arm_description')
    gz_pkg = get_package_share_directory('ros_gz_sim')
    xacro_file = os.path.join(desc_pkg, 'urdf', 'arm.urdf.xacro')
    rviz_file = os.path.join(desc_pkg, 'rviz', 'arm.rviz')
    controllers_file = os.path.join(
        get_package_share_directory('arm_gazebo'), 'config', 'controllers.yaml')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]), value_type=str)

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description,
                     'use_sim_time': True}])

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gz_pkg, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': '-r empty.sdf'}.items())

    spawn = Node(
        package='ros_gz_sim', executable='create',
        arguments=['-topic', 'robot_description', '-name', 'arm'],
        output='screen')

    clock_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen')

    jsb = Node(
        package='controller_manager', executable='spawner',
        arguments=['joint_state_broadcaster'])

    arm_ctrl = Node(
        package='controller_manager', executable='spawner',
        arguments=['arm_controller',
                   '--param-file', controllers_file])

    rviz = Node(
        package='rviz2', executable='rviz2',
        arguments=['-d', rviz_file],
        parameters=[{'use_sim_time': True}])

    return LaunchDescription([
        robot_state_publisher,
        gz_sim,
        clock_bridge,
        spawn,
        RegisterEventHandler(OnProcessExit(
            target_action=spawn, on_exit=[jsb])),
        RegisterEventHandler(OnProcessExit(
            target_action=jsb, on_exit=[arm_ctrl])),
        rviz,
    ])
