## 上下文

个人投资分析平台，无后端，使用 GitHub Pages 静态部署 + GitHub Actions 定时数据获取。数据源为 Tushare API，所有数据以 JSON 文件形式存储在仓库中。

**技术约束：**
- 纯前端应用，无后端服务
- 数据存储仅限 JSON 文件
- API Key 存储于 GitHub Secrets
- 支持中/港/美三区域指数，需处理时区差异

**用户：**个人使用，单人操作

## 目标 / 非目标

**目标：**
- 提供指数均值偏差分析能力，支持均值回归投资理念
- 支持历史策略回溯，验证投资策略有效性
- 纯静态部署，零运维成本
- 科技感界面，信息密集但不拥挤

**非目标：**
- 不支持实盘交易
- 不支持多用户/权限系统
- 不支持实时盘中数据（仅收盘后更新）
- 不支持复杂数据库或后端服务

## 决策

### 1. 技术栈选择：Vue 3 + Vite + ECharts

**理由：**
- Vue 3 组合式 API 适合数据驱动应用
- Vite 构建快速，开发体验好
- ECharts 原生支持双Y轴、dataZoom 拖拽、markPoint 信号标注
- 中文文档完善，问题易查

**替代方案：**
- React + Recharts：ECharts 对双Y轴和 dataZoom 支持更好
- 纯原生：开发效率低，图表库功能重复造轮子

### 2. 数据存储：JSON 文件 + 按年份分片

**方案：**
```
data/
├── indices/
│   ├── 000300.SH-2024.json  # 沪深300 2024年数据
│   ├── 000300.SH-2023.json  # 沪深300 2023年数据
│   └── ...
├── config/
│   ├── indices.json         # 指数配置列表
│   └── strategies.json      # 策略配置列表
└── status/
    └── update-log.json      # 更新日志与状态
```

**理由：**
- 按年份分片避免单个文件过大
- 历史数据只读，无需频繁修改
- 配置文件独立，易于管理

**替代方案：**
- 单文件存储：数据量大时加载慢
- SQLite：需要后端，违背静态部署原则
- IndexedDB：数据无法跨设备同步

### 3. 数据获取：GitHub Actions 分区域定时

**方案：**
- A股：北京时间 17:00（收盘后）
- 港股：北京时间 18:00（收盘后）
- 美股：北京时间 06:00（次日收盘后）
- 失败重试：30分钟间隔，最多10次

**理由：**
- 分区域定时避免一次性请求过多
- 重试机制保证数据完整性
- 近7日覆盖更新防止遗漏

### 4. 时间选择：ECharts dataZoom 内置拖拽

**理由：**
- 无需额外日期选择器库
- 交互体验流畅
- 与图表无缝集成

**替代方案：**
- 外部日期选择器 + 联动：增加复杂度，交互割裂

### 5. 图表导出：SVG 格式

**理由：**
- 矢量格式，无损缩放
- 文件小，适合分享
- ECharts 原生支持

**替代方案：**
- PNG：无法无损缩放
- 两者都支持：增加选项复杂度，个人使用不需要

## 架构设计

### 前端架构

```
src/
├── views/                    # 页面组件
│   ├── Dashboard.vue         # 首页仪表盘
│   ├── IndexManagement.vue   # 指数管理
│   ├── DataAnalysis.vue      # 数据分析
│   ├── StrategyBacktest.vue  # 策略回溯
│   └── StrategyManagement.vue# 策略管理
├── components/               # 通用组件
│   ├── charts/               # 图表组件
│   │   ├── PriceChart.vue    # 收盘价图表
│   │   ├── DeviationChart.vue# 偏差趋势图
│   │   └── DistributionChart.vue# 分布柱状图
│   ├── TimeSelector.vue      # 时间选择器
│   └── StrategyForm.vue      # 策略配置表单
├── composables/              # 组合式函数
│   ├── useIndices.ts         # 指数数据
│   ├── useStrategies.ts      # 策略数据
│   ├── useBacktest.ts        # 回测计算
│   └── useDataFetch.ts       # 数据获取
├── stores/                   # 状态管理
│   └── main.ts
├── utils/                    # 工具函数
│   ├── sma.ts                # SMA 计算
│   ├── deviation.ts          # 偏差计算
│   └── backtest.ts           # 回测引擎
└── types/                    # 类型定义
    └── index.ts
```

### 数据结构

**指数配置 (indices.json)：**
```json
{
  "indices": [
    {
      "id": "000300.SH",
      "name": "沪深300",
      "code": "000300.SH",
      "region": "CN",
      "createdAt": "2024-01-01",
      "updatedAt": "2024-01-15"
    }
  ]
}
```

**指数数据 ({code}-{year}.json)：**
```json
{
  "code": "000300.SH",
  "year": 2024,
  "data": [
    {
      "date": "2024-01-02",
      "close": 3500.12,
      "sma30": 3450.50,
      "sma60": 3400.80,
      "sma90": 3380.20,
      "sma180": 3350.00,
      "sma240": 3320.50,
      "sma360": 3300.00,
      "deviation30": 49.62,
      "deviation60": 99.32,
      "deviation90": 119.92,
      "deviation180": 150.12,
      "deviation240": 179.62,
      "deviation360": 200.12
    }
  ]
}
```

**策略配置 (strategies.json)：**
```json
{
  "strategies": [
    {
      "id": "strategy-001",
      "name": "激进均值回归",
      "type": "deviation",
      "params": {
        "smaPeriod": 60,
        "buyThreshold": -5,
        "sellThreshold": 5,
        "buyRatio": 100,
        "sellRatio": 100,
        "initialCapital": 100000
      },
      "createdAt": "2024-01-01"
    }
  ]
}
```

**更新日志 (update-log.json)：**
```json
{
  "logs": [
    {
      "region": "CN",
      "timestamp": "2024-01-15T17:00:00Z",
      "status": "success",
      "indicesUpdated": 5,
      "message": ""
    },
    {
      "region": "US",
      "timestamp": "2024-01-15T06:00:00Z",
      "status": "failed",
      "indicesUpdated": 0,
      "message": "API rate limit exceeded",
      "retryCount": 3
    }
  ]
}
```

## 风险 / 权衡

### 风险1：Tushare API 限流
→ **缓解：** GitHub Actions 内置重试机制，30分钟间隔最多10次；使用近7日覆盖更新减少历史数据请求

### 风险2：JSON 文件体积过大
→ **缓解：** 按年份分片存储；前端按需加载当年数据；历史年份数据可选加载

### 风险3：GitHub Pages 静态限制
→ **缓解：** 单文件体积控制在合理范围；避免频繁大型 JSON 更新

### 风险4：时区处理复杂
→ **缓解：** 统一使用 UTC 存储，前端根据指数区域显示本地时间

### 权衡1：无实时数据
→ 只能进行收盘后分析，无法盘中监控

### 权衡2：无用户系统
→ 配置和策略通过 JSON 文件管理，换设备需手动迁移

## 迁移计划

无需迁移（全新项目）。

## 待定问题

无。