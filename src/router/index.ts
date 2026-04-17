// 路由配置
import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import IndexManagement from '@/views/IndexManagement.vue'
import DataAnalysis from '@/views/DataAnalysis.vue'
import StrategyBacktest from '@/views/StrategyBacktest.vue'
import StrategyManagement from '@/views/StrategyManagement.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/indices',
    name: 'IndexManagement',
    component: IndexManagement
  },
  {
    path: '/analysis',
    name: 'DataAnalysis',
    component: DataAnalysis
  },
  {
    path: '/backtest',
    name: 'StrategyBacktest',
    component: StrategyBacktest
  },
  {
    path: '/strategies',
    name: 'StrategyManagement',
    component: StrategyManagement
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router