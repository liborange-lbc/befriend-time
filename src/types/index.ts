// 指数相关类型定义

export type Region = 'CN' | 'HK' | 'US'
export type DataSource = 'tushare' | 'csindex' | 'yfinance'

export interface Index {
  id: string
  name: string
  code: string
  region: Region
  source?: DataSource
  createdAt: string
  updatedAt: string
}

export interface IndexConfig {
  indices: Index[]
}

export interface IndexDataPoint {
  date: string
  close: number
  sma30: number | null
  sma60: number | null
  sma90: number | null
  sma180: number | null
  sma240: number | null
  sma360: number | null
  deviation30: number | null
  deviation60: number | null
  deviation90: number | null
  deviation180: number | null
  deviation240: number | null
  deviation360: number | null
}

export interface IndexData {
  code: string
  year: number
  data: IndexDataPoint[]
}

// 策略相关类型定义

export type StrategyType = 'deviation' | 'crossover'

export interface DeviationParams {
  smaPeriod: number
  buyThreshold: number
  sellThreshold: number
  buyRatio: number
  sellRatio: number
  initialCapital: number
}

export interface CrossoverParams {
  smaPeriod: number
  ratio: number
  initialCapital: number
}

export type StrategyParams = DeviationParams | CrossoverParams

export interface Strategy {
  id: string
  name: string
  type: StrategyType
  params: StrategyParams
  createdAt: string
}

export interface StrategyConfig {
  strategies: Strategy[]
}

// 回测结果相关类型定义

export interface Trade {
  date: string
  type: 'buy' | 'sell'
  price: number
  shares: number
  amount: number
  commission: number
}

export interface TradeMetrics {
  totalTrades: number
  winningTrades: number
  losingTrades: number
  winRate: number
  avgHoldingDays: number
  profitLossRatio: number
}

export interface BacktestResult {
  strategyId: string
  indexCode: string
  startDate: string
  endDate: string
  initialCapital: number
  finalCapital: number
  totalReturn: number
  annualizedReturn: number
  totalProfitLoss: number
  maxDrawdown: number
  maxDrawdownDuration: number
  volatility: number
  sharpeRatio: number
  benchmarkReturn: number
  benchmarkFinalCapital: number
  trades: Trade[]
  metrics: TradeMetrics
}

// 更新日志相关类型定义

export type UpdateStatus = 'success' | 'failed' | 'retrying'

export interface UpdateLog {
  region: Region
  timestamp: string
  status: UpdateStatus
  indicesUpdated: number
  message: string
  retryCount?: number
}

export interface UpdateLogConfig {
  logs: UpdateLog[]
}

// 图表相关类型

export interface ChartDataItem {
  date: string
  value: number
}

export interface DeviationDistributionItem {
  range: string
  count: number
  percentage: number
}

export interface SignalItem {
  date: string
  type: 'buy' | 'sell'
  price: number
  deviation: number
}