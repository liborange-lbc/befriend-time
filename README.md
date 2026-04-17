# BefriendTime 基金分析平台

个人投资者使用的基金指数分析工具，支持均值偏差分析和策略回测。

## 快速开始

### 1. 创建 GitHub 仓库

```bash
# 在 GitHub 上创建新仓库，命名为 befriend-time
# 然后在本地执行：
git remote add origin https://github.com/YOUR_USERNAME/befriend-time.git
git branch -M main
git push -u origin main
```

### 2. 配置 GitHub Pages

1. 进入仓库设置 (Settings) → Pages
2. Source 选择 "GitHub Actions"
3. 推送代码后会自动部署

### 3. 配置 Tushare API（可选）

如需自动获取数据：

1. 在仓库 Settings → Secrets and variables → Actions
2. 添加 secret: `TUSHARE_TOKEN`
3. 值为你的 Tushare API token

## 本地开发

```bash
npm install
npm run dev
```

## 功能

- **指数管理** - 查看已配置的指数
- **数据分析** - 查看指数历史走势和均值偏差
- **策略回测** - 测试均值偏差/穿越策略
- **策略管理** - 保存常用策略

## 目录结构

```
├── src/                 # 前端源码
├── public/data/        # 数据配置
├── scripts/            # Python 数据获取脚本
└── .github/workflows/ # GitHub Actions
```