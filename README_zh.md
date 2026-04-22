# smartcarrace

[English Version](C:/Users/Jasonzzhu_/Desktop/smartcarrace/README.md)

## 项目简介

本仓库用于归档我在全国大学生智能汽车竞赛讯飞创意组中的 ROS 智能车项目，保留了 2024 和 2025 两个年度的核心功能包、任务链路和比赛逻辑。

这个仓库最核心的功能包是 `ucar_startup`。它并不是底层驱动包，而是将每年比赛规则转化为可执行流程的任务编排层：什么时候启动、先去哪里、在哪个区域做识别、什么时候播报语音、什么时候进入循迹，以及如何把整条比赛链路串起来。

因此，如果想快速理解这个项目，最推荐的阅读方式是：先看规则 PDF，再看对应年份的 `ucar_startup`。

## 仓库结构

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

## 功能包说明

### `common_src`

- `geometry`、`geometry2`、`navigation`：ROS 导航栈相关基础依赖。
- `ydlidar`：激光雷达驱动，用于定位、避障和导航链路。
- `fdilink_ahrs`：IMU / AHRS 驱动包。
- `ucar_camera`：摄像头相关功能支持包。

这部分是两个年份都需要的公共基础能力，因此在归档时只保留一份。

### 年度比赛功能包

- `speech_command`：语音唤醒、语音交互入口。
- `ucar_controller`：底盘驱动与底层运动控制接口。
- `ucar_map`：地图、RViz 配置及相关资源。
- `ucar_nav`：导航启动、定位、规划与地图调用。
- `ucar_startup`：比赛流程编排，是整个项目最重要的功能包。

从职责上看，`ucar_controller` 和 `ucar_nav` 负责“让小车能动起来”，而 `ucar_startup` 负责“让小车按照比赛规则完成任务”。

## 2024 规则与 `ucar_startup`

参考 [rules/2024_rule.pdf](C:/Users/Jasonzzhu_/Desktop/smartcarrace/rules/2024_rule.pdf)，2024 年决赛任务主要是一个纯实车的救援流程。整体任务包括：

1. 语音交互后启动
2. 进入恐怖分子识别区域
3. 识别恐怖分子数量
4. 判断后续救援物资任务分支
5. 继续完成后续救援、避障与路径任务
6. 在实车端完成整条比赛流程

对应到代码层面，2024 年的关键入口是：

- [archive_2024/ucar_startup/launch/ucar_startup.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2024/ucar_startup/launch/ucar_startup.launch)
- [archive_2024/ucar_startup/scripts/ucar_startup.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2024/ucar_startup/scripts/ucar_startup.py)
- [archive_2024/ucar_startup/scripts/rk.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2024/ucar_startup/scripts/rk.py)

这一年的 `ucar_startup` 逻辑比较直接，核心可以概括为：

1. 启动语音和导航
2. 控制小车到达恐怖分子识别区域
3. 订阅识别结果
4. 通过 RKNN 模型判断目标类别或数量
5. 播放对应语音提示
6. 进入后续救援流程

该包中保留了与比赛逻辑直接相关的资源，包括：

- `mp3/`：比赛语音播报资源
- `best.rknn`：推理模型文件
- `DetectResult.msg`：识别结果消息定义

从归档角度看，2024 年的 `ucar_startup` 代表的是“实车识别 + 导航决策”的核心实现。

## 2025 规则与 `ucar_startup`

参考 [rules/2025_rule.pdf](C:/Users/Jasonzzhu_/Desktop/smartcarrace/rules/2025_rule.pdf)，2025 年的任务流程更完整，包含实车阶段与仿真阶段的协同。主要流程包括：

1. 语音或键盘启动
2. 进入任务区并获取采购任务类别
3. 完成实物货物识别与获取阶段
4. 到达等待区
5. 触发仿真任务
6. 由仿真车完成房间搜索与目标识别
7. 实车端接收仿真返回结果
8. 识别路径标志并选择正确入口
9. 完成循迹与后续通行任务
10. 播报最终采购结果、总价与找零

对应到代码层面，2025 年的关键入口是：

- [archive_2025/ucar_startup/launch/ucar_startup.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/launch/ucar_startup.launch)
- [archive_2025/ucar_startup/launch/line.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/launch/line.launch)
- [archive_2025/ucar_startup/launch/tts.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/launch/tts.launch)
- [archive_2025/ucar_startup/scripts/start.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/scripts/start.py)
- [archive_2025/ucar_startup/scripts/line.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/scripts/line.py)
- [archive_2025/ucar_startup/scripts/tts.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/scripts/tts.py)
- [archive_2025/ucar_startup/scripts/rk.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/scripts/rk.py)

这一年的 `ucar_startup` 是整个系统的流程中心，基本可以看作对 2025 年规则的代码化实现。其主要逻辑可以概括为：

1. 等待 `speech_command` 唤醒
2. 前往任务区域并识别任务类别
3. 通过离线 TTS 播报当前任务
4. 前往实物货物区域
5. 结合视觉与激光信息完成目标识别和对位
6. 播报实物阶段结果
7. 前往等待区
8. 通过 rosbridge / websocket 与仿真端通信
9. 接收仿真端返回的房间结果
10. 播报仿真结果
11. 识别路径标志并选择路线入口
12. 触发循迹
13. 计算总价与找零
14. 播报最终结果

这一版 `ucar_startup` 同时整合了多种比赛能力：

- 任务类别获取
- RKNN 目标识别
- 摄像头与雷达辅助对位
- 离线 TTS 播报
- rosbridge 通信
- 路标识别与入口选择
- 循迹触发
- 最终结算播报

如果说 2024 年的 `ucar_startup` 更偏向单条实车任务链，那么 2025 年的 `ucar_startup` 已经具备了完整的阶段控制、任务切换和结果汇总能力。

## 导航执行链路

实车端的核心执行链路大致如下：

`ucar_startup -> ucar_nav -> ucar_controller + ydlidar + ucar_map`

对应关系可以理解为：

- `ucar_startup`：决定任务顺序、目标点与阶段切换
- `ucar_nav`：启动地图、定位、规划与导航
- `ucar_controller`：驱动底盘运动
- `ydlidar`：提供雷达数据
- `ucar_map`：提供地图与可视化资源

所以从项目理解上，`ucar_startup` 是比赛逻辑中心，而 `ucar_nav` 和 `ucar_controller` 是执行基础。

## 2025 仿真部分

2025 年新增的仿真部分保存在：

- [archive_2025/gazebo_test_ws](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/gazebo_test_ws)

关键入口包括：

- [archive_2025/gazebo_test_ws/src/gazebo_pkg/launch/race.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/gazebo_test_ws/src/gazebo_pkg/launch/race.launch)
- [archive_2025/gazebo_test_ws/src/gazebo_pkg/scripts/start.py](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/gazebo_test_ws/src/gazebo_pkg/scripts/start.py)

这部分主要负责仿真端房间遍历、目标识别以及将结果返回给实车端，是 2025 年规则中非常关键的一段链路。

## U-CAR-02 部署说明

本项目的实车环境基于 `U-CAR-02`。如果需要在车上恢复运行，一个常见的工作空间结构可以是：

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

### 2024 部署包

- `common_src/geometry`
- `common_src/geometry2`
- `common_src/navigation`
- `common_src/ydlidar`
- `archive_2024/speech_command`
- `archive_2024/ucar_controller`
- `archive_2024/ucar_map`
- `archive_2024/ucar_nav`
- `archive_2024/ucar_startup`

启动入口：

- [archive_2024/ucar_startup/launch/ucar_startup.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2024/ucar_startup/launch/ucar_startup.launch)

### 2025 部署包

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

启动入口：

- [archive_2025/ucar_startup/launch/ucar_startup.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/launch/ucar_startup.launch)

辅助入口：

- [archive_2025/ucar_startup/launch/tts.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/launch/tts.launch)
- [archive_2025/ucar_startup/launch/line.launch](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup/launch/line.launch)

部署前建议重点检查：

1. 底盘与雷达串口配置
2. `ucar_nav` 中使用的地图文件
3. 模型路径与脚本中的本地路径
4. 麦克风、扬声器和语音输入输出环境
5. 2025 年仿真通信所需的 IP 与 rosbridge 配置

## 推荐阅读顺序

如果想快速理解这个项目，推荐按下面顺序阅读：

1. [rules/2024_rule.pdf](C:/Users/Jasonzzhu_/Desktop/smartcarrace/rules/2024_rule.pdf) 和 [rules/2025_rule.pdf](C:/Users/Jasonzzhu_/Desktop/smartcarrace/rules/2025_rule.pdf)
2. [archive_2024/ucar_startup](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2024/ucar_startup)
3. [archive_2025/ucar_startup](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_startup)
4. [archive_2025/gazebo_test_ws](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/gazebo_test_ws)
5. [archive_2024/ucar_nav](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2024/ucar_nav) 和 [archive_2025/ucar_nav](C:/Users/Jasonzzhu_/Desktop/smartcarrace/archive_2025/ucar_nav)
