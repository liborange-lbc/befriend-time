import { ref, computed } from 'vue'
import type { BacktestResult, IndexDataPoint } from '@/types'
import {
  backtestDeviationStrategy,
  backtestCrossoverStrategy,
  type DeviationStrategyParams,
  type CrossoverStrategyParams,
  defaultDeviationParams,
  defaultCrossoverParams
} from '@/utils/backtest'

export type StrategyType = 'deviation' | 'crossover'

export function useBacktest() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const result = ref<BacktestResult | null>(null)

  // 默认参数
  const deviationParams = ref<DeviationStrategyParams>({ ...defaultDeviationParams })
  const crossoverParams = ref<CrossoverStrategyParams>({ ...defaultCrossoverParams })

  // 运行回测
  const runBacktest = async (
    data: IndexDataPoint[],
    strategyType: StrategyType
  ): Promise<BacktestResult | null> => {
    if (!data || data.length === 0) {
      error.value = '数据为空，无法回测'
      return null
    }

    loading.value = true
    error.value = null

    try {
      let backtestResult: BacktestResult

      if (strategyType === 'deviation') {
        backtestResult = backtestDeviationStrategy(data, deviationParams.value)
      } else {
        backtestResult = backtestCrossoverStrategy(data, crossoverParams.value)
      }

      result.value = backtestResult
      return backtestResult
    } catch (e) {
      error.value = `回测失败: ${e}`
      console.error(e)
      return null
    } finally {
      loading.value = false
    }
  }

  // 清除结果
  const clearResult = () => {
    result.value = null
    error.value = null
  }

  // 设置偏差策略参数
  const setDeviationParams = (params: Partial<DeviationStrategyParams>) => {
    deviationParams.value = { ...deviationParams.value, ...params }
  }

  // 设置穿越策略参数
  const setCrossoverParams = (params: Partial<CrossoverStrategyParams>) => {
    crossoverParams.value = { ...crossoverParams.value, ...params }
  }

  return {
    loading,
    error,
    result,
    deviationParams,
    crossoverParams,
    runBacktest,
    clearResult,
    setDeviationParams,
    setCrossoverParams
  }
}