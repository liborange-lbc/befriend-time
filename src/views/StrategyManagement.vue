<template>
  <div class="strategy-management">
    <div class="page-header">
      <h1>策略管理</h1>
      <button class="btn btn-primary" @click="showAddModal = true">
        新建策略
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      加载中...
    </div>

    <!-- 策略列表 -->
    <div v-else-if="strategies.length === 0" class="empty-state">
      <p>暂无策略，请创建第一个策略</p>
    </div>

    <div v-else class="strategy-list">
      <div v-for="strategy in strategies" :key="strategy.id" class="strategy-card">
        <div class="strategy-info">
          <h3>{{ strategy.name }}</h3>
          <span class="tag" :class="strategy.type === 'deviation' ? 'tag-info' : 'tag-warning'">
            {{ getTypeLabel(strategy.type) }}
          </span>
        </div>

        <div class="strategy-params">
          <template v-if="strategy.type === 'deviation'">
            <div class="param">
              <span class="label">均线周期：</span>
              <span class="value">{{ (strategy.params as any).smaPeriod }}日</span>
            </div>
            <div class="param">
              <span class="label">买入阈值：</span>
              <span class="value">{{ (strategy.params as any).buyThreshold }}%</span>
            </div>
            <div class="param">
              <span class="label">卖出阈值：</span>
              <span class="value">{{ (strategy.params as any).sellThreshold }}%</span>
            </div>
          </template>
          <template v-else>
            <div class="param">
              <span class="label">均线周期：</span>
              <span class="value">{{ (strategy.params as any).smaPeriod }}日</span>
            </div>
            <div class="param">
              <span class="label">仓位比例：</span>
              <span class="value">{{ (strategy.params as any).ratio }}%</span>
            </div>
          </template>
          <div class="param">
            <span class="label">初始资金：</span>
            <span class="value">¥{{ (strategy.params as any).initialCapital?.toLocaleString() }}</span>
          </div>
        </div>

        <div class="strategy-actions">
          <button class="btn btn-secondary btn-sm" @click="applyStrategy(strategy)">
            应用
          </button>
          <button class="btn btn-secondary btn-sm" @click="editStrategy(strategy)">
            编辑
          </button>
          <button class="btn btn-danger btn-sm" @click="confirmDelete(strategy)">
            删除
          </button>
        </div>

        <div class="strategy-meta">
          创建于 {{ strategy.createdAt }}
        </div>
      </div>
    </div>

    <!-- 添加/编辑弹窗 -->
    <div v-if="showAddModal || showEditModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <h2>{{ showEditModal ? '编辑策略' : '新建策略' }}</h2>

        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label>策略名称</label>
            <input v-model="formData.name" type="text" class="input" placeholder="例如：激进均值回归" required />
          </div>

          <div class="form-group">
            <label>策略类型</label>
            <div class="strategy-type-select">
              <button type="button" class="type-btn" :class="{ active: formData.type === 'deviation' }" @click="formData.type = 'deviation'">
                均值偏差策略
              </button>
              <button type="button" class="type-btn" :class="{ active: formData.type === 'crossover' }" @click="formData.type = 'crossover'">
                均值穿越策略
              </button>
            </div>
          </div>

          <!-- 均值偏差策略参数 -->
          <div v-if="formData.type === 'deviation'" class="params-form">
            <div class="form-group">
              <label>均线周期 (SMA)</label>
              <select v-model.number="(formData.params as any).smaPeriod" class="select">
                <option v-for="p in [30, 60, 90, 180, 240, 360]" :key="p" :value="p">{{ p }}日</option>
              </select>
            </div>
            <div class="form-group">
              <label>买入阈值 (%)</label>
              <input v-model.number="(formData.params as any).buyThreshold" type="number" class="input" />
            </div>
            <div class="form-group">
              <label>卖出阈值 (%)</label>
              <input v-model.number="(formData.params as any).sellThreshold" type="number" class="input" />
            </div>
            <div class="form-group">
              <label>买入比例 (%)</label>
              <input v-model.number="(formData.params as any).buyRatio" type="number" class="input" />
            </div>
            <div class="form-group">
              <label>卖出比例 (%)</label>
              <input v-model.number="(formData.params as any).sellRatio" type="number" class="input" />
            </div>
            <div class="form-group">
              <label>初始资金</label>
              <input v-model.number="(formData.params as any).initialCapital" type="number" class="input" />
            </div>
          </div>

          <!-- 均值穿越策略参数 -->
          <div v-else class="params-form">
            <div class="form-group">
              <label>均线周期 (SMA)</label>
              <select v-model.number="(formData.params as any).smaPeriod" class="select">
                <option v-for="p in [30, 60, 90, 180, 240, 360]" :key="p" :value="p">{{ p }}日</option>
              </select>
            </div>
            <div class="form-group">
              <label>仓位比例 (%)</label>
              <input v-model.number="(formData.params as any).ratio" type="number" class="input" />
            </div>
            <div class="form-group">
              <label>初始资金</label>
              <input v-model.number="(formData.params as any).initialCapital" type="number" class="input" />
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="btn btn-secondary" @click="closeModal">取消</button>
            <button type="submit" class="btn btn-primary">{{ showEditModal ? '保存' : '创建' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
      <div class="modal">
        <h2>确认删除</h2>
        <p>确定要删除策略 "{{ strategyToDelete?.name }}" 吗？</p>
        <div class="form-actions">
          <button class="btn btn-secondary" @click="showDeleteModal = false">取消</button>
          <button class="btn btn-danger" @click="handleDelete">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStrategies } from '@/composables/useStrategies'
import type { Strategy, StrategyType, StrategyParams } from '@/types'

const router = useRouter()
const {
  strategies,
  loading,
  loadStrategies,
  getTypeLabel,
  addStrategy,
  updateStrategy,
  deleteStrategy
} = useStrategies()

const showAddModal = ref(false)
const showEditModal = ref(false)
const showDeleteModal = ref(false)
const editingStrategy = ref<Strategy | null>(null)
const strategyToDelete = ref<Strategy | null>(null)

const defaultParams: Record<StrategyType, StrategyParams> = {
  deviation: {
    smaPeriod: 60,
    buyThreshold: -5,
    sellThreshold: 5,
    buyRatio: 100,
    sellRatio: 100,
    initialCapital: 100000
  },
  crossover: {
    smaPeriod: 60,
    ratio: 100,
    initialCapital: 100000
  }
}

const formData = reactive({
  name: '',
  type: 'deviation' as StrategyType,
  params: { ...defaultParams.deviation } as StrategyParams
})

// 关闭弹窗
const closeModal = () => {
  showAddModal.value = false
  showEditModal.value = false
  editingStrategy.value = null
  formData.name = ''
  formData.type = 'deviation'
  formData.params = { ...defaultParams.deviation }
}

// 编辑策略
const editStrategy = (strategy: Strategy) => {
  editingStrategy.value = strategy
  formData.name = strategy.name
  formData.type = strategy.type
  formData.params = { ...strategy.params } as any
  showEditModal.value = true
}

// 确认删除
const confirmDelete = (strategy: Strategy) => {
  strategyToDelete.value = strategy
  showDeleteModal.value = true
}

// 处理删除
const handleDelete = () => {
  if (strategyToDelete.value) {
    deleteStrategy(strategyToDelete.value.id)
    showDeleteModal.value = false
    strategyToDelete.value = null
  }
}

// 提交表单
const handleSubmit = () => {
  if (showEditModal.value && editingStrategy.value) {
    updateStrategy(editingStrategy.value.id, {
      name: formData.name,
      type: formData.type,
      params: formData.params
    })
  } else {
    addStrategy({
      name: formData.name,
      type: formData.type,
      params: formData.params
    })
  }
  closeModal()
}

// 应用策略 - 跳转到回测页面
const applyStrategy = (strategy: Strategy) => {
  const paramsAny = strategy.params as any
  // 将策略参数编码到 URL
  const params = new URLSearchParams({
    strategy: strategy.id,
    type: strategy.type,
    smaPeriod: String(paramsAny.smaPeriod),
    initialCapital: String(paramsAny.initialCapital)
  })

  if (strategy.type === 'deviation') {
    const devParams = strategy.params as { buyThreshold: number; sellThreshold: number; buyRatio: number; sellRatio: number }
    params.set('buyThreshold', String(devParams.buyThreshold))
    params.set('sellThreshold', String(devParams.sellThreshold))
    params.set('buyRatio', String(devParams.buyRatio))
    params.set('sellRatio', String(devParams.sellRatio))
  } else {
    const crossParams = strategy.params as { ratio: number }
    params.set('ratio', String(crossParams.ratio))
  }

  router.push({ path: '/backtest', query: Object.fromEntries(params) })
}

onMounted(() => {
  loadStrategies()
})
</script>

<style scoped>
.strategy-management {
  padding: var(--spacing-lg);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.loading, .empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-secondary);
}

.strategy-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: var(--spacing-lg);
}

.strategy-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
}

.strategy-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.strategy-info h3 {
  font-size: 18px;
  font-weight: 600;
}

.strategy-params {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.param {
  display: flex;
  gap: 4px;
  font-size: 13px;
  background: var(--bg-secondary);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
}

.param .label {
  color: var(--text-secondary);
}

.param .value {
  font-weight: 500;
}

.strategy-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.strategy-meta {
  margin-top: var(--spacing-md);
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background-color: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  width: 90%;
  max-width: 500px;
  box-shadow: var(--shadow-lg);
}

.modal h2 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: var(--spacing-lg);
}

.modal p {
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
}

.strategy-type-select {
  display: flex;
  gap: var(--spacing-sm);
}

.type-btn {
  flex: 1;
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.type-btn.active {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.params-form {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
}
</style>