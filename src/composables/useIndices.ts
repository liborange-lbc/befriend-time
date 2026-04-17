import { ref, computed } from 'vue'
import type { Index, IndexConfig, Region } from '@/types'

export function useIndices() {
  const indices = ref<Index[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 加载指数数据 - 从服务器文件加载
  const loadIndices = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/data/config/indices.json')
      if (!response.ok) {
        indices.value = []
        return
      }
      const data: IndexConfig = await response.json()
      indices.value = data.indices || []
    } catch (e) {
      error.value = '加载指数数据失败'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  // 获取区域标签
  const getRegionLabel = (region: Region): string => {
    const labels: Record<Region, string> = {
      CN: 'A股',
      HK: '港股',
      US: '美股'
    }
    return labels[region]
  }

  // 按区域筛选
  const indicesByRegion = computed(() => {
    const grouped: Record<Region, Index[]> = {
      CN: [],
      HK: [],
      US: []
    }
    indices.value.forEach(index => {
      grouped[index.region].push(index)
    })
    return grouped
  })

  // 根据ID获取指数
  const getIndexById = (id: string): Index | undefined => {
    return indices.value.find(i => i.id === id)
  }

  // 根据代码获取指数
  const getIndexByCode = (code: string): Index | undefined => {
    return indices.value.find(i => i.code === code)
  }

  return {
    indices,
    loading,
    error,
    loadIndices,
    getRegionLabel,
    indicesByRegion,
    getIndexById,
    getIndexByCode
  }
}