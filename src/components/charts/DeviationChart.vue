<template>
  <div class="deviation-chart">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { IndexDataPoint } from '@/types'

const props = defineProps<{
  data: IndexDataPoint[]
  showPeriods?: number[]
}>()

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const defaultPeriods = [30, 60, 90]

const getDeviationKey = (period: number): keyof IndexDataPoint => `deviation${period}` as keyof IndexDataPoint

const initChart = () => {
  if (!chartRef.value || !props.data.length) return

  chart = echarts.init(chartRef.value)

  const dates = props.data.map(d => d.date)
  const periods = props.showPeriods || defaultPeriods

  // 创建偏差数据系列
  const series: echarts.SeriesOption[] = periods.map((period, index) => {
    const key = getDeviationKey(period)
    const deviationData = props.data.map(d => d[key] as number | null)

    return {
      name: `偏差${period}`,
      type: 'line',
      data: deviationData,
      smooth: true,
      lineStyle: { width: 1.5 },
      symbol: 'none',
      z: index + 1
    }
  })

  // 获取最新的偏差值用于标注
  const lastPoint = props.data[props.data.length - 1]
  const markPoints: any[] = periods.map(period => {
    const key = getDeviationKey(period)
    const value = lastPoint[key] as number | null
    if (value === null) return null

    return {
      name: `SMA${period}`,
      coord: [dates.length - 1, value],
      value: value.toFixed(2),
      label: {
        show: true,
        position: 'top',
        formatter: `{b}: {c}`
      }
    }
  }).filter(Boolean)

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params: any) => {
        let result = params[0].axisValueLabel + '<br/>'
        params.forEach((p: any) => {
          if (p.value !== null) {
            result += `${p.seriesName}: ${p.value.toFixed(2)}<br/>`
          }
        })
        return result
      }
    },
    legend: {
      data: periods.map(p => `偏差${p}`),
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
    yAxis: {
      type: 'value',
      name: '偏差值'
    },
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
    series: series as any
  }

  if (markPoints.length > 0) {
    option.series = series.map((s: any, i: number) => ({
      ...s,
      markPoint: {
        data: [markPoints[i]].filter(Boolean)
      }
    }))
  }

  chart.setOption(option)
}

// 导出 SVG
const exportSvg = () => {
  if (chart) {
    const url = chart.getDataURL({ type: 'svg', pixelRatio: 2, backgroundColor: '#fff' })
    const link = document.createElement('a')
    link.download = 'deviation-chart.svg'
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

watch(() => props.showPeriods, () => {
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
.deviation-chart {
  width: 100%;
}

.chart-container {
  width: 100%;
  height: 400px;
}
</style>