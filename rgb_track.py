"""Closed-loop color tracking for QArm Mini using simple HSV segmentation."""

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
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--duration", type=float, default=300)
    return parser.parse_args()


def clamp_joints(joints: np.ndarray) -> np.ndarray:
    joints[0] = np.clip(joints[0], -1.0, 1.0)
    joints[1] = np.clip(joints[1], 0.4, 1.6)
    joints[2] = np.clip(joints[2], -1.9, -0.8)
    return joints


def main() -> None:
    args = parse_args()
    image_center_x = args.width // 2
    image_center_y = args.height // 2
    roi = (100, 540, 60, 330)

    joint_cmd = np.array([0.0, 0.9, -1.4, 1.57], dtype=float)
    gripper_cmd = 0.0

    camera = Camera2D(args.camera, frameWidth=args.width, frameHeight=args.height, frameRate=30)
    arm = QArmMini(hardware=1, id=args.arm_id)
    timer = QTimer(sampleRate=30.0, totalTime=args.duration)

    lost_count = 0
    last_error_x = 0
    last_error_y = 0

    try:
        while timer.check():
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
            blob = find_largest_blob(mask, min_area=450)

            status = "search"
            if blob is not None:
                x, y, w, h, cx, cy, area = blob
                x += x1
                y += y1
                cx += x1
                cy += y1

                error_x = cx - image_center_x
                error_y = cy - image_center_y
                last_error_x = error_x
                last_error_y = error_y
                lost_count = 0

                if error_x < -60:
                    joint_cmd[0] += 0.006
                elif error_x > 60:
                    joint_cmd[0] -= 0.006
                elif error_x < -20:
                    joint_cmd[0] += 0.003
                elif error_x > 20:
                    joint_cmd[0] -= 0.003

                if error_y < -40:
                    joint_cmd[1] += 0.006
                elif error_y > 40:
                    joint_cmd[1] -= 0.006
                elif error_y < -15:
                    joint_cmd[1] += 0.003
                elif error_y > 15:
                    joint_cmd[1] -= 0.003

                if abs(error_x) < 20 and abs(error_y) < 15:
                    status = "centered"
                else:
                    status = "tracking"

                cv2.rectangle(image, (x, y), (x + w, y + h), draw_color, 2)
                cv2.circle(image, (cx, cy), 4, draw_color, -1)
                cv2.putText(image, f"area={int(area)}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.55, draw_color, 2)
            else:
                lost_count += 1
                if lost_count < 10:
                    if last_error_x > 20:
                        joint_cmd[0] -= 0.0025
                    elif last_error_x < -20:
                        joint_cmd[0] += 0.0025
                    if last_error_y > 15:
                        joint_cmd[1] -= 0.0015
                    elif last_error_y < -15:
                        joint_cmd[1] += 0.0015

            joint_cmd = clamp_joints(joint_cmd)
            cv2.rectangle(image, (x1, y1), (x2, y2), (255, 255, 0), 2)
            cv2.line(image, (image_center_x, 0), (image_center_x, args.height), (255, 255, 255), 1)
            cv2.line(image, (0, image_center_y), (args.width, image_center_y), (255, 255, 255), 1)
            cv2.putText(image, f"target={args.color} status={status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
            cv2.putText(image, f"joints={np.round(joint_cmd, 3)}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

            cv2.imshow("QArm Mini RGB Tracking", image)
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
