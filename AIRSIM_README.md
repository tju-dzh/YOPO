# YOPO + AirSim 集成

将 YOPO 无人机自主导航系统迁移到 AirSim + Unreal Engine 仿真环境。

## 快速开始

### 1. 安装

```bash
cd /home/user/YOPO
./setup_airsim.sh
```

### 2. 启动 Unreal Engine

```bash
# 使用预编译环境
cd ~/Documents/AirSim/Blocks/LinuxNoEditor
./Blocks.sh -ResX=1280 -ResY=720 -windowed
```

### 3. 启动 YOPO + AirSim

**终端 1 - AirSim ROS 节点:**
```bash
cd ~/YOPO/Controller
source devel/setup.bash
roslaunch airsim_ros_pkgs airsim_yopo.launch
```

**终端 2 - YOPO 规划器:**
```bash
cd ~/YOPO/YOPO
source ~/YOPO/Controller/devel/setup.bash
python3 test_yopo_ros.py --trial=1 --epoch=50
```

**终端 3 - 可视化:**
```bash
source ~/YOPO/Controller/devel/setup.bash
rviz -d ~/YOPO/yopo.rviz
```

### 4. 设置目标

在 RViz 中:
1. 点击 "2D Nav Goal"
2. 在地图上点击设置目标点
3. 观察无人机自主导航

## 系统架构

```
Unreal Engine + AirSim
         ↓ (NED坐标系)
   AirSim ROS Wrapper
         ↓
    桥接节点 (坐标系转换)
         ↓ (ENU坐标系)
     YOPO 规划器
```

## 文件结构

```
YOPO/
├── airsim_config/
│   └── settings.json              # AirSim 配置
├── airsim_ros_pkgs/               # ROS 包
│   ├── launch/
│   │   └── airsim_yopo.launch     # 启动文件
│   ├── scripts/
│   │   ├── airsim_yopo_bridge.py  # 传感器数据桥接
│   │   └── yopo_airsim_control_bridge.py  # 控制命令桥接
│   ├── CMakeLists.txt
│   └── package.xml
├── setup_airsim.sh                # 自动安装脚本
├── AIRSIM_MIGRATION_GUIDE.md      # 详细迁移指南
└── AIRSIM_README.md               # 本文件
```

## 话题映射

| AirSim 话题 (NED) | → | YOPO 话题 (ENU) |
|-------------------|---|-----------------|
| `/airsim_node/Drone1/odom_local_ned` | → | `/sim/odom` |
| `/airsim_node/Drone1/imu/Imu` | → | `/sim/imu` |
| `/airsim_node/Drone1/depth_cam/DepthPlanar` | → | `/depth_image` |
| `/so3_control/pos_cmd` | → | `/airsim_node/Drone1/pose_cmd_body_frame` |

## 系统要求

- **OS**: Ubuntu 20.04 LTS
- **ROS**: Noetic
- **GPU**: NVIDIA GTX 1060+ (推荐 RTX 2060+)
- **RAM**: 16GB+ (推荐 32GB)
- **存储**: 50GB+

## 关键特性

✅ **无需修改 YOPO 代码** - 通过桥接节点实现接口适配
✅ **坐标系自动转换** - NED ↔ ENU 透明转换
✅ **真实感仿真** - Unreal Engine 逼真渲染
✅ **性能优化** - 支持 TensorRT 加速推理
✅ **易于扩展** - 支持添加更多传感器和环境

## 常见问题

### Q: AirSim 无法连接？
A: 确保 Unreal Engine 已完全启动 (看到无人机出现)，然后再启动 ROS 节点。

### Q: 深度图无输出？
A: 检查 `settings.json` 中相机配置，确保 `ImageType: 2` (DepthPlanar)。

### Q: 无人机不响应控制？
A: 检查控制话题是否正确发布:
```bash
rostopic echo /so3_control/pos_cmd
rostopic echo /airsim_node/Drone1/pose_cmd_body_frame
```

### Q: 性能卡顿？
A:
1. 降低 Unreal 图形质量 (设置 → 可扩展性 → 低)
2. 使用 TensorRT: `python3 test_yopo_ros.py --use_tensorrt=1`
3. 禁用可视化: 修改 `test_yopo_ros.py` 中 `'visualize': False`

## 性能对比

| 组件 | 原系统 | AirSim 系统 |
|------|--------|-------------|
| 深度图 | >1000 fps (CUDA) | 30-60 fps (Unreal) |
| 动力学 | 100 Hz | 100+ Hz |
| 物理真实感 | 简化 SO3 | 完整动力学 |
| 视觉真实感 | 射线投射 | 逼真渲染 |

## 下一步

- 📖 阅读 [详细迁移指南](AIRSIM_MIGRATION_GUIDE.md)
- 🏗️ 创建自定义 Unreal 环境
- 🚁 部署到真实无人机

## 支持

有问题? 查看 [故障排除](AIRSIM_MIGRATION_GUIDE.md#故障排除) 或提交 Issue。

---

**迁移完成**: 2025-11-19
**版本**: 1.0
