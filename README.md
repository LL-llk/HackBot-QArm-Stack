# HackBot QArm Stack

HackBot QArm Stack is a 24-hour HackBot project for the Quanser QArm Mini. It implements a camera-guided manipulation demo that detects colored blocks, tracks a selected target, closes the gripper when the target is aligned, and places blocks into a small stack.

This is the minimal project version. It contains only the HackBot demo code and documentation, not the full Quanser academic resource tree.

## Project Files

```text
rgb_detect.py
rgb_track.py
rgb_gripper.py
sequential_rgb_stack.py
color_utils.py
pick_helpers.py
runtime_paths.py
HACKBOT_DEMO_README.md
```

## What It Does

The demo uses a simple perception-to-control pipeline:

```text
camera frame
  -> HSV color segmentation
  -> mask cleanup
  -> largest colored blob
  -> target center and blob area
  -> closed-loop joint correction
  -> grasp / lift / place state machine
```

The main pipeline is rule-based and does not require model training. `sequential_rgb_stack.py` includes optional hooks for a local RL policy, but the policy is only loaded when an RL flag is explicitly passed.

## Capabilities

| Capability | Implementation |
|---|---|
| RGB block detection | HSV masks for red, green, and blue blocks. |
| Mask cleanup | Gaussian blur plus morphological open/close operations. |
| Target selection | Largest contour above an area threshold. |
| Visual tracking | Image-center error drives small base and shoulder corrections. |
| Grasp timing | A state machine waits for alignment and target area before closing the gripper. |
| Sequential stacking | Red, green, and blue blocks can be picked and placed into one stack. |
| Optional policy mode | A local `model.pt` can be used for tracking or approach corrections, but is not committed. |

## File Guide

| File | Description |
|---|---|
| `rgb_detect.py` | Perception-only demo. It displays red, green, and blue detections from the QArm Mini camera stream. |
| `rgb_track.py` | Closed-loop tracking demo for one selected color. It uses target center error to move the base and shoulder slowly. |
| `rgb_gripper.py` | One-block visual grasping demo with `SEARCH`, `TRACK`, `APPROACH`, `PREGRASP`, `GRASP`, `LIFT`, and `DONE` states. |
| `sequential_rgb_stack.py` | Full demo script. It searches for blocks in sequence, grasps each one, and places it at a stack location. |
| `color_utils.py` | Shared HSV color ranges, mask preprocessing, and largest-contour detection. |
| `pick_helpers.py` | Blocking placement commands and calibrated stack-height helper angles. |
| `runtime_paths.py` | Adds a local Quanser Python library path when available. |

## Dependency Notes

This minimal repository does not vendor Quanser's Python libraries. To run on hardware, the Python environment must be able to import:

```text
pal.products.qarm_mini
pal.utilities.timing
pal.utilities.vision
```

Two supported setups:

1. Run inside a full Quanser resource checkout that contains `0_libraries/python`.
2. Set `QUANSER_PYTHON_PATH` to the local Quanser Python library path.

Example:

```powershell
$env:QUANSER_PYTHON_PATH="C:\Users\kliu6\Documents\Quanser\0_libraries\python"
```

The computer also needs the usual runtime packages used by the scripts, including `opencv-python` and `numpy`.

## Perception

`color_utils.py` defines HSV ranges for red, green, and blue. Red uses two HSV intervals because red wraps around the hue boundary. Each camera frame is converted from BGR to HSV, then thresholded into a binary mask.

The mask is cleaned with Gaussian blur, morphological opening, and morphological closing. The detector keeps the largest external contour above a minimum area and returns the bounding box, center pixel, and contour area.

## Tracking

`rgb_track.py` computes:

```text
error_x = target_center_x - image_center_x
error_y = target_center_y - image_center_y
```

The controller adjusts base yaw for horizontal error and shoulder angle for vertical error. Motion increments are intentionally small and joint commands are clipped for safer first tests.

## Grasping State Machine

`rgb_gripper.py` turns perception and tracking into a one-block grasping routine:

| State | Behavior |
|---|---|
| `SEARCH` | Waits until the target color is detected consistently. |
| `TRACK` | Aligns the target near the image center. |
| `APPROACH` | Uses contour area to move closer or back away. |
| `PREGRASP` | Holds the pose briefly before closing. |
| `GRASP` | Closes the gripper. |
| `LIFT` | Raises the block after grasping. |
| `DONE` | Keeps the final state after the lift. |

## Sequential Stacking

`sequential_rgb_stack.py` extends the same idea to multiple blocks. By default it runs through:

```text
red -> green -> blue
```

For each target color, it performs:

```text
SEARCH -> TRACK -> APPROACH -> DESCEND -> GRASP -> LIFT -> PLACE
```

After each grasp, `pick_helpers.py` sends the arm through calibrated placement poses.

## How to Run

Start with perception only:

```powershell
python rgb_detect.py --camera 1
```

Then test closed-loop tracking:

```powershell
python rgb_track.py --camera 1 --arm-id 3 --color red
```

Then test one-block grasping:

```powershell
python rgb_gripper.py --camera 1 --arm-id 3 --color red
```

Finally run the sequential stacking demo:

```powershell
python sequential_rgb_stack.py --camera 1 --arm-id 3
```

Press `ESC` in the OpenCV window to stop a running demo.

## Optional RL Policy

`sequential_rgb_stack.py` can optionally load a local policy network for tracking or approach correction:

```powershell
python sequential_rgb_stack.py --use-rl-track --model-path model.pt
```

or:

```powershell
python sequential_rgb_stack.py --use-rl-approach --model-path model.pt
```

Important details:

- `model.pt` is not included in this repository.
- The policy is not loaded unless `--use-rl-track` or `--use-rl-approach` is provided.
- Without RL flags, the script uses rule-based control only.

## Hardware Notes

- Default camera device: `--camera 1`
- Default QArm Mini id: `--arm-id 3`
- Run `rgb_detect.py` first to verify camera index, lighting, and color thresholds.
- Keep the QArm Mini workspace clear before running grasping or stacking.
- HSV thresholds and placement angles may need tuning under different lighting or camera positions.

## Attribution

This project uses Quanser QArm Mini Python APIs from Quanser's academic resources:

```text
https://github.com/quanser/Quanser_Academic_Resources
```

The HackBot code in this repository is a focused vision-grasping and stacking demo built for the competition project.
