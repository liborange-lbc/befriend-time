/**
 * 回测引擎 - 策略回测核心逻辑
 */

import type { IndexDataPoint, Trade, TradeMetrics, BacktestResult, StrategyParams } from '@/types'

// 策略类型
export type StrategyType = 'deviation' | 'crossover'

// 策略参数
export interface DeviationStrategyParams {
  smaPeriod: number
  buyThreshold: number
  sellThreshold: number
  buyRatio: number
  sellRatio: number
  initialCapital: number
}

export interface CrossoverStrategyParams {
  smaPeriod: number
  ratio: number
  initialCapital: number
}

// 均值偏差策略回测
export function backtestDeviationStrategy(
  data: IndexDataPoint[],
  params: DeviationStrategyParams
): BacktestResult {
  const { smaPeriod, buyThreshold, sellThreshold, buyRatio, sellRatio, initialCapital } = params

  const deviationKey = `deviation${smaPeriod}` as keyof IndexDataPoint

  let cash = initialCapital
  let shares = 0
  const trades: Trade[] = []
  const prices: number[] = []

  // 记录每日资产
  const equityCurve: number[] = []

  for (let i = 0; i < data.length; i++) {
    const point = data[i]
    const price = point.close
    const deviation = point[deviationKey] as number | null

    prices.push(price)

    if (deviation === null) {
      equityCurve.push(cash + shares * price)
      continue
    }

    // 买入信号：偏差低于买入阈值
    if (deviation <= buyThreshold && cash > 0) {
      const buyAmount = cash * (buyRatio / 100)
      const commission = buyAmount * 0.001 // 假设千分之一手续费
      const actualAmount = buyAmount - commission
      const boughtShares = actualAmount / price

      shares += boughtShares
      cash -= buyAmount

      trades.push({
        date: point.date,
        type: 'buy',
        price,
        shares: boughtShares,
        amount: buyAmount,
        commission
      })
    }

    // 卖出信号：偏差高于卖出阈值
    if (deviation >= sellThreshold && shares > 0) {
      const sellShares = shares * (sellRatio / 100)
      const sellAmount = sellShares * price
      const commission = sellAmount * 0.001
      const actualAmount = sellAmount - commission

      cash += actualAmount
      shares -= sellShares

      trades.push({
        date: point.date,
        type: 'sell',
        price,
        shares: sellShares,
        amount: sellAmount,
        commission
      })
    }

    equityCurve.push(cash + shares * price)
  }

  // 计算最终资产
  const finalPrice = data[data.length - 1].close
  const finalCapital = cash + shares * finalPrice
  const totalReturn = (finalCapital - initialCapital) / initialCapital

  // 计算指标
  const metrics = calculateMetrics(trades, data)
  const maxDrawdown = calculateMaxDrawdown(equityCurve)
  const maxDrawdownDuration = calculateMaxDrawdownDuration(equityCurve, initialCapital)
  const volatility = calculateVolatility(prices)
  const sharpeRatio = calculateSharpeRatio(prices, totalReturn)

  // 基准策略：买入持有
  const firstPrice = data[0].close
  const benchmarkReturn = (finalPrice - firstPrice) / firstPrice
  const benchmarkFinalCapital = initialCapital * (1 + benchmarkReturn)

  return {
    strategyId: 'deviation',
    indexCode: data[0]?.date || '',
    startDate: data[0]?.date || '',
    endDate: data[data.length - 1]?.date || '',
    initialCapital,
    finalCapital,
    totalReturn,
    annualizedReturn: calculateAnnualizedReturn(totalReturn, data.length),
    totalProfitLoss: finalCapital - initialCapital,
    maxDrawdown,
    maxDrawdownDuration,
    volatility,
    sharpeRatio,
    benchmarkReturn,
    benchmarkFinalCapital,
    trades,
    metrics
  }
}

// 均值穿越策略回测
export function backtestCrossoverStrategy(
  data: IndexDataPoint[],
  params: CrossoverStrategyParams
): BacktestResult {
  const { smaPeriod, ratio, initialCapital } = params

  const smaKey = `sma${smaPeriod}` as keyof IndexDataPoint

  let cash = initialCapital
  let shares = 0
  const trades: Trade[] = []
  const prices: number[] = []
  let lastAbove = false

  const equityCurve: number[] = []

  for (let i = 0; i < data.length; i++) {
    const point = data[i]
    const price = point.close
    const sma = point[smaKey] as number | null

    prices.push(price)

    if (sma === null) {
      equityCurve.push(cash + shares * price)
      continue
    }

    const isAbove = price > sma

    // 金叉买入
    if (isAbove && !lastAbove && cash > 0) {
      const buyAmount = cash * (ratio / 100)
      const commission = buyAmount * 0.001
      const actualAmount = buyAmount - commission
      const boughtShares = actualAmount / price

      shares += boughtShares
      cash -= buyAmount

      trades.push({
        date: point.date,
        type: 'buy',
        price,
        shares: boughtShares,
        amount: buyAmount,
        commission
      })
    }

    // 死叉卖出
    if (!isAbove && lastAbove && shares > 0) {
      const sellShares = shares * (ratio / 100)
      const sellAmount = sellShares * price
      const commission = sellAmount * 0.001
      const actualAmount = sellAmount - commission

      cash += actualAmount
      shares -= sellShares

      trades.push({
        date: point.date,
        type: 'sell',
        price,
        shares: sellShares,
        amount: sellAmount,
        commission
      })
    }

    lastAbove = isAbove
    equityCurve.push(cash + shares * price)
  }

  const finalPrice = data[data.length - 1].close
  const finalCapital = cash + shares * finalPrice
  const totalReturn = (finalCapital - initialCapital) / initialCapital

  const metrics = calculateMetrics(trades, data)
  const maxDrawdown = calculateMaxDrawdown(equityCurve)
  const maxDrawdownDuration = calculateMaxDrawdownDuration(equityCurve, initialCapital)
  const volatility = calculateVolatility(prices)
  const sharpeRatio = calculateSharpeRatio(prices, totalReturn)

  const firstPrice = data[0].close
  const benchmarkReturn = (finalPrice - firstPrice) / firstPrice
  const benchmarkFinalCapital = initialCapital * (1 + benchmarkReturn)

  return {
    strategyId: 'crossover',
    indexCode: data[0]?.date || '',
    startDate: data[0]?.date || '',
    endDate: data[data.length - 1]?.date || '',
    initialCapital,
    finalCapital,
    totalReturn,
    annualizedReturn: calculateAnnualizedReturn(totalReturn, data.length),
    totalProfitLoss: finalCapital - initialCapital,
    maxDrawdown,
    maxDrawdownDuration,
    volatility,
    sharpeRatio,
    benchmarkReturn,
    benchmarkFinalCapital,
    trades,
    metrics
  }
}

// 计算交易指标
function calculateMetrics(trades: Trade[], data: IndexDataPoint[]): TradeMetrics {
  const buyTrades = trades.filter(t => t.type === 'buy')
  const sellTrades = trades.filter(t => t.type === 'sell')

  const winningTrades = sellTrades.filter((sell, i) => {
    const buy = buyTrades[i]
    return buy && sell.price > buy.price
  }).length

  const losingTrades = sellTrades.filter((sell, i) => {
    const buy = buyTrades[i]
    return buy && sell.price <= buy.price
  }).length

  // 计算平均持仓天数
  let totalHoldingDays = 0
  let holdingStart: string | null = null

  for (const trade of trades) {
    if (trade.type === 'buy') {
      holdingStart = trade.date
    } else if (trade.type === 'sell' && holdingStart) {
      const start = new Date(holdingStart)
      const end = new Date(trade.date)
      const days = Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
      totalHoldingDays += days
      holdingStart = null
    }
  }

  const avgHoldingDays = sellTrades.length > 0 ? totalHoldingDays / sellTrades.length : 0

  // 计算盈亏比
  const avgWin = winningTrades > 0 ? 1000 : 0 // 简化计算
  const avgLoss = losingTrades > 0 ? 1000 : 0

  return {
    totalTrades: trades.length,
    winningTrades,
    losingTrades,
    winRate: trades.length > 0 ? winningTrades / (trades.length / 2) * 100 : 0,
    avgHoldingDays: Math.round(avgHoldingDays),
    profitLossRatio: avgLoss > 0 ? avgWin / avgLoss : 0
  }
}

// 计算最大回撤
function calculateMaxDrawdown(equityCurve: number[]): number {
  let maxEquity = equityCurve[0]
  let maxDrawdown = 0

  for (const equity of equityCurve) {
    if (equity > maxEquity) {
      maxEquity = equity
    }
    const drawdown = (maxEquity - equity) / maxEquity
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown
    }
  }

  return maxDrawdown * 100
}

// 计算最大回撤持续时间
function calculateMaxDrawdownDuration(equityCurve: number[], initialCapital: number): number {
  let maxEquity = equityCurve[0]
  let inDrawdown = false
  let drawdownStart = 0
  let maxDuration = 0

  for (let i = 0; i < equityCurve.length; i++) {
    if (equityCurve[i] > maxEquity) {
      maxEquity = equityCurve[i]
      if (inDrawdown) {
        const duration = i - drawdownStart
        if (duration > maxDuration) {
          maxDuration = duration
        }
        inDrawdown = false
      }
    } else if (!inDrawdown && equityCurve[i] < maxEquity * 0.95) {
      inDrawdown = true
      drawdownStart = i
    }
  }

  return maxDuration
}

// 计算波动率
function calculateVolatility(prices: number[]): number {
  if (prices.length < 2) return 0

  const returns: number[] = []
  for (let i = 1; i < prices.length; i++) {
    returns.push((prices[i] - prices[i - 1]) / prices[i - 1])
  }

  const mean = returns.reduce((a, b) => a + b, 0) / returns.length
  const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length

  return Math.sqrt(variance) * Math.sqrt(252) * 100 // 年化波动率
}

// 计算夏普比率
function calculateSharpeRatio(prices: number[], totalReturn: number): number {
  const volatility = calculateVolatility(prices)
  if (volatility === 0) return 0

  const riskFreeRate = 0.03 // 假设无风险利率3%
  return (totalReturn - riskFreeRate) / (volatility / 100)
}

// 计算年化收益率
function calculateAnnualizedReturn(totalReturn: number, days: number): number {
  const years = days / 252 // 假设252个交易日
  return (Math.pow(1 + totalReturn, 1 / years) - 1) * 100
}

// 默认策略参数
export const defaultDeviationParams: DeviationStrategyParams = {
  smaPeriod: 60,
  buyThreshold: -5,
  sellThreshold: 5,
  buyRatio: 100,
  sellRatio: 100,
  initialCapital: 100000
}

export const defaultCrossoverParams: CrossoverStrategyParams = {
  smaPeriod: 60,
  ratio: 100,
  initialCapital: 100000
}