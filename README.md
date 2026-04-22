# smartcarrace

[中文说明 / Chinese Version]([C:/Users/Jasonzzhu_/Desktop/smartcarrace/README_zh.md](https://github.com/Jasonzzhu0514/smartcarrace_xunfei/blob/main/README_zh.md))

## Overview

This repository archives my ROS-based smart car projects for the iFlytek creative track of the National College Student Smart Car Competition. It preserves the core packages, task flow, and competition logic from both the 2024 and 2025 projects in a cleaner GitHub-friendly structure.

The most important package in this repository is `ucar_startup`. It is not a low-level driver package, but the orchestration layer that turns each year's written rules into an executable workflow: when the car starts, where it moves, what it recognizes, when it speaks, and how the full competition pipeline is connected.

If someone wants to understand this project quickly, the best reading path is: read the rule PDF first, then inspect the corresponding `ucar_startup` package.

## Repository Layout

```text
smartcarrace
+-- README.md
+-- README_zh.md
+-- .gitignore
+-- rules
|   +-- 2024_rule.pdf
|   `-- 2025_rule.pdf
+-- common_src
|   +-- fdilink_ahrs
|   +-- geometry
|   +-- geometry2
|   +-- navigation
|   +-- ucar_camera
|   `-- ydlidar
+-- archive_2024
|   +-- speech_command
|   +-- ucar_controller
|   +-- ucar_map
|   +-- ucar_nav
|   `-- ucar_startup
`-- archive_2025
    +-- speech_command
    +-- ucar_controller
    +-- ucar_map
    +-- ucar_nav
    +-- ucar_startup
    `-- gazebo_test_ws
```

## Package Roles

### `common_src`

- `geometry`, `geometry2`, `navigation`: foundational ROS navigation-related dependencies
- `ydlidar`: lidar driver used for localization, navigation, and obstacle-related behavior
- `fdilink_ahrs`: IMU / AHRS driver package
- `ucar_camera`: camera support package

These packages were shared across both yearly workspaces, so they were archived as a single common set.

### Year-specific competition packages

- `speech_command`: voice wake-up and speech interaction entry
- `ucar_controller`: chassis driver and low-level motion interface
- `ucar_map`: maps, RViz configuration, and related resources
- `ucar_nav`: navigation startup, localization, planning, and map integration
- `ucar_startup`: competition orchestration and top-level task logic

In simple terms, `ucar_controller` and `ucar_nav` make the car move, while `ucar_startup` makes the car follow the competition rules.

## 2024 Rules And `ucar_startup`

According to [rules/2024_rule.pdf](C:/Users/Jasonzzhu_/Desktop/smartcarrace/rules/2024_rule.pdf), the 2024 finals task was a pure real-robot rescue workflow. The overall process included:

1. starting after voice interaction
2. entering the terrorist recognition area
3. identifying the number of terrorists
4. deciding the next rescue-item branch
5. continuing through the later rescue and obstacle sections
6. completing the full task chain on the physical car

The key 2024 entry files are:

- [archive_2024/ucar_startup/launch/ucar_startup.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2024/ucar_startup/launch/ucar_startup.launch)
- [archive_2024/ucar_startup/scripts/ucar_startup.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2024/ucar_startup/scripts/ucar_startup.py)
- [archive_2024/ucar_startup/scripts/rk.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2024/ucar_startup/scripts/rk.py)

The 2024 `ucar_startup` logic is relatively direct. Its main flow can be summarized as:

1. launch speech and navigation
2. drive to the terrorist recognition area
3. subscribe to detection results
4. use the RKNN model to infer target class or count
5. play the corresponding voice prompt
6. continue into the later rescue process

This package also preserves the assets directly tied to the competition pipeline:

- `mp3/` for prerecorded prompts
- `best.rknn` for the inference model
- `DetectResult.msg` for the detection message definition

From an archival perspective, the 2024 `ucar_startup` package represents the core implementation of a real-robot recognition and navigation workflow.

## 2025 Rules And `ucar_startup`

According to [rules/2025_rule.pdf](C:/Users/Jasonzzhu_/Desktop/smartcarrace/rules/2025_rule.pdf), the 2025 task flow was more complete and included collaboration between the physical robot and a simulation stage. The main process included:

1. starting by voice or keyboard
2. entering the task area and obtaining the purchase category
3. completing the real cargo acquisition stage
4. arriving at the waiting area
5. triggering the simulation task
6. letting the simulation robot search rooms and identify the target
7. receiving the simulation result on the physical robot side
8. recognizing route signs and choosing the correct entrance
9. completing line-following and later path tasks
10. announcing the final purchase result, total cost, and change

The key 2025 entry files are:

- [archive_2025/ucar_startup/launch/ucar_startup.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/launch/ucar_startup.launch)
- [archive_2025/ucar_startup/launch/line.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/launch/line.launch)
- [archive_2025/ucar_startup/launch/tts.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/launch/tts.launch)
- [archive_2025/ucar_startup/scripts/start.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/scripts/start.py)
- [archive_2025/ucar_startup/scripts/line.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/scripts/line.py)
- [archive_2025/ucar_startup/scripts/tts.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/scripts/tts.py)
- [archive_2025/ucar_startup/scripts/rk.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/scripts/rk.py)

The 2025 `ucar_startup` package is the orchestration center of the entire system. It can largely be read as a code-level implementation of the 2025 rules. Its main logic can be summarized as:

1. wait for wake-up from `speech_command`
2. move to the task area and identify the task category
3. announce the task through offline TTS
4. navigate to the real cargo area
5. combine vision and lidar information to perform recognition and alignment
6. announce the result of the physical stage
7. move to the waiting area
8. communicate with the simulation side through rosbridge / websocket
9. receive the returned room result
10. announce the simulation result
11. recognize route signs and choose the route entrance
12. trigger line-following
13. compute total cost and change
14. announce the final result

This version of `ucar_startup` integrates several competition-facing capabilities:

- task-category acquisition
- RKNN-based object recognition
- camera and lidar-assisted alignment
- offline TTS output
- rosbridge communication
- route-sign handling and entrance selection
- line-following trigger logic
- final settlement-style reporting

If the 2024 `ucar_startup` package represents a single real-robot task chain, the 2025 package represents a more complete system with stage control, task switching, and result aggregation.

## Navigation Execution Chain

The core execution chain on the physical robot is roughly:

`ucar_startup -> ucar_nav -> ucar_controller + ydlidar + ucar_map`

This can be understood as:

- `ucar_startup`: decides task order, target points, and stage transitions
- `ucar_nav`: launches maps, localization, planning, and navigation
- `ucar_controller`: drives the chassis
- `ydlidar`: provides lidar data
- `ucar_map`: provides map and visualization resources

So from a project-understanding perspective, `ucar_startup` is the competition logic center, while `ucar_nav` and `ucar_controller` provide the execution foundation.

## 2025 Simulation Workspace

The 2025 simulation side is archived in:

- [archive_2025/gazebo_test_ws](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/gazebo_test_ws)

Key entry files include:

- [archive_2025/gazebo_test_ws/src/gazebo_pkg/launch/race.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/gazebo_test_ws/src/gazebo_pkg/launch/race.launch)
- [archive_2025/gazebo_test_ws/src/gazebo_pkg/scripts/start.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/gazebo_test_ws/src/gazebo_pkg/scripts/start.py)

This part handles room traversal, target recognition, and sending the result back to the physical robot, making it a key part of the 2025 competition workflow.

## Deployment Notes For U-CAR-02

This project was developed around the `U-CAR-02` platform. If it needs to be restored on the vehicle, a practical workspace layout can be:

```text
ucar_ws/src
+-- geometry
+-- geometry2
+-- navigation
+-- ydlidar
+-- fdilink_ahrs
+-- ucar_camera
+-- speech_command
+-- ucar_controller
+-- ucar_map
+-- ucar_nav
`-- ucar_startup
```

### 2024 deployment set

- `common_src/geometry`
- `common_src/geometry2`
- `common_src/navigation`
- `common_src/ydlidar`
- `archive_2024/speech_command`
- `archive_2024/ucar_controller`
- `archive_2024/ucar_map`
- `archive_2024/ucar_nav`
- `archive_2024/ucar_startup`

Launch entry:

- [archive_2024/ucar_startup/launch/ucar_startup.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2024/ucar_startup/launch/ucar_startup.launch)

### 2025 deployment set

- `common_src/geometry`
- `common_src/geometry2`
- `common_src/navigation`
- `common_src/ydlidar`
- `common_src/fdilink_ahrs`
- `common_src/ucar_camera`
- `archive_2025/speech_command`
- `archive_2025/ucar_controller`
- `archive_2025/ucar_map`
- `archive_2025/ucar_nav`
- `archive_2025/ucar_startup`

Launch entry:

- [archive_2025/ucar_startup/launch/ucar_startup.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/launch/ucar_startup.launch)

Supporting entries:

- [archive_2025/ucar_startup/launch/tts.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/launch/tts.launch)
- [archive_2025/ucar_startup/launch/line.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/launch/line.launch)

Before deployment, the main things to verify are:

1. serial settings for the chassis and lidar
2. map files used by `ucar_nav`
3. model paths and local script paths
4. microphone, speaker, and speech I/O environment
5. IP and rosbridge configuration for the 2025 simulation workflow

## Suggested Reading Order

To understand this repository quickly, the recommended reading order is:

1. [rules/2024_rule.pdf](C:/Users/Jasonzzhu_/Desktop/smartcarrace/rules/2024_rule.pdf) and [rules/2025_rule.pdf](C:/Users/Jasonzzhu_/Desktop/smartcarrace/rules/2025_rule.pdf)
2. [archive_2024/ucar_startup](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2024/ucar_startup)
3. [archive_2025/ucar_startup](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup)
4. [archive_2025/gazebo_test_ws](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/gazebo_test_ws)
5. [archive_2024/ucar_nav](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2024/ucar_nav) and [archive_2025/ucar_nav](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_nav)
