# QArm Mini Vision Grasping Demos

This folder contains clean, self-contained QArm Mini demos for camera-based color block perception, tracking, grasping, and sequential stacking.

The demos are intended to be run from this repository with Quanser's local Python libraries available under `0_libraries/python`. No trained model weights, cached files, IDE files, or generated logs are included.

## Demos

| File | Purpose |
|---|---|
| `rgb_detect.py` | Detect red, green, and blue blocks in the QArm Mini camera stream. |
| `rgb_track.py` | Track one color block with conservative closed-loop joint commands. |
| `rgb_gripper.py` | Run a rule-based visual grasping state machine. |
| `sequential_rgb_stack.py` | Pick red, green, and blue blocks in sequence and place them at a stack location. |
| `pick_helpers.py` | Shared place/stack helper functions. |

## Typical Run Order

Start with perception only:

```powershell
python 5_research\qarm_mini\vision_grasping_demos\rgb_detect.py --camera 1
```

Then test visual tracking:

```powershell
python 5_research\qarm_mini\vision_grasping_demos\rgb_track.py --camera 1 --arm-id 3 --color red
```

Then test grasping:

```powershell
python 5_research\qarm_mini\vision_grasping_demos\rgb_gripper.py --camera 1 --arm-id 3 --color red
```

Finally run sequential stacking:

```powershell
python 5_research\qarm_mini\vision_grasping_demos\sequential_rgb_stack.py --camera 1 --arm-id 3
```

## Optional RL Policy

`sequential_rgb_stack.py` supports an optional policy network for tracking or approach corrections. The model file is not included in this repository. Use it only when you have a local compatible `model.pt`:

```powershell
python 5_research\qarm_mini\vision_grasping_demos\sequential_rgb_stack.py --use-rl-track --model-path model.pt
```

If RL flags are not enabled, the script uses rule-based control and does not load `model.pt`.

## Notes

- Default hardware settings are `--camera 1` and `--arm-id 3`.
- Press `ESC` in the OpenCV window to stop a demo.
- Keep motion slow when first testing with hardware.
- The scripts do not modify Quanser core libraries.

