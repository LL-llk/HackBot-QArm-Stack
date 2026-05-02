"""Small helper routines for QArm Mini block placement."""

import time
import numpy as np


HEIGHT_ANGLES = [np.pi / 13, 0.48207, 0.68949, 0.75291]


def move_blocking(robot, pose, gripper, wait_s: float = 1.0) -> None:
    """Send one pose command and wait for the motion to settle."""
    robot.read_write_std(np.array(pose, dtype=np.float64), gripper=gripper)
    time.sleep(wait_s)


def place_block(robot, angle=-np.pi / 2, theta=np.pi / 13, height: int = 0) -> None:
    """Place a grasped block at a stack location."""
    phi = theta + (np.pi / 2) - np.arccos(1.1097 * np.sin(theta) + 0.456 - (height * 0.402))

    place_pose = np.array([angle, theta, -phi, np.pi - theta - phi], dtype=np.float64)
    above_pose = np.array([angle, np.pi / 4, -phi, np.pi / 2 - theta + phi], dtype=np.float64)

    move_blocking(robot, above_pose, gripper=0.5333333333333, wait_s=2.0)
    move_blocking(robot, place_pose, gripper=0.5333333333333, wait_s=2.2)
    move_blocking(robot, place_pose, gripper=0.4, wait_s=1.8)
    time.sleep(0.8)
    move_blocking(robot, above_pose, gripper=0.0, wait_s=2.0)


def stack_theta(height_index: int) -> float:
    """Return the calibrated shoulder angle for a stack level."""
    return HEIGHT_ANGLES[min(height_index, len(HEIGHT_ANGLES) - 1)]

