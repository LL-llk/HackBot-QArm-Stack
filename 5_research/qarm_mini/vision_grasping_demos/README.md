# QArm Mini Vision Grasping Demos

This folder contains the clean demo code for HackBot QArm Stack. The demos use camera-based RGB block detection, closed-loop tracking, rule-based grasping, and sequential stacking on the Quanser QArm Mini.

The scripts are self-contained and use Quanser's local Python libraries from `0_libraries/python`. They do not modify Quanser core libraries and do not require a trained model unless an optional RL mode is explicitly enabled.

## Files

| File | Purpose |
|---|---|
| `rgb_detect.py` | Shows red, green, and blue block detections from the camera stream. |
| `rgb_track.py` | Tracks one selected color with small base and shoulder corrections. |
| `rgb_gripper.py` | Runs a one-block visual grasping state machine. |
| `sequential_rgb_stack.py` | Picks red, green, and blue blocks and places them into one stack. |
| `color_utils.py` | Provides HSV masks, mask cleanup, and largest-blob detection. |
| `pick_helpers.py` | Provides placement poses and stack-height helpers. |
| `runtime_paths.py` | Adds the repository-local Quanser Python path at runtime. |

## Control Pipeline

```text
camera frame
  -> HSV mask for target color
  -> mask cleanup
  -> largest contour
  -> target center and area
  -> joint correction
  -> grasp / lift / place state machine
```

The closed-loop controller uses the target center error for alignment and the contour area as a simple distance cue. The stacking script reuses the same perception loop and calls calibrated placement helpers after each grasp.

## Run Order

Start with perception only:

```powershell
python 5_research\qarm_mini\vision_grasping_demos\rgb_detect.py --camera 1
```

Then test visual tracking:

```powershell
python 5_research\qarm_mini\vision_grasping_demos\rgb_track.py --camera 1 --arm-id 3 --color red
```

Then test one-block grasping:

```powershell
python 5_research\qarm_mini\vision_grasping_demos\rgb_gripper.py --camera 1 --arm-id 3 --color red
```

Finally run sequential stacking:

```powershell
python 5_research\qarm_mini\vision_grasping_demos\sequential_rgb_stack.py --camera 1 --arm-id 3
```

Press `ESC` in the OpenCV window to stop a demo.

## Optional RL Policy

`sequential_rgb_stack.py` supports an optional local policy network for tracking or approach correction:

```powershell
python 5_research\qarm_mini\vision_grasping_demos\sequential_rgb_stack.py --use-rl-track --model-path model.pt
```

The model file is not included in this repository. If RL flags are not enabled, the script uses rule-based control and does not load `model.pt`.

## Practical Notes

- Default hardware settings are `--camera 1` and `--arm-id 3`.
- Use `rgb_detect.py` first to confirm lighting and color thresholds.
- Keep motion slow when first testing with hardware.
- The current controller is calibrated for a simple tabletop color-block setup.
- No generated logs, caches, trained weights, or local pose files are committed.
