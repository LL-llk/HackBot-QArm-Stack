# HackBot QArm Stack

HackBot QArm Stack is a 24-hour HackBot project for the Quanser QArm Mini. It implements a camera-guided manipulation demo that detects colored blocks, tracks a selected target, closes the gripper when the target is aligned, and places blocks into a small stack.

The project code is intentionally placed at the repository root so the main demo scripts are visible immediately:

```text
rgb_detect.py
rgb_track.py
rgb_gripper.py
sequential_rgb_stack.py
color_utils.py
pick_helpers.py
runtime_paths.py
```

This repository is based on Quanser's official `Quanser_Academic_Resources` codebase. The HackBot contribution adds a focused QArm Mini vision and grasping demo. Quanser core libraries are not modified, and no generated logs, cache files, trained weights, or hardware recordings are included.

## Project Summary

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

The system is rule-based by default. It does not require model training to run the main demos. `sequential_rgb_stack.py` includes optional hooks for a local RL policy, but the policy is only loaded when an RL flag is explicitly passed.

## Main Capabilities

| Capability | Implementation |
|---|---|
| RGB block detection | HSV masks for red, green, and blue blocks. |
| Robust mask cleanup | Gaussian blur plus morphological open/close operations. |
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
| `rgb_gripper.py` | One-block visual grasping demo. It uses states such as `SEARCH`, `TRACK`, `APPROACH`, `PREGRASP`, `GRASP`, `LIFT`, and `DONE`. |
| `sequential_rgb_stack.py` | Full demo script. It searches for blocks in sequence, grasps each one, and places it at a stack location. |
| `color_utils.py` | Shared HSV color ranges, mask preprocessing, and largest-contour detection. |
| `pick_helpers.py` | Blocking placement commands and calibrated stack-height helper angles. |
| `runtime_paths.py` | Adds the repository-local Quanser Python library path, `0_libraries/python`, at runtime. |
| `HACKBOT_DEMO_README.md` | Shorter quick-start README for the demo scripts. |

## Perception

`color_utils.py` defines HSV ranges for red, green, and blue. Red uses two HSV intervals because red wraps around the hue boundary. Each camera frame is converted from BGR to HSV, then thresholded into a binary mask.

The mask is cleaned with:

- Gaussian blur
- morphological opening
- morphological closing

The detector then finds external contours and keeps the largest contour above a minimum area. The returned target data includes:

- bounding box
- center pixel `(cx, cy)`
- contour area

The center is used for alignment. The area is used as a rough distance cue during approach.

## Tracking

`rgb_track.py` tracks one selected color with conservative joint updates.

The script computes:

```text
error_x = target_center_x - image_center_x
error_y = target_center_y - image_center_y
```

The controller then adjusts:

- base yaw for horizontal error
- shoulder angle for vertical error

The motion is intentionally slow and clipped. If the target is briefly lost, the script uses the last known error for a small recovery motion before returning to search behavior.

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

This design keeps the logic easy to inspect and tune during a short hardware hackathon.

## Sequential Stacking

`sequential_rgb_stack.py` extends the same idea to multiple blocks. By default it runs through:

```text
red -> green -> blue
```

For each target color, it performs:

```text
SEARCH -> TRACK -> APPROACH -> DESCEND -> GRASP -> LIFT -> PLACE
```

After each grasp, `pick_helpers.py` sends the arm through calibrated placement poses. `stack_theta()` selects a shoulder angle for each stack height, and `place_block()` performs the place-and-release motion.

You can change the color order:

```powershell
python sequential_rgb_stack.py --colors blue red green
```

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

## Command Options

Common options:

| Option | Meaning |
|---|---|
| `--camera` | Camera device id passed to Quanser `Camera2D`. Default: `1`. |
| `--arm-id` | QArm Mini hardware id. Default: `3`. |
| `--color` | Target color for single-color demos: `red`, `green`, or `blue`. |
| `--duration` | Maximum demo runtime in seconds. |
| `--colors` | Color order for sequential stacking. |

Example:

```powershell
python rgb_gripper.py --camera 1 --arm-id 3 --color blue --duration 180
```

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

## Hardware and Safety Notes

- Default hardware settings are `--camera 1` and `--arm-id 3`.
- Run `rgb_detect.py` first to verify camera index, lighting, and color thresholds.
- Keep the QArm Mini workspace clear before running grasping or stacking.
- The controller uses small joint increments, but physical hardware should still be tested carefully.
- The HSV thresholds and placement angles are calibrated for a simple tabletop color-block setup and may need tuning under different lighting or camera positions.

## What Is Not Included

This clean branch does not include:

- trained weights such as `model.pt`
- generated logs
- cached Python files
- IDE files
- local pose recordings
- copied Quanser `hal/` or `pal/` directories

The goal is to keep the HackBot contribution easy to review and easy to run from the public repository.

## Attribution

This project builds on Quanser's public academic resource repository:

```text
https://github.com/quanser/Quanser_Academic_Resources
```

Quanser's original repository provides the device libraries, examples, and setup resources. This HackBot branch adds a root-level QArm Mini vision-grasping and stacking demo.
