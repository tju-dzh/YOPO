# Clean Lab Scene Guide - 基础验证场景

## 场景概述

**Clean Lab** 是一个极简、高性能的 AirSim 测试环境，专为：
- ✅ AirSim 基础功能验证
- ✅ 传感器校准和测试
- ✅ 控制算法调试
- ✅ 性能基准测试
- ✅ 视觉算法验证（高对比度）

**性能目标**: >60 FPS (甚至可达 120+ FPS)

---

## 场景特点

### 1. 极简设计
- 无复杂几何体
- 无植被和粒子系统
- 最少的材质和纹理
- 静态光照（预烘焙）

### 2. 高对比度
- 黑白棋盘格地面（视觉基准）
- 清晰的阴影和轮廓
- 无环境光干扰
- 强烈的方向光

### 3. 高帧率
- 目标：60-120 FPS
- 极低渲染负载
- 最小化 Draw Call
- 优化的碰撞检测

---

## 快速创建步骤

### 步骤 1: 创建新地图

1. **打开 ForestDrone 项目**:
   ```bash
   cd ~/UnrealEngine
   ./Engine/Binaries/Linux/UE4Editor ~/YOPO/UnrealProjects/ForestDrone/ForestDrone.uproject
   ```

2. **File** → **New Level** → **Empty Level**

3. **保存地图**:
   - 路径: `/Game/Maps/CleanLab`
   - 名称: `CleanLab`

### 步骤 2: 创建棋盘格地面

#### 方法 A: 使用 Plane (简单)

1. **Place Actors** → 搜索 **"Plane"**
2. 拖拽到场景中
3. 设置 Transform:
   ```yaml
   Location: (0, 0, 0)
   Rotation: (0, 0, 0)
   Scale: (100, 100, 1)  # 10000cm x 10000cm
   ```

#### 方法 B: 使用 Landscape (推荐)

1. **Landscape Mode** (Shift+2)
2. **Manage** 标签:
   ```yaml
   Section Size: 63x63
   Sections Per Component: 1x1
   Number of Components: 8x8  # 小型场景
   Overall Resolution: 505x505
   ```
3. **Create**
4. 保持完全平坦（不雕刻）

### 步骤 3: 创建棋盘格材质

#### 3.1 创建材质

1. **Content Browser** → 右键
2. **Material** → 命名为 `M_Checkerboard`
3. 双击打开材质编辑器

#### 3.2 材质节点设置

**节点图**:
```
World Position (Absolute)
    ↓
Divide (÷ 500)  ← 棋盘格大小 (500cm = 5m)
    ↓
Floor (取整)
    ↓
Add (X + Y)
    ↓
Fmod (% 2)  ← 模 2 运算
    ↓
If (Value < 1)
    ├─ True:  Constant3Vector (1,1,1) 白色
    └─ False: Constant3Vector (0,0,0) 黑色
    ↓
Base Color
```

**详细步骤**:

1. **获取世界坐标**:
   - 添加节点: `Absolute World Position`

2. **缩放坐标** (控制棋盘格大小):
   ```
   Absolute World Position
   ├─ Component Mask (R, G) → 只取 X 和 Y
   └─ Divide → Constant (500, 500) → 除以 500
   ```

3. **取整**:
   ```
   Divide → Floor (每个分量)
   ```

4. **计算棋盘格模式**:
   ```
   Floor X
      ↓
   Add (Floor X + Floor Y)
      ↓
   Fmod → Constant (2)  # 取模 2
      ↓
   Less Than → Constant (1)  # 判断 < 1
      ↓
   If
   ├─ A (True):  Constant3 (1, 1, 1) 白色
   ├─ B (False): Constant3 (0, 0, 0) 黑色
   └─ Alpha: Less Than 结果
   ```

5. **连接输出**:
   ```
   If → Base Color
   ```

6. **材质设置**:
   ```yaml
   Shading Model: Default Lit
   Blend Mode: Opaque
   Two Sided: False
   ```

7. **保存并关闭**

#### 3.3 应用材质

1. 选择地面 Plane/Landscape
2. **Details** → **Materials**
3. Element 0 → `M_Checkerboard`

### 步骤 4: 添加光照

#### 4.1 Directional Light (太阳)

1. **Place Actors** → **Lights** → **Directional Light**
2. 拖拽到场景
3. 设置 Transform:
   ```yaml
   Location: (0, 0, 1000)
   Rotation: (-60, 0, 0)  # 向下 60 度照射
   ```

4. **Light** 设置:
   ```yaml
   Intensity: 10.0 lux
   Light Color: (255, 255, 255) 纯白
   Temperature: 6500 K
   Use Temperature: ✓
   Cast Shadows: ✓
   ```

5. **Cascaded Shadow Maps** (高质量阴影):
   ```yaml
   Dynamic Shadow Distance: 20000 cm
   Num Dynamic Shadows: 4
   Shadow Amount: 1.0
   ```

6. **Mobility**: **Stationary** (预烘焙 + 动态阴影)

#### 4.2 Sky Light (环境光)

1. **Place Actors** → **Lights** → **Sky Light**
2. 设置:
   ```yaml
   Intensity: 0.5  # 低强度，保持高对比度
   Light Color: (200, 220, 255) 微蓝（天空色）
   Source Type: SLS Captured Scene
   Mobility: Stationary
   ```

#### 4.3 Sky Sphere (天空)

1. **Place Actors** → 搜索 **"BP_Sky_Sphere"**
2. 拖拽到场景
3. **Details** → **Default**:
   ```yaml
   Sun Brightness: 50.0
   Cloud Speed: 0.0  # 无云移动
   Cloud Opacity: 0.0  # 完全晴朗
   Horizon Falloff: 3.0
   Zenith Color: (0.034, 0.109, 0.295) 深蓝
   Horizon Color: (0.78, 0.84, 1.0) 浅蓝
   ```

4. **连接太阳光**:
   - 选择 BP_Sky_Sphere
   - **Details** → **Directional Light Actor**
   - 选择场景中的 Directional Light

### 步骤 5: 添加基准标记 (可选)

#### 5.1 网格线标记

创建地面参考网格:

1. **Place Actors** → **Cube**
2. 创建 10x10 的网格:
   ```python
   # 伪代码: 在 UE 中手动放置或用蓝图生成
   for x in range(-5, 6):
       for y in range(-5, 6):
           Spawn Cube at (x*1000, y*1000, 5)
           Scale: (10, 10, 1)  # 细长的线
           Material: 红色
   ```

#### 5.2 高度标记杆

放置垂直标记杆供无人机高度参考:

1. **Cylinder** Actor
2. 位置: (0, 0, 500)
3. 缩放: (10, 10, 1000)  # 10m 高
4. 材质: 红白相间

### 步骤 6: AirSim 配置

#### 6.1 Player Start

1. **Place Actors** → **Player Start**
2. 位置: (0, 0, 200)  # 地面上方 2m
3. 旋转: (0, 0, 0)

#### 6.2 AirSim Settings

确保 `~/Documents/AirSim/settings.json` 配置简化:

```json
{
  "SettingsVersion": 1.2,
  "SimMode": "Multirotor",

  "Vehicles": {
    "Drone1": {
      "VehicleType": "SimpleFlight",
      "X": 0, "Y": 0, "Z": -2.0,

      "Cameras": {
        "front_center": {
          "CaptureSettings": [{
            "ImageType": 0,
            "Width": 640,
            "Height": 480,
            "FOV_Degrees": 90
          }]
        },
        "depth_cam": {
          "CaptureSettings": [{
            "ImageType": 2,
            "Width": 640,
            "Height": 480,
            "FOV_Degrees": 90
          }]
        }
      }
    }
  },

  "PhysicsEngineName": "FastPhysicsEngine",
  "ClockSpeed": 1.0
}
```

### 步骤 7: 光照烘焙 (可选但推荐)

为了达到最高性能，烘焙静态光照:

1. **Build** → **Build Lighting Only**
2. **Lighting Quality**: **Production**
3. 等待烘焙完成 (1-5 分钟)

**优势**:
- 预计算阴影 (无运行时开销)
- 更高帧率 (80-120 FPS)
- 一致的视觉效果

### 步骤 8: 性能优化

#### 8.1 World Settings

1. **Window** → **World Settings**
2. **Lightmass Settings**:
   ```yaml
   Force No Precomputed Lighting: ✗
   Static Lighting Level Scale: 1.0
   Num Indirect Lighting Bounces: 1  # 减少反弹
   ```

3. **LOD System**:
   ```yaml
   Default: Disabled (无复杂模型)
   ```

#### 8.2 Post Process Volume

1. **Place Actors** → **Post Process Volume**
2. **Details**:
   ```yaml
   Infinite Extent (Unbound): ✓
   ```

3. **Post Process Settings**:
   ```yaml
   # 禁用不必要的效果
   Motion Blur Amount: 0.0
   Bloom Intensity: 0.0
   Vignette Intensity: 0.0

   # 保留必要的
   Anti-Aliasing Method: TAA
   Screen Space Reflections: ✗
   Ambient Occlusion: ✗
   ```

#### 8.3 引擎优化

**控制台命令** (按 ~ 键):

```bash
# 禁用不需要的功能
r.Fog 0                          # 禁用雾
r.MotionBlur.Max 0               # 禁用运动模糊
r.BloomQuality 0                 # 禁用光晕
r.AmbientOcclusionLevels 0       # 禁用 AO

# 优化阴影
r.Shadow.MaxResolution 2048      # 降低阴影分辨率
r.Shadow.CSM.MaxCascades 2       # 减少级联

# 显示性能
stat fps                         # 显示帧率
stat unit                        # 显示各项时间
```

---

## 场景验证清单

### 视觉验证

- [ ] 棋盘格清晰可见
- [ ] 黑白对比度高
- [ ] 无人机阴影清晰
- [ ] 天空纯净无云
- [ ] 无闪烁或 artifacts

### 性能验证

- [ ] FPS > 60 (目标 80-120)
- [ ] GPU 使用率 < 50%
- [ ] 无卡顿或掉帧
- [ ] Draw Calls < 100
- [ ] 内存使用 < 2GB

### AirSim 验证

- [ ] 无人机正确生成
- [ ] 深度相机输出正常
- [ ] RGB 相机输出清晰
- [ ] 碰撞检测正常（地面）
- [ ] Odom 数据稳定

---

## 测试场景变体

### 变体 1: 不同棋盘格尺寸

测试不同空间尺度的视觉效果:

```yaml
小格子 (1m):  Divide → 100
中格子 (5m):  Divide → 500
大格子 (10m): Divide → 1000
```

### 变体 2: 彩色网格

替代黑白，使用彩色标记:

```
If (Checkerboard < 1):
  红色 (1, 0, 0)
Else:
  蓝色 (0, 0, 1)
```

### 变体 3: 高度梯度

添加微小的高度变化测试高度估计:

1. Landscape Mode → Sculpt
2. 创建非常平缓的坡度 (±10cm)
3. 测试无人机高度控制

---

## 高级功能（可选）

### 1. 自动化测试路径

创建 **BP_TestPath** 蓝图:

```cpp
Variables:
  Array<Vector> Waypoints = [
    (0, 0, 200),      // 起点
    (1000, 0, 200),   // 向前 10m
    (1000, 1000, 200),// 右转
    (0, 1000, 200),   // 返回
    (0, 0, 200)       // 降落
  ]

Event BeginPlay:
  For Each Waypoint:
    Draw Debug Sphere (Waypoint, 50, Yellow)
    Draw Debug Line (Current → Next, Green)
```

### 2. 性能监测 HUD

创建性能显示 UI:

```cpp
BP_PerformanceHUD:

  Event Tick:
    GetFrameRate() → FPS
    GetGPUTime() → GPU_ms
    GetMemoryUsage() → Memory_MB

    Draw Text on Screen:
      "FPS: {FPS}"
      "GPU: {GPU_ms} ms"
      "Memory: {Memory_MB} MB"
```

### 3. 相机校准标记

添加 ArUco 标记或棋盘格校准板:

1. 创建 **Plane** (100x100 cm)
2. 应用标准校准图案材质
3. 放置在地面多个位置
4. 用于相机内参标定

---

## 快速启动脚本

创建 **setup_clean_lab.sh**:

```bash
#!/bin/bash
# Clean Lab 场景快速设置脚本

echo "Setting up Clean Lab scene..."

# 1. 复制 AirSim 设置
cp ~/YOPO/UnrealProjects/ForestDrone/Config/CleanLab_settings.json \
   ~/Documents/AirSim/settings.json

# 2. 启动 UE 编辑器
cd ~/UnrealEngine
./Engine/Binaries/Linux/UE4Editor \
  ~/YOPO/UnrealProjects/ForestDrone/ForestDrone.uproject \
  /Game/Maps/CleanLab

echo "Clean Lab ready!"
echo "Press Alt+P to start simulation"
```

---

## 性能基准

### 硬件配置 vs 预期 FPS

| GPU | 分辨率 | 预期 FPS | 备注 |
|-----|-------|---------|------|
| **RTX 3070** | 1920x1080 | 120+ | 完美 |
| **RTX 2060** | 1920x1080 | 100-120 | 优秀 |
| **GTX 1660** | 1920x1080 | 80-100 | 良好 |
| **GTX 1060** | 1920x1080 | 60-80 | 可用 |

**注意**: 如果 FPS 低于预期，检查:
1. 是否禁用了运动模糊和光晕
2. 阴影质量是否过高
3. 是否有后台程序占用 GPU

---

## 与复杂场景对比

| 特性 | Clean Lab | Forest Scene |
|-----|----------|--------------|
| **FPS** | 80-120 | 30-50 |
| **Draw Calls** | <100 | 3000-5000 |
| **内存** | <2GB | 8-12GB |
| **创建时间** | 15 分钟 | 2-3 小时 |
| **用途** | 基础测试 | 真实导航 |
| **复杂度** | 极简 | 高 |

---

## 常见问题

### Q1: 棋盘格显示模糊？

**A**:
1. 检查材质 UV Tiling
2. 增大 `Divide` 值（更大的格子）
3. 启用 TAA 抗锯齿

### Q2: 阴影不清晰？

**A**:
1. 增大 `r.Shadow.MaxResolution` (2048 → 4096)
2. Directional Light → Dynamic Shadow Distance: 20000
3. 烘焙静态光照（Build Lighting）

### Q3: 性能不如预期？

**A**:
```bash
# 检查瓶颈
stat gpu
stat unit

# 如果 GPU 时间高
r.ScreenPercentage 90  # 降低渲染分辨率

# 如果 CPU 时间高
r.MaxFPS 120  # 限制最大帧率
```

### Q4: 地面穿透（无碰撞）？

**A**:
1. 选择 Plane/Landscape
2. **Details** → **Collision**
3. Collision Presets: **BlockAll**
4. Generate Overlap Events: ✗

---

## 导出独立程序

### 打包 Clean Lab 场景

1. **Edit** → **Project Settings**
2. **Maps & Modes**:
   - Game Default Map: `/Game/Maps/CleanLab`
   - Editor Startup Map: `/Game/Maps/CleanLab`

3. **File** → **Package Project** → **Linux**
4. 选择输出目录
5. 等待打包 (5-10 分钟)

### 运行独立程序

```bash
cd Output/LinuxNoEditor
./ForestDrone.sh -ResX=1920 -ResY=1080 -windowed
```

---

## 扩展应用

### 1. 视觉 SLAM 测试

Clean Lab 的高对比度棋盘格非常适合:
- ORB-SLAM 特征点检测
- 回环检测验证
- 位姿估计精度测试

### 2. 深度估计校准

使用已知的平面几何:
- 验证深度相机精度
- 标定深度缩放因子
- 测试不同高度的深度误差

### 3. 控制算法调试

简单环境便于:
- PID 参数调优
- 轨迹跟踪测试
- 悬停稳定性验证

---

## 下一步

完成 Clean Lab 后:

1. ✅ **验证 AirSim**: 确保所有传感器正常
2. ✅ **测试 YOPO**: 在简单环境中测试导航
3. ✅ **性能基准**: 记录最佳性能指标
4. 🚀 **进入森林**: 切换到复杂 Forest 场景

---

**场景版本**: 1.0 - Clean Lab
**创建时间**: 15 分钟
**目标 FPS**: 80-120
**适用于**: AirSim 基础验证和算法调试

**相关文档**:
- [ForestDrone README](../README.md) - 项目概述
- [FOREST_SCENE_GUIDE.md](FOREST_SCENE_GUIDE.md) - 复杂场景创建
- [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) - 性能优化
