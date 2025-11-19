# YOPO AirSim 迁移指南

## 目录
1. [概述](#概述)
2. [系统要求](#系统要求)
3. [架构变更](#架构变更)
4. [安装步骤](#安装步骤)
5. [配置说明](#配置说明)
6. [使用方法](#使用方法)
7. [话题映射](#话题映射)
8. [故障排除](#故障排除)
9. [性能优化](#性能优化)

---

## 概述

本文档描述如何将 YOPO 项目从自定义仿真器迁移到 **AirSim + Unreal Engine** 仿真环境。

### 迁移动机
- **真实感提升**: AirSim 提供逼真的 3D 环境和物理仿真
- **硬件在环**: 支持无缝过渡到真实无人机
- **丰富传感器**: 支持多种相机、激光雷达等传感器
- **社区支持**: Microsoft 维护，文档完善

### 主要变更
| 组件 | 原系统 | 新系统 (AirSim) |
|------|--------|----------------|
| **仿真器** | 自定义 SO3 动力学仿真器 | AirSim SimpleFlight |
| **深度相机** | CUDA 加速射线投射 | Unreal Engine 深度渲染 |
| **坐标系** | ENU (East-North-Up) | NED (North-East-Down) → 桥接转换为 ENU |
| **控制接口** | SO3 推力命令 | 位置/速度命令 |
| **物理引擎** | 100Hz SO3 微分几何 | FastPhysicsEngine (可调) |

---

## 系统要求

### 硬件要求
- **CPU**: Intel i5 或更高 (推荐 i7/Ryzen 7)
- **GPU**: NVIDIA GTX 1060 或更高 (推荐 RTX 2060+)
  - 支持 Vulkan 或 DirectX 11
  - 至少 4GB 显存 (推荐 8GB+)
- **RAM**: 16GB+ (推荐 32GB)
- **存储**: 50GB+ 可用空间

### 软件要求
- **操作系统**: Ubuntu 20.04 LTS
- **ROS**: Noetic (1.15.x)
- **AirSim**: 1.8.1
- **Unreal Engine**: 4.27.2
- **Python**: 3.8+
- **CUDA**: 11.x (可选，用于 TensorRT)

---

## 架构变更

### 原系统架构
```
┌─────────────────────────────────────────────────────┐
│ 自定义仿真器 (C++/CUDA)                              │
│  ├─ SO3 动力学仿真 (100Hz)                          │
│  ├─ CUDA 深度图生成 (>1000fps)                      │
│  └─ 随机地图生成                                     │
└──────────────┬──────────────────────────────────────┘
               │ ROS Topics
               ├─ /sim/odom (Odometry, ENU, 100Hz)
               ├─ /sim/imu (IMU, ENU, 100Hz)
               ├─ /depth_image (Image 32FC1, 30Hz)
               └─ so3_cmd (SO3Command) ← Control Input
               │
┌──────────────┴──────────────────────────────────────┐
│ YOPO 规划器 (Python + PyTorch)                      │
│  ├─ ResNet-18 视觉特征提取                          │
│  ├─ 15条轨迹候选评估                                │
│  └─ 5阶多项式轨迹生成                               │
└─────────────────────────────────────────────────────┘
```

### 新系统架构 (AirSim)
```
┌─────────────────────────────────────────────────────┐
│ Unreal Engine 4.27 + AirSim 1.8.1                   │
│  ├─ SimpleFlight 物理引擎                           │
│  ├─ 深度相机 (Unreal 渲染, NED)                     │
│  └─ IMU + 里程计 (NED)                              │
└──────────────┬──────────────────────────────────────┘
               │ AirSim ROS Wrapper
               ├─ /airsim_node/Drone1/odom_local_ned (NED)
               ├─ /airsim_node/Drone1/imu/Imu (NED)
               ├─ /airsim_node/Drone1/depth_cam/DepthPlanar
               └─ /airsim_node/Drone1/pose_cmd_body_frame
               │
┌──────────────┴──────────────────────────────────────┐
│ 桥接节点 (Python)                                    │
│  ├─ airsim_yopo_bridge.py                           │
│  │   ├─ NED → ENU 坐标转换                          │
│  │   ├─ 深度图格式转换                              │
│  │   └─ 话题重映射                                  │
│  └─ yopo_airsim_control_bridge.py                   │
│      ├─ ENU → NED 坐标转换                          │
│      ├─ PositionCommand → PoseStamped               │
│      └─ 控制模式选择 (位置/速度)                    │
└──────────────┬──────────────────────────────────────┘
               │ YOPO Interface (unchanged)
               ├─ /sim/odom (ENU, 100Hz)
               ├─ /sim/imu (ENU, 100Hz)
               ├─ /depth_image (32FC1, 30Hz)
               └─ /so3_control/pos_cmd ← Control Input
               │
┌──────────────┴──────────────────────────────────────┐
│ YOPO 规划器 (无需修改)                              │
│  └─ test_yopo_ros.py                                │
└─────────────────────────────────────────────────────┘
```

**关键设计理念**: 通过桥接节点实现接口适配，**YOPO 核心代码无需修改**。

---

## 安装步骤

### 步骤 1: 安装 Unreal Engine 4.27.2

#### 1.1 注册 Epic Games 账号并关联 GitHub
1. 注册 [Epic Games 账号](https://www.epicgames.com/)
2. 在 [Epic Games 设置](https://www.epicgames.com/account/connections) 关联你的 GitHub 账号
3. 访问 [Unreal Engine GitHub](https://github.com/EpicGames/UnrealEngine) 并接受邀请

#### 1.2 克隆并编译 Unreal Engine
```bash
# 克隆 Unreal Engine 4.27
cd ~
git clone -b 4.27 https://github.com/EpicGames/UnrealEngine.git
cd UnrealEngine

# 下载依赖
./Setup.sh

# 生成项目文件
./GenerateProjectFiles.sh

# 编译 (需要 1-2 小时, 40GB+ 磁盘空间)
make

# 启动编辑器 (验证安装)
./Engine/Binaries/Linux/UE4Editor
```

### 步骤 2: 编译 AirSim

```bash
# 安装依赖
sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    libboost-all-dev \
    libeigen3-dev

# 克隆 AirSim
cd ~
git clone https://github.com/Microsoft/AirSim.git --branch v1.8.1
cd AirSim

# 编译
./setup.sh
./build.sh

# 测试 (可选)
cd build_debug/output/bin
./AirSimUnitTests
```

### 步骤 3: 安装 YOPO + AirSim 集成

```bash
# 返回 YOPO 项目目录
cd /home/user/YOPO

# 运行自动安装脚本
./setup_airsim.sh
```

安装脚本会自动完成：
- ✓ 检查系统依赖
- ✓ 安装 ROS 包和 Python 库
- ✓ 克隆 AirSim ROS wrapper
- ✓ 复制自定义桥接节点
- ✓ 配置 AirSim 设置文件
- ✓ 编译 ROS 工作空间

### 步骤 4: 下载或创建 Unreal 环境

#### 选项 A: 使用预编译环境 (推荐)

从 [AirSim Releases](https://github.com/microsoft/AirSim/releases) 下载预编译的 Linux 环境:
```bash
cd ~/Documents/AirSim
wget https://github.com/microsoft/AirSim/releases/download/v1.8.1/Blocks.zip
unzip Blocks.zip
```

#### 选项 B: 使用自定义 Unreal 项目

```bash
# 打开 Unreal Engine
cd ~/UnrealEngine
./Engine/Binaries/Linux/UE4Editor

# 创建新项目或打开现有项目
# 在项目根目录运行:
cd ~/YourUnrealProject
~/AirSim/Unreal/Environments/Blocks/update_from_git.sh
```

---

## 配置说明

### AirSim 配置文件 (`~/Documents/AirSim/settings.json`)

已自动配置，关键参数说明：

```json
{
  "SimMode": "Multirotor",  // 多旋翼模式
  "ClockSpeed": 1.0,        // 仿真速度 (1.0 = 实时)

  "Vehicles": {
    "Drone1": {
      "VehicleType": "SimpleFlight",  // 物理模型

      "Cameras": {
        "depth_cam": {
          "CaptureSettings": [{
            "ImageType": 2,          // 2 = DepthPlanar
            "Width": 640,
            "Height": 480,
            "FOV_Degrees": 90        // 视场角 (匹配 YOPO 训练数据)
          }],
          "X": 0.0, "Y": 0.0, "Z": 0.0,  // 相机位置 (相对机体)
          "Pitch": 0.0, "Roll": 0.0, "Yaw": 0.0  // 相机姿态
        }
      },

      "X": 0.0, "Y": 0.0, "Z": -2.0,  // 初始位置 (NED, Z负表示向上)
      "Yaw": 0.0
    }
  },

  "PhysicsEngineName": "FastPhysicsEngine"  // 高性能物理引擎
}
```

**重要参数调整:**

1. **相机俯仰角**: 如果 YOPO 训练时相机有俯仰，修改 `Pitch`:
   ```json
   "Pitch": -10.0,  // 向下俯视 10 度
   ```

2. **仿真速度**: 如果硬件性能不足，降低仿真速度:
   ```json
   "ClockSpeed": 0.5,  // 0.5倍速
   ```

3. **深度图分辨率**: 匹配 YOPO 配置 (默认 640x480):
   ```json
   "Width": 640, "Height": 480
   ```

### ROS 启动文件配置 (`airsim_ros_pkgs/launch/airsim_yopo.launch`)

关键参数：

```xml
<!-- 更新频率 -->
<param name="update_airsim_control_every_n_sec" type="double" value="0.01" />  <!-- 100 Hz -->
<param name="update_airsim_img_response_every_n_sec" type="double" value="0.033" />  <!-- 30 Hz -->

<!-- 控制模式 -->
<param name="control_mode" type="string" value="position" />  <!-- "position" 或 "velocity" -->
```

**控制模式选择:**
- `position`: 位置控制 (默认，更稳定)
- `velocity`: 速度控制 (响应更快，但可能不稳定)

---

## 使用方法

### 完整启动流程 (4 个终端)

#### 终端 1: 启动 Unreal Engine + AirSim

```bash
# 如果使用预编译环境
cd ~/Documents/AirSim/Blocks/LinuxNoEditor
./Blocks.sh -ResX=1280 -ResY=720 -windowed

# 如果使用自定义 Unreal 项目
cd ~/UnrealEngine
./Engine/Binaries/Linux/UE4Editor ~/YourUnrealProject/YourProject.uproject
```

**等待 Unreal 完全加载** (看到无人机出现)

#### 终端 2: 启动 AirSim ROS 节点和桥接

```bash
cd ~/YOPO/Controller
source devel/setup.bash
roslaunch airsim_ros_pkgs airsim_yopo.launch
```

**验证输出:**
```
[ INFO] [1234567890.123]: AirSim-YOPO Bridge Node Started!
[ INFO] [1234567890.124]:   Odom: /airsim_node/Drone1/odom_local_ned -> /sim/odom
[ INFO] [1234567890.125]:   IMU:  /airsim_node/Drone1/imu/Imu -> /sim/imu
[ INFO] [1234567890.126]:   Depth: /airsim_node/Drone1/depth_cam/DepthPlanar -> /depth_image
[ INFO] [1234567890.127]: YOPO-AirSim Control Bridge Node Started!
```

#### 终端 3: 启动 YOPO 规划器

```bash
cd ~/YOPO/YOPO
source ~/YOPO/Controller/devel/setup.bash
python3 test_yopo_ros.py --trial=1 --epoch=50
```

**验证输出:**
```
load weight from: /home/user/YOPO/YOPO/saved/YOPO_1/epoch50.pth
YOPO Net Node Ready!
```

#### 终端 4: 可视化 (RViz)

```bash
source ~/YOPO/Controller/devel/setup.bash
rviz -d ~/YOPO/yopo.rviz
```

**在 RViz 中:**
1. 点击工具栏的 **"2D Nav Goal"**
2. 在地图上点击设置目标点
3. 观察无人机自主导航

### 快速启动脚本

创建 `~/YOPO/launch_airsim.sh`:
```bash
#!/bin/bash
# 在新终端中启动各个组件

# 启动 Unreal (假设使用 Blocks)
gnome-terminal -- bash -c "cd ~/Documents/AirSim/Blocks/LinuxNoEditor && ./Blocks.sh -ResX=1280 -ResY=720 -windowed; exec bash"

# 等待 Unreal 启动
sleep 15

# 启动 ROS 节点
gnome-terminal -- bash -c "cd ~/YOPO/Controller && source devel/setup.bash && roslaunch airsim_ros_pkgs airsim_yopo.launch; exec bash"

# 等待 ROS 初始化
sleep 5

# 启动 YOPO
gnome-terminal -- bash -c "cd ~/YOPO/YOPO && source ~/YOPO/Controller/devel/setup.bash && python3 test_yopo_ros.py --trial=1 --epoch=50; exec bash"

# 启动 RViz
gnome-terminal -- bash -c "source ~/YOPO/Controller/devel/setup.bash && rviz -d ~/YOPO/yopo.rviz; exec bash"
```

---

## 话题映射

### 传感器数据流 (AirSim → YOPO)

| AirSim ROS Topic | 桥接节点 | YOPO Topic | 消息类型 | 频率 |
|------------------|----------|------------|----------|------|
| `/airsim_node/Drone1/odom_local_ned` | `airsim_yopo_bridge` | `/sim/odom` | `nav_msgs/Odometry` | 100 Hz |
| `/airsim_node/Drone1/imu/Imu` | `airsim_yopo_bridge` | `/sim/imu` | `sensor_msgs/Imu` | 100 Hz |
| `/airsim_node/Drone1/depth_cam/DepthPlanar` | `airsim_yopo_bridge` | `/depth_image` | `sensor_msgs/Image` (32FC1) | 30 Hz |

### 控制命令流 (YOPO → AirSim)

| YOPO Topic | 桥接节点 | AirSim ROS Topic | 消息类型 | 频率 |
|------------|----------|------------------|----------|------|
| `/so3_control/pos_cmd` | `yopo_airsim_control_bridge` | `/airsim_node/Drone1/pose_cmd_body_frame` | `geometry_msgs/PoseStamped` | 50 Hz |

### 坐标系转换

#### ENU (YOPO) ↔ NED (AirSim)

```
位置转换:
  NED.x = ENU.y  (North = East 的 y 分量)
  NED.y = ENU.x  (East = East 的 x 分量)
  NED.z = -ENU.z (Down = -Up)

速度转换:
  同位置转换

四元数转换:
  R_enu = R_z(90°) * R_x(180°) * R_ned
```

#### 深度图处理
```python
# AirSim DepthPlanar: 沿相机主轴的距离 (米)
# YOPO 需要: 32FC1 格式，归一化到 [0, 20] 米

depth_image = clip(depth_airsim, 0.04, 20.0)
depth_image = nan_to_num(depth_image)  # 处理 NaN/Inf
```

---

## 故障排除

### 问题 1: AirSim 连接失败

**症状:**
```
[ ERROR]: Could not connect to AirSim API server
```

**解决方法:**
1. 确认 Unreal Engine 已完全启动 (看到无人机)
2. 检查 `settings.json` 中的端口:
   ```json
   "ApiServerPort": 41451
   ```
3. 测试 Python API:
   ```python
   import airsim
   client = airsim.MultirotorClient()
   client.confirmConnection()
   ```

### 问题 2: 深度图无输出

**症状:**
```
[ WARN]: Depth topic /depth_image has no data
```

**解决方法:**
1. 检查相机配置 (`settings.json`):
   ```json
   "ImageType": 2,  // 必须是 2 (DepthPlanar)
   ```
2. 在 Unreal 中启用深度相机:
   - 按 `;` 键打开子窗口
   - 选择 "depth_cam"
3. 检查话题发布:
   ```bash
   rostopic hz /airsim_node/Drone1/depth_cam/DepthPlanar
   ```

### 问题 3: 无人机不响应控制命令

**症状:**
无人机悬停不动，不响应目标点

**解决方法:**
1. 检查 API 控制是否启用:
   ```bash
   # 在 Python 中
   client.enableApiControl(True)
   client.armDisarm(True)
   ```
2. 检查控制话题:
   ```bash
   rostopic echo /so3_control/pos_cmd  # 确认 YOPO 在发布
   rostopic echo /airsim_node/Drone1/pose_cmd_body_frame  # 确认桥接在转发
   ```
3. 手动测试控制:
   ```python
   import airsim
   client = airsim.MultirotorClient()
   client.enableApiControl(True)
   client.armDisarm(True)
   client.takeoffAsync().join()
   client.moveToPositionAsync(0, 0, -10, 5).join()
   ```

### 问题 4: 坐标系不匹配

**症状:**
无人机向错误的方向移动

**解决方法:**
1. 验证坐标系转换:
   ```bash
   # 发布测试目标: ENU (10, 0, 2)
   # 预期 AirSim 移动到 NED (0, 10, -2)
   rostopic pub /move_base_simple/goal geometry_msgs/PoseStamped "..."
   ```
2. 检查桥接节点日志:
   ```bash
   rosnode log list yopo_airsim_control_bridge
   ```

### 问题 5: 性能不足

**症状:**
- 仿真卡顿
- 深度图帧率 < 30 Hz
- YOPO 处理时间超时

**解决方法:**
1. 降低 Unreal 图形质量:
   - 设置 → 可扩展性 → 低
2. 降低仿真速度 (`settings.json`):
   ```json
   "ClockSpeed": 0.5
   ```
3. 禁用 YOPO 可视化 (`test_yopo_ros.py`):
   ```python
   'visualize': False
   ```
4. 使用 TensorRT 加速:
   ```bash
   python3 test_yopo_ros.py --use_tensorrt=1 --trial=1 --epoch=50
   ```

### 问题 6: ROS 包依赖缺失

**症状:**
```
CMake Error: Could not find package airsim_ros_pkgs
```

**解决方法:**
```bash
cd ~/YOPO/Controller
source /opt/ros/noetic/setup.bash
catkin_make
source devel/setup.bash
```

---

## 性能优化

### 1. GPU 加速

确保使用 NVIDIA GPU:
```bash
# 检查 GPU
nvidia-smi

# Unreal 启动参数
./Blocks.sh -ResX=1280 -ResY=720 -windowed -graphicsadapter=0
```

### 2. TensorRT 优化

将 PyTorch 模型转换为 TensorRT:
```bash
cd ~/YOPO/YOPO
python3 yopo_trt_transfer.py --trial=1 --epoch=50

# 使用 TensorRT 模型
python3 test_yopo_ros.py --use_tensorrt=1 --trial=1 --epoch=50
```

**性能提升**: 推理速度从 ~5ms 降至 ~1ms (5倍提升)

### 3. 降低分辨率

如果性能不足，降低深度图分辨率 (`settings.json`):
```json
"Width": 320,   // 从 640 降至 320
"Height": 240   // 从 480 降至 240
```

**注意**: 需要重新训练或微调 YOPO 网络以适应新分辨率。

### 4. 多线程优化

确保桥接节点使用多线程 (已默认启用):
```python
# airsim_yopo_bridge.py
self.depth_sub = rospy.Subscriber(..., queue_size=1, tcp_nodelay=True)
```

### 5. 网络带宽优化

减少不必要的话题发布:
```bash
# 关闭 RGB 相机 (只使用深度)
# 在 settings.json 中注释掉 front_center 相机配置
```

---

## 性能基准

### 原系统 (自定义仿真器)

| 组件 | 性能 |
|------|------|
| 动力学仿真 | 100 Hz |
| 深度图生成 | >1000 fps (CUDA) |
| YOPO 推理 | ~5 ms (PyTorch) / ~1 ms (TensorRT) |
| 端到端延迟 | ~33 ms (30 Hz 深度图) |

### 新系统 (AirSim)

| 组件 | 性能 (推荐硬件) | 性能 (最低硬件) |
|------|----------------|----------------|
| 动力学仿真 | 100+ Hz | 50-100 Hz |
| 深度图生成 | 30-60 fps | 15-30 fps |
| YOPO 推理 | 同上 | 同上 |
| 端到端延迟 | ~33-50 ms | ~50-100 ms |
| Unreal 渲染 | 60+ fps | 30 fps |

**推荐硬件**: RTX 2060+, i7-9700K+, 32GB RAM
**最低硬件**: GTX 1060, i5-8400, 16GB RAM

---

## 下一步

### 环境定制
- 在 Unreal Engine 中创建自定义场景 (森林、建筑等)
- 添加动态障碍物 (移动行人、车辆)
- 调整光照条件 (日夜、天气)

### 传感器扩展
- 添加激光雷达 (Lidar)
- 添加多个相机 (立体视觉)
- 添加 GPS 噪声模拟

### 真机部署
- 使用相同的 YOPO 代码
- 替换 AirSim 话题为真实传感器话题
- 参考 `test_yopo_ros.py` 的话题配置

---

## 参考资源

- [AirSim 官方文档](https://microsoft.github.io/AirSim/)
- [AirSim ROS 文档](https://microsoft.github.io/AirSim/airsim_ros_pkgs/)
- [Unreal Engine 文档](https://docs.unrealengine.com/4.27/en-US/)
- [ROS Noetic 文档](http://wiki.ros.org/noetic)
- [YOPO 原始论文](https://arxiv.org/abs/...)

---

## 支持

如有问题，请提交 Issue 或联系维护者。

**迁移完成日期**: 2025-11-19
**文档版本**: 1.0
