<template>
  <div class="index-management">
    <div class="page-header">
      <h1>指数管理</h1>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      加载中...
    </div>

    <!-- 错误提示 -->
    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- 指数列表 -->
    <div v-else class="index-list">
      <div v-if="indices.length === 0" class="empty-state">
        暂无指数
      </div>

      <template v-else>
        <!-- A股 -->
        <div v-if="indicesByRegion.CN.length > 0" class="region-section">
          <h2>A股</h2>
          <table class="table">
            <thead>
              <tr>
                <th>名称</th>
                <th>代码</th>
                <th>创建时间</th>
                <th>更新时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in indicesByRegion.CN" :key="item.id">
                <td>{{ item.name }}</td>
                <td><code>{{ item.code }}</code></td>
                <td>{{ item.createdAt }}</td>
                <td>{{ item.updatedAt }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 港股 -->
        <div v-if="indicesByRegion.HK.length > 0" class="region-section">
          <h2>港股</h2>
          <table class="table">
            <thead>
              <tr>
                <th>名称</th>
                <th>代码</th>
                <th>创建时间</th>
                <th>更新时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in indicesByRegion.HK" :key="item.id">
                <td>{{ item.name }}</td>
                <td><code>{{ item.code }}</code></td>
                <td>{{ item.createdAt }}</td>
                <td>{{ item.updatedAt }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 美股 -->
        <div v-if="indicesByRegion.US.length > 0" class="region-section">
          <h2>美股</h2>
          <table class="table">
            <thead>
              <tr>
                <th>名称</th>
                <th>代码</th>
                <th>创建时间</th>
                <th>更新时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in indicesByRegion.US" :key="item.id">
                <td>{{ item.name }}</td>
                <td><code>{{ item.code }}</code></td>
                <td>{{ item.createdAt }}</td>
                <td>{{ item.updatedAt }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useIndices } from '@/composables/useIndices'

const {
  indices,
  loading,
  error,
  loadIndices,
  indicesByRegion
} = useIndices()

onMounted(() => {
  loadIndices()
})
</script>

<style scoped>
.index-management {
  padding: var(--spacing-lg);
}

.page-header {
  margin-bottom: var(--spacing-lg);
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.loading, .error-message, .empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-secondary);
}

.error-message {
  color: var(--danger-color);
}

.region-section {
  margin-bottom: var(--spacing-xl);
}

.region-section h2 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: var(--spacing-md);
  color: var(--text-primary);
}

code {
  background-color: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: 13px;
}
</style>