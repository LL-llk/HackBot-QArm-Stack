"""Detect red, green, and blue blocks from the QArm Mini camera."""

import argparse
import cv2

import runtime_paths  # noqa: F401
from color_utils import color_mask, find_largest_blob, preprocess_mask
from pal.utilities.vision import Camera2D


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", default="1", help="Camera device index used by Camera2D.")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--min-area", type=float, default=300)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    camera = Camera2D(args.camera, frameWidth=args.width, frameHeight=args.height, frameRate=30)

    try:
        while True:
            if not camera.read():
                continue

            image = camera.imageData.copy()
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            for name in ("red", "green", "blue"):
                raw_mask, draw_color = color_mask(hsv, name)
                mask = preprocess_mask(raw_mask)
                blob = find_largest_blob(mask, min_area=args.min_area)
                if blob is None:
                    continue

                x, y, w, h, cx, cy, area = blob
                cv2.rectangle(image, (x, y), (x + w, y + h), draw_color, 2)
                cv2.circle(image, (cx, cy), 4, draw_color, -1)
                cv2.putText(
                    image,
                    f"{name} ({cx},{cy}) area={int(area)}",
                    (x, max(20, y - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    draw_color,
                    1,
                )

            cv2.imshow("QArm Mini RGB Block Detection", image)
            if cv2.waitKey(1) & 0xFF == 27:
                break
    finally:
        try:
            camera.terminate()
        finally:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
