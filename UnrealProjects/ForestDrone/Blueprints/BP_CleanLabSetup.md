# Clean Lab 场景自动构建蓝图

本文档描述如何创建自动化蓝图来快速搭建 Clean Lab 测试场景。

---

## BP_CleanLabBuilder - 场景构建器

**路径**: `/Game/Blueprints/BP_CleanLabBuilder`

### 用途

一键生成完整的 Clean Lab 场景，包括:
- 棋盘格地面
- 优化的光照
- 天空球
- 测试标记
- 性能监测 HUD

### 创建步骤

1. **Content Browser** → 右键
2. **Blueprint Class** → **Actor**
3. 命名为 `BP_CleanLabBuilder`
4. 双击打开

### 变量定义

```cpp
//====================
// Scene Configuration
//====================

// Ground Settings
Boolean UseCheckerboard = True        // 使用棋盘格或纯色
Float GridSize = 500.0                // 棋盘格大小 (cm)
Float GroundSize = 10000.0            // 地面尺寸 (cm)
LinearColor ColorA = (0, 0, 0)        // 颜色 A (黑)
LinearColor ColorB = (1, 1, 1)        // 颜色 B (白)

// Lighting Settings
Float SunBrightness = 10.0            // 太阳亮度 (lux)
Rotator SunRotation = (-60, 0, 0)     // 太阳角度
Float SkyBrightness = 0.5             // 天空光强度

// Test Markers
Boolean SpawnGridMarkers = True       // 生成网格标记
Boolean SpawnHeightPoles = True       // 生成高度标记杆
Float MarkerSpacing = 1000.0          // 标记间距 (cm)

// Performance
Boolean ShowPerformanceHUD = True     // 显示性能 HUD
Boolean EnableLightBaking = False     // 启用光照烘焙

//====================
// Runtime Variables
//====================

// References (存储生成的 Actor)
Actor GroundPlane
DirectionalLight SunLight
SkyLight EnvironmentLight
Actor SkySphere
Array<Actor> TestMarkers

// Materials
Material M_Checkerboard
Material M_GroundSolid
Material M_GridLines
Material M_HeightPole
```

### Event Graph

#### Event BeginPlay

```cpp
Event BeginPlay:
│
├─ Clear Existing Scene
│  └─ DestroyExistingActors()
│
├─ Build Ground
│  └─ CreateGround()
│     ├─ If UseCheckerboard:
│     │  └─ SpawnGroundPlane(M_Checkerboard)
│     └─ Else:
│        └─ SpawnGroundPlane(M_GroundSolid)
│
├─ Setup Lighting
│  └─ CreateLighting()
│     ├─ SpawnDirectionalLight()
│     ├─ SpawnSkyLight()
│     └─ SpawnSkySphere()
│
├─ Add Test Markers (Optional)
│  ├─ If SpawnGridMarkers:
│  │  └─ CreateGridMarkers()
│  └─ If SpawnHeightPoles:
│     └─ CreateHeightPoles()
│
├─ Optimize Scene
│  └─ ApplyOptimizations()
│     ├─ DisableUnnecessaryFeatures()
│     ├─ SetScalabilityLevels()
│     └─ If EnableLightBaking:
│        └─ TriggerLightBuild()
│
├─ Setup Performance Monitoring
│  └─ If ShowPerformanceHUD:
│     └─ CreatePerformanceHUD()
│
└─ Print String: "Clean Lab Setup Complete!"
```

### Function: CreateGround()

```cpp
Function CreateGround():
│
├─ Spawn Actor: StaticMeshActor
│  ├─ Static Mesh: Plane
│  ├─ Location: (0, 0, 0)
│  ├─ Rotation: (0, 0, 0)
│  └─ Scale: (GroundSize/100, GroundSize/100, 1)
│     // Default plane is 100x100, scale to GroundSize
│
├─ Set Material:
│  └─ If UseCheckerboard:
│     ├─ Load Asset: M_Checkerboard
│     ├─ Create Dynamic Material Instance
│     ├─ Set Parameters:
│     │  ├─ GridSize: GridSize
│     │  ├─ ColorA: ColorA
│     │  └─ ColorB: ColorB
│     └─ Apply to Plane
│  └─ Else:
│     ├─ Load Asset: M_GroundSolid
│     └─ Apply to Plane
│
├─ Set Collision:
│  ├─ Collision Preset: BlockAll
│  └─ Generate Overlap Events: False
│
├─ Set Mobility: Static (for baking)
│
└─ Store Reference: GroundPlane
```

### Function: CreateLighting()

```cpp
Function CreateLighting():
│
├─ Spawn Directional Light:
│  ├─ Location: (0, 0, 1000)
│  ├─ Rotation: SunRotation
│  ├─ Intensity: SunBrightness
│  ├─ Light Color: (255, 255, 255)
│  ├─ Temperature: 6500 K
│  ├─ Cast Shadows: True
│  ├─ Mobility: Stationary
│  └─ Store: SunLight
│
├─ Spawn Sky Light:
│  ├─ Location: (0, 0, 500)
│  ├─ Intensity: SkyBrightness
│  ├─ Light Color: (200, 220, 255)
│  ├─ Source Type: Captured Scene
│  ├─ Mobility: Stationary
│  └─ Store: EnvironmentLight
│
└─ Spawn Sky Sphere:
   ├─ Blueprint: BP_Sky_Sphere
   ├─ Location: (0, 0, 0)
   ├─ Set Parameters:
   │  ├─ Sun Brightness: SunBrightness * 5
   │  ├─ Cloud Speed: 0
   │  ├─ Cloud Opacity: 0
   │  └─ Directional Light: SunLight
   └─ Store: SkySphere
```

### Function: CreateGridMarkers()

```cpp
Function CreateGridMarkers():
│
├─ Calculate Grid Bounds:
│  ├─ MinX = -GroundSize / 2
│  ├─ MaxX = +GroundSize / 2
│  ├─ MinY = -GroundSize / 2
│  └─ MaxY = +GroundSize / 2
│
├─ For X = MinX to MaxX (Step: MarkerSpacing):
│  └─ For Y = MinY to MaxY (Step: MarkerSpacing):
│     │
│     ├─ Skip if (X=0 AND Y=0) ← Origin marker 特殊处理
│     │
│     ├─ Spawn Cube:
│     │  ├─ Location: (X, Y, 5)
│     │  ├─ Scale: (5, 5, 1) ← 50cm x 50cm x 10cm
│     │  └─ Material: M_GridLines (红色半透明)
│     │
│     └─ Add to Array: TestMarkers
│
└─ Spawn Origin Marker (Special):
   ├─ Sphere at (0, 0, 50)
   ├─ Scale: (50, 50, 50) ← 5m 直径
   └─ Material: 黄色发光
```

### Function: CreateHeightPoles()

```cpp
Function CreateHeightPoles():
│
├─ Pole Positions:
│  └─ Array<Vector> = [
│     (2000, 0, 0),      // 右侧 20m
│     (-2000, 0, 0),     // 左侧
│     (0, 2000, 0),      // 前方
│     (0, -2000, 0),     // 后方
│     (2000, 2000, 0)    // 对角
│  ]
│
├─ For Each Position:
│  │
│  ├─ Spawn Cylinder:
│  │  ├─ Location: Position + (0, 0, 500) ← 中心在 5m 高
│  │  ├─ Scale: (5, 5, 1000) ← 50cm 直径, 10m 高
│  │  └─ Material: M_HeightPole (红白相间)
│  │
│  ├─ Add Text Render Component:
│  │  ├─ Text: "{Position.X/100}m, {Position.Y/100}m"
│  │  ├─ Location: Position + (0, 0, 1050)
│  │  ├─ Scale: (5, 5, 5)
│  │  └─ Color: Yellow
│  │
│  └─ Add to Array: TestMarkers
│
└─ Add Height Scale Markers (每米标记):
   └─ For Z = 100 to 1000 (Step: 100):
      └─ Spawn Small Cube at Pole + (0, 0, Z)
```

### Function: ApplyOptimizations()

```cpp
Function ApplyOptimizations():
│
├─ Disable Unnecessary Features:
│  ├─ Execute Console Command: "r.Fog 0"
│  ├─ Execute Console Command: "r.MotionBlur.Max 0"
│  ├─ Execute Console Command: "r.BloomQuality 0"
│  ├─ Execute Console Command: "r.AmbientOcclusionLevels 0"
│  └─ Execute Console Command: "r.ScreenSpaceReflections 0"
│
├─ Set Shadow Quality:
│  ├─ Execute Console Command: "r.Shadow.MaxResolution 2048"
│  └─ Execute Console Command: "r.Shadow.CSM.MaxCascades 2"
│
├─ Optimize View Distance:
│  └─ Execute Console Command: "r.ViewDistanceScale 1.5"
│
└─ Set Target FPS:
   └─ Execute Console Command: "t.MaxFPS 120"
```

### Function: CreatePerformanceHUD()

```cpp
Function CreatePerformanceHUD():
│
├─ Spawn Actor: BP_PerformanceHUD
│  └─ See separate blueprint below
│
└─ Enable Stats:
   ├─ Execute Console Command: "stat fps"
   └─ Execute Console Command: "stat unit"
```

---

## BP_PerformanceHUD - 性能监测 HUD

**路径**: `/Game/Blueprints/BP_PerformanceHUD`

### 用途

实时显示性能指标和场景信息。

### 变量

```cpp
// Display Settings
Boolean ShowFPS = True
Boolean ShowFrameTimes = True
Boolean ShowMemory = True
Boolean ShowDrawCalls = False

// Cached Values
Float CurrentFPS = 0.0
Float GameThreadTime = 0.0
Float RenderThreadTime = 0.0
Float GPUTime = 0.0
Float MemoryUsage = 0.0
```

### Event Graph

```cpp
Event Tick:
│
├─ Get Performance Stats:
│  ├─ CurrentFPS = GetFrameRate()
│  ├─ GameThreadTime = GetGameThreadTime()
│  ├─ RenderThreadTime = GetRenderThreadTime()
│  ├─ GPUTime = GetGPUTime()
│  └─ MemoryUsage = GetProcessMemoryUsage() / 1024 / 1024
│
└─ Update HUD Display
   └─ Call DrawHUD()

Event DrawHUD (Canvas):
│
├─ Set Font: Large Bold
│
├─ If ShowFPS:
│  └─ Draw Text:
│     ├─ Position: (20, 20)
│     ├─ Text: "FPS: {CurrentFPS:.1f}"
│     └─ Color: If FPS > 60: Green, Else If > 30: Yellow, Else: Red
│
├─ If ShowFrameTimes:
│  └─ Draw Text:
│     ├─ Position: (20, 50)
│     ├─ Text: "Game: {GameThreadTime:.2f}ms  Render: {RenderThreadTime:.2f}ms  GPU: {GPUTime:.2f}ms"
│     └─ Color: White
│
├─ If ShowMemory:
│  └─ Draw Text:
│     ├─ Position: (20, 80)
│     ├─ Text: "Memory: {MemoryUsage:.0f} MB"
│     └─ Color: If < 2048: Green, Else If < 4096: Yellow, Else: Red
│
└─ Draw Scene Info:
   ├─ Position: (20, 120)
   ├─ Text: "Scene: Clean Lab  |  Grid Size: {GridSize}cm"
   └─ Color: Cyan
```

---

## BP_TestPathGenerator - 测试路径生成器

**路径**: `/Game/Blueprints/BP_TestPathGenerator`

### 用途

生成预定义的无人机测试飞行路径。

### 变量

```cpp
// Path Configuration
Enum EPathType PathType = Square
  // [Square, Circle, Figure8, Grid, Random]

Float PathSize = 2000.0           // 路径尺寸 (cm)
Float FlightHeight = 200.0        // 飞行高度 (cm)
Integer NumWaypoints = 10         // 航点数量

// Runtime
Array<Vector> Waypoints
Array<Actor> WaypointMarkers
```

### Functions

#### GenerateSquarePath()

```cpp
Function GenerateSquarePath():
│
└─ Waypoints = [
   (0, 0, FlightHeight),                    // 起点
   (PathSize, 0, FlightHeight),             // 右
   (PathSize, PathSize, FlightHeight),      // 右前
   (0, PathSize, FlightHeight),             // 前
   (0, 0, FlightHeight)                     // 回到起点
]
```

#### GenerateCirclePath()

```cpp
Function GenerateCirclePath():
│
├─ Radius = PathSize / 2
│
└─ For i = 0 to NumWaypoints:
   │
   ├─ Angle = (i / NumWaypoints) * 2 * PI
   ├─ X = Radius * cos(Angle)
   ├─ Y = Radius * sin(Angle)
   ├─ Z = FlightHeight
   │
   └─ Waypoints.Add( (X, Y, Z) )
```

#### VisualizeRTH()

```cpp
Function VisualizePath():
│
├─ Clear Old Markers:
│  └─ ForEach WaypointMarker: Destroy
│
├─ For Each Waypoint:
│  │
│  ├─ Spawn Sphere:
│  │  ├─ Location: Waypoint
│  │  ├─ Scale: (25, 25, 25)
│  │  └─ Material: Yellow Emissive
│  │
│  └─ Add to WaypointMarkers
│
└─ Draw Lines Between Waypoints:
   └─ For i = 0 to Waypoints.Length - 1:
      └─ Draw Debug Line:
         ├─ Start: Waypoints[i]
         ├─ End: Waypoints[i+1]
         ├─ Color: Green
         ├─ Thickness: 5.0
         └─ Duration: -1 (Persistent)
```

---

## BP_CleanLabGameMode - 游戏模式

**路径**: `/Game/Blueprints/BP_CleanLabGameMode`

### 用途

管理 Clean Lab 场景的游戏逻辑和状态。

### 变量

```cpp
// Scene State
Boolean SceneReady = False
Float ElapsedTime = 0.0

// References
BP_CleanLabBuilder SceneBuilder
BP_PerformanceHUD PerformanceDisplay
BP_TestPathGenerator PathGenerator
```

### Event Graph

```cpp
Event BeginPlay:
│
├─ Spawn Scene Builder:
│  └─ SceneBuilder = SpawnActor(BP_CleanLabBuilder)
│     └─ Wait until SceneReady
│
├─ Spawn Performance HUD:
│  └─ PerformanceDisplay = SpawnActor(BP_PerformanceHUD)
│
├─ Spawn Path Generator (Optional):
│  └─ PathGenerator = SpawnActor(BP_TestPathGenerator)
│     └─ Generate Square Path
│     └─ Visualize Path
│
└─ Print String: "Clean Lab Game Mode Initialized"

Event Tick:
│
├─ ElapsedTime += DeltaTime
│
└─ Update Scene (if dynamic)
```

---

## 使用流程

### 方法 1: 手动放置蓝图

1. 打开 `/Game/Maps/CleanLab`
2. **Place Actors** → 搜索 `BP_CleanLabBuilder`
3. 拖拽到场景 (0, 0, 0)
4. **Details** → 配置参数:
   ```yaml
   UseCheckerboard: ✓
   GridSize: 500
   SunBrightness: 10
   ShowPerformanceHUD: ✓
   ```
5. **Play** (Alt+P)
6. 场景自动构建

### 方法 2: 设置为默认 GameMode

1. **World Settings**
2. **Game Mode** → `BP_CleanLabGameMode`
3. 保存地图
4. 每次打开地图自动初始化

### 方法 3: 控制台命令

在运行时动态生成:

```bash
# 生成场景
SpawnActor BP_CleanLabBuilder (0,0,0)

# 调整参数 (需要暴露为蓝图可调用函数)
BP_CleanLabBuilder.SetGridSize 1000
BP_CleanLabBuilder.RebuildScene
```

---

## 键盘快捷键

在 BP_CleanLabGameMode 中添加输入处理:

```cpp
Event: InputAction "Rebuild"  // 按键: R
│
└─ SceneBuilder.DestroyExistingActors()
   └─ SceneBuilder.BeginPlay()  // 重新构建

Event: InputAction "ToggleGrid"  // 按键: G
│
└─ SceneBuilder.UseCheckerboard = NOT UseCheckerboard
   └─ SceneBuilder.CreateGround()

Event: InputAction "CycleGridSize"  // 按键: MouseWheel
│
├─ GridSize = Clamp(GridSize + WheelDelta * 100, 100, 2000)
└─ Update Material Parameter
```

---

## 性能目标

### 预期性能 (RTX 2060)

| 场景配置 | FPS | Draw Calls | Memory |
|---------|-----|-----------|--------|
| **基础** (无标记) | 120+ | <50 | <1GB |
| **标准** (网格标记) | 100-120 | <100 | <1.5GB |
| **完整** (所有标记) | 80-100 | <150 | <2GB |

### 性能优化建议

如果 FPS < 80:

1. 禁用标记: `SpawnGridMarkers = False`
2. 降低阴影: `r.Shadow.MaxResolution 1024`
3. 简化材质: 使用 `M_GroundSolid` 代替棋盘格

---

## 总结

Clean Lab 蓝图系统提供:

✅ **自动化搭建** - 一键生成完整场景
✅ **参数化配置** - 灵活调整所有设置
✅ **性能监测** - 实时HUD显示
✅ **测试工具** - 路径生成和可视化
✅ **高性能** - 目标 80-120 FPS

**创建时间**: 30-45 分钟 (蓝图开发)
**使用时间**: <1 分钟 (场景生成)

---

**文档版本**: 1.0
**最后更新**: 2025-11-19
**适用于**: UE 4.27.1 Clean Lab Scene
