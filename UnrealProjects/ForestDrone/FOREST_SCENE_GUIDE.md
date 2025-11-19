# 森林场景创建完整指南

## 目录
1. [项目概述](#项目概述)
2. [快速开始](#快速开始)
3. [地形系统](#地形系统)
4. [植被系统](#植被系统)
5. [光照系统](#光照系统)
6. [天气系统](#天气系统)
7. [音效系统](#音效系统)
8. [优化技巧](#优化技巧)
9. [AirSim 集成](#airsim-集成)

---

## 项目概述

**ForestDrone** 是一个为 AirSim 无人机导航设计的逼真森林环境，包含：

- 🌲 **大规模森林**: 程序化生成的密集树木
- 🏔️ **起伏地形**: 山丘、河流、岩石
- ☀️ **动态光照**: 可变时间和天气
- 🌿 **丰富植被**: 草地、灌木、花朵
- 🦋 **环境细节**: 粒子效果、音效、野生动物
- 🎮 **交互控制**: 实时调整环境参数

---

## 快速开始

### 步骤 1: 安装 AirSim 插件

```bash
cd /home/user/YOPO/UnrealProjects/ForestDrone
./setup_airsim_plugin.sh
```

### 步骤 2: 打开项目

```bash
cd ~/UnrealEngine
./Engine/Binaries/Linux/UE4Editor ~/YOPO/UnrealProjects/ForestDrone/ForestDrone.uproject
```

### 步骤 3: 创建主场景

在 UE 编辑器中：

1. **File** → **New Level** → **Empty Level**
2. 保存为 `/Game/Maps/ForestMain`
3. 按照下面的步骤添加元素

---

## 地形系统

### 1. 创建 Landscape

#### 步骤 A: 基础地形

1. **Landscape Mode** (Shift+2)
2. **Manage** 标签:
   - Section Size: **63x63** quads
   - Sections Per Component: **1x1**
   - Number of Components: **32x32** (较大的森林)
   - Overall Resolution: **2017x2017**
   - Total Components: **1024**

3. **Material**: 暂时使用默认材质
4. 点击 **Create** 创建地形

#### 步骤 B: 雕刻地形

1. **Sculpt** 标签
2. 使用工具:
   - **Smooth**: 平滑整体
   - **Noise**: 添加自然起伏
   - **Flatten**: 创建平坦区域(起飞/降落点)
   - **Ramp**: 创建斜坡和山谷

**推荐雕刻流程**:
```
1. 使用 Noise (强度 0.3) 创建整体起伏
2. 使用 Sculpt 手动添加山丘和山谷
3. 使用 Smooth (强度 0.5) 柔化边缘
4. 使用 Flatten 创建 2-3 个平坦起飞区
5. 使用 Erosion 添加侵蚀效果
```

#### 步骤 C: 地形材质

**创建地形材质** (`/Game/Materials/M_Landscape_Forest`):

```
基础层:
- Layer 1: 草地 (占主导)
- Layer 2: 泥土路径
- Layer 3: 岩石 (陡峭区域)
- Layer 4: 苔藓 (潮湿区域)

混合方式:
- 根据坡度自动混合 (Landscape Layer Blend)
- 根据高度自动混合
- 支持手动绘制路径
```

**材质节点设置**:

1. 创建 Material → 命名为 `M_Landscape_Forest`
2. 设置 **Material Domain** = Surface
3. 添加节点:
   ```
   Landscape Layer Blend
   ├─ Layer "Grass" (Weight Blend)
   │  └─ Texture: T_Grass_Basecolor
   ├─ Layer "Dirt" (Weight Blend)
   │  └─ Texture: T_Dirt_Basecolor
   ├─ Layer "Rock" (Height Blend)
   │  └─ Texture: T_Rock_Basecolor
   └─ Layer "Moss" (Weight Blend)
      └─ Texture: T_Moss_Basecolor
   ```

4. 添加自动坡度混合:
   ```
   Landscape Layer Weight (Rock)
   ├─ Landscape Layer Coords → Slope
   └─ If Slope > 0.5 → Blend to Rock
   ```

#### 步骤 D: 绘制地形纹理

1. **Paint** 标签
2. 选择 Layer (Grass/Dirt/Rock/Moss)
3. 调整 Brush Size 和 Strength
4. 绘制区域:
   - **Grass**: 平坦开阔区域
   - **Dirt**: 无人机飞行路径下方
   - **Rock**: 陡峭山坡和悬崖
   - **Moss**: 潮湿阴暗区域

---

## 植被系统

### 1. 获取树木资产

#### 选项 A: Quixel Megascans (推荐)

免费高质量资产:

1. 打开 **Quixel Bridge** (需要 Epic Games 账号)
2. 搜索:
   - "European Beech" (欧洲山毛榉)
   - "Norway Spruce" (挪威云杉)
   - "Scots Pine" (苏格兰松)
   - "Oak Tree" (橡树)
3. 下载 3-5 种不同树木 (LOD: 高)
4. 导入到 `/Game/Megascans/3D_Plants/`

#### 选项 B: UE Marketplace 免费资源

- **Open World Demo Collection**
- **Landscape Mountains**
- **Free Forest Pack**

#### 选项 C: 程序化树木

使用 UE 的 SpeedTree 插件:

1. **Window** → **SpeedTree Modeler**
2. 创建自定义树木
3. 导出为 `.st` 文件并导入

### 2. 设置 Foliage 系统

#### 步骤 A: 创建 Foliage Type

1. **Foliage Mode** (Shift+4)
2. 拖拽树木模型到 Foliage 面板
3. 右键树木 → **Show Instance Settings**

**关键设置** (以松树为例):

```yaml
Placement:
  Density / 1Kuu²: 0.5 - 2.0  # 密度 (调整树木间距)
  Radius: 200 - 500 cm        # 最小间距
  Align to Normal: ✓          # 贴合地形
  Random Yaw: ✓               # 随机旋转

Scaling:
  Scale X: (0.8, 1.2)         # 随机大小
  Scale Y: (0.8, 1.2)
  Scale Z: (0.9, 1.1)
  Lock Scaling: ✗

Instance Settings:
  Cull Distance: 0 - 10000    # 可见距离
  Cast Shadow: ✓
  Mobility: Static            # 静态 (性能优化)

Collision:
  Collision Presets: BlockAll # 阻挡无人机
  Custom Depth: ✓             # 深度相机需要
```

#### 步骤 B: 绘制森林

**分层绘制策略**:

```
第一层 - 背景森林 (低密度):
- 树种: 高大树木 (20-30m)
- 密度: 0.3 /1Kuu²
- 范围: 整个地形
- 目的: 填充背景

第二层 - 主要森林 (中密度):
- 树种: 中等树木 (10-20m)
- 密度: 1.0 /1Kuu²
- 范围: 飞行区域周围
- 目的: 主要障碍物

第三层 - 密集灌木 (高密度):
- 树种: 小树和灌木 (3-8m)
- 密度: 2.0 /1Kuu²
- 范围: 地面附近
- 目的: 增加复杂度

第四层 - 地面植被:
- 草地、花朵、蕨类
- 密度: 5-10 /1Kuu²
- 范围: 所有可见区域
- 目的: 视觉真实感
```

**绘制技巧**:

1. **创建飞行通道**: 用 Erase 工具清除无人机路径上的树木
2. **自然分布**: 不要均匀分布，创建树木丛和空地
3. **边缘渐变**: 森林边缘使用较低密度
4. **高度变化**: 高地用矮树，低地用高树

### 3. 程序化森林生成 (高级)

#### 使用 PCG (Procedural Content Generation) - UE 4.27+

**创建 PCG Graph** (`BP_ForestGenerator`):

```
Input: Landscape
  ↓
Density Map (Noise)
  ↓
Point Sampling (树木位置)
  ↓
Height Filter (避开陡坡)
  ↓
Spawn Static Mesh (树木实例)
  ↓
Collision Setup
```

**蓝图实现** (简化版):

1. **EventBeginPlay**:
   ```
   Get Landscape Bounds
   → Generate Grid Points (间距 500cm)
   → For Each Point:
      └─ Random Chance (70%)
         └─ Spawn Tree (Random Selection)
            ├─ Random Scale (0.8-1.2)
            ├─ Random Rotation Z (0-360)
            └─ Align to Surface Normal
   ```

---

## 光照系统

### 1. 天空和大气

#### Directional Light (太阳)

**创建并配置**:

```yaml
Transform:
  Rotation: (-45, 0, 0)  # 初始太阳角度
  Mobility: Movable      # 允许动态时间

Light:
  Intensity: 10.0 lux
  Light Color: (255, 247, 230) # 温暖日光
  Temperature: 6500 K
  Use Temperature: ✓

Cascaded Shadow Maps:
  Dynamic Shadow Distance: 10000 cm
  Num Dynamic Shadows: 4
  Cascade Distribution: 0.7

Atmosphere:
  Atmosphere Sun Light: ✓
  Cast Cloud Shadows: ✓
```

#### Sky Atmosphere

1. 添加 **Sky Atmosphere** Actor
2. 连接到 Directional Light
3. 设置:
   ```yaml
   Atmosphere:
     Rayleigh Scattering: Default
     Mie Scattering: 0.005
     Absorption: 0.001

   Art Direction:
     Sky Luminance Factor: 1.0
     Aerial Perspective: ✓
   ```

#### Sky Light

```yaml
Light:
  Source Type: SLS Captured Scene
  Intensity: 1.0
  Color: (255, 255, 255)

Distance Field:
  Cast Shadows: ✓
  Occlusion Max Distance: 1000 cm
```

#### Volumetric Clouds

1. 添加 **Volumetric Cloud** Actor
2. 设置:
   ```yaml
   Layer:
     Layer Bottom: 1000 m
     Layer Height: 3000 m

   Material:
     Tracing Sample Count: 16
     Shadow Tracing Sample Count: 4

   Cloud Appearance:
     Coverage: 0.3 - 0.7 (调整云量)
     Density: 0.5
   ```

### 2. 环境光

#### Exponential Height Fog

```yaml
Fog:
  Fog Density: 0.02
  Fog Height Falloff: 0.2
  Fog Max Opacity: 0.6
  Start Distance: 0

Directional Inscattering:
  Use: ✓
  Color: (200, 220, 255) # 蓝色雾气
  Exponent: 4.0

Volumetric Fog:
  Enable: ✓
  Scattering Distribution: 0.2
  Albedo: (0.9, 0.9, 0.9)
  Extinction Scale: 1.0
```

### 3. 动态时间系统 (蓝图)

**创建 BP_TimeOfDayController**:

**变量**:
```cpp
float TimeOfDay = 12.0;  // 0-24 小时
float TimeSpeed = 0.1;   // 时间流速
DirectionalLight SunLight;
```

**Event Tick**:
```cpp
// 更新时间
TimeOfDay += DeltaTime * TimeSpeed;
if (TimeOfDay >= 24.0) TimeOfDay -= 24.0;

// 计算太阳角度
float SunAngle = (TimeOfDay / 24.0) * 360.0 - 90.0;
SunLight.SetRotation(FRotator(SunAngle, 0, 0));

// 调整光照颜色
if (TimeOfDay < 6 or TimeOfDay > 20) {
    // 夜晚: 蓝色月光
    SunLight.SetIntensity(0.1);
    SunLight.SetColor(FLinearColor(0.2, 0.2, 0.5));
} else if (TimeOfDay < 8 or TimeOfDay > 18) {
    // 黄昏/黎明: 橙色
    SunLight.SetIntensity(5.0);
    SunLight.SetColor(FLinearColor(1.0, 0.6, 0.3));
} else {
    // 白天: 明亮日光
    SunLight.SetIntensity(10.0);
    SunLight.SetColor(FLinearColor(1.0, 0.97, 0.9));
}
```

---

## 天气系统

### 1. 雨天效果

#### Niagara 粒子系统 (雨滴)

**创建 NS_Rain**:

```yaml
Emitter Properties:
  Spawn Rate: 10000
  Lifetime: 2.0 - 3.0

Particle Spawn:
  Box Location: (10000, 10000, 5000) # 覆盖范围

Particle Update:
  Gravity Force: (0, 0, -980)
  Drag: 0.1

Sprite Rendering:
  Size: (10, 200) # 雨滴大小
  Color: (180, 200, 255, 128)
  Material: M_RainDrop
```

#### 雨声音效

```cpp
BP_WeatherController:
  Audio Component: Rain_Loop.wav
  Volume: 0.5
  Attenuation: 5000 cm radius
```

### 2. 风效果

**创建 BP_WindZone**:

```cpp
Variables:
  Vector WindDirection = (1, 0, 0);
  float WindStrength = 500.0;

Event Tick:
  // 影响 Foliage
  ApplyWindToFoliage(WindDirection, WindStrength);

  // 影响粒子 (树叶、灰尘)
  UpdateWindParticles();
```

**树木风动材质**:

在树叶材质中添加 **Simple Grass Wind** 节点:

```
World Position Offset:
  Simple Grass Wind
  ├─ Wind Intensity: 500
  ├─ Wind Weight: 0.5
  └─ Wind Speed: 1.0
```

---

## 音效系统

### 1. 环境音效

**创建 Audio Cues**:

```
/Game/Audio/
├─ AMB_Forest_Day.uasset      # 白天: 鸟鸣、昆虫
├─ AMB_Forest_Night.uasset    # 夜晚: 蟋蟀、猫头鹰
├─ AMB_Wind_Loop.uasset       # 风声
├─ AMB_Rain_Loop.uasset       # 雨声
└─ AMB_River.uasset           # 河流 (如果有)
```

**放置 Ambient Sound Actors**:

1. 拖拽 `AMB_Forest_Day` 到场景中央
2. 设置:
   ```yaml
   Attenuation Settings:
     Falloff Distance: 50000 cm  # 覆盖整个森林
     Spatialization: None        # 全局环境音

   Modulation:
     Volume Modulation: (0.5, 0.8) # 随机音量变化
     Pitch Modulation: (0.9, 1.1)  # 随机音高变化
   ```

### 2. 空间音效 (3D Sound)

**鸟鸣和动物叫声**:

```cpp
BP_Wildlife_Sound_Spawner:
  Event BeginPlay:
    For i = 0 to 20:  // 生成 20 个音源
      RandomLocation = GetRandomPointInForest()
      SpawnSound(AMB_Bird_Chirp, RandomLocation)
        ├─ Attenuation: 2000 cm
        ├─ Random Delay: 5-15 秒
        └─ Volume: 0.3
```

---

## 优化技巧

### 1. Foliage 优化

**LOD (Level of Detail) 设置**:

```yaml
Static Mesh LOD:
  LOD 0 (近距离): Full Detail
  LOD 1 (中距离): 50% Triangles
  LOD 2 (远距离): 25% Triangles
  LOD 3 (极远): Billboard (2D Sprite)

Cull Distance:
  Grass: 5000 cm
  Bushes: 8000 cm
  Trees: 15000 cm
  Large Trees: 25000 cm
```

**Hierarchical Instanced Static Mesh (HISM)**:

所有 Foliage 自动使用 HISM，确保:
- ✓ Mobility = Static
- ✓ Generate Overlap Events = False
- ✓ Can Ever Affect Navigation = False

### 2. 光照优化

**Lightmass 烘焙** (如果使用静态光照):

```yaml
World Settings → Lightmass:
  Num Indirect Lighting Bounces: 3
  Static Lighting Level Scale: 0.5

Lightmap Resolution:
  Landscape: 2.0
  Trees: 64
  Rocks: 128
```

**动态光照优化**:

```yaml
Directional Light:
  Dynamic Shadow Cascades: 3 (降低到3)
  Distance: 8000 cm (限制阴影距离)

Point Lights:
  Max Draw Distance: 3000 cm
  Fade Distance: 500 cm
```

### 3. Streaming 优化

**World Composition**:

1. **World Settings** → Enable World Composition
2. **Window** → World Composition
3. 将地形分块:
   - Tile Size: 2 km x 2 km
   - Streaming Distance: 5 km

**Data Layers** (UE 4.27+):

```yaml
Layer 1: Terrain (Always Loaded)
Layer 2: Forest_Dense (Load when near)
Layer 3: Forest_Background (Load at distance)
Layer 4: Details (Load when very near)
```

---

## AirSim 集成

### 1. 无人机起飞点

**创建 Player Start**:

1. 搜索 **Player Start** → 拖到场景
2. 放置在平坦、开阔区域
3. 设置:
   ```yaml
   Transform:
     Location: (0, 0, 200) # 地面上方 2 米
     Rotation: (0, 0, 0)
   ```

4. AirSim 将在此位置生成无人机

### 2. 飞行路径规划

**创建导航 Waypoints**:

```cpp
BP_Flight_Waypoints:
  Array<Vector> Waypoints = [
    (0, 0, 200),        // 起点
    (2000, 0, 300),     // 穿过树林
    (4000, 2000, 400),  // 绕过山丘
    (6000, 0, 200),     // 返回降落
  ]

  Event: Draw Debug Path
    For Each Waypoint:
      DrawDebugSphere(Waypoint, 50, Blue)
      DrawDebugLine(Waypoint[i], Waypoint[i+1], Yellow)
```

### 3. 障碍物设置

确保所有树木和岩石有碰撞:

```yaml
Foliage Collision:
  Collision Complexity: Simple
  Collision Preset: BlockAll

Depth Camera Support:
  Render Custom Depth: ✓
  Custom Depth Stencil Value: 255
```

### 4. 测试飞行

1. **Play** (Alt+P) 进入游戏模式
2. 按 **;** 键打开 AirSim 子窗口
3. 查看无人机视角和深度图
4. 使用键盘或 API 控制飞行

---

## 蓝图脚本示例

### BP_环境控制器

**完整蓝图逻辑**:

```
Event BeginPlay:
  ├─ Get Directional Light → Store as "SunLight"
  ├─ Get Sky Atmosphere
  ├─ Get Volumetric Clouds
  └─ Get Weather Audio Components

Event Tick:
  ├─ Update Time of Day
  │  ├─ TimeOfDay += DeltaTime * TimeSpeed
  │  ├─ Clamp (0, 24)
  │  └─ Update Sun Rotation
  │
  ├─ Update Weather
  │  ├─ If Rain:
  │  │  ├─ Enable Rain Particles
  │  │  ├─ Enable Rain Audio
  │  │  ├─ Increase Cloud Coverage
  │  │  └─ Decrease Sun Intensity
  │  └─ Else:
  │     └─ Disable Rain Effects
  │
  └─ Update Ambient Audio
     ├─ If Day: Play Bird Sounds
     └─ If Night: Play Cricket Sounds

Custom Events:
  ├─ SetTimeOfDay(float Hour)
  ├─ ToggleWeather()
  ├─ SetWeatherIntensity(float Intensity)
  └─ CycleDayNight()
```

---

## 高级功能

### 1. 动态树木生长 (可选)

**时间流逝效果**:

```cpp
BP_GrowingTree:
  float Age = 0.0;  // 0-10 年

  Event Tick:
    Age += DeltaTime * GrowthSpeed;
    float Scale = Lerp(0.1, 1.0, Age / 10.0);
    SetActorScale3D(FVector(Scale));
```

### 2. 野生动物 (鹿、鸟)

**AI 巡逻行为**:

```cpp
BP_Deer:
  Navigation:
    ├─ Nav Mesh Bounds Volume (覆盖森林)
    └─ AI Controller (Simple Move to Location)

  Behavior:
    每 10 秒随机选择新的巡逻点
    如果检测到无人机 → 逃跑
```

### 3. 季节变化

**材质参数集合**:

```cpp
MPC_Season (Material Parameter Collection):
  ├─ SeasonIndex (0=春, 1=夏, 2=秋, 3=冬)
  ├─ LeafColor (绿色 → 黄色 → 棕色)
  ├─ GroundSnow (0-1, 积雪量)
  └─ FogDensity (雾气浓度)

树叶材质:
  Base Color = Lerp(GreenLeaf, YellowLeaf, SeasonIndex)
```

---

## 常见问题

### Q1: 树木太多导致性能下降？

**A**:
1. 减少 Foliage 密度 (降至 0.5-1.0)
2. 降低 Cull Distance (树木 10000 → 8000)
3. 使用更激进的 LOD (减少 LOD 0 距离)
4. 启用 World Composition 分块加载

### Q2: 无人机穿过树木？

**A**:
1. 检查 Foliage Collision = BlockAll
2. 检查树木 Mobility = Static
3. 在 AirSim settings.json 启用碰撞检测

### Q3: 深度相机看不到树木？

**A**:
1. 勾选 Foliage → Render Custom Depth
2. 设置 Custom Depth Stencil Value = 255
3. 在材质中启用 Output Custom Depth

### Q4: 雾气太浓看不清？

**A**:
调整 Exponential Height Fog:
- Fog Density: 0.02 → 0.01
- Fog Max Opacity: 0.6 → 0.3

---

## 资源清单

### 必需资产

- ✓ 树木模型 (至少 3 种, LOD 完整)
- ✓ 地形纹理 (草地、泥土、岩石、苔藓)
- ✓ 草地和灌木模型
- ✓ 岩石模型 (3-5 个变体)

### 推荐资产

- 树叶、树枝散落物
- 蕨类植物
- 花朵 (多种颜色)
- 蘑菇
- 倒木 (dead trees)
- 树桩

### 音效资产

- 环境: 鸟鸣、昆虫、风声
- 天气: 雨声、雷声
- 自然: 河流、瀑布 (如果有)

---

## 下一步

1. ✅ 创建基础地形和森林
2. 🎨 调整光照和天气
3. 🎮 测试 AirSim 飞行
4. 📊 性能优化
5. 🚀 与 YOPO 集成 (参考 AIRSIM_README.md)

---

**文档版本**: 1.0
**最后更新**: 2025-11-19
**适用于**: Unreal Engine 4.27.1 + AirSim 1.8.1
