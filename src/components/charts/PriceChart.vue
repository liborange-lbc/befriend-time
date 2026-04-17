<template>
  <div class="price-chart">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { IndexDataPoint } from '@/types'

const props = defineProps<{
  data: IndexDataPoint[]
  showSmas?: number[]
}>()

const emit = defineEmits<{
  exportSvg: []
}>()

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const defaultSmas = [30, 60, 90]

const getSmaKey = (period: number): keyof IndexDataPoint => `sma${period}` as keyof IndexDataPoint

const initChart = () => {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)

  const dates = props.data.map(d => d.date)
  const closes = props.data.map(d => d.close)

  // 收盘价数据
  const series: echarts.SeriesOption[] = [
    {
      name: '收盘价',
      type: 'line',
      data: closes,
      smooth: true,
      lineStyle: { width: 2 },
      symbol: 'none',
      z: 10
    }
  ]

  // SMA 均线数据
  const smaPeriods = props.showSmas || defaultSmas
  const smaColors = ['#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899']

  smaPeriods.forEach((period, index) => {
    const key = getSmaKey(period)
    const smaData = props.data.map(d => d[key] as number | null)

    series.push({
      name: `SMA${period}`,
      type: 'line',
      data: smaData,
      smooth: true,
      lineStyle: { width: 1, type: 'dashed' as const, color: smaColors[index % smaColors.length] },
      symbol: 'none',
      z: 5
    })
  })

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['收盘价', ...smaPeriods.map(p => `SMA${p}`)],
      top: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false
    },
    yAxis: [
      {
        type: 'value',
        name: '价格',
        position: 'left'
      },
      {
        type: 'value',
        name: '均线',
        position: 'right',
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        start: 0,
        end: 100
      }
    ],
    series
  }

  chart.setOption(option)
}

// 导出 SVG
const exportSvg = () => {
  if (chart) {
    const url = chart.getDataURL({ type: 'svg', pixelRatio: 2, backgroundColor: '#fff' })
    const link = document.createElement('a')
    link.download = 'price-chart.svg'
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
.price-chart {
  width: 100%;
}

.chart-container {
  width: 100%;
  height: 500px;
}
</style>