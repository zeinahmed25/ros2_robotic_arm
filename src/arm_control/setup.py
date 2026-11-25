from setuptools import find_packages, setup

package_name = 'arm_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Marina',
    maintainer_email='rinamoheb1@gmail.com',
    description='Joint trajectory publisher and slider GUI for the arm',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'trajectory_publisher = arm_control.trajectory_publisher:main',
            'slider_gui = arm_control.slider_gui:main',
        ],
    },
)
