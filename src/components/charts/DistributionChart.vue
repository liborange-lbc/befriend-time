<template>
  <div class="distribution-chart">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { IndexDataPoint } from '@/types'

const props = defineProps<{
  data: IndexDataPoint[]
  period: number
}>()

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

// 计算偏差分布（20个区间）
const calculateDistribution = (data: IndexDataPoint[], period: number) => {
  const key = `deviation${period}` as keyof IndexDataPoint
  const deviations = data
    .map(d => d[key])
    .filter((v): v is number => v !== null && v !== undefined)

  if (deviations.length === 0) {
    return { ranges: [], counts: [] }
  }

  const min = Math.floor(Math.min(...deviations))
  const max = Math.ceil(Math.max(...deviations))
  const step = (max - min) / 20

  const ranges: string[] = []
  const counts: number[] = []

  for (let i = 0; i < 20; i++) {
    const rangeStart = min + i * step
    const rangeEnd = min + (i + 1) * step
    ranges.push(`${rangeStart.toFixed(0)}~${rangeEnd.toFixed(0)}`)

    const count = deviations.filter(d => d >= rangeStart && d < rangeEnd).length
    counts.push(count)
  }

  return { ranges, counts }
}

// 获取当前偏差在分布中的位置
const getCurrentPosition = (data: IndexDataPoint[], period: number): { value: number; percentile: number } | null => {
  const key = `deviation${period}` as keyof IndexDataPoint
  const current = data[data.length - 1]
  if (!current || current[key] === null) return null

  const currentValue = current[key] as number

  const deviations = data
    .map(d => d[key])
    .filter((v): v is number => v !== null && v !== undefined)
    .sort((a, b) => a - b)

  const percentile = (deviations.filter(d => d <= currentValue).length / deviations.length) * 100

  return { value: currentValue, percentile }
}

const initChart = () => {
  if (!chartRef.value || !props.data.length) return

  chart = echarts.init(chartRef.value)

  const { ranges, counts } = calculateDistribution(props.data, props.period)
  const currentPos = getCurrentPosition(props.data, props.period)

  // 计算颜色（根据偏差位置）
  const maxCount = Math.max(...counts)

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const p = params[0]
        return `${p.name}<br/>数量: ${p.value}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ranges,
      axisLabel: {
        rotate: 45,
        interval: 2,
        fontSize: 10
      }
    },
    yAxis: {
      type: 'value',
      name: '天数'
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      }
    ],
    series: [
      {
        name: '分布',
        type: 'bar',
        data: counts.map((count, index) => {
          // 标记当前值所在的区间
          if (currentPos && index < counts.length - 1) {
            const { ranges: r } = calculateDistribution(props.data, props.period)
            const [start, end] = r[index].split('~').map(Number)
            if (currentPos.value >= start && currentPos.value < end) {
              return {
                value: count,
                itemStyle: { color: '#ef4444' }
              }
            }
          }
          return count
        }),
        label: {
          show: false
        }
      }
    ],
    // 添加当前值标注
    graphic: currentPos ? [
      {
        type: 'text',
        left: 'center',
        top: 10,
        style: {
          text: `当前偏差: ${currentPos.value.toFixed(2)} (位于 ${currentPos.percentile.toFixed(1)}% 分位)`,
          fontSize: 14,
          fontWeight: 'bold',
          fill: '#1e293b'
        }
      }
    ] : []
  }

  chart.setOption(option)
}

// 导出 SVG
const exportSvg = () => {
  if (chart) {
    const url = chart.getDataURL({ type: 'svg', pixelRatio: 2, backgroundColor: '#fff' })
    const link = document.createElement('a')
    link.download = 'distribution-chart.svg'
    link.href = url
    link.click()
  }
}

defineExpose({ exportSvg })

watch(() => props.data, () => {
  nextTick(() => {
    initChart()
  })
}, { deep: true })

watch(() => props.period, () => {
  nextTick(() => {
    initChart()
  })
})

onMounted(() => {
  nextTick(() => {
    initChart()
  })

  window.addEventListener('resize', () => {
    chart?.resize()
  })
})

onUnmounted(() => {
  chart?.dispose()
})
</script>

<style scoped>
.distribution-chart {
  width: 100%;
}

.chart-container {
  width: 100%;
  height: 350px;
}
</style>