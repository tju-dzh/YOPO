# 性能优化指南

ForestDrone 项目的性能优化策略和最佳实践。

## 目标性能指标

| 配置 | 目标帧率 | 最低帧率 |
|-----|---------|---------|
| **高端** (RTX 3070+) | 60 FPS | 50 FPS |
| **中端** (GTX 1660+) | 45 FPS | 30 FPS |
| **最低** (GTX 1060) | 30 FPS | 25 FPS |

AirSim 深度相机需要稳定 30 FPS 以上才能正常工作。

---

## 1. Foliage 优化

### 密度调整

**控制台命令** (按 ~ 键):
```
foliage.DensityScale 0.5        # 减少50%密度
foliage.DiscardDataOnLoad 1     # 加载后丢弃CPU数据
foliage.MinimumScreenSize 0.001 # 减小最小屏幕尺寸
```

### LOD 距离

**Foliage Settings** (每个植物类型):
```yaml
LOD 0 Distance: 0 - 1000 cm
LOD 1 Distance: 1000 - 3000 cm
LOD 2 Distance: 3000 - 6000 cm
LOD 3 Distance: 6000 - 10000 cm
Cull Distance: 10000 cm
```

### HISM 实例化

确保所有 Foliage 使用 Hierarchical Instanced Static Mesh:

```yaml
Static Mesh Settings:
  Enable GPU Instancing: ✓
  Mobility: Static
  Generate Overlap Events: ✗
  Affect Dynamic Indirect Lighting: ✗
```

---

## 2. 地形优化

### Landscape Component Size

**推荐配置**:
```yaml
小场景 (<2km²):
  Component Size: 63x63
  Num Components: 16x16
  Total Size: 1009x1009

中场景 (2-8km²):
  Component Size: 63x63
  Num Components: 32x32
  Total Size: 2017x2017

大场景 (>8km²):
  Component Size: 127x127
  Num Components: 32x32
  Total Size: 4065x4065
  + 启用 World Composition
```

### LOD 设置

**DefaultEngine.ini**:
```ini
[/Script/Landscape.LandscapeSettings]
LOD0DistributionSetting=1.5
LOD1DistributionSetting=2.0
LOD2DistributionSetting=3.0
LOD3DistributionSetting=4.0
```

### Landscape Material

优化材质节点:

```
✅ 推荐:
- 使用 Landscape Layer Weight (高效混合)
- 启用 Use Material Attributes
- 限制纹理采样 (<8个)

❌ 避免:
- 过多的 Lerp 节点
- 复杂的 Math 运算
- 高分辨率 Normal Map (>2K)
```

---

## 3. 光照优化

### 静态光照烘焙

**Lightmass Settings** (World Settings):
```yaml
Static Lighting Level Scale: 0.5  # 降低精度提升性能
Num Indirect Lighting Bounces: 2  # 减少反弹次数
Num Sky Lighting Bounces: 1
Indirect Lighting Quality: 2.0
Indirect Lighting Smoothness: 1.0
```

**Lightmap Resolution**:
```yaml
Landscape: 1.0 - 2.0
Trees (Static): 32 - 64
Rocks: 64 - 128
Ground Props: 128
```

### 动态光照

如果使用动态光照 (AirSim 推荐):

```yaml
Directional Light:
  Dynamic Shadow Distance: 8000 cm  # 阴影距离
  Num Dynamic Shadow Cascades: 3    # CSM 级联数
  Cascade Distribution Exponent: 2.0
  Far Shadow Cascade Count: 0       # 禁用远距离阴影

Point Lights:
  Attenuation Radius: 3000 cm
  Use Inverse Squared Falloff: ✓
  Cast Shadows: 仅重要光源
```

### Distance Field Shadows

**启用距离场** (更高效的软阴影):

```ini
[/Script/Engine.RendererSettings]
r.GenerateMeshDistanceFields=True
r.DistanceFieldShadowing=True
r.DFShadowQuality=2
r.AOQuality=2
```

---

## 4. 渲染优化

### 后处理

**Post Process Volume** 设置:

```yaml
优先级: 1

Ambient Occlusion:
  Intensity: 0.5
  Radius: 100 cm
  Quality: 2 (Medium)

Bloom:
  Intensity: 0.5
  Threshold: 1.0
  Method: Standard

Motion Blur:
  Amount: 0.0  # 禁用 (AirSim 不需要)

Screen Space Reflections:
  Enabled: ✗  # 禁用 (森林中不明显)
```

### 视野距离

**Scalability Settings**:

```yaml
ViewDistanceQuality: 2 (Medium)
  r.ViewDistanceScale: 1.0 (中端GPU)
  r.ViewDistanceScale: 0.75 (低端GPU)
```

**Cull Distance Volumes**:

在森林远端放置 Cull Distance Volume:
```yaml
Size: 5000 x 5000 x 3000 cm
Cull Distances:
  0 cm: 0 (不剔除)
  5000 cm: 10000 (5m外物体在10m外消失)
  10000 cm: 20000
```

---

## 5. 粒子系统优化

### Niagara 性能设置

**雨粒子系统**:
```yaml
高性能:
  Max Particles: 5000
  Spawn Rate: 3000/s
  Fixed Bounds: ✓ (5000x5000x3000)

中性能:
  Max Particles: 10000
  Spawn Rate: 5000/s

低性能:
  Disable雨效果
```

### LOD Distances

```yaml
Niagara System:
  LOD 0: 0 - 3000 cm (Full Quality)
  LOD 1: 3000 - 6000 cm (50% Particles)
  LOD 2: 6000+ cm (Disabled)
```

---

## 6. Collision 优化

### 简化碰撞体

**树木碰撞**:
```yaml
Collision Complexity: Simple Collision
Collision Presets: BlockAll

Static Mesh:
  Simple Collision: Capsule or Box
  ❌ 避免 Complex Collision (Per-Poly)
```

**地形碰撞**:
```yaml
Landscape:
  Collision Mip Level: 1 (降低分辨率)
  Simple Collision Mip Level: 2
```

### 物理子步进

**Project Settings → Physics**:
```yaml
Max Physics Delta Time: 0.033333 (30 FPS)
Enable Substepping: ✓
Max Substep Delta Time: 0.016667
Max Substeps: 4
```

---

## 7. 内存优化

### 纹理流送

**DefaultEngine.ini**:
```ini
[/Script/Engine.StreamingSettings]
s.MinBulkDataSizeForAsyncLoading=131072
s.AsyncLoadingThreadEnabled=True
s.EventDrivenLoaderEnabled=True

[/Script/Engine.RendererSettings]
r.Streaming.PoolSize=3000          # 3GB 纹理池
r.Streaming.LimitPoolSizeToVRAM=1
r.Streaming.UseFixedPoolSize=1
r.Streaming.MaxNumTexturesToStreamPerFrame=10
```

### 纹理压缩

**所有纹理设置**:
```yaml
Compression: BC1/BC3/BC5 (DXT)
LOD Group: World
Mip Gen Settings: From Texture Group
Never Stream: ✗
```

**纹理分辨率指南**:
```yaml
地形 Base Color: 2048x2048
地形 Normal: 2048x2048
树木 Base Color: 1024x1024
树叶 Base Color: 512x512
草地: 256x256 (高重复)
```

---

## 8. CPU 优化

### Tick 优化

**禁用不必要的 Tick**:

```cpp
BP Settings:
  Start with Tick Enabled: ✗

// 仅在需要时启用
Event BeginPlay:
  Set Actor Tick Enabled: False

// 需要更新时
Custom Event:
  Set Actor Tick Enabled: True
  // ... do work ...
  Set Actor Tick Enabled: False
```

### Tick Interval

```cpp
// 不需要每帧更新的逻辑
Component Tick Interval: 0.1  // 每 0.1 秒更新一次
```

### Event-Driven Logic

用 Timer 替代 Tick:

```cpp
// ❌ 不好
Event Tick:
  UpdateWeather()

// ✅ 好
Event BeginPlay:
  Set Timer by Function Name:
    Function: UpdateWeather
    Time: 1.0
    Looping: True
```

---

## 9. World Composition (大场景)

### 启用 World Composition

**适用于 >4km² 的场景**:

1. **World Settings** → Enable World Composition
2. **Window** → World Composition
3. 将 Landscape 分块:
   - Tile Size: 2km x 2km
   - Streaming Distance: 5km

### Layer Streaming

**创建 Streaming Levels**:

```
PersistentLevel (Always Loaded):
├─ Lighting
├─ Global Actors
└─ Player Start

Forest_00_00 (Dynamic):
├─ Terrain Tile
└─ Foliage Instance

Forest_01_00 (Dynamic):
├─ Terrain Tile
└─ Foliage Instance
```

---

## 10. AirSim 特定优化

### 深度相机优化

**settings.json**:
```json
{
  "CameraDefaults": {
    "CaptureSettings": [{
      "ImageType": 2,
      "Width": 640,
      "Height": 480,
      "FOV_Degrees": 90,
      "AutoExposureSpeed": 100,
      "MotionBlurAmount": 0
    }]
  }
}
```

**性能权衡**:
```yaml
高性能 (推荐):
  Resolution: 640x480
  FOV: 90°
  Update Rate: 30 Hz

中性能:
  Resolution: 512x384
  FOV: 80°
  Update Rate: 25 Hz

低性能:
  Resolution: 320x240
  FOV: 70°
  Update Rate: 20 Hz
```

### Custom Depth Pass

确保启用但优化:

```yaml
Foliage:
  Render Custom Depth: ✓
  Custom Depth Stencil Value: 255

Project Settings:
  r.CustomDepth: 3 (With Stencil)
  r.CustomDepthTemporalAAJitter: ✓
```

---

## 11. Scalability 配置

### 自定义可扩展性设置

**Config/DefaultScalability.ini**:

```ini
[ScalabilityGroups]

[ViewDistanceQuality@0]
r.ViewDistanceScale=0.5
r.SkeletalMeshLODBias=2

[ViewDistanceQuality@1]
r.ViewDistanceScale=0.75
r.SkeletalMeshLODBias=1

[ViewDistanceQuality@2]
r.ViewDistanceScale=1.0
r.SkeletalMeshLODBias=0

[ViewDistanceQuality@3]
r.ViewDistanceScale=1.5
r.SkeletalMeshLODBias=0

[FoliageQuality@0]
foliage.DensityScale=0.25
foliage.DiscardDataOnLoad=1

[FoliageQuality@1]
foliage.DensityScale=0.5
foliage.DiscardDataOnLoad=1

[FoliageQuality@2]
foliage.DensityScale=1.0
foliage.DiscardDataOnLoad=0

[FoliageQuality@3]
foliage.DensityScale=1.5
foliage.DiscardDataOnLoad=0
```

### 运行时切换

**控制台命令**:
```
sg.ViewDistanceQuality 2      # 中等视野距离
sg.FoliageQuality 1           # 低植被密度
sg.ShadowQuality 2            # 中等阴影
sg.PostProcessQuality 2       # 中等后处理
sg.TextureQuality 2           # 中等纹理
sg.EffectsQuality 2           # 中等特效
```

---

## 12. Profiling 工具

### 内置性能分析

**控制台命令**:

```bash
stat fps               # 显示帧率
stat unit              # 显示CPU/GPU/Draw时间
stat scenerendering    # 场景渲染统计
stat foliage           # Foliage 统计
stat gpu               # GPU 性能详情
stat particles         # 粒子系统统计
```

### GPU Profiler

```bash
profilegpu             # 打开GPU Profiler
```

查看耗时最多的渲染操作:
- Base Pass
- Shadow Depths
- Foliage
- Post Processing

### Session Frontend

**Window → Developer Tools → Session Frontend**:

- **Profiler** 标签: CPU 性能分析
- **Task Graph**: 多线程分析
- **Memory**: 内存使用情况

---

## 13. 性能检查清单

### 启动项目前

- [ ] 所有 Foliage Mobility = Static
- [ ] LOD 设置正确 (至少 3 级)
- [ ] Lightmap 已烘焙 (如果使用静态光照)
- [ ] Texture Streaming 已启用
- [ ] Cull Distance 已设置
- [ ] World Composition (大场景)

### 运行时检查

- [ ] FPS > 30 (最低要求)
- [ ] GPU 使用率 < 90%
- [ ] CPU Frame Time < 20ms
- [ ] Draw Calls < 5000
- [ ] Foliage Instances < 500,000

### AirSim 特定

- [ ] 深度相机帧率 > 25 FPS
- [ ] Custom Depth Pass 启用
- [ ] 无穿透碰撞 (树木)
- [ ] Odom 发布 > 90 Hz

---

## 14. 常见性能问题

### 问题 1: FPS <30

**诊断**:
```bash
stat unit
stat gpu
```

**解决方案**:
1. 检查 Draw Thread 时间
   - 如果 >20ms → 减少 Foliage 密度
2. 检查 GPU 时间
   - 如果 >25ms → 降低后处理质量
3. 检查 Shadow Depths
   - 如果 >10ms → 减少阴影距离

### 问题 2: 内存不足

**诊断**:
```bash
stat memory
memreport
```

**解决方案**:
1. 减小纹理池 (Streaming.PoolSize)
2. 降低纹理分辨率 (LOD Bias)
3. 启用 Texture Streaming
4. 使用 World Composition

### 问题 3: Foliage 卡顿

**解决方案**:
1. 启用 GPU Instancing
2. 减少唯一 Mesh 种类 (<10)
3. 使用 HISM (自动)
4. 降低密度 (foliage.DensityScale 0.5)

---

## 推荐配置

### 高性能 (RTX 3070+)

```ini
[/Script/Engine.RendererSettings]
r.ViewDistanceScale=1.5
r.PostProcessAAQuality=4
r.MaxAnisotropy=8
r.Shadow.MaxResolution=2048

foliage.DensityScale=1.2
foliage.LODDistanceScale=1.0
```

### 中性能 (GTX 1660)

```ini
r.ViewDistanceScale=1.0
r.PostProcessAAQuality=2
r.MaxAnisotropy=4
r.Shadow.MaxResolution=1024

foliage.DensityScale=0.8
foliage.LODDistanceScale=0.8
```

### 低性能 (GTX 1060)

```ini
r.ViewDistanceScale=0.75
r.PostProcessAAQuality=1
r.MaxAnisotropy=2
r.Shadow.MaxResolution=512
r.DynamicShadowCascades=2

foliage.DensityScale=0.5
foliage.LODDistanceScale=0.6
r.ScreenPercentage=90
```

---

**文档版本**: 1.0
**最后更新**: 2025-11-19
