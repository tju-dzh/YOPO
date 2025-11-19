# 材质创建详细指南 - Clean Lab

本文档提供 Clean Lab 场景所需材质的详细创建步骤。

---

## 1. 棋盘格材质 (M_Checkerboard)

### 完整节点图

```
┌─────────────────────────────────────────────────────────────┐
│                      材质编辑器                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Absolute World Position]                                  │
│         │                                                    │
│         ├─ R (X) ─┐                                         │
│         └─ G (Y) ─┼─ [Component Mask (RG)]                  │
│                   │                                          │
│                   ↓                                          │
│              [Divide]                                        │
│              ├─ A: World Position (RG)                       │
│              └─ B: [Constant2Vector (500, 500)]             │
│                   │         ↑                                │
│                   │    Grid Size Parameter                   │
│                   ↓                                          │
│              [Floor] ← 取整到最近的整数                       │
│              ├─ X                                            │
│              └─ Y                                            │
│                   │                                          │
│         ┌─────────┴─────────┐                               │
│         ↓                   ↓                                │
│    [Append] ← 重新组合 X 和 Y                               │
│         │                                                    │
│         ↓                                                    │
│    [Add] ← X + Y                                            │
│         │                                                    │
│         ↓                                                    │
│    [Fmod]                                                    │
│    ├─ A: (X + Y)                                            │
│    └─ B: [Constant (2)]                                     │
│         │                                                    │
│         ↓                                                    │
│    [Less] ← 比较 < 1                                        │
│    ├─ A: Fmod 结果                                          │
│    └─ B: [Constant (1)]                                     │
│         │                                                    │
│         ↓                                                    │
│    [If] ← 条件选择                                          │
│    ├─ A > B: [Constant3 (0,0,0)] 黑色                       │
│    ├─ A = B: [Constant3 (0.5,0.5,0.5)] 灰色 (unused)       │
│    ├─ A < B: [Constant3 (1,1,1)] 白色                       │
│    └─ Alpha: Less 结果                                       │
│         │                                                    │
│         ↓                                                    │
│    [Material Attributes]                                     │
│         │                                                    │
│         ├─ Base Color ←─────────┐                           │
│         ├─ Metallic: [Constant (0)] ← 非金属                │
│         ├─ Specular: [Constant (0.5)] ← 默认高光            │
│         └─ Roughness: [Constant (0.8)] ← 粗糙表面           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 详细创建步骤

#### 步骤 1: 创建材质

1. **Content Browser** → 右键
2. **Material** → 命名为 `M_Checkerboard`
3. 双击打开材质编辑器

#### 步骤 2: 添加世界坐标节点

1. 右键材质图 → 搜索 **"Absolute World Position"**
2. 放置节点

**说明**: 这个节点返回像素在世界空间中的绝对坐标 (X, Y, Z)

#### 步骤 3: 提取 X 和 Y 坐标

1. 右键 → 搜索 **"Component Mask"**
2. 连接:
   ```
   Absolute World Position → Component Mask
   ```
3. 选择 Component Mask 节点
4. **Details** 面板 → 勾选:
   - ✓ R (X 坐标)
   - ✓ G (Y 坐标)
   - ✗ B (Z 坐标 - 不需要)

#### 步骤 4: 创建网格尺寸参数

1. 右键 → **Constant** → **Scalar Parameter**
2. 命名: `GridSize`
3. **Default Value**: `500.0` (单位: cm, 即 5m)

**为什么使用参数?**
- 可以在材质实例中动态调整
- 无需重新编译材质

#### 步骤 5: 缩放坐标

1. 右键 → 搜索 **"Divide"**
2. 连接:
   ```
   Component Mask (RG) → Divide (A)
   GridSize Parameter  → Divide (B)
   ```

**效果**: 将世界坐标除以网格大小，将连续坐标转换为网格索引

#### 步骤 6: 取整

1. 右键 → 搜索 **"Floor"**
2. 连接:
   ```
   Divide → Floor
   ```

**效果**: Floor(-2.7) = -3, Floor(3.2) = 3
将浮点坐标取整到最近的整数网格

#### 步骤 7: 分离和相加 X, Y

由于 Floor 节点只对标量有效，我们需要分别处理 X 和 Y:

**方法 A: 使用两个 Floor 节点** (推荐)

1. 添加两个 **Floor** 节点: `Floor_X` 和 `Floor_Y`
2. 从 `Divide` 输出:
   - R 通道 → Floor_X
   - G 通道 → Floor_Y
3. 添加 **Add** 节点:
   ```
   Floor_X → Add (A)
   Floor_Y → Add (B)
   ```

**方法 B: 使用向量运算** (更简洁)

UE 材质支持向量运算，可以直接:
```
Divide → Floor (自动对每个分量)
```
然后提取 R 和 G 并相加。

#### 步骤 8: 模运算

1. 右键 → 搜索 **"Fmod"**
2. 连接:
   ```
   Add (X+Y) → Fmod (A)
   Constant (2) → Fmod (B)
   ```

**效果**:
- Fmod(0, 2) = 0 (偶数)
- Fmod(1, 2) = 1 (奇数)
- Fmod(2, 2) = 0 (偶数)

这会产生 0 和 1 交替的棋盘格模式。

#### 步骤 9: 条件判断

1. 右键 → 搜索 **"If"**
2. 连接:
   ```
   Fmod → If (A)
   Constant (1) → If (B)
   ```

3. 创建颜色常量:
   - 右键 → **Constant3Vector** → 命名 `Color_White`
     - R: 1.0, G: 1.0, B: 1.0
   - 右键 → **Constant3Vector** → 命名 `Color_Black`
     - R: 0.0, G: 0.0, B: 0.0

4. 连接到 If 节点:
   ```
   Color_White → If (A > B)
   Color_Black → If (A < B)
   Color_White → If (A = B)  # 不会触发，Fmod 结果只有 0 或 1
   ```

**If 节点逻辑**:
- 如果 Fmod 结果 < 1 (即 0) → 输出白色
- 如果 Fmod 结果 >= 1 (即 1) → 输出黑色

**可选**: 使用 **Lerp** 节点替代 If (更高效):

```
Fmod → Lerp (Alpha)
Color_Black → Lerp (A)
Color_White → Lerp (B)
```

#### 步骤 10: 连接到材质输出

1. 连接:
   ```
   If (或 Lerp) → Base Color
   ```

2. 添加物理属性:
   - **Metallic**: Constant (0.0) - 非金属
   - **Specular**: Constant (0.5) - 中等高光
   - **Roughness**: Constant (0.8) - 粗糙表面

#### 步骤 11: 材质设置

选择材质根节点 (M_Checkerboard):

```yaml
Material Domain: Surface
Blend Mode: Opaque
Shading Model: Default Lit
Two Sided: False  # 单面
Use Material Attributes: False
```

#### 步骤 12: 保存和应用

1. **Ctrl+S** 保存材质
2. 关闭材质编辑器
3. 拖拽到场景中的 Plane/Landscape

---

## 2. 棋盘格材质变体

### 变体 A: 可调颜色

将黑白常量改为参数:

1. 替换 `Color_Black`:
   - 右键 → **Vector Parameter** → `ColorA`
   - Default: (0, 0, 0)

2. 替换 `Color_White`:
   - 右键 → **Vector Parameter** → `ColorB`
   - Default: (1, 1, 1)

**用途**: 可以在材质实例中自定义颜色（如红蓝、黄绿）

### 变体 B: 边框高亮

在每个格子添加边框:

```
1. Frac (Divide) → 边界检测
2. If (Frac < 0.05 OR Frac > 0.95) → 边框
3. Lerp (边框颜色, 原颜色, 边界 Mask)
```

**节点图**:
```
Divide
  ↓
Frac ← 提取小数部分
  ↓
OneMinus ← 1 - Frac
  ↓
Min (Frac, OneMinus)
  ↓
Less (< 0.05) ← 边界厚度
  ↓
Lerp
├─ A: Border Color (红色)
├─ B: Original Checkerboard
└─ Alpha: Border Mask
```

### 变体 C: 渐变棋盘格

添加高度或距离渐变:

```
Absolute World Position
  ↓
Distance (from Origin)
  ↓
Divide (/ 10000) ← 衰减速率
  ↓
Saturate ← 限制 0-1
  ↓
Lerp
├─ A: Checkerboard (近)
├─ B: Solid Color (远)
└─ Alpha: Distance Fade
```

---

## 3. 地面材质 - 单色 (M_GroundSolid)

### 用途

用于极简测试，完全去除视觉干扰。

### 创建步骤

1. **Material** → `M_GroundSolid`
2. 添加 **Vector Parameter**:
   - Name: `GroundColor`
   - Default: (0.5, 0.5, 0.5) 中灰

3. 连接:
   ```
   GroundColor → Base Color
   Constant (0) → Metallic
   Constant (0.5) → Specular
   Constant (1.0) → Roughness  ← 完全粗糙，无反射
   ```

4. 保存

**颜色建议**:
- 中灰 (0.5, 0.5, 0.5) - 18% 灰卡标准
- 浅灰 (0.7, 0.7, 0.7) - 更明亮
- 米色 (0.8, 0.75, 0.6) - 温暖色调

---

## 4. 标记材质 - 高对比度

### 网格线材质 (M_GridLines)

用于地面参考网格。

```
World Position
  ↓
Fmod (%, 1000) ← 每 10m 一条线
  ↓
Less (< 10) ← 线宽 10cm
  ↓
If (True: 红色, False: 透明)
  ↓
Base Color + Opacity
```

**材质设置**:
- Blend Mode: **Translucent** (支持透明)
- Two Sided: ✓

### 高度标记材质 (M_HeightPole)

红白相间柱子:

```
World Position Z
  ↓
Divide (/ 100) ← 每 1m 切换
  ↓
Floor
  ↓
Fmod (% 2)
  ↓
If (0: 红色, 1: 白色)
```

---

## 5. 材质实例

### 为什么使用材质实例?

- 可以调整参数而无需重新编译
- 更快的迭代速度
- 便于测试不同配置

### 创建材质实例

1. 右键 `M_Checkerboard`
2. **Create Material Instance**
3. 命名: `MI_Checkerboard_5m`

4. 打开材质实例
5. **Parameter Groups** → 勾选参数:
   - ✓ GridSize: 500 (5m 网格)
   - ✓ ColorA: (0, 0, 0) 黑色
   - ✓ ColorB: (1, 1, 1) 白色

### 预设实例

创建多个实例用于不同测试:

| 实例名称 | GridSize | 用途 |
|---------|----------|------|
| MI_Checkerboard_1m | 100 | 精细网格 |
| MI_Checkerboard_5m | 500 | 标准网格 |
| MI_Checkerboard_10m | 1000 | 大网格 |
| MI_Checkerboard_RedBlue | 500 | 彩色网格 |

---

## 6. 性能优化

### 材质复杂度分析

1. 打开材质编辑器
2. **Window** → **Statistics**
3. 查看:
   ```
   Base Pass Shader:
     - Instructions: <100 (优秀)
     - Texture Samples: 0 (无纹理)
   ```

### 优化建议

1. **避免复杂运算**:
   - ✅ 使用 Floor, Fmod (简单)
   - ❌ 避免 Sin, Cos, Pow (复杂)

2. **减少纹理采样**:
   - 棋盘格材质无纹理 = 最快

3. **使用材质实例**:
   - 运行时调整参数零开销

4. **禁用不必要的功能**:
   - Two Sided: ✗
   - Use Material Attributes: ✗

---

## 7. 故障排除

### 问题 1: 棋盘格变形或不对齐

**原因**: 地面缩放不均匀

**解决**:
```
Transform → Scale: (X, Y, Z) 必须相同
例如: (100, 100, 1) ✓
     (100, 50, 1) ✗ 会拉伸
```

### 问题 2: 网格边缘有锯齿

**原因**: 抗锯齿不足

**解决**:
```ini
# 启用 TAA
r.DefaultFeature.AntiAliasing 2

# 或使用 MSAA (性能消耗更高)
r.DefaultFeature.AntiAliasing 1
r.MSAACount 4
```

### 问题 3: 远处网格闪烁 (Moire)

**原因**: 高频细节超过屏幕分辨率

**解决**:
1. 增大 GridSize (降低频率)
2. 添加距离渐变 (远处淡化)
3. 使用 Mipmap 过滤 (如果有纹理)

### 问题 4: 材质太暗或太亮

**原因**: 光照强度不匹配

**解决**:
1. 调整 Directional Light Intensity
2. 修改材质颜色:
   ```
   ColorA: (0.1, 0.1, 0.1) 深灰 (instead of 黑色)
   ColorB: (0.9, 0.9, 0.9) 浅灰 (instead of 白色)
   ```

---

## 8. 高级技巧

### 技巧 1: 世界坐标对齐

确保棋盘格从世界原点 (0,0,0) 对齐:

```
Absolute World Position
  ↓
Add (Offset Parameter)  ← 调整对齐
  ↓
Divide (GridSize)
```

### 技巧 2: 自定义图案

替换简单的棋盘格为复杂图案:

```
# 圆点图案
Floor(X), Floor(Y)
  ↓
Frac(X/2), Frac(Y/2)
  ↓
Distance from (0.5, 0.5)
  ↓
Less (< 0.3) ← 圆形半径
```

### 技巧 3: 动画棋盘格

添加时间偏移:

```
Time → Sin → Multiply (0.1)
  ↓
Add to World Position
  ↓
(rest of checkerboard logic)
```

**用途**: 验证视觉系统是否检测运动

---

## 9. 材质库

### 完整材质列表

```
/Game/Materials/
├── M_Checkerboard.uasset           # 主棋盘格材质
├── M_Checkerboard_Border.uasset    # 带边框变体
├── M_GroundSolid.uasset            # 单色地面
├── M_GridLines.uasset              # 网格线
├── M_HeightPole.uasset             # 高度标记
└── Instances/
    ├── MI_Checkerboard_1m.uasset
    ├── MI_Checkerboard_5m.uasset
    ├── MI_Checkerboard_10m.uasset
    └── MI_Checkerboard_RedBlue.uasset
```

### 导出材质

分享给其他项目:

1. 右键材质 → **Asset Actions** → **Migrate**
2. 选择目标项目
3. 自动复制所有依赖

---

## 总结

Clean Lab 材质系统的关键:

✅ **零纹理** - 完全程序化生成
✅ **高性能** - <100 shader instructions
✅ **高对比度** - 黑白分明
✅ **可参数化** - 材质实例快速调整
✅ **无锯齿** - TAA 抗锯齿支持

**创建时间**: 10-15 分钟
**性能影响**: 可忽略 (<1 ms)

---

**文档版本**: 1.0
**最后更新**: 2025-11-19
**适用于**: UE 4.27.1 + Clean Lab Scene
