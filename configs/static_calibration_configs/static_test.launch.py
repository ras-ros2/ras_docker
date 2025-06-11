""" Static transform publisher acquired via MoveIt 2 hand-eye calibration """
""" EYE-TO-HAND: link_base -> camera_link """
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    nodes = [
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            output="log",
            arguments=[
                "--frame-id",
                "link_base",
                "--child-frame-id",
                "camera_link",
                "--x",
                "0.329782",
                "--y",
                "0.0661466",
                "--z",
                "0.635587",
                "--qx",
                "-0.0046194",
                "--qy",
                "0.713497",
                "--qz",
                "0.0127323",
                "--qw",
                "0.700528",
                # "--roll",
                # "0.934689",
                # "--pitch",
                # "1.60143",
                # "--yaw",
                # "-0.923214",
            ],
        ),
    ]
    return LaunchDescription(nodes)

