# 蓝图系统文档

本目录包含 ForestDrone 项目的所有蓝图脚本。由于蓝图是 UE 内部的可视化脚本，这里提供创建说明和逻辑伪代码。

## 目录

### 核心蓝图

1. **BP_GameMode_Forest** - 游戏模式控制器
2. **BP_EnvironmentController** - 环境系统总控制器
3. **BP_TimeOfDayController** - 时间系统
4. **BP_WeatherController** - 天气系统
5. **BP_ForestGenerator** - 程序化森林生成器

---

## 1. BP_GameMode_Forest

**路径**: `/Game/Blueprints/BP_GameMode_Forest`

### 创建步骤

1. **Content Browser** → 右键 → **Blueprint Class** → **Game Mode Base**
2. 命名为 `BP_GameMode_Forest`
3. 打开蓝图编辑器

### 配置

**Class Defaults**:
```
Default Pawn Class: None (AirSim 控制)
HUD Class: None
Player Controller Class: PlayerController
Game State Class: GameState
```

### Event Graph

```cpp
Event BeginPlay:
│
├─ Spawn Actor from Class: BP_EnvironmentController
│  └─ Store as: EnvironmentController
│
├─ Spawn Actor from Class: BP_TimeOfDayController
│  └─ Store as: TimeController
│
├─ Spawn Actor from Class: BP_WeatherController
│  └─ Store as: WeatherController
│
└─ Print String: "Forest Environment Initialized"
```

---

## 2. BP_EnvironmentController

**路径**: `/Game/Blueprints/BP_EnvironmentController`

### 创建步骤

1. **Blueprint Class** → **Actor**
2. 命名为 `BP_EnvironmentController`

### 变量

```cpp
// References
Directional Light DirectionalLight_Sun
Sky Atmosphere SkyAtmosphere
Exponential Height Fog HeightFog
Volumetric Cloud VolumetricCloud

// Settings
Boolean AutomaticTimeProgression = True
Float GlobalEnvironmentQuality = 1.0  // 0.0 - 1.0
```

### Event Graph

```cpp
Event BeginPlay:
│
├─ Get All Actors of Class: DirectionalLight
│  └─ Store Index 0: DirectionalLight_Sun
│
├─ Get All Actors of Class: SkyAtmosphere
│  └─ Store Index 0: SkyAtmosphere
│
├─ Get All Actors of Class: ExponentialHeightFog
│  └─ Store Index 0: HeightFog
│
└─ Get All Actors of Class: VolumetricCloud
   └─ Store Index 0: VolumetricCloud

Event Tick:
│
└─ Update Environment Quality
   ├─ Get Frame Rate
   ├─ If FPS < 30:
   │  └─ Reduce Quality (降低 Foliage 密度, 禁用云)
   └─ If FPS > 50:
      └─ Increase Quality (恢复正常)

Custom Event: SetEnvironmentPreset(String PresetName)
│
├─ Switch on PresetName:
│  ├─ "Morning":
│  │  ├─ Set Time: 7.0
│  │  ├─ Set Weather: Clear
│  │  └─ Set Fog: Light
│  │
│  ├─ "Noon":
│  │  ├─ Set Time: 12.0
│  │  ├─ Set Weather: Clear
│  │  └─ Set Fog: None
│  │
│  ├─ "Evening":
│  │  ├─ Set Time: 18.0
│  │  ├─ Set Weather: Cloudy
│  │  └─ Set Fog: Medium
│  │
│  ├─ "Night":
│  │  ├─ Set Time: 22.0
│  │  ├─ Set Weather: Clear
│  │  └─ Set Fog: Heavy
│  │
│  └─ "Storm":
│     ├─ Set Time: 14.0
│     ├─ Set Weather: Rain
│     └─ Set Fog: Heavy
```

---

## 3. BP_TimeOfDayController

**路径**: `/Game/Blueprints/BP_TimeOfDayController`

### 变量

```cpp
// Time Settings
Float TimeOfDay = 12.0          // 0-24 hours
Float TimeSpeed = 0.1           // Real seconds per game hour
Boolean IsPaused = False

// References
Directional Light SunLight
Sky Light SkyLight
Light Component MoonLight

// Sun Path Settings
Float SunriseTime = 6.0
Float SunsetTime = 20.0
Float NoonIntensity = 10.0 lux
Float NightIntensity = 0.1 lux
```

### Functions

#### UpdateTimeOfDay()

```cpp
Function UpdateTimeOfDay(Float DeltaTime):
│
├─ If NOT IsPaused:
│  ├─ TimeOfDay += DeltaTime * TimeSpeed
│  └─ If TimeOfDay >= 24.0:
│     └─ TimeOfDay -= 24.0
│
├─ Calculate Sun Angle:
│  └─ SunAngle = ((TimeOfDay - 6.0) / 12.0) * 180.0
│     // 6:00 = 0°, 12:00 = 90°, 18:00 = 180°
│
├─ Update Sun Rotation:
│  └─ SunLight.SetRotation(FRotator(SunAngle, 180, 0))
│
├─ Calculate Light Intensity:
│  ├─ If TimeOfDay between Sunrise and Sunset:
│  │  ├─ Progress = (TimeOfDay - Sunrise) / (Sunset - Sunrise)
│  │  ├─ IntensityCurve = sin(Progress * π)
│  │  └─ Intensity = IntensityCurve * NoonIntensity
│  └─ Else:
│     └─ Intensity = NightIntensity
│
├─ Update Light Color:
│  ├─ If TimeOfDay < 7 or TimeOfDay > 19:
│  │  └─ Color = Lerp(Blue(0.2,0.2,0.5), Orange(1.0,0.6,0.3), Factor)
│  ├─ If TimeOfDay < 9 or TimeOfDay > 17:
│  │  └─ Color = Orange(1.0,0.7,0.4) // Golden hour
│  └─ Else:
│     └─ Color = White(1.0,0.97,0.9) // Midday
│
└─ Apply to Sun Light:
   ├─ SunLight.SetIntensity(Intensity)
   └─ SunLight.SetLightColor(Color)
```

### Event Graph

```cpp
Event BeginPlay:
│
└─ Get All Actors of Class: DirectionalLight
   └─ Store: SunLight

Event Tick:
│
└─ UpdateTimeOfDay(DeltaTime)

// Keyboard shortcuts
Event: OnKeyPressed "T"
│
└─ CycleDayNight()
   ├─ If TimeOfDay < 12:
   │  └─ SetTimeOfDay(12)  // Jump to noon
   └─ Else:
      └─ SetTimeOfDay(22)  // Jump to night

Custom Event: SetTimeOfDay(Float NewTime)
│
├─ TimeOfDay = Clamp(NewTime, 0, 24)
└─ UpdateTimeOfDay(0)  // Immediate update
```

---

## 4. BP_WeatherController

**路径**: `/Game/Blueprints/BP_WeatherController`

### 变量

```cpp
// Weather State
Enum EWeatherType CurrentWeather = Clear
  // [Clear, Cloudy, Rainy, Stormy, Foggy]

Float WeatherIntensity = 0.0  // 0.0 - 1.0
Float TransitionSpeed = 0.1

// Particle Systems
Niagara System NS_Rain
Niagara System NS_Snow
Niagara System NS_Fog_Particles

// Audio
Audio Component AC_Rain
Audio Component AC_Wind
Audio Component AC_Thunder

// References
Volumetric Cloud CloudActor
Exponential Height Fog FogActor
```

### Functions

#### SetWeather(EWeatherType NewWeather, Float Intensity)

```cpp
Function SetWeather(EWeatherType NewWeather, Float Intensity):
│
├─ CurrentWeather = NewWeather
├─ WeatherIntensity = Clamp(Intensity, 0, 1)
│
├─ Switch on NewWeather:
│  │
│  ├─ Clear:
│  │  ├─ Disable All Particles
│  │  ├─ Set Cloud Coverage: 0.2
│  │  ├─ Set Fog Density: 0.01
│  │  └─ Stop All Weather Audio
│  │
│  ├─ Cloudy:
│  │  ├─ Disable Particles
│  │  ├─ Set Cloud Coverage: 0.6
│  │  ├─ Set Fog Density: 0.02
│  │  └─ Play Wind Audio (Low)
│  │
│  ├─ Rainy:
│  │  ├─ Enable NS_Rain
│  │  │  └─ Spawn Rate: 5000 * Intensity
│  │  ├─ Set Cloud Coverage: 0.8
│  │  ├─ Set Fog Density: 0.04
│  │  ├─ Reduce Sun Intensity: 50%
│  │  ├─ Play Rain Audio
│  │  └─ Play Wind Audio (Medium)
│  │
│  ├─ Stormy:
│  │  ├─ Enable NS_Rain (Heavy)
│  │  │  └─ Spawn Rate: 10000
│  │  ├─ Set Cloud Coverage: 1.0
│  │  ├─ Set Fog Density: 0.06
│  │  ├─ Reduce Sun Intensity: 20%
│  │  ├─ Play Rain Audio (Loud)
│  │  ├─ Play Thunder Audio (Random intervals)
│  │  └─ Spawn Lightning (Random)
│  │
│  └─ Foggy:
│     ├─ Enable NS_Fog_Particles
│     ├─ Set Cloud Coverage: 0.5
│     ├─ Set Fog Density: 0.1 * Intensity
│     └─ Reduce Visibility: 500m
│
└─ Trigger Transition Timeline (smooth change)
```

#### UpdateWeather(Float DeltaTime)

```cpp
Function UpdateWeather(Float DeltaTime):
│
├─ Interpolate Cloud Coverage:
│  └─ Current → Target (over TransitionSpeed)
│
├─ Interpolate Fog Density:
│  └─ Current → Target (over TransitionSpeed)
│
└─ Update Particle Systems:
   └─ Adjust spawn rate based on intensity
```

### Event Graph

```cpp
Event BeginPlay:
│
├─ Spawn Niagara Systems
│  ├─ NS_Rain (Deactivated)
│  ├─ NS_Snow (Deactivated)
│  └─ NS_Fog_Particles (Deactivated)
│
├─ Create Audio Components
│  ├─ AC_Rain (Stopped)
│  ├─ AC_Wind (Stopped)
│  └─ AC_Thunder (Stopped)
│
└─ Set Initial Weather: Clear

Event Tick:
│
└─ UpdateWeather(DeltaTime)

// Keyboard shortcut
Event: OnKeyPressed "W"
│
└─ CycleWeather()
   ├─ Switch CurrentWeather:
   │  ├─ Clear → Cloudy
   │  ├─ Cloudy → Rainy
   │  ├─ Rainy → Stormy
   │  ├─ Stormy → Foggy
   │  └─ Foggy → Clear
   └─ SetWeather(NextWeather, 0.7)

Custom Event: RandomizeWeather()
│
└─ SetWeather(
     Random Enum Value,
     Random Float (0.3, 1.0)
   )
```

---

## 5. BP_ForestGenerator

**路径**: `/Game/Blueprints/BP_ForestGenerator`

**用途**: 程序化生成森林，可选替代手动 Foliage 绘制

### 变量

```cpp
// Generation Settings
Float ForestSize = 10000.0 cm      // 森林半径
Float TreeDensity = 0.5            // 每 1000cm² 的树木数量
Float MinTreeDistance = 300.0 cm   // 树木最小间距

// Tree Assets
Array<Static Mesh> TreeMeshes = [
  SM_Pine_01,
  SM_Oak_01,
  SM_Birch_01,
  SM_Spruce_01
]

Array<Float> TreeWeights = [0.4, 0.3, 0.2, 0.1]  // 出现概率

// Scale Variation
Vector MinScale = (0.8, 0.8, 0.9)
Vector MaxScale = (1.2, 1.2, 1.1)

// References
Landscape LandscapeActor
Hierarchical Instanced Static Mesh Component HISM_Trees
```

### Functions

#### GenerateForest()

```cpp
Function GenerateForest():
│
├─ Clear Existing Instances:
│  └─ HISM_Trees.ClearInstances()
│
├─ Calculate Number of Trees:
│  ├─ Area = π * ForestSize²
│  └─ TreeCount = (Area / 1000000) * TreeDensity
│
├─ Generate Tree Positions:
│  └─ For i = 0 to TreeCount:
│     │
│     ├─ Generate Random Position:
│     │  ├─ X = Random(-ForestSize, +ForestSize)
│     │  ├─ Y = Random(-ForestSize, +ForestSize)
│     │  └─ Distance = sqrt(X² + Y²)
│     │
│     ├─ If Distance > ForestSize:
│     │  └─ Continue (跳过圆形边界外)
│     │
│     ├─ Check Minimum Distance:
│     │  ├─ For each existing tree:
│     │  │  └─ If Distance < MinTreeDistance:
│     │  │     └─ Continue (太近,跳过)
│     │
│     ├─ Get Landscape Height:
│     │  └─ Z = LineTrace(From=(X,Y,10000), To=(X,Y,-10000))
│     │
│     ├─ Get Surface Normal:
│     │  └─ Normal = LineTrace.Normal
│     │
│     ├─ Check Slope:
│     │  ├─ Slope = acos(Normal.Z)
│     │  └─ If Slope > 45°:
│     │     └─ Continue (太陡,跳过)
│     │
│     ├─ Select Random Tree Mesh:
│     │  └─ Mesh = WeightedRandom(TreeMeshes, TreeWeights)
│     │
│     ├─ Generate Random Transform:
│     │  ├─ Location = (X, Y, Z)
│     │  ├─ Rotation = Align to Normal + Random Yaw
│     │  └─ Scale = Random(MinScale, MaxScale)
│     │
│     └─ Add Instance:
│        └─ HISM_Trees.AddInstance(Transform, Mesh)
│
└─ Print String: "Generated {TreeCount} trees"
```

#### AddTreeCluster(Vector Center, Int Count, Float Radius)

```cpp
Function AddTreeCluster(Vector Center, Int Count, Float Radius):
│
└─ For i = 0 to Count:
   │
   ├─ Random Offset:
   │  ├─ Angle = Random(0, 360)
   │  ├─ Distance = Random(0, Radius)
   │  └─ Offset = (cos(Angle)*Distance, sin(Angle)*Distance, 0)
   │
   └─ Spawn Tree at: Center + Offset
```

### Event Graph

```cpp
Event BeginPlay:
│
├─ Get Landscape:
│  └─ Get All Actors of Class: Landscape
│     └─ Store: LandscapeActor
│
├─ Create HISM Components:
│  └─ For each TreeMesh:
│     ├─ Add Component: HierarchicalInstancedStaticMesh
│     ├─ Set Static Mesh: TreeMesh
│     └─ Set Collision: Block All
│
└─ If AutoGenerate:
   └─ GenerateForest()

Custom Event: RegenerateForest()
│
├─ Clear All Instances
└─ GenerateForest()

Custom Event: AddTreesInRadius(Vector Location, Float Radius)
│
└─ AddTreeCluster(Location, 10, Radius)
```

---

## 6. 辅助蓝图

### BP_WaypointMarker

**用途**: 可视化无人机航点

```cpp
Components:
├─ Sphere (Collision)
│  └─ Radius: 50 cm
├─ Billboard (Editor visualization)
│  └─ Sprite: WaypointIcon
└─ Text Render
   └─ Text: "Waypoint {Index}"

Variables:
├─ Int WaypointIndex = 0
├─ Vector NextWaypoint = (0,0,0)
└─ Boolean IsStart = False

Event BeginPlay:
│
└─ Draw Debug Line to Next Waypoint
```

### BP_FlightPathVisualizer

**用途**: 显示规划的飞行路径

```cpp
Variables:
Array<Vector> PathPoints = []

Function DrawPath():
│
└─ For i = 0 to PathPoints.Length - 1:
   │
   ├─ Draw Debug Sphere(PathPoints[i], 30, Blue)
   └─ Draw Debug Line(PathPoints[i], PathPoints[i+1], Yellow)

Event Tick:
│
└─ DrawPath()
```

---

## 蓝图创建顺序

建议按以下顺序创建蓝图:

1. ✅ **BP_GameMode_Forest** (游戏基础)
2. ✅ **BP_TimeOfDayController** (时间系统)
3. ✅ **BP_WeatherController** (天气系统)
4. ✅ **BP_EnvironmentController** (环境总控)
5. ⚠️ **BP_ForestGenerator** (可选,程序化生成)
6. ⚠️ **BP_WaypointMarker** (可选,调试用)

---

## 蓝图通信

### 事件分发器 (Event Dispatchers)

在 **BP_TimeOfDayController**:
```cpp
Event Dispatcher: OnTimeChanged(Float NewTime)
Event Dispatcher: OnDayNightCycle(Boolean IsDay)
```

在 **BP_WeatherController**:
```cpp
Event Dispatcher: OnWeatherChanged(EWeatherType NewWeather)
Event Dispatcher: OnRainStarted()
Event Dispatcher: OnRainStopped()
```

### 使用示例

在其他蓝图中监听:
```cpp
Event BeginPlay:
│
├─ Get Actor of Class: BP_TimeOfDayController
│  └─ Bind Event: OnTimeChanged
│     └─ Custom Event: HandleTimeChange(Float Time)
│
└─ Get Actor of Class: BP_WeatherController
   └─ Bind Event: OnRainStarted
      └─ Custom Event: HandleRainStart()
```

---

## 性能优化

### 蓝图优化技巧

1. **Event Tick 优化**:
   ```cpp
   // 不要每帧都执行重计算
   Event Tick:
   │
   ├─ FrameCounter++
   └─ If FrameCounter % 30 == 0:  // 每30帧执行一次
      └─ UpdateExpensiveCalculation()
   ```

2. **使用 Timers**:
   ```cpp
   Event BeginPlay:
   │
   └─ Set Timer by Function Name:
      ├─ Function: UpdateWeather
      ├─ Time: 1.0 seconds
      └─ Looping: True
   ```

3. **缓存引用**:
   ```cpp
   // ❌ 不好: 每帧查找
   Event Tick:
      Get All Actors of Class: DirectionalLight

   // ✅ 好: BeginPlay 时缓存
   Event BeginPlay:
      Get All Actors of Class: DirectionalLight
      Store as: CachedSunLight

   Event Tick:
      Use: CachedSunLight
   ```

---

## 调试技巧

### 打印调试信息

```cpp
Print String:
  In String: "Time: {TimeOfDay}, Weather: {CurrentWeather}"
  Duration: 0.0 (一帧)
  Text Color: Yellow
```

### 可视化调试

```cpp
Draw Debug Sphere:
  Center: ActorLocation
  Radius: 100
  Color: Red
  Duration: 0.0 (永久,直到下次更新)

Draw Debug Line:
  Start: StartPoint
  End: EndPoint
  Color: Green
  Thickness: 2.0
```

---

**注意**: 实际创建蓝图时，在 UE 编辑器中使用可视化节点编辑器实现以上逻辑。

**文档版本**: 1.0
**创建日期**: 2025-11-19
