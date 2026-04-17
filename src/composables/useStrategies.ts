import { ref, computed } from 'vue'
import type { Strategy, StrategyConfig, StrategyType, StrategyParams } from '@/types'

const STORAGE_KEY = 'befriend-time-strategies'

export function useStrategies() {
  const strategies = ref<Strategy[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 默认策略参数
  const defaultDeviationParams: StrategyParams = {
    smaPeriod: 60,
    buyThreshold: -5,
    sellThreshold: 5,
    buyRatio: 100,
    sellRatio: 100,
    initialCapital: 100000
  }

  const defaultCrossoverParams: StrategyParams = {
    smaPeriod: 60,
    ratio: 100,
    initialCapital: 100000
  }

  // 加载策略
  const loadStrategies = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/data/config/strategies.json')
      if (!response.ok) {
        strategies.value = []
        saveToStorage({ strategies: [] })
        return
      }
      const data: StrategyConfig = await response.json()
      strategies.value = data.strategies || []
      saveToStorage(data)
    } catch (e) {
      // 尝试从 localStorage 加载
      const stored = loadFromStorage()
      if (stored) {
        strategies.value = stored.strategies || []
      }
    } finally {
      loading.value = false
    }
  }

  // 保存到本地存储
  const saveToStorage = (data: StrategyConfig) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }

  // 从本地存储加载
  const loadFromStorage = (): StrategyConfig | null => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        return JSON.parse(stored)
      } catch {
        return null
      }
    }
    return null
  }

  // 获取策略类型标签
  const getTypeLabel = (type: StrategyType): string => {
    return type === 'deviation' ? '均值偏差' : '均值穿越'
  }

  // 添加策略
  const addStrategy = (strategy: Omit<Strategy, 'id' | 'createdAt'>) => {
    const newStrategy: Strategy = {
      ...strategy,
      id: `str-${Date.now()}`,
      createdAt: new Date().toISOString().split('T')[0]
    }
    strategies.value.push(newStrategy)
    saveToStorage({ strategies: strategies.value })
    return newStrategy
  }

  // 更新策略
  const updateStrategy = (id: string, updates: Partial<Strategy>) => {
    const strategy = strategies.value.find(s => s.id === id)
    if (strategy) {
      Object.assign(strategy, updates)
      saveToStorage({ strategies: strategies.value })
      return true
    }
    return false
  }

  // 删除策略
  const deleteStrategy = (id: string) => {
    const index = strategies.value.findIndex(s => s.id === id)
    if (index !== -1) {
      strategies.value.splice(index, 1)
      saveToStorage({ strategies: strategies.value })
      return true
    }
    return false
  }

  // 根据ID获取策略
  const getStrategyById = (id: string): Strategy | undefined => {
    return strategies.value.find(s => s.id === id)
  }

  // 获取默认参数
  const getDefaultParams = (type: StrategyType): StrategyParams => {
    return type === 'deviation'
      ? { ...defaultDeviationParams }
      : { ...defaultCrossoverParams }
  }

  return {
    strategies,
    loading,
    error,
    loadStrategies,
    getTypeLabel,
    addStrategy,
    updateStrategy,
    deleteStrategy,
    getStrategyById,
    getDefaultParams
  }
}