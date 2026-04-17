<template>
  <div class="data-analysis">
    <div class="page-header">
      <h1>数据分析</h1>
    </div>

    <!-- 指数选择器 -->
    <div class="controls">
      <select v-model="selectedIndexCode" class="select" @change="loadData">
        <option value="">请选择指数</option>
        <option v-for="idx in indices" :key="idx.id" :value="idx.code">
          {{ idx.name }} ({{ idx.code }})
        </option>
      </select>

      <!-- 时间快选 -->
      <div class="time-selector">
        <button
          v-for="year in [1, 3, 5, 10]"
          :key="year"
          class="btn btn-sm"
          :class="selectedYears === year ? 'btn-primary' : 'btn-secondary'"
          @click="selectYears(year)"
        >
          近{{ year }}年
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      加载数据中...
    </div>

    <!-- 无数据提示 -->
    <div v-else-if="!dataLoaded" class="empty-state">
      请选择指数查看数据分析
    </div>

    <!-- 数据展示 -->
    <div v-else class="analysis-content">
      <!-- Tab 切换 -->
      <div class="tabs">
        <button
          class="tab"
          :class="{ active: activeTab === 'price' }"
          @click="activeTab = 'price'"
        >
          收盘价分析
        </button>
        <button
          class="tab"
          :class="{ active: activeTab === 'deviation' }"
          @click="activeTab = 'deviation'"
        >
          均值偏差分析
        </button>
      </div>

      <!-- 收盘价分析 -->
      <div v-if="activeTab === 'price'" class="tab-content">
        <div class="chart-wrapper">
          <PriceChart
            ref="priceChartRef"
            :data="chartData"
            :show-smas="[30, 60, 90, 180]"
          />
        </div>
        <div class="chart-actions">
          <button class="btn btn-secondary" @click="exportPriceChart">
            导出图表 (SVG)
          </button>
        </div>
      </div>

      <!-- 均值偏差分析 -->
      <div v-if="activeTab === 'deviation'" class="tab-content">
        <!-- 周期选择 -->
        <div class="period-selector">
          <label>选择周期：</label>
          <select v-model="selectedPeriod" class="select" style="width: auto;">
            <option v-for="p in [30, 60, 90, 180, 240, 360]" :key="p" :value="p">
              {{ p }}日
            </option>
          </select>
        </div>

        <!-- 偏差趋势图 -->
        <div class="chart-wrapper">
          <DeviationChart
            ref="deviationChartRef"
            :data="chartData"
            :show-periods="[30, 60, 90, 180]"
          />
        </div>

        <!-- 偏差分布图 -->
        <div class="chart-section">
          <h3>偏差分布 ({{ selectedPeriod }}日)</h3>
          <DistributionChart
            ref="distributionChartRef"
            :data="chartData"
            :period="selectedPeriod"
          />
        </div>

        <div class="chart-actions">
          <button class="btn btn-secondary" @click="exportDeviationChart">
            导出偏差趋势图 (SVG)
          </button>
          <button class="btn btn-secondary" @click="exportDistributionChart">
            导出分布图 (SVG)
          </button>
        </div>

        <!-- 当前偏差统计 -->
        <div v-if="latestData" class="stats-card">
          <h3>当前偏差统计 ({{ selectedPeriod }}日)</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="label">当前偏差</span>
              <span class="value">{{ getDeviationValue(latestData) }}</span>
            </div>
            <div class="stat-item">
              <span class="label">历史最小</span>
              <span class="value">{{ deviationStats.min.toFixed(2) }}</span>
            </div>
            <div class="stat-item">
              <span class="label">历史最大</span>
              <span class="value">{{ deviationStats.max.toFixed(2) }}</span>
            </div>
            <div class="stat-item">
              <span class="label">历史均值</span>
              <span class="value">{{ deviationStats.mean.toFixed(2) }}</span>
            </div>
            <div class="stat-item">
              <span class="label">25%分位</span>
              <span class="value">{{ deviationStats.percentiles.p25.toFixed(2) }}</span>
            </div>
            <div class="stat-item">
              <span class="label">50%分位</span>
              <span class="value">{{ deviationStats.percentiles.p50.toFixed(2) }}</span>
            </div>
            <div class="stat-item">
              <span class="label">75%分位</span>
              <span class="value">{{ deviationStats.percentiles.p75.toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useIndices } from '@/composables/useIndices'
import { useDataFetch } from '@/composables/useDataFetch'
import PriceChart from '@/components/charts/PriceChart.vue'
import DeviationChart from '@/components/charts/DeviationChart.vue'
import DistributionChart from '@/components/charts/DistributionChart.vue'
import type { IndexDataPoint } from '@/types'

const { indices, loadIndices } = useIndices()
const { loadDataByYears, calculateDeviationStats, getLatestDataPoint } = useDataFetch()

const selectedIndexCode = ref('')
const selectedYears = ref(1)
const selectedPeriod = ref(60)
const activeTab = ref('price')
const loading = ref(false)
const chartData = ref<IndexDataPoint[]>([])
const deviationStats = ref({ min: 0, max: 0, mean: 0, current: 0, percentiles: { p25: 0, p50: 0, p75: 0 } })

const priceChartRef = ref<InstanceType<typeof PriceChart> | null>(null)
const deviationChartRef = ref<InstanceType<typeof DeviationChart> | null>(null)
const distributionChartRef = ref<InstanceType<typeof DistributionChart> | null>(null)

const dataLoaded = computed(() => chartData.value.length > 0)
const latestData = computed(() => chartData.value.length > 0 ? chartData.value[chartData.value.length - 1] : null)

const getDeviationValue = (data: IndexDataPoint): number | null => {
  const key = `deviation${selectedPeriod.value}` as keyof IndexDataPoint
  return (data[key] as number) ?? null
}

const loadData = async () => {
  if (!selectedIndexCode.value) {
    chartData.value = []
    return
  }

  loading.value = true

  try {
    const years = []
    const currentYear = new Date().getFullYear()
    for (let i = 0; i < selectedYears.value; i++) {
      years.push(currentYear - i)
    }

    chartData.value = await loadDataByYears(selectedIndexCode.value, years)

    // 计算偏差统计
    deviationStats.value = calculateDeviationStats(chartData.value, selectedPeriod.value)
  } catch (e) {
    console.error('Failed to load data:', e)
    chartData.value = []
  } finally {
    loading.value = false
  }
}

const selectYears = (years: number) => {
  selectedYears.value = years
  loadData()
}

// 导出图表
const exportPriceChart = () => {
  priceChartRef.value?.exportSvg()
}

const exportDeviationChart = () => {
  deviationChartRef.value?.exportSvg()
}

const exportDistributionChart = () => {
  distributionChartRef.value?.exportSvg()
}

// 监听周期变化
watch(selectedPeriod, () => {
  if (chartData.value.length > 0) {
    deviationStats.value = calculateDeviationStats(chartData.value, selectedPeriod.value)
  }
})

onMounted(() => {
  loadIndices()
})
</script>

<style scoped>
.data-analysis {
  padding: var(--spacing-lg);
}

.page-header {
  margin-bottom: var(--spacing-lg);
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.controls {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  flex-wrap: wrap;
}

.controls .select {
  max-width: 300px;
}

.time-selector {
  display: flex;
  gap: var(--spacing-xs);
}

.loading, .empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-secondary);
}

.analysis-content {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.tabs {
  display: flex;
  gap: var(--spacing-xs);
  border-bottom: 1px solid var(--border-color);
  margin-bottom: var(--spacing-lg);
}

.tab {
  padding: var(--spacing-sm) var(--spacing-md);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.tab:hover {
  color: var(--text-primary);
}

.tab.active {
  color: var(--primary-color);
  border-bottom-color: var(--primary-color);
}

.tab-content {
  margin-top: var(--spacing-md);
}

.chart-wrapper {
  margin-bottom: var(--spacing-md);
}

.chart-section {
  margin-top: var(--spacing-lg);
}

.chart-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: var(--spacing-md);
}

.chart-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.period-selector {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.period-selector label {
  font-weight: 500;
}

.stats-card {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.stats-card h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: var(--spacing-md);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: var(--spacing-md);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.stat-item .label {
  font-size: 12px;
  color: var(--text-secondary);
}

.stat-item .value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}
</style>