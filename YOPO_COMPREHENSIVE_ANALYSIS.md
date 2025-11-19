# YOPO项目详细结构分析

## 项目概述
YOPO (You Only Plan Once) 是一个**学习型无人机自主导航规划系统**，包含：
- 动态学仿真器 (SO3四旋翼)
- 传感器仿真器 (CUDA加速深度图/LiDAR)
- 深度学习规划网络 (PyTorch)
- 高层控制接口

---

## 1. 整体项目结构

```
/home/user/YOPO/
├── Controller/          # ROS控制器和动力学仿真 (C++/CMake)
├── Simulator/           # 传感器仿真器 (C++/CUDA)
├── YOPO/               # 学习型规划网络 (Python/PyTorch)
├── docs/               # 文档
├── hardware/           # 硬件设计文件
└── README.md
```

---

## 2. 仿真环境架构

### 2.1 使用的仿真环境
YOPO使用**双层仿真架构**：

| 层级 | 仿真器 | 类型 | 功能 |
|-----|--------|------|------|
| **动力学层** | SO3四旋翼仿真器 | C++ ROS | 物理动力学计算、马达模型、扰动 |
| **传感器层** | 传感器仿真器 | CUDA加速 | 深度图、LiDAR点云、环境映射 |

**NOT Gazebo**: 项目自实现了轻量级、高性能的仿真器，避免Gazebo的复杂性

### 2.2 动力学仿真器 (SO3)

**文件路径**: `/home/user/YOPO/Controller/src/so3_quadrotor_simulator/`

**核心文件**:
- `src/quadrotor_simulator_so3.cpp` - 主仿真节点
- `src/dynamics/Quadrotor.cpp` - 四旋翼动力学
- `include/ode/` - ODE数值积分库（Boost)

**启动方式**:
```bash
cd Controller
source devel/setup.bash
roslaunch so3_quadrotor_simulator simulator_attitude_control.launch  # 用于YOPO规划器
# 或
roslaunch so3_quadrotor_simulator simulator_position_control.launch  # 用于传统规划器
```

**发布的ROS话题**:
- `/sim/odom` (nav_msgs/Odometry) - 100Hz - 位置、速度、方向
- `/sim/imu` (sensor_msgs/Imu) - IMU数据

**发布的控制命令接收**:
- `so3_cmd` (quadrotor_msgs/SO3Command) - 期望方向四元数、推力、增益

### 2.3 传感器仿真器 (CUDA加速)

**文件路径**: `/home/user/YOPO/Simulator/src/`

**核心包**:
- `sensor_simulator` - 主要传感器仿真（支持CPU/GPU)
- `dataset_generator` - 数据收集工具

**核心文件**:
- `src/sensor_simulator.cpp` - 深度图/LiDAR渲染主逻辑
- `include/sensor_simulator.h` - 核心类定义
- `include/sensor_simulator.cuh` - CUDA核心函数
- `include/maps.hpp` - 环境地图生成

**启动方式**:
```bash
cd Simulator
source devel/setup.bash
rosrun sensor_simulator sensor_simulator_cuda    # GPU版本（推荐，>1000fps）
# 或
rosrun sensor_simulator sensor_simulator         # CPU版本
```

**发布的ROS话题**:
- `/depth_image` (sensor_msgs/Image, 32FC1) - 深度图像，宽度160 x 高度90像素
- `/lidar_points` (sensor_msgs/PointCloud2) - 16线LiDAR点云

**订阅的ROS话题**:
- `/sim/odom` - 用于渲染相机视图

---

## 3. 仿真相关配置文件

### 3.1 传感器仿真配置

**文件**: `/home/user/YOPO/Simulator/src/config/config.yaml`

**关键参数**:
```yaml
# ROS话题名称
odom_topic: "/sim/odom"
depth_topic: "/depth_image"
lidar_topic: "/lidar_points"

# 深度相机参数
camera:
  fx: 80.0              # 焦距X
  fy: 80.0              # 焦距Y
  cx: 80.0, cy: 45.0    # 主点
  image_width: 160, image_height: 90
  max_depth_dist: 20.0
  pitch: 0.0            # 相机俯仰角

# LiDAR参数
lidar:
  vertical_lines: 16    # 16条扫描线
  vertical_angle_start: -15.0, end: 15.0
  horizontal_num: 360   # 360度水平分辨率
  max_lidar_dist: 20.0

# 环境生成
random_map: true
maze_type: 5            # 1:洞穴 2:柱子 3:迷宫 5:森林 6:房间 7:墙面
x_length: 60, y_length: 60, z_length: 15
resolution: 0.1         # 地图分辨率
```

### 3.2 动力学仿真启动配置

**文件**: 
- `/home/user/YOPO/Controller/src/so3_quadrotor_simulator/launch/simulator_attitude_control.launch`
- `/home/user/YOPO/Controller/src/so3_quadrotor_simulator/launch/simulator_position_control.launch`

**attitude_control.launch** (用于YOPO):
```xml
<node pkg="so3_quadrotor_simulator" type="quadrotor_simulator_so3" ...>
  <param name="rate/odom" value="100.0"/>
  <remap from="~odom" to="/sim/odom"/>
  <remap from="~imu" to="/sim/imu"/>
  <remap from="~cmd" to="so3_cmd"/>
</node>

<node pkg="so3_control" type="network_control_node" ...>
  <!-- 没有位置控制器，直接控制姿态 -->
  <param name="is_simulation" value="true"/>
  <param name="use_disturbance_observer" value="true"/>
  <remap from="~position_cmd" to="/so3_control/pos_cmd"/>
</node>
```

### 3.3 规划器轨迹优化配置

**文件**: `/home/user/YOPO/YOPO/config/traj_opt.yaml`

**关键参数**:
```yaml
# 仿真速度（重要）
velocity: 6.0

# 轨迹成本权重
wg: 0.12   # 制导成本
ws: 10.0   # 平滑成本
wc: 0.1    # 碰撞成本

# 运动原语网格
horizon_num: 5            # 水平5个方向
vertical_num: 3           # 竖直3个高度
horizon_camera_fov: 90.0  # 相机视场角
horizon_anchor_fov: 30.0  # 原语视场角
radio_range: 5.0          # 规划地平线: 2*radio_range = 10m

# 数据集配置
image_height: 96, image_width: 160
```

---

## 4. 与仿真交互的代码模块

### 4.1 主要交互流程

```
┌─────────────────────────────────────────────────────────────┐
│ 仿真环境交互流程                                              │
└─────────────────────────────────────────────────────────────┘

SO3仿真器 (100Hz)          传感器仿真器              YOPO规划网络
      │                      │                         │
      ├──> /sim/odom ───────>├─────────────────────>│
      │                      │                         │
      │                      ├──> /depth_image ───>│
      │                      │                         │
      │                      ├──> /lidar_points ──>│
      │                      │                         │
      │<──── so3_cmd ────────┤<─ /pos_cmd ─────────┤
      │     (10-20Hz)        │    (50Hz)             │
```

### 4.2 YOPO规划网络与ROS交互

**文件**: `/home/user/YOPO/YOPO/test_yopo_ros.py`

**主类**: `YopoNet`

**订阅的ROS话题**:
```python
self.odom_sub = rospy.Subscriber(
    self.config['odom_topic'],        # "/sim/odom"
    Odometry, 
    self.callback_odometry, 
    queue_size=1, tcp_nodelay=True
)

self.depth_sub = rospy.Subscriber(
    self.config['depth_topic'],       # "/depth_image"
    Image, 
    self.callback_depth, 
    queue_size=1, tcp_nodelay=True
)

self.goal_sub = rospy.Subscriber(
    "/move_base_simple/goal",         # 在RVIZ中点击2D导航目标
    PoseStamped, 
    self.callback_set_goal, 
    queue_size=1
)
```

**发布的ROS话题**:
```python
self.ctrl_pub = rospy.Publisher(
    self.config["ctrl_topic"],        # "/so3_control/pos_cmd"
    PositionCommand, 
    queue_size=1
)

# 可视化话题
self.best_traj_pub = rospy.Publisher(
    "/yopo_net/best_traj_visual", 
    PointCloud2, 
    queue_size=1
)
self.lattice_traj_pub = rospy.Publisher(
    "/yopo_net/lattice_trajs_visual", 
    PointCloud2, 
    queue_size=1
)
```

**处理流程**:
1. `callback_depth()` - 接收深度图像，处理NaN值，进行网络推理
2. `process_odom()` - 提取当前状态（速度、加速度、目标方向）
3. 神经网络前向传播 - 预测轨迹端点和成本
4. `control_pub()` - 用5阶多项式插值生成轨迹，发布位置命令

---

## 5. ROS节点和话题结构

### 5.1 完整的ROS节点拓扑

```
ROS节点:
├── /quadrotor_simulator_so3           (Publisher)
│   ├── /sim/odom
│   └── /sim/imu
│
├── /sensor_simulator_cuda/node        (Subscriber & Publisher)
│   ├── Subscribes: /sim/odom
│   ├── Publishes: /depth_image
│   └── Publishes: /lidar_points
│
├── /network_controller_node           (Subscriber & Publisher)
│   ├── Subscribes: /sim/odom, /sim/imu
│   ├── Subscribes: /so3_control/pos_cmd
│   └── Publishes: so3_cmd
│
├── /yopo_net                          (Main Planning Node)
│   ├── Subscribes: /sim/odom
│   ├── Subscribes: /depth_image
│   ├── Subscribes: /move_base_simple/goal
│   ├── Publishes: /so3_control/pos_cmd
│   ├── Publishes: /yopo_net/best_traj_visual
│   ├── Publishes: /yopo_net/lattice_trajs_visual
│   └── Publishes: /yopo_net/trajs_visual
```

### 5.2 关键ROS消息类型

**PositionCommand** (quadrotor_msgs):
```
Header header
geometry_msgs/Point position         # 期望位置 [x, y, z]
geometry_msgs/Vector3 velocity       # 期望速度 [vx, vy, vz]
geometry_msgs/Vector3 acceleration   # 期望加速度 [ax, ay, az]
float64 yaw, yaw_dot                 # 期望偏航角及其导数
float64[3] kx, kv                    # 位置和速度增益
uint8 trajectory_flag                # 轨迹状态标志
```

**SO3Command** (quadrotor_msgs):
```
Header header
geometry_msgs/Vector3 force          # 期望推力 [fx, fy, fz]
geometry_msgs/Quaternion orientation # 期望方向四元数
float64[3] kR, kOm                   # 旋转和角速度增益
```

---

## 6. 传感器数据处理

### 6.1 深度图像处理

**文件**: `/home/user/YOPO/Simulator/src/src/sensor_simulator.cpp`

**核心方法**: `renderDepthImage()`

**处理流程**:
```cpp
// 1. 射线投射：为每个像素投射光线
for (v = 0 to image_height) {
    for (u = 0 to image_width) {
        // 计算射线方向
        float y = -(u - cx) / fx;
        float z = -(v - cy) / fy;
        Eigen::Vector3f d(1.0f, y, z);
        d.normalize();
        
        // 变换到世界坐标系
        Eigen::Vector3f ray_direction = R_wc * d;
        Eigen::Vector3f ray_origin = pos;
        
        // 2. Octree查询：找最近交点
        octree->getIntersectedVoxelIndices(
            ray_origin, ray_direction, pointIdxVec, 1
        );
        
        // 3. 距离计算
        float distance = closest_point_camera.x();
        depth_image.at<float>(v, u) = distance;
    }
}

// 4. 后处理
- 归一化深度到 [0, max_depth_dist]
- 无效值设置为 max_depth_dist
```

**性能指标**:
- GPU版本 (RTX 3060): **> 1000fps**
- CPU版本 (i7-9700): **50fps**

### 6.2 LiDAR点云处理

**核心方法**: `renderLidarPointcloud()`

**处理流程**:
```cpp
for (v = 0 to vertical_lines) {          // 16条扫描线
    for (h = 0 to horizontal_num) {      // 360个水平点
        // 1. 计算射线方向（球坐标）
        float vertical_angle = ...;
        float horizontal_angle = h * horizontal_resolution;
        Eigen::Vector3f ray_direction = [
            cos(vert)*cos(horiz),
            cos(vert)*sin(horiz),
            sin(vert)
        ];
        
        // 2. 世界坐标系变换
        ray_direction = R_wc * ray_direction;
        
        // 3. Octree查询
        octree->getIntersectedVoxelIndices(...);
        
        // 4. 点云帧体坐标表示
        point_in_body = R_cw * (point_in_world - pos);
    }
}
```

### 6.3 YOPO网络中的深度处理

**文件**: `/home/user/YOPO/YOPO/test_yopo_ros.py` (行150-165)

```python
def callback_depth(self, data):
    # 1. 图像解码
    depth = np.frombuffer(data.data, dtype=np.float32).reshape(
        data.height, data.width
    )
    
    # 2. 图像大小调整
    if depth.shape != (self.height, self.width):
        depth = cv2.resize(depth, (self.width, self.height), 
                          interpolation=cv2.INTER_NEAREST)
    
    # 3. 尺度转换和归一化
    depth = np.minimum(depth * self.scale, self.max_dis) / self.max_dis
    
    # 4. NaN值插值（Telea算法）
    nan_mask = np.isnan(depth) | (depth < self.min_dis / self.max_dis)
    depth = cv2.inpaint(np.uint8(depth * 255), 
                       np.uint8(nan_mask), 
                       1, cv2.INPAINT_NS)
    
    # 5. 归一化和reshape
    depth = depth.astype(np.float32) / 255.0
    depth = depth.reshape([1, 1, self.height, self.width])
```

---

## 7. 无人机控制接口

### 7.1 控制架构

```
┌────────────────────────────────┐
│   YOPO规划网络                  │
│   (位置和加速度命令)             │
└────────────┬────────────────────┘
             │ PositionCommand
             ▼
┌────────────────────────────────┐
│   NetworkController             │
│   (位置→态度转换)                │
│   (带干扰观测器)                 │
└────────────┬────────────────────┘
             │ SO3Command
             ▼
┌────────────────────────────────┐
│   SO3姿态控制器                  │
│   (四元数→推力分配)              │
└────────────┬────────────────────┘
             │ 马达转速
             ▼
┌────────────────────────────────┐
│   四旋翼动力学仿真器              │
│   (物理状态计算)                 │
└────────────────────────────────┘
```

### 7.2 NetworkController

**文件**: `/home/user/YOPO/Controller/src/so3_control/include/so3_control/NetworkControl.h`

**核心功能**:
```cpp
class NetworkControl {
    // 订阅
    position_cmd_sub_  // PositionCommand
    odom_sub_          // Odometry
    imu_sub_           // IMU
    
    // 发布
    so3_command_pub_   // SO3Command
    
    // 参数
    double kx_xy = 5.7, kx_z = 6.2;  // 位置增益
    double kv_xy = 3.4, kv_z = 4.0;  // 速度增益
    
    // 功能
    void network_cmd_callback(PositionCommand msg) {
        // 将期望位置、速度、加速度转换为期望姿态
        // 使用PD控制
        // 计算期望推力
    }
};
```

### 7.3 轨迹生成和控制发布

**文件**: `/home/user/YOPO/YOPO/test_yopo_ros.py` (行207-240)

```python
def control_pub(self, _timer):
    """
    50Hz定时器，发布位置命令
    """
    if self.ctrl_time is None:
        return
    
    # 用5阶多项式插值轨迹
    control_msg = PositionCommand()
    control_msg.position.x = self.optimal_poly_x.get_position(self.ctrl_time)
    control_msg.position.y = self.optimal_poly_y.get_position(self.ctrl_time)
    control_msg.position.z = self.optimal_poly_z.get_position(self.ctrl_time)
    control_msg.velocity.x = self.optimal_poly_x.get_velocity(self.ctrl_time)
    control_msg.velocity.y = self.optimal_poly_y.get_velocity(self.ctrl_time)
    control_msg.velocity.z = self.optimal_poly_z.get_velocity(self.ctrl_time)
    control_msg.acceleration.x = self.optimal_poly_x.get_acceleration(...)
    # ... (y, z 加速度)
    
    # 计算期望偏航角
    yaw, yaw_dot = calculate_yaw(
        self.desire_vel, 
        goal_direction, 
        self.last_yaw, 
        self.ctrl_dt
    )
    control_msg.yaw = yaw
    control_msg.yaw_dot = yaw_dot
    
    self.ctrl_pub.publish(control_msg)
```

### 7.4 SO3姿态控制器

**文件**: `/home/user/YOPO/Controller/src/so3_quadrotor_simulator/src/quadrotor_simulator_so3.cpp`

**控制律** (第100-150行):
```cpp
// 期望旋转矩阵 Rd（从四元数转换）
float Rd11 = cmd.qw*cmd.qw + cmd.qx*cmd.qx - cmd.qy*cmd.qy - cmd.qz*cmd.qz;
// ... (完整的3x3矩阵)

// 旋转误差
float eR1 = 0.5f * (R12*Rd13 - R13*Rd12 + ...);  // 误差向量

// 角速度误差
float eOm1 = Om1;
float eOm2 = Om2;
float eOm3 = Om3;

// 力矩控制律
float M1 = -cmd.kR[0]*eR1 - cmd.kOm[0]*eOm1 + in1;
float M2 = -cmd.kR[1]*eR2 - cmd.kOm[1]*eOm2 + in2;
float M3 = -cmd.kR[2]*eR3 - cmd.kOm[2]*eOm3 + in3;
```

### 7.5 运动原语和轨迹优化

**文件**: `/home/user/YOPO/YOPO/policy/primitive.py`

**轨迹参数**:
```python
horizon_num = 5           # 5个水平方向
vertical_num = 3          # 3个垂直高度
radio_num = 1             # 距离（目前只支持1）
total_primitives = 5×3×1 = 15

# 极坐标索引
lattice_pos_list = [
    cos(β)*cos(α)*r,      # x
    cos(β)*sin(α)*r,      # y
    sin(β)*r               # z
]
```

**5阶多项式轨迹**:
```python
# Poly5Solver(p0, v0, a0, pf, vf, af, T)
# p(t) = c0 + c1*t + c2*t² + c3*t³ + c4*t⁴ + c5*t⁵
# 约束：
#   p(0) = p0, p(T) = pf
#   v(0) = v0, v(T) = vf
#   a(0) = a0, a(T) = af
```

---

## 8. 神经网络架构

### 8.1 YOPO网络结构

**文件**: `/home/user/YOPO/YOPO/policy/yopo_network.py`

```python
class YopoNetwork(nn.Module):
    def __init__(self):
        # 输入维度：深度图像 (1, 96, 160)
        #          观察状态 (9)：[vx,vy,vz, ax,ay,az, gx,gy,gz]
        
        # 主干网络
        self.image_backbone = YopoBackbone(64)  # ResNet-18
        self.state_backbone = nn.Sequential()   # 直通
        
        # 头部网络
        self.yopo_head = YopoHead(64+9, 10)
        
    def forward(self, depth, obs):
        # depth: [B, 1, 96, 160]
        # obs: [B, 9]
        
        depth_feature = self.image_backbone(depth)  # [B, 64, 3, 5]
        obs_feature = self.state_backbone(obs)      # [B, 9]
        
        input_tensor = torch.cat((obs_feature, depth_feature), 1)
        output = self.yopo_head(input_tensor)       # [B, 10, 3, 5]
        
        endstate = torch.tanh(output[:, :9])        # 归一化 [-1, 1]
        score = torch.nn.functional.softplus(...)   # 非负成本
        
        return endstate, score
```

### 8.2 BackBone网络

**文件**: `/home/user/YOPO/YOPO/policy/models/backbone.py`

```python
class ResNet18(nn.Module):
    def __init__(self, output_dim=64):
        self.cnn = resnet18(pretrained=False)
        # 修改首层：单通道输入
        self.cnn.conv1 = Conv2d(1, 64, kernel_size=7, stride=2, padding=3)
        # 输出层：特征图
        self.cnn.output_layer = Conv2d(512, output_dim, kernel_size=1)
    
    def forward(self, depth):  # [1, 96, 160]
        return self.cnn(depth)  # [64, 3, 5]
```

### 8.3 Head网络

**文件**: `/home/user/YOPO/YOPO/policy/models/head.py`

```python
class YopoHead(nn.Module):
    def __init__(self, input_dim, output_dim):
        # input_dim = 64 + 9 = 73
        # output_dim = 10 (9个状态 + 1个成本)
        
        self.model = nn.Sequential(
            Conv2d(73, 256, kernel_size=1),
            ReLU(),
            Conv2d(256, 256, kernel_size=1),
            ReLU(),
            Conv2d(256, 10, kernel_size=1)
        )
```

---

## 9. 损失函数和训练策略

### 9.1 损失函数组成

**文件**: `/home/user/YOPO/YOPO/loss/loss_function.py`

```python
class YOPOLoss(nn.Module):
    def __init__(self):
        self.smoothness_loss = SmoothnessLoss()  # 轨迹平滑性
        self.safety_loss = SafetyLoss()          # 碰撞避免
        self.goal_loss = GuidanceLoss()          # 目标制导
        
        # 权重（可在traj_opt.yaml配置）
        self.smoothness_weight = 10.0   # ws
        self.safety_weight = 0.1        # wc
        self.goal_weight = 0.12         # wg
```

**损失项**:
1. **平滑性** (SmoothnessLoss): 时间积分的jerk²
2. **安全性** (SafetyLoss): 轨迹与障碍的最小距离
3. **制导** (GuidanceLoss): 轨迹在目标方向上的投影

### 9.2 状态变换

**文件**: `/home/user/YOPO/YOPO/policy/state_transform.py`

```python
class StateTransform:
    def pred_to_endstate(self, endstate_pred):
        """
        原语坐标系 → 体坐标系
        
        输入: endstate_pred [B, 9, 3, 5]
             (px, py, pz, vx, vy, vz, ax, ay, az)
        
        变换步骤:
        1. 提取运动原语的角度 (yaw, pitch)
        2. 应用偏移 (delta_yaw, delta_pitch, delta_radio)
        3. 极坐标→笛卡尔坐标
        4. 速度/加速度旋转到体坐标系
        
        输出: endstate [B, 9, 3, 5] 体坐标系
        """
```

---

## 10. 数据集收集

### 10.1 数据生成

**文件**: `/home/user/YOPO/Simulator/src/src/dataset_generator.cpp`

**运行方式**:
```bash
cd Simulator
rosrun sensor_simulator dataset_generator
```

**生成的数据结构**:
```
dataset/
├── env_0/
│   ├── images/       # 深度图像 (PNG 16bit)
│   ├── pointclouds/  # 点云 (PLY)
│   ├── states/       # 状态数据 (NPZ)
│   └── maps/         # 环境地图
├── env_1/
...
```

**配置参数** (config.yaml):
```yaml
env_num: 10            # 生成10个不同的环境
image_num: 10000       # 每个环境采样10000张图像
sampling_range:
  roll: 30°, pitch: 30°  # 姿态范围
  x: 40m, y: 40m        # 位置范围
  z: [0.5, 4]m          # 高度范围
safe_dist: 0.5m        # 采样点与障碍的最小距离
```

---

## 11. 训练流程

### 11.1 训练入口

**文件**: `/home/user/YOPO/YOPO/train_yopo.py`

```python
if __name__ == "__main__":
    trainer = YopoTrainer(
        learning_rate=1.5e-4,
        batch_size=16,
        loss_weight=[1.0, 1.0],  # [safety, smoothness]
        tensorboard_path="./saved",
        checkpoint_path=None
    )
    
    trainer.train(epoch=50)
```

**训练统计**:
- 数据集: 100,000样本 (16:9分辨率，90° FOV)
- 时间: <1小时 (RTX 3080, i9-12900K)
- GPU内存: ~4GB
- 推荐: 绑定P-cores运行以提高性能

### 11.2 测试/推理

**文件**: `/home/user/YOPO/YOPO/test_yopo_ros.py`

```python
# 实时推理流程
# 1. 接收深度图像 (30Hz)
# 2. 神经网络前向传播 (1-5ms)
# 3. 轨迹优化 (多项式插值)
# 4. 发布控制命令 (50Hz)

# 启动命令
python test_yopo_ros.py --trial=1 --epoch=50
```

### 11.3 TensorRT部署优化

**文件**: `/home/user/YOPO/YOPO/yopo_trt_transfer.py`

```bash
# 转换PyTorch → TensorRT
python yopo_trt_transfer.py --trial=1 --epoch=50

# TensorRT推理 (1-5ms)
python test_yopo_ros.py --use_tensorrt=1
```

---

## 12. 关键文件总结

| 功能 | 文件路径 | 语言 |
|-----|---------|------|
| 动力学仿真 | `/Controller/src/so3_quadrotor_simulator/` | C++ |
| 传感器仿真 | `/Simulator/src/sensor_simulator/` | C++/CUDA |
| 规划网络 | `/YOPO/policy/yopo_network.py` | Python |
| 网络训练 | `/YOPO/policy/yopo_trainer.py` | Python |
| 实时测试 | `/YOPO/test_yopo_ros.py` | Python |
| 轨迹优化 | `/YOPO/policy/poly_solver.py` | Python |
| 损失函数 | `/YOPO/loss/loss_function.py` | Python |
| ROS控制 | `/Controller/src/so3_control/` | C++ |
| 配置文件 | `/YOPO/config/traj_opt.yaml` | YAML |
| 传感器配置 | `/Simulator/src/config/config.yaml` | YAML |

---

## 13. 常见操作

### 13.1 启动完整仿真

```bash
# 终端1: 动力学仿真 + SO3控制器
cd Controller && source devel/setup.bash
roslaunch so3_quadrotor_simulator simulator_attitude_control.launch

# 终端2: 传感器仿真 (GPU)
cd Simulator && source devel/setup.bash
rosrun sensor_simulator sensor_simulator_cuda

# 终端3: YOPO规划器
cd YOPO && conda activate yopo
python test_yopo_ros.py --trial=1 --epoch=50

# 终端4: 可视化
cd YOPO && rviz -d yopo.rviz
```

### 13.2 数据集收集

```bash
cd Simulator && source devel/setup.bash
rosrun sensor_simulator dataset_generator
```

### 13.3 训练模型

```bash
cd YOPO && conda activate yopo
python train_yopo.py
```

---

## 14. 系统性能指标

| 指标 | 值 |
|-----|---|
| 深度图渲染 (GPU) | >1000fps |
| 深度图渲染 (CPU) | 50fps |
| 网络推理 (PyTorch) | 5-10ms |
| 网络推理 (TensorRT) | 1-5ms |
| 控制命令发布频率 | 50Hz |
| 仿真里程碑速度 | 0-6m/s |
| 规划地平线 | 10m |
| RVIZ可视化延迟 | <100ms |

---

## 15. 特色技术

1. **CUDA加速传感器仿真**: 相比Gazebo显著更快
2. **自定义动力学仿真**: 轻量级、高精度
3. **学习型规划**: 端到端学习而非强化学习
4. **引导学习**: 直接反传轨迹成本梯度
5. **运动原语**: 15个预定义轨迹基元
6. **实时性优化**: 支持TensorRT部署
7. **零样本迁移**: 仿真训练→真实机器人

