<template>
  <div class="dashboard">
    <h1>BefriendTime 基金分析平台</h1>

    <div class="dashboard-grid">
      <!-- 快捷入口 -->
      <div class="card quick-links">
        <h2>快捷入口</h2>
        <div class="links-grid">
          <router-link to="/analysis" class="link-item">
            <span class="icon">📊</span>
            <span>数据分析</span>
          </router-link>
          <router-link to="/backtest" class="link-item">
            <span class="icon">🔬</span>
            <span>策略回测</span>
          </router-link>
          <router-link to="/indices" class="link-item">
            <span class="icon">📈</span>
            <span>指数管理</span>
          </router-link>
          <router-link to="/strategies" class="link-item">
            <span class="icon">⚙️</span>
            <span>策略管理</span>
          </router-link>
        </div>
      </div>

      <!-- 偏差监控 -->
      <div class="card deviation-monitor">
        <h2>偏差监控</h2>
        <div v-if="indices.length === 0" class="empty-tip">
          暂无指数，请先在指数管理中添加
        </div>
        <div v-else class="deviation-list">
          <div v-for="idx in deviationData" :key="idx.code" class="deviation-item">
            <div class="idx-info">
              <span class="name">{{ idx.name }}</span>
              <span class="code">{{ idx.code }}</span>
            </div>
            <div class="deviation-values">
              <span v-for="p in [30, 60, 90]" :key="p" class="dev" :class="getDeviationClass(idx[`dev${p}`])">
                SMA{{ p }}: {{ idx[`dev${p}`]?.toFixed(1) || '-' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 数据更新状态 -->
      <div class="card update-status">
        <h2>数据更新状态</h2>
        <div class="status-list">
          <div class="status-item">
            <span class="region">A股</span>
            <span class="status" :class="cnStatus?.status">{{ cnStatus?.status || 'unknown' }}</span>
            <span class="time">{{ cnStatus?.timestamp?.split('T')[0] || '-' }}</span>
          </div>
          <div class="status-item">
            <span class="region">港股</span>
            <span class="status" :class="hkStatus?.status">{{ hkStatus?.status || 'unknown' }}</span>
            <span class="time">{{ hkStatus?.timestamp?.split('T')[0] || '-' }}</span>
          </div>
          <div class="status-item">
            <span class="region">美股</span>
            <span class="status" :class="usStatus?.status">{{ usStatus?.status || 'unknown' }}</span>
            <span class="time">{{ usStatus?.timestamp?.split('T')[0] || '-' }}</span>
          </div>
        </div>
      </div>

      <!-- 最近查看 -->
      <div class="card recent-indices">
        <h2>最近查看</h2>
        <div v-if="recentIndices.length === 0" class="empty-tip">
          暂无最近查看记录
        </div>
        <div v-else class="recent-list">
          <router-link
            v-for="idx in recentIndices"
            :key="idx.code"
            :to="{ path: '/analysis', query: { code: idx.code } }"
            class="recent-item"
          >
            {{ idx.name }}
          </router-link>
        </div>
      </div>
    </div>

    <!-- 说明 -->
    <div class="info-card">
      <h3>使用说明</h3>
      <ul>
        <li>在<b>指数管理</b>中添加想要跟踪的指数（A股、港股、美股）</li>
        <li>通过<b>数据分析</b>查看指数的历史走势和均值偏差</li>
        <li>在<b>策略回测</b>中测试和优化您的交易策略</li>
        <li>在<b>策略管理</b>中保存常用策略以便快速调用</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useIndices } from '@/composables/useIndices'
import { useDataFetch } from '@/composables/useDataFetch'
import type { UpdateLog, Index } from '@/types'

const { indices, loadIndices } = useIndices()
const { loadDataByYear, getLatestDataPoint } = useDataFetch()

const updateLogs = ref<UpdateLog[]>([])
const recentIndices = ref<{ name: string; code: string }[]>([])
const deviationData = ref<any[]>([])

// 加载更新日志
const loadUpdateLogs = async () => {
  try {
    const response = await fetch('/data/status/update-log.json')
    if (response.ok) {
      const data = await response.json()
      updateLogs.value = data.logs || []
    }
  } catch (e) {
    console.error('Failed to load update logs:', e)
  }
}

// 获取最新状态
const cnStatus = computed(() => updateLogs.value.find(l => l.region === 'CN'))
const hkStatus = computed(() => updateLogs.value.find(l => l.region === 'HK'))
const usStatus = computed(() => updateLogs.value.find(l => l.region === 'US'))

// 加载偏差数据
const loadDeviationData = async () => {
  if (indices.value.length === 0) return

  const currentYear = new Date().getFullYear()
  const results: any[] = []

  for (const idx of indices.value.slice(0, 5)) {
    try {
      const data = await loadDataByYear(idx.code, currentYear)
      const latest = getLatestDataPoint(data)
      if (latest) {
        results.push({
          name: idx.name,
          code: idx.code,
          dev30: latest.deviation30 as number,
          dev60: latest.deviation60 as number,
          dev90: latest.deviation90 as number
        })
      }
    } catch (e) {
      console.error(`Failed to load data for ${idx.code}:`, e)
    }
  }

  deviationData.value = results
}

// 获取偏差样式
const getDeviationClass = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return ''
  if (value < -10) return 'dev-low'
  if (value < 0) return 'dev-negative'
  if (value > 10) return 'dev-high'
  if (value > 0) return 'dev-positive'
  return ''
}

// 加载最近查看
const loadRecentIndices = () => {
  try {
    const stored = localStorage.getItem('befriend-time-recent')
    if (stored) {
      recentIndices.value = JSON.parse(stored)
    }
  } catch (e) {
    console.error('Failed to load recent indices:', e)
  }
}

onMounted(async () => {
  await loadIndices()
  await loadUpdateLogs()
  loadDeviationData()
  loadRecentIndices()
})
</script>

<style scoped>
.dashboard {
  padding: var(--spacing-lg);
}

.dashboard h1 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: var(--spacing-lg);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.card h2 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-color);
}

.links-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-sm);
}

.link-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--text-primary);
  transition: all 0.2s;
}

.link-item:hover {
  background: var(--primary-color);
  color: white;
}

.link-item .icon {
  font-size: 24px;
}

.empty-tip {
  color: var(--text-tertiary);
  font-size: 14px;
  text-align: center;
  padding: var(--spacing-lg);
}

.deviation-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.deviation-item {
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.idx-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-xs);
}

.idx-info .name {
  font-weight: 500;
}

.idx-info .code {
  font-size: 12px;
  color: var(--text-tertiary);
}

.deviation-values {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.dev {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.dev-positive {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
}

.dev-negative {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
}

.dev-high {
  background: rgba(239, 68, 68, 0.2);
  color: var(--danger-color);
}

.dev-low {
  background: rgba(34, 197, 94, 0.2);
  color: var(--success-color);
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.status-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.status-item .region {
  font-weight: 500;
  width: 40px;
}

.status-item .status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 9999px;
}

.status-item .status.success {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
}

.status-item .status.failed {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
}

.status-item .status.retrying {
  background: rgba(245, 158, 11, 0.1);
  color: var(--warning-color);
}

.status-item .status.unknown {
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
}

.status-item .time {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-tertiary);
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.recent-item {
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--text-primary);
  transition: all 0.2s;
}

.recent-item:hover {
  background: var(--primary-color);
  color: white;
}

.info-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.info-card h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: var(--spacing-md);
}

.info-card ul {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.info-card li {
  color: var(--text-secondary);
}

.info-card b {
  color: var(--text-primary);
}
</style>