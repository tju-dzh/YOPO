# YOPO项目快速参考指南

## 项目三层架构

```
┌─────────────────────────────────────────────────────────┐
│ 第1层: 规划网络 (Python/PyTorch)                        │
│ - YopoNetwork: 深度神经网络                             │
│   输入: 深度图像 (1×96×160) + 状态 (9维)                │
│   输出: 轨迹端点 + 成本分布 (15个运动原语)               │
│ - 15个运动原语: 5水平 × 3竖直方向                       │
│ - 5阶多项式轨迹插值 (平滑约束)                          │
└──────────────────────┬────────────────────────────────┘
                       │ PositionCommand (50Hz)
┌──────────────────────▼────────────────────────────────┐
│ 第2层: 控制器 (C++ ROS)                                │
│ - NetworkController: 位置→姿态转换                     │
│ - SO3Control: 四元数→推力分配                          │
│ - SO3SimulatorNode: 发布/订阅100Hz Odom/IMU           │
└──────────────────────┬────────────────────────────────┘
                       │ SO3Command
┌──────────────────────▼────────────────────────────────┐
│ 第3层: 仿真环境                                         │
│ - 动力学: 四旋翼ODE积分 (100Hz)                        │
│ - 传感器: CUDA深度图/LiDAR (30Hz, >1000fps)            │
│ - 地图: 随机生成 (森林/迷宫/柱子等)                     │
└─────────────────────────────────────────────────────────┘
```

## 核心代码位置

| 功能 | 文件 | 关键类/函数 |
|-----|------|-----------|
| **深度学习网络** | `/YOPO/policy/yopo_network.py` | YopoNetwork, forward() |
| **CNN主干** | `/YOPO/policy/models/backbone.py` | ResNet18 (改为单通道) |
| **CNN头部** | `/YOPO/policy/models/head.py` | YopoHead (1×1卷积) |
| **运动原语** | `/YOPO/policy/primitive.py` | LatticePrimitive (15个节点) |
| **轨迹优化** | `/YOPO/policy/poly_solver.py` | Poly5Solver (5阶多项式) |
| **损失函数** | `/YOPO/loss/loss_function.py` | YOPOLoss (3项：安全+平滑+制导) |
| **ROS接口** | `/YOPO/test_yopo_ros.py` | YopoNet (订阅/发布) |
| **动力学** | `/Controller/src/.../quadrotor_simulator_so3.cpp` | 四旋翼模型 |
| **传感器** | `/Simulator/src/src/sensor_simulator.cpp` | renderDepthImage() |
| **控制器** | `/Controller/src/so3_control/NetworkControl.h` | NetworkControl类 |

## ROS话题映射

```
深度图:     /depth_image     ← Simulator (30Hz, 160×90)
里程表:     /sim/odom        ← Dynamics  (100Hz, 位置/速度/姿态)
IMU:       /sim/imu         ← Dynamics  (加速度/角速度)
┌─────────────────────────────────────┐
│          YOPO 规划网络              │
└─────────────────────────────────────┘
位置命令:   /so3_control/pos_cmd  → NetworkController (50Hz)
姿态命令:   so3_cmd             → Simulator (10-20Hz)
```

## 仿真环境配置

### 传感器参数 (config.yaml)
```yaml
相机: 160×90像素, fx=fy=80, 最大距离20m
雷达: 16线, 360度水平, -15到+15度垂直
地图: 60m×60m×15m, 分辨率0.1m
```

### 规划参数 (traj_opt.yaml)
```yaml
速度: 6.0 m/s (预训练值)
地平线: 5水平 × 3竖直 = 15条轨迹
距离: 5m规划距离 → 10m地平线
成本权重: 制导0.12, 平滑10.0, 碰撞0.1
```

## 数据流处理

### 推理周期 (30Hz深度图)
```
1. callback_depth()
   ├─ 解码: np.frombuffer (160×90)
   ├─ 缩放: 尺寸调整 → (160×90)
   ├─ 归一化: [0, 20m] → [0, 1]
   ├─ 填补: NaN插值 (Telea算法)
   └─ 重塑: (1,1,96,160) → PyTorch张量

2. process_odom()
   ├─ 提取: 位置, 速度, 加速度
   ├─ 变换: 世界→相机坐标系
   └─ 归一化: 状态向量 (9维)

3. YopoNetwork.forward()
   ├─ backbone: ResNet-18 (深度→64通道特征)
   ├─ head: 1×1卷积 (特征→10输出)
   ├─ endstate: tanh(output[0:9]) ∈ [-1,1]
   └─ score: softplus(output[9]) ≥ 0 (成本)

4. process_output()
   ├─ 选择: argmin(score) → 最优轨迹
   ├─ 变换: 原语→体→世界坐标系
   └─ 插值: 5阶多项式 (平滑约束)

5. control_pub()
   ├─ 采样: Poly5(t) → p,v,a (50Hz)
   ├─ 计算: 偏航角 (目标方向)
   └─ 发布: PositionCommand
```

## 启动命令 (完整流程)

```bash
# 终端1: 动力学 + 控制器
cd /home/user/YOPO/Controller
source devel/setup.bash
roslaunch so3_quadrotor_simulator simulator_attitude_control.launch

# 终端2: 传感器仿真
cd /home/user/YOPO/Simulator
source devel/setup.bash
rosrun sensor_simulator sensor_simulator_cuda    # GPU优先

# 终端3: 规划网络
cd /home/user/YOPO/YOPO
conda activate yopo
python test_yopo_ros.py --trial=1 --epoch=50

# 终端4: 可视化
cd /home/user/YOPO/YOPO
rviz -d yopo.rviz
```

## 训练流程

```bash
# 1. 数据收集 (1-2分钟, 100k样本)
cd /home/user/YOPO/Simulator && source devel/setup.bash
rosrun sensor_simulator dataset_generator

# 2. 模型训练 (<1小时, 50 epoch)
cd /home/user/YOPO/YOPO && conda activate yopo
python train_yopo.py

# 3. 模型部署 (可选: TensorRT加速)
python yopo_trt_transfer.py --trial=1 --epoch=50
python test_yopo_ros.py --use_tensorrt=1
```

## 关键参数调整

### 速度/性能权衡
- **velocity** (traj_opt.yaml): 影响规划地平线和成本权重
- **smoothness_weight (ws)**: 增大→轨迹更平滑
- **safety_weight (wc)**: 增大→离障碍更远
- **goal_weight (wg)**: 增大→偏向目标

### 传感器模拟
- **maze_type**: 1(洞穴), 2(柱子), 3(迷宫), 5(森林), 6(房间)
- **resolution**: 0.1m推荐 (小→高分辨率, 慢)
- **camera.pitch**: 相机倾角 (通常0)

### 运算优化
- **绑定P-cores**: `taskset -c 1,2,3,4 python train_yopo.py`
- **GPU版本**: sensor_simulator_cuda (>1000fps)
- **TensorRT**: 推理加速5x (1-5ms)

## 文件索引 (按功能分类)

**神经网络** (Python/PyTorch):
- yopo_network.py - 网络架构
- backbone.py - ResNet-18改进
- head.py - 预测头
- primitive.py - 运动原语定义
- poly_solver.py - 多项式求解
- state_transform.py - 坐标变换
- yopo_trainer.py - 训练循环

**损失函数** (Python):
- loss_function.py - 主损失类
- safety_loss.py - 碰撞成本
- smoothness_loss.py - 光滑成本
- guidance_loss.py - 目标成本

**ROS接口** (Python/C++):
- test_yopo_ros.py - 实时推理
- network_control_node.cpp - 位置→姿态
- so3_control_nodelet.cpp - 姿态控制器
- quadrotor_simulator_so3.cpp - 动力学仿真

**配置文件** (YAML):
- traj_opt.yaml - 规划参数
- config.yaml - 传感器参数

## 性能基准

| 操作 | 时间 | 硬件 |
|-----|------|------|
| 深度渲染 | >1000fps | RTX 3060 (CUDA) |
| 深度渲染 | 50fps | i7-9700 (CPU) |
| 网络推理 | 5-10ms | PyTorch+GPU |
| 网络推理 | 1-5ms | TensorRT |
| 数据收集 | 1-2min | 100k样本 |
| 模型训练 | <1hr | RTX 3080 |
| 控制周期 | 50Hz | 实时 |

## 常见问题

**Q: 深度图太快怎么办?**
- A: 降低config.yaml中的depth_fps参数

**Q: 网络推理超时?**
- A: 使用TensorRT加速, 或降低depth_fps

**Q: 训练不收敛?**
- A: 检查权重比例, 调整learning_rate, 或增加数据

**Q: 绑定P-core有什么好处?**
- A: 避免E-core降频, 训练快2-3倍

**Q: 真实无人机怎么部署?**
- A: 修改odom_topic为真实传感器, 转为NWU帧

