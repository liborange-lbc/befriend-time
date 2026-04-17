## 为什么

个人投资者需要一个简洁高效的基金指数分析工具，能够追踪指数均值偏差，识别投资机会，并验证投资策略的历史表现。现有工具要么功能过于复杂，要么缺乏均值偏差分析能力，无法满足"均值回归"投资理念的分析需求。

## 变更内容

构建一个纯前端的基金分析平台，具备以下核心能力：

- **指数管理**：录入指数基本信息（名称、代码、区域：中/港/美）
- **数据获取**：通过 GitHub Actions 定时从 Tushare 获取收盘价数据，计算 SMA 均值（30/60/90/180/240/360日）及偏差
- **数据分析**：收盘价趋势分析、均值偏差分析（含历史分布柱状图、当前位置标注）
- **策略回溯**：支持均值偏差策略和均值穿越策略的历史回测
- **静态部署**：Vue 3 + Vite + ECharts，GitHub Pages 部署，JSON 文件存储数据

## 功能 (Capabilities)

### 新增功能

- `index-management`: 指数录入与管理功能，包括指数的增删改查，支持中/港/美三区域分类
- `data-pipeline`: 数据获取与处理管道，通过 GitHub Actions 定时获取 Tushare 数据，计算多周期 SMA 均值及绝对偏差，JSON 文件存储
- `price-analysis`: 收盘价趋势分析功能，包括价格走势图、均线叠加展示、双Y轴图表、时间范围选择（快选+拖拽）
- `deviation-analysis`: 均值偏差分析功能，包括偏差历史趋势、多周期偏差分布柱状图（20区间）、当前位置标注
- `strategy-backtest`: 策略回溯功能，支持均值偏差策略（阈值触发）和均值穿越策略（均线突破），计算收益、风险、交易全量指标，买卖信号可视化
- `strategy-management`: 策略保存与管理功能，支持策略命名、参数保存、编辑删除、快速复用
- `dashboard`: 首页仪表盘，展示策略信号、数据更新状态、偏差监控、快捷入口

### 修改功能

无（全新项目）

## 影响

- **新建项目**：仓库名 `befriend-time`，GitHub Pages 静态部署
- **技术栈**：Vue 3 + Vite + ECharts + TypeScript
- **外部依赖**：Tushare API（需配置 API Key 到 GitHub Secrets）
- **数据存储**：JSON 文件存储于仓库中
  - `data/indices/{code}-{year}.json`：指数历史数据（收盘价、均值、偏差）
  - `data/config/indices.json`：指数配置
  - `data/config/strategies.json`：策略配置
  - `data/status/update-log.json`：数据更新日志