"""Sequentially grasp red, green, and blue blocks and place them in one stack."""

import argparse
import os
import cv2
import numpy as np

import runtime_paths  # noqa: F401
from color_utils import color_mask, find_largest_blob, preprocess_mask
from pick_helpers import place_block, stack_theta
from pal.products.qarm_mini import QArmMini
from pal.utilities.timing import QTimer
from pal.utilities.vision import Camera2D


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", default="1")
    parser.add_argument("--arm-id", type=int, default=3)
    parser.add_argument("--duration", type=float, default=600)
    parser.add_argument("--colors", nargs="+", default=["red", "green", "blue"], choices=["red", "green", "blue"])
    parser.add_argument("--model-path", default="model.pt")
    parser.add_argument("--use-rl-track", action="store_true")
    parser.add_argument("--use-rl-approach", action="store_true")
    return parser.parse_args()


def maybe_load_policy(args):
    """Load the optional policy only when an RL mode is requested."""
    if not (args.use_rl_track or args.use_rl_approach):
        return None
    if not os.path.exists(args.model_path):
        raise FileNotFoundError(f"RL mode requested but model was not found: {args.model_path}")

    import torch
    import torch.nn as nn

    class Policy(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(3, 64),
                nn.ReLU(),
                nn.Linear(64, 64),
                nn.ReLU(),
                nn.Linear(64, 3),
                nn.Tanh(),
            )

        def forward(self, x):
            return self.net(x)

    policy = Policy()
    policy.load_state_dict(torch.load(args.model_path, map_location="cpu"))
    policy.eval()
    return policy


def rl_action(policy, error_x, error_y, area):
    """Return clipped RL joint deltas for base, shoulder, and elbow."""
    import torch

    obs = np.array([error_x / 320.0, error_y / 180.0, area / 8000.0], dtype=np.float32)
    with torch.no_grad():
        action = policy(torch.tensor(obs, dtype=torch.float32)).numpy()
    return (
        float(np.clip(action[0] * 0.30, -0.010, 0.010)),
        float(np.clip(action[1] * 0.30, -0.010, 0.010)),
        float(np.clip(action[2] * 0.30, -0.010, 0.010)),
    )


def clamp_joints(joints):
    joints[0] = np.clip(joints[0], -1.0, 1.0)
    joints[1] = np.clip(joints[1], 0.4, 1.6)
    joints[2] = np.clip(joints[2], -1.9, -0.8)
    joints[3] = np.clip(joints[3], 0.8, 2.3)
    return joints


def main() -> None:
    args = parse_args()
    policy = maybe_load_policy(args)

    width, height = 640, 360
    center_x, center_y = width // 2, height // 2
    home_pose = np.array([0.0, 0.90, -1.40, 1.57], dtype=float)
    joint_cmd = home_pose.copy()
    gripper_cmd = 0.0

    camera = Camera2D(args.camera, frameWidth=width, frameHeight=height, frameRate=30)
    arm = QArmMini(hardware=1, id=args.arm_id)
    timer = QTimer(sampleRate=30.0, totalTime=args.duration)

    color_index = 0
    target_color = args.colors[color_index]
    stack_angle = None
    height_index = 0
    state = "SEARCH"
    state_timer = 0
    hold_counter = 0
    done = False

    try:
        while timer.check() and not done:
            state_timer += 1
            if not camera.read():
                arm.read_write_std(joint_cmd, gripper=gripper_cmd)
                timer.sleep()
                continue

            image = camera.imageData.copy()
            arm.read_write_std(joint_cmd, gripper=gripper_cmd)

            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            raw_mask, draw_color = color_mask(hsv, target_color)
            mask = preprocess_mask(raw_mask)
            blob = find_largest_blob(mask, min_area=300)

            found = False
            error_x = 0
            error_y = 0
            area = 0

            if blob is not None:
                x, y, w, h, cx, cy, area = blob
                found = True
                error_x = cx - center_x
                error_y = cy - center_y
                cv2.rectangle(image, (x, y), (x + w, y + h), draw_color, 2)
                cv2.circle(image, (cx, cy), 5, draw_color, -1)

            status = ""
            if state == "SEARCH":
                gripper_cmd = 0.0
                if found:
                    state, state_timer, hold_counter = "TRACK", 0, 0
                    status = "found"
                else:
                    status = "search"

            elif state == "TRACK":
                if not found:
                    state, state_timer, hold_counter = "SEARCH", 0, 0
                else:
                    if args.use_rl_track and policy is not None:
                        db, ds, de = rl_action(policy, error_x, error_y, area)
                        joint_cmd[0] += db
                        joint_cmd[1] += ds
                        joint_cmd[2] += de
                    else:
                        joint_cmd[0] += -error_x * 0.000018
                        joint_cmd[1] += -error_y * 0.000018
                    hold_counter = hold_counter + 1 if abs(error_x) < 45 and abs(error_y) < 40 else 0
                    if hold_counter > 2:
                        state, state_timer, hold_counter = "APPROACH", 0, 0
                    status = "track"

            elif state == "APPROACH":
                if not found:
                    state, state_timer, hold_counter = "SEARCH", 0, 0
                else:
                    if args.use_rl_approach and policy is not None:
                        db, ds, de = rl_action(policy, error_x, error_y, area)
                        joint_cmd[0] += db
                        joint_cmd[1] += ds
                        joint_cmd[2] += de
                    else:
                        joint_cmd[0] += -error_x * 0.000014
                        joint_cmd[1] += -error_y * 0.000014
                        if area < 4500:
                            joint_cmd[2] -= 0.002
                            joint_cmd[3] += 0.0012
                            hold_counter = 0
                        elif area > 9000:
                            joint_cmd[2] += 0.002
                            hold_counter = 0
                        else:
                            hold_counter += 1
                    if hold_counter > 2:
                        state, state_timer, hold_counter = "DESCEND", 0, 0
                    status = "approach"

            elif state == "DESCEND":
                joint_cmd[1] -= 0.0015
                joint_cmd[2] -= 0.0014
                joint_cmd[3] -= 0.0023
                if state_timer > 42:
                    state, state_timer = "GRASP", 0
                status = "descend"

            elif state == "GRASP":
                gripper_cmd = 0.75
                if state_timer > 22:
                    state, state_timer = "LIFT", 0
                status = "grasp"

            elif state == "LIFT":
                gripper_cmd = 0.75
                joint_cmd[1] += 0.003
                if state_timer > 20:
                    if stack_angle is None:
                        stack_angle = float(joint_cmd[0])
                    state, state_timer = "PLACE", 0
                status = "lift"

            elif state == "PLACE":
                theta = stack_theta(height_index)
                place_block(arm, angle=stack_angle, theta=theta, height=height_index)
                height_index += 1
                color_index += 1
                if color_index >= len(args.colors):
                    done = True
                    joint_cmd = home_pose.copy()
                    gripper_cmd = 0.0
                else:
                    target_color = args.colors[color_index]
                    state, state_timer, hold_counter = "SEARCH", 0, 0
                    joint_cmd = home_pose.copy()
                    gripper_cmd = 0.0
                status = "place"

            joint_cmd = clamp_joints(joint_cmd)
            cv2.putText(image, f"target={target_color} state={state} {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
            cv2.putText(image, f"area={int(area)} err=({int(error_x)},{int(error_y)})", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
            cv2.imshow("QArm Mini Sequential RGB Stack", image)
            cv2.imshow("Mask", mask)
            if cv2.waitKey(1) & 0xFF == 27:
                break
            timer.sleep()
    finally:
        try:
            arm.terminate()
        finally:
            try:
                camera.terminate()
            finally:
                cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
