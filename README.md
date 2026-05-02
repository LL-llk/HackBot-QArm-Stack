# HackBot QArm Stack

HackBot QArm Stack is a 24-hour HackBot project for the Quanser QArm Mini. The project uses camera-based RGB color segmentation and closed-loop visual servoing to detect, track, grasp, and stack colored blocks.

This repository is based on Quanser's official `Quanser_Academic_Resources` codebase. The project contribution is added as a clean top-level demo package under:

```text
hackbot_qarm_stack/
```

The Quanser core libraries are not modified. No trained weights, generated caches, IDE files, or hardware logs are included.

## Project Goal

The goal is to make the QArm Mini perform a practical vision-guided manipulation pipeline:

1. Detect red, green, and blue blocks from the camera stream.
2. Track a selected target color with conservative joint updates.
3. Close the gripper when the block is aligned and inside the grasp window.
4. Lift and place blocks sequentially into a stack.

The current implementation is intentionally simple and reviewable. It prioritizes a working hardware demo over a large learning pipeline.

## What Was Implemented

| File | Role |
|---|---|
| `hackbot_qarm_stack/rgb_detect.py` | Detect red, green, and blue blocks using HSV masks and contour filtering. |
| `hackbot_qarm_stack/rgb_track.py` | Track one target color with closed-loop base and shoulder corrections. |
| `hackbot_qarm_stack/rgb_gripper.py` | Run a rule-based visual grasping state machine. |
| `hackbot_qarm_stack/sequential_rgb_stack.py` | Pick red, green, and blue blocks in sequence and place them into one stack. |
| `hackbot_qarm_stack/color_utils.py` | Shared HSV segmentation and largest-blob detection helpers. |
| `hackbot_qarm_stack/pick_helpers.py` | Shared block placement and stack-height helper functions. |
| `hackbot_qarm_stack/runtime_paths.py` | Adds the repository-local Quanser Python libraries to `sys.path`. |

## Method Overview

The demo follows this pipeline:

```text
camera frame
  -> HSV color mask
  -> morphology cleanup
  -> largest contour selection
  -> target center and area estimate
  -> closed-loop joint correction
  -> grasp / lift / place state machine
```

The scripts use rule-based control by default. `sequential_rgb_stack.py` also supports an optional local RL policy for tracking or approach corrections, but the model file is not included and is not loaded unless an RL flag is explicitly enabled.

## Recommended Demo Order

Run the perception demo first:

```powershell
python hackbot_qarm_stack\rgb_detect.py --camera 1
```

Then test closed-loop tracking:

```powershell
python hackbot_qarm_stack\rgb_track.py --camera 1 --arm-id 3 --color red
```

Then test one-block grasping:

```powershell
python hackbot_qarm_stack\rgb_gripper.py --camera 1 --arm-id 3 --color red
```

Finally run the sequential stack demo:

```powershell
python hackbot_qarm_stack\sequential_rgb_stack.py --camera 1 --arm-id 3
```

Press `ESC` in the OpenCV window to stop a demo.

## Optional Policy Mode

The stacking script can use a local compatible policy for tracking or approach:

```powershell
python hackbot_qarm_stack\sequential_rgb_stack.py --use-rl-track --model-path model.pt
```

If `--use-rl-track` and `--use-rl-approach` are not provided, the script does not load `model.pt`.

## Hardware Notes

- Default camera device: `--camera 1`
- Default QArm Mini id: `--arm-id 3`
- Motion commands are intentionally small for safer first tests.
- Test perception before enabling arm motion.
- Keep the workspace clear while testing grasping and stacking.

## Repository Hygiene

This branch only adds the clean HackBot demo files and a small `.gitignore`.

Excluded from the commit:

- trained model weights such as `model.pt`
- Python caches
- IDE files
- generated logs
- local pose files
- copied Quanser `hal/` or `pal/` trees

## Attribution

This project is built on top of Quanser's public academic resource repository:

```text
https://github.com/quanser/Quanser_Academic_Resources
```

Quanser's original repository provides the device libraries, examples, and setup resources. This HackBot branch adds a focused top-level QArm Mini vision-grasping demo package.
