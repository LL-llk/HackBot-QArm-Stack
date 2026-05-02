"""Rule-based visual grasping state machine for QArm Mini."""

import argparse
import cv2
import numpy as np

import runtime_paths  # noqa: F401
from color_utils import color_mask, find_largest_blob, preprocess_mask
from pal.products.qarm_mini import QArmMini
from pal.utilities.timing import QTimer
from pal.utilities.vision import Camera2D


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", default="1")
    parser.add_argument("--arm-id", type=int, default=3)
    parser.add_argument("--color", choices=["red", "green", "blue"], default="red")
    parser.add_argument("--duration", type=float, default=300)
    return parser.parse_args()


def clamp_joints(joints: np.ndarray) -> np.ndarray:
    joints[0] = np.clip(joints[0], -1.0, 1.0)
    joints[1] = np.clip(joints[1], 0.4, 1.6)
    joints[2] = np.clip(joints[2], -1.9, -0.8)
    return joints


def main() -> None:
    args = parse_args()
    width, height = 640, 360
    center_x, center_y = width // 2, height // 2
    roi = (100, 540, 60, 330)

    joint_cmd = np.array([0.0, 0.90, -1.40, 1.57], dtype=float)
    gripper_cmd = 0.0

    state = "SEARCH"
    state_timer = 0
    hold_count = 0
    lost_count = 0
    last_error_x = 0
    last_error_y = 0

    camera = Camera2D(args.camera, frameWidth=width, frameHeight=height, frameRate=30)
    arm = QArmMini(hardware=1, id=args.arm_id)
    timer = QTimer(sampleRate=30.0, totalTime=args.duration)

    try:
        while timer.check():
            state_timer += 1
            if not camera.read():
                arm.read_write_std(joint_cmd, gripper=gripper_cmd)
                timer.sleep()
                continue

            image = camera.imageData.copy()
            arm.read_write_std(joint_cmd, gripper=gripper_cmd)

            x1, x2, y1, y2 = roi
            hsv = cv2.cvtColor(image[y1:y2, x1:x2], cv2.COLOR_BGR2HSV)
            raw_mask, draw_color = color_mask(hsv, args.color)
            mask = preprocess_mask(raw_mask)
            blob = find_largest_blob(mask, min_area=300)

            found = False
            error_x = 0
            error_y = 0
            area = 0
            cx = center_x
            cy = center_y

            if blob is not None:
                x, y, w, h, cx, cy, area = blob
                x += x1
                y += y1
                cx += x1
                cy += y1
                found = True
                lost_count = 0
                error_x = cx - center_x
                error_y = cy - center_y
                last_error_x = error_x
                last_error_y = error_y
                cv2.rectangle(image, (x, y), (x + w, y + h), draw_color, 2)
                cv2.circle(image, (cx, cy), 4, draw_color, -1)
            else:
                lost_count += 1

            status = ""
            if state == "SEARCH":
                gripper_cmd = 0.0
                if found:
                    hold_count += 1
                else:
                    hold_count = 0
                if hold_count >= 3:
                    state, state_timer, hold_count = "TRACK", 0, 0
                    status = "target found"
                else:
                    status = "search"

            elif state == "TRACK":
                gripper_cmd = 0.0
                if not found and lost_count > 15:
                    state, state_timer, hold_count = "SEARCH", 0, 0
                    status = "lost"
                else:
                    if error_x < -65:
                        joint_cmd[0] += 0.004
                    elif error_x > 65:
                        joint_cmd[0] -= 0.004
                    elif error_x < -28:
                        joint_cmd[0] += 0.0015
                    elif error_x > 28:
                        joint_cmd[0] -= 0.0015

                    if error_y < -40:
                        joint_cmd[1] += 0.003
                    elif error_y > 40:
                        joint_cmd[1] -= 0.003
                    elif error_y < -18:
                        joint_cmd[1] += 0.001
                    elif error_y > 18:
                        joint_cmd[1] -= 0.001

                    if abs(error_x) < 35 and abs(error_y) < 28:
                        hold_count += 1
                    else:
                        hold_count = 0
                    if hold_count >= 6:
                        state, state_timer, hold_count = "APPROACH", 0, 0
                    status = "align"

            elif state == "APPROACH":
                if not found and lost_count > 15:
                    state, state_timer, hold_count = "SEARCH", 0, 0
                elif abs(error_x) > 35 or abs(error_y) > 28:
                    state, state_timer, hold_count = "TRACK", 0, 0
                else:
                    if area < 4300:
                        joint_cmd[2] -= 0.001
                        hold_count = 0
                        status = "forward"
                    elif area > 5600:
                        joint_cmd[2] += 0.001
                        hold_count = 0
                        status = "back"
                    else:
                        hold_count += 1
                        status = "grasp window"
                    if hold_count >= 8:
                        state, state_timer, hold_count = "PREGRASP", 0, 0

            elif state == "PREGRASP":
                if state_timer >= 10:
                    state, state_timer = "GRASP", 0
                status = "stabilize"

            elif state == "GRASP":
                gripper_cmd = 1.0
                if state_timer >= 30:
                    state, state_timer = "LIFT", 0
                status = "close"

            elif state == "LIFT":
                gripper_cmd = 1.0
                joint_cmd[1] += 0.003
                if state_timer >= 25:
                    state, state_timer = "DONE", 0
                status = "lift"

            elif state == "DONE":
                status = "done"

            joint_cmd = clamp_joints(joint_cmd)
            cv2.rectangle(image, (x1, y1), (x2, y2), (255, 255, 0), 2)
            cv2.putText(image, f"target={args.color} state={state} {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
            cv2.putText(image, f"area={int(area)} err=({int(error_x)},{int(error_y)})", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
            cv2.imshow("QArm Mini Visual Grasping", image)
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
