import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'arm_hardware'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Marina',
    maintainer_email='rinamoheb1@gmail.com',
    description='Bridge from ROS 2 joint trajectories to Arduino servos',
    license='MIT',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'hardware_bridge = arm_hardware.hardware_bridge:main',
        ],
    },
)
