# 糖糖it GitHub README 画布规范

**作者：糖糖it** | **版本：1.0** | **最后更新：2026-07-30**

---

## 一、GitHub 可靠支持范围

在 GitHub README 中，我们仅使用以下可靠渲染的特性，避免因 Markdown 解析差异导致的显示问题：

### ✅ 推荐使用
- **标准 Markdown**：标题、段落、列表、粗体/斜体、引用
- **表格**：标准 Markdown 表格语法
- **链接**：相对路径和绝对路径链接
- **代码块**：围栏代码块（带语法高亮）
- **details 折叠块**：`<details>` + `<summary>` 实现可折叠内容
- **本地图片**：仓库内相对路径引用的图片（PNG/JPG/GIF/SVG）

### ⚠️ HTML 谨慎使用
HTML 仅用于简单场景：
- 图片对齐：`<p align="center">`、`<div align="right">`
- 图片尺寸控制：`<img width="600" src="...">`
- 不使用复杂 HTML 结构、不使用 CSS 样式表、不使用 JavaScript

---

## 二、动画策略：GIF + SVG 回退

GitHub 的渲染环境对动画支持有限制：

- ✅ **GIF 动画**：GitHub 会正常播放 GIF 动画
- ❌ **SVG 内联动画**：GitHub 不播放 SVG 内的 `<animate>`、`<animateTransform>`、SMIL 动画或 CSS 动画

### 推荐策略
```
动图方案：优先使用 GIF 展示动画效果
静态回退：提供 SVG 静态版本作为高清晰度备选
```

当需要动画时：
1. 输出 GIF 动画版本（用于 GitHub 实际显示）
2. 同时提供同构图的 SVG 静态版本（用于高清查看/打印/参考）
3. 用 `<picture>` 标签实现优雅降级（GitHub 部分环境支持）

---

## 三、图片嵌入方式推荐

### 标准 Markdown（推荐）
```markdown
![项目预览](./assets/readme/hero.png)
```

### HTML 控制尺寸和对齐
```html
<p align="center">
  <img width="800" alt="项目功能展示" src="./assets/readme/features.svg">
</p>
```

### 响应式图片组（明暗主题）
```html
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/readme/hero-dark.svg">
    <img width="800" alt="项目 Hero 图" src="./assets/readme/hero-light.svg">
  </picture>
</p>
```

---

## 四、SVG 默认规范

所有为 README 创建的 SVG 文件需遵循以下规范：

### 画布尺寸
| 类型 | viewBox 宽度 | viewBox 高度 | 用途 |
|------|-------------|-------------|------|
| Hero 主视觉 | 1200 | 300–420 | README 顶部大横幅 |
| Section 横幅 | 1200 | 120–170 | 章节标题分隔 |
| 图表/图示 | 1200 | 320–760 | 架构图、流程图、对比图 |
| 图标/徽章 | 按需 | 按需 | 小尺寸装饰元素 |

- 统一使用 `viewBox="0 0 1200 H"`（H 为对应高度）
- 不固定 `width`/`height` 属性，让其自适应容器
- 坐标原点在左上角，绘图区域充分利用画布

### 字体规范
- **只使用系统字体栈**，不嵌入任何网络字体
- 推荐字体栈：
  ```svg
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif
  ```
- 中文字体可加入：`"PingFang SC", "Microsoft YaHei", "Hiragino Sans GB"`
- 文字大小不小于 16px（viewBox 单位下），确保缩小后可读

### 测试基准
- **桌面端测试**：按 900px 宽度渲染检查
- **移动端测试**：按 360px 宽度渲染检查
- 在 GitHub 明暗两种主题下都要测试可读性

---

## 五、避免脆弱的 SVG 特性

为确保 SVG 在 GitHub 各个环境（markdown 渲染、raw 查看、图片代理）下正常显示，**禁止使用**以下特性：

| 禁用特性 | 原因 | 替代方案 |
|---------|------|---------|
| `<script>` | GitHub 会移除脚本 | 用 GIF 做动画，SVG 只做静态 |
| `<foreignObject>` | 兼容性差，渲染不一致 | 用纯 SVG 元素绘制 |
| 外部 CSS 样式表 | 不会加载 | 内联样式或 presentation attributes |
| 网络字体 (@font-face) | 不会加载，导致文字回退 | 使用系统字体栈 |
| `:hover` 等交互伪类 | GitHub 环境无交互 | 静态设计，不依赖悬停效果 |
| 远程图片 URL (xlink:href) | 可能被防盗链或代理拦截 | 图片内嵌为 data URI 或只用本地资源 |
| 大面积阴影滤镜 (feGaussianBlur) | 渲染慢、易出问题、易被裁剪 | 简化为扁平设计或简单渐变 |
| `data:` URI 以外的外部引用 | 加载失败风险 | 全部内容内嵌在单个 SVG 文件中 |

---

## 六、响应式行为设计

GitHub README 在桌面和移动端宽度差异很大，图片需要适配：

### 缩放原则
1. **图片整体等比缩放**：不使用 CSS 媒体查询在 SVG 内重排
2. **viewBox 正确设置**：确保缩放时不变形
3. **内容安全边距**：四周保留至少 40px 空白，避免贴边裁切

### 文字处理
- 如果文字在 360px 宽度下小于 10px 物理像素：
  - 方案 A：简化文字，减少字数，增大字号
  - 方案 B：拆分为多张图片，每张展示较少内容
  - 方案 C：将长文字移出图片，用 Markdown 正文展示
- 永远不要让用户需要放大才能看清图中文字

### 预览检查清单
- [ ] 900px 宽度下清晰可读
- [ ] 360px 宽度下核心信息仍可辨认
- [ ] 不依赖特定宽度显示
- [ ] 缩放时没有元素被意外裁切

---

## 七、资产目录结构

推荐在仓库中按以下结构组织 README 相关资产：

```
your-repo/
├── README.md
└── assets/
    └── readme/
        ├── hero.svg              # 主视觉
        ├── hero-dark.svg         # 暗色版（可选）
        ├── demo.gif              # 演示动画
        ├── sections/
        │   ├── features.svg      # 功能章节横幅
        │   ├── installation.svg  # 安装章节横幅
        │   └── architecture.svg  # 架构图
        └── examples/
            └── screenshot-1.png  # 截图示例
```

### 路径引用原则
- README.md 中统一使用**相对路径**：`./assets/readme/hero.svg`
- 不要使用绝对路径或 `blob/main/...` 形式的 URL
- 图片名全部小写，用连字符分隔，不用空格或中文

---

## 八、无障碍与信任建设

### Alt 文本规范
所有图片必须写有意义的 `alt` 属性：

✅ **好的示例**：
```markdown
![项目架构图：展示前端、API、数据库三层结构](./assets/readme/architecture.svg)
<img alt="安装命令演示动画" src="./assets/readme/install-demo.gif">
```

❌ **坏的示例**：
```markdown
![banner](./hero.png)
![image](./img1.png)
<img alt="" src="...">  <!-- 纯装饰图片才留空 -->
```

alt 文本要描述**图片传递的信息/目的**，不是描述图片本身。

### 不要在图片里藏关键信息
- ❌ 不要把安装命令、配置代码、版本号写在图片里——用户无法复制
- ❌ 不要把重要链接只放在图里——用户无法点击
- ✅ 图片做视觉吸引，可复制的命令、可点击的链接放在 Markdown 正文中

### 真实与概念图区分
- **真实输出截图**：标注为"实际运行截图"，不做过度美化
- **概念示意图/抽象图**：标注为"示意图"或"概念图"
- 不要把概念图伪装成真实产品截图，避免误导用户

### 明暗背景可读性
- 所有 SVG 必须**自带背景色**（白色或深色），不要透明依赖
- 检查在 GitHub 白色背景下文字清晰
- 检查在 GitHub 深色背景下文字清晰
- 如果明暗差异大，准备两套图用 `prefers-color-scheme` 切换

### SVG 安全
SVG 是 XML 格式，可以包含恶意内容。为安全和兼容性：
- SVG 自带矩形背景，避免透明时的显示异常
- 不引用外部资源
- 不使用 `onload` 等事件属性
- 提交前检查：SVG 文件能用浏览器直接打开正常显示，不报错

---

## 九、快速检查清单

提交 README 前，对照此清单检查：

- [ ] 所有图片使用相对路径，放在 `assets/readme/` 目录
- [ ] 动画使用 GIF，SVG 为静态版本
- [ ] SVG viewBox 为 1200 宽度，高度符合类型规范
- [ ] SVG 只使用系统字体，无外部字体引用
- [ ] SVG 未使用 script/foreignObject/外部资源/悬停/大阴影
- [ ] 900px 和 360px 宽度下都测试过
- [ ] 所有图片都有描述目的的 alt 文本
- [ ] 安装命令、链接等可交互内容在 Markdown 正文，不只在图里
- [ ] SVG 自带背景色，明暗主题下都可读
- [ ] 纯 HTML 仅用于对齐和尺寸，无复杂结构

---

**规范维护：糖糖it**
**遵循此规范，让你的 README 在 GitHub 上稳定、美观、专业地展示。**
