import { ref, computed } from 'vue'
import type { IndexData, IndexDataPoint } from '@/types'

const SMA_PERIODS = [30, 60, 90, 180, 240, 360]

export function useDataFetch() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const dataCache = ref<Map<string, IndexDataPoint[]>>(new Map())

  // 获取可用年份
  const getAvailableYears = (code: string): number[] => {
    // 根据当前年份和历史数据推断可用年份
    const currentYear = new Date().getFullYear()
    const years: number[] = []
    for (let year = currentYear; year >= currentYear - 10; year--) {
      years.push(year)
    }
    return years
  }

  // 按年份加载数据
  const loadDataByYear = async (code: string, year: number): Promise<IndexDataPoint[]> => {
    const cacheKey = `${code}-${year}`

    // 检查缓存
    if (dataCache.value.has(cacheKey)) {
      return dataCache.value.get(cacheKey) as IndexDataPoint[]
    }

    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/data/indices/${code}-${year}.json`)

      if (!response.ok) {
        // 文件不存在，返回空数组
        return []
      }

      const data: IndexData = await response.json()
      const points = data.data || []

      // 缓存数据
      dataCache.value.set(cacheKey, points)

      return points
    } catch (e) {
      error.value = `加载数据失败: ${code}-${year}`
      console.error(e)
      return []
    } finally {
      loading.value = false
    }
  }

  // 加载多个年份的数据
  const loadDataByYears = async (code: string, years: number[]): Promise<IndexDataPoint[]> => {
    const allData: IndexDataPoint[] = []

    for (const year of years) {
      const yearData = await loadDataByYear(code, year)
      allData.push(...yearData)
    }

    // 按日期排序
    allData.sort((a, b) => a.date.localeCompare(b.date))

    return allData
  }

  // 获取最近N年的年份列表
  const getYearsForRange = (yearsBack: number): number[] => {
    const currentYear = new Date().getFullYear()
    const years: number[] = []
    for (let i = 0; i < yearsBack; i++) {
      years.push(currentYear - i)
    }
    return years
  }

  // 获取最新数据点
  const getLatestDataPoint = (data: IndexDataPoint[]): IndexDataPoint | null => {
    if (!data || data.length === 0) return null
    return data[data.length - 1]
  }

  // 计算偏差统计
  const calculateDeviationStats = (data: IndexDataPoint[], period: number): {
    min: number
    max: number
    mean: number
    current: number
    percentiles: { p25: number; p50: number; p75: number }
  } => {
    const key = `deviation${period}` as keyof IndexDataPoint
    const deviations = data
      .map(d => d[key])
      .filter((v): v is number => v !== null && v !== undefined)

    if (deviations.length === 0) {
      return { min: 0, max: 0, mean: 0, current: 0, percentiles: { p25: 0, p50: 0, p75: 0 } }
    }

    const sorted = [...deviations].sort((a, b) => a - b)
    const sum = sorted.reduce((a, b) => a + b, 0)

    return {
      min: sorted[0],
      max: sorted[sorted.length - 1],
      mean: sum / sorted.length,
      current: deviations[deviations.length - 1],
      percentiles: {
        p25: sorted[Math.floor(sorted.length * 0.25)],
        p50: sorted[Math.floor(sorted.length * 0.5)],
        p75: sorted[Math.floor(sorted.length * 0.75)]
      }
    }
  }

  // 清除缓存
  const clearCache = () => {
    dataCache.value.clear()
  }

  return {
    loading,
    error,
    getAvailableYears,
    loadDataByYear,
    loadDataByYears,
    getYearsForRange,
    getLatestDataPoint,
    calculateDeviationStats,
    clearCache
  }
}