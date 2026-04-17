<template>
  <div class="app-container">
    <nav class="top-nav">
      <div class="nav-brand">BefriendTime</div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link to="/indices" class="nav-link">指数管理</router-link>
        <router-link to="/analysis" class="nav-link">数据分析</router-link>
        <router-link to="/backtest" class="nav-link">策略回测</router-link>
        <router-link to="/strategies" class="nav-link">策略管理</router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
// App root component
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.top-nav {
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  padding: 0 var(--spacing-lg);
  display: flex;
  align-items: center;
  height: 56px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand {
  font-size: 18px;
  font-weight: 600;
  color: var(--primary-color);
  margin-right: var(--spacing-xl);
}

.nav-links {
  display: flex;
  gap: var(--spacing-xs);
}

.nav-link {
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: var(--text-primary);
  background-color: var(--bg-secondary);
}

.nav-link.router-link-active {
  color: var(--primary-color);
  background-color: rgba(59, 130, 246, 0.1);
}

.main-content {
  flex: 1;
  background-color: var(--bg-secondary);
}
</style>