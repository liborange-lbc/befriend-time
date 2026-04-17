<template>
  <div class="strategy-backtest">
    <div class="page-header">
      <h1>策略回测</h1>
    </div>

    <div class="backtest-layout">
      <!-- 左侧：策略配置 -->
      <div class="config-panel">
        <!-- 选择指数 -->
        <div class="form-section">
          <h3>选择指数</h3>
          <select v-model="selectedIndexCode" class="select" @change="loadData">
            <option value="">请选择指数</option>
            <option v-for="idx in indices" :key="idx.id" :value="idx.code">
              {{ idx.name }} ({{ idx.code }})
            </option>
          </select>
        </div>

        <!-- 选择时间范围 -->
        <div class="form-section">
          <h3>时间范围</h3>
          <div class="time-options">
            <button
              v-for="year in [1, 3, 5, 10]"
              :key="year"
              class="btn btn-sm"
              :class="selectedYears === year ? 'btn-primary' : 'btn-secondary'"
              @click="selectedYears = year; loadData()"
            >
              近{{ year }}年
            </button>
          </div>
        </div>

        <!-- 策略类型 -->
        <div class="form-section">
          <h3>策略类型</h3>
          <div class="strategy-tabs">
            <button
              class="tab"
              :class="{ active: strategyType === 'deviation' }"
              @click="strategyType = 'deviation'"
            >
              均值偏差策略
            </button>
            <button
              class="tab"
              :class="{ active: strategyType === 'crossover' }"
              @click="strategyType = 'crossover'"
            >
              均值穿越策略
            </button>
          </div>
        </div>

        <!-- 策略参数 -->
        <div class="form-section">
          <h3>策略参数</h3>

          <!-- 均值偏差策略参数 -->
          <div v-if="strategyType === 'deviation'" class="params-form">
            <div class="form-group">
              <label>均线周期 (SMA)</label>
              <select v-model="backtestParams.smaPeriod" class="select">
                <option v-for="p in [30, 60, 90, 180, 240, 360]" :key="p" :value="p">
                  {{ p }}日
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>买入阈值 (%)</label>
              <input v-model.number="backtestParams.buyThreshold" type="number" class="input" />
              <span class="hint">当偏差低于此值时买入</span>
            </div>
            <div class="form-group">
              <label>卖出阈值 (%)</label>
              <input v-model.number="backtestParams.sellThreshold" type="number" class="input" />
              <span class="hint">当偏差高于此值时卖出</span>
            </div>
            <div class="form-group">
              <label>买入比例 (%)</label>
              <input v-model.number="backtestParams.buyRatio" type="number" class="input" />
            </div>
            <div class="form-group">
              <label>卖出比例 (%)</label>
              <input v-model.number="backtestParams.sellRatio" type="number" class="input" />
            </div>
            <div class="form-group">
              <label>初始资金</label>
              <input v-model.number="backtestParams.initialCapital" type="number" class="input" />
            </div>
          </div>

          <!-- 均值穿越策略参数 -->
          <div v-else class="params-form">
            <div class="form-group">
              <label>均线周期 (SMA)</label>
              <select v-model="crossoverParams.smaPeriod" class="select">
                <option v-for="p in [30, 60, 90, 180, 240, 360]" :key="p" :value="p">
                  {{ p }}日
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>仓位比例 (%)</label>
              <input v-model.number="crossoverParams.ratio" type="number" class="input" />
            </div>
            <div class="form-group">
              <label>初始资金</label>
              <input v-model.number="crossoverParams.initialCapital" type="number" class="input" />
            </div>
          </div>
        </div>

        <!-- 运行回测按钮 -->
        <button class="btn btn-primary w-full" :disabled="loading || !selectedIndexCode" @click="runBacktest">
          {{ loading ? '回测中...' : '运行回测' }}
        </button>
      </div>

      <!-- 右侧：回测结果 -->
      <div class="result-panel">
        <div v-if="!result" class="empty-state">
          <p>请选择指数和策略参数，然后运行回测</p>
        </div>

        <div v-else class="result-content">
          <!-- 收益概览 -->
          <div class="result-section">
            <h3>收益概览</h3>
            <div class="metrics-grid">
              <div class="metric">
                <span class="label">累计收益率</span>
                <span class="value" :class="{ positive: result.totalReturn > 0, negative: result.totalReturn < 0 }">
                  {{ (result.totalReturn * 100).toFixed(2) }}%
                </span>
              </div>
              <div class="metric">
                <span class="label">年化收益率</span>
                <span class="value" :class="{ positive: result.annualizedReturn > 0, negative: result.annualizedReturn < 0 }">
                  {{ result.annualizedReturn.toFixed(2) }}%
                </span>
              </div>
              <div class="metric">
                <span class="label">总盈亏</span>
                <span class="value" :class="{ positive: result.totalProfitLoss > 0, negative: result.totalProfitLoss < 0 }">
                  ¥{{ result.totalProfitLoss.toFixed(2) }}
                </span>
              </div>
              <div class="metric">
                <span class="label">最终资产</span>
                <span class="value">¥{{ result.finalCapital.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <!-- 风险指标 -->
          <div class="result-section">
            <h3>风险指标</h3>
            <div class="metrics-grid">
              <div class="metric">
                <span class="label">最大回撤</span>
                <span class="value negative">{{ result.maxDrawdown.toFixed(2) }}%</span>
              </div>
              <div class="metric">
                <span class="label">回撤持续天数</span>
                <span class="value">{{ result.maxDrawdownDuration }}天</span>
              </div>
              <div class="metric">
                <span class="label">波动率</span>
                <span class="value">{{ result.volatility.toFixed(2) }}%</span>
              </div>
              <div class="metric">
                <span class="label">夏普比率</span>
                <span class="value">{{ result.sharpeRatio.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <!-- 交易指标 -->
          <div class="result-section">
            <h3>交易指标</h3>
            <div class="metrics-grid">
              <div class="metric">
                <span class="label">交易次数</span>
                <span class="value">{{ result.metrics.totalTrades }}</span>
              </div>
              <div class="metric">
                <span class="label">胜率</span>
                <span class="value">{{ result.metrics.winRate.toFixed(2) }}%</span>
              </div>
              <div class="metric">
                <span class="label">平均持仓天数</span>
                <span class="value">{{ result.metrics.avgHoldingDays }}天</span>
              </div>
              <div class="metric">
                <span class="label">盈亏比</span>
                <span class="value">{{ result.metrics.profitLossRatio.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <!-- 基准对比 -->
          <div class="result-section">
            <h3>基准对比 (买入持有)</h3>
            <div class="metrics-grid">
              <div class="metric">
                <span class="label">基准收益率</span>
                <span class="value" :class="{ positive: result.benchmarkReturn > 0, negative: result.benchmarkReturn < 0 }">
                  {{ (result.benchmarkReturn * 100).toFixed(2) }}%
                </span>
              </div>
              <div class="metric">
                <span class="label">超额收益</span>
                <span class="value" :class="{ positive: result.totalReturn > result.benchmarkReturn, negative: result.totalReturn < result.benchmarkReturn }">
                  {{ ((result.totalReturn - result.benchmarkReturn) * 100).toFixed(2) }}%
                </span>
              </div>
            </div>
          </div>

          <!-- 交易明细 -->
          <div class="result-section">
            <h3>交易明细</h3>
            <div class="trades-table">
              <table class="table">
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>操作</th>
                    <th>价格</th>
                    <th>数量</th>
                    <th>金额</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(trade, i) in result.trades" :key="i">
                    <td>{{ trade.date }}</td>
                    <td>
                      <span :class="trade.type === 'buy' ? 'tag-success' : 'tag-danger'">
                        {{ trade.type === 'buy' ? '买入' : '卖出' }}
                      </span>
                    </td>
                    <td>¥{{ trade.price.toFixed(2) }}</td>
                    <td>{{ trade.shares.toFixed(2) }}</td>
                    <td>¥{{ trade.amount.toFixed(2) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useIndices } from '@/composables/useIndices'
import { useDataFetch } from '@/composables/useDataFetch'
import { useBacktest, type StrategyType } from '@/composables/useBacktest'
import type { IndexDataPoint } from '@/types'

const { indices, loadIndices } = useIndices()
const { loadDataByYears } = useDataFetch()
const { runBacktest: executeBacktest, loading, result } = useBacktest()

const selectedIndexCode = ref('')
const selectedYears = ref(3)
const strategyType = ref<StrategyType>('deviation')
const chartData = ref<IndexDataPoint[]>([])

// 偏差策略参数
const backtestParams = reactive({
  smaPeriod: 60,
  buyThreshold: -5,
  sellThreshold: 5,
  buyRatio: 100,
  sellRatio: 100,
  initialCapital: 100000
})

// 穿越策略参数
const crossoverParams = reactive({
  smaPeriod: 60,
  ratio: 100,
  initialCapital: 100000
})

const loadData = async () => {
  if (!selectedIndexCode.value) {
    chartData.value = []
    return
  }

  const years = []
  const currentYear = new Date().getFullYear()
  for (let i = 0; i < selectedYears.value; i++) {
    years.push(currentYear - i)
  }

  chartData.value = await loadDataByYears(selectedIndexCode.value, years)
}

const runBacktest = async () => {
  if (chartData.value.length === 0) {
    await loadData()
  }

  await executeBacktest(chartData.value, strategyType.value)
}

onMounted(() => {
  loadIndices()
})
</script>

<style scoped>
.strategy-backtest {
  padding: var(--spacing-lg);
}

.page-header {
  margin-bottom: var(--spacing-lg);
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.backtest-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: var(--spacing-lg);
}

@media (max-width: 900px) {
  .backtest-layout {
    grid-template-columns: 1fr;
  }
}

.config-panel {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  height: fit-content;
}

.form-section {
  margin-bottom: var(--spacing-lg);
}

.form-section h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
}

.strategy-tabs {
  display: flex;
  gap: var(--spacing-xs);
}

.strategy-tabs .tab {
  flex: 1;
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.strategy-tabs .tab.active {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.params-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
}

.hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

.result-panel {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  min-height: 400px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-secondary);
}

.result-section {
  margin-bottom: var(--spacing-lg);
}

.result-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-color);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: var(--spacing-md);
}

.metric {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.metric .label {
  font-size: 12px;
  color: var(--text-secondary);
}

.metric .value {
  font-size: 18px;
  font-weight: 600;
}

.metric .value.positive {
  color: var(--success-color);
}

.metric .value.negative {
  color: var(--danger-color);
}

.trades-table {
  max-height: 300px;
  overflow-y: auto;
}

.time-options {
  display: flex;
  gap: var(--spacing-xs);
}

.w-full {
  width: 100%;
}
</style>