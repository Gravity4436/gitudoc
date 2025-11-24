<template>
  <div class="app-container">
    <!-- SVG Filter Definition for Liquid Effect -->
    <svg style="position: absolute; width: 0; height: 0;">
      <defs>
        <filter id="liquid-filter">
          <feTurbulence baseFrequency="0.01 0.01" numOctaves="3" result="noise" seed="1"/>
          <feDisplacementMap in="SourceGraphic" in2="noise" scale="2" />
        </filter>
      </defs>
    </svg>

    <header class="glass-panel">
      <div class="wrapper">
        <nav v-if="store.hasActiveProject">
          <button @click="store.deselectProject" class="back-btn">
            <span class="icon">←</span> Back
          </button>
          <span class="project-name">{{ store.activeProject }}</span>
        </nav>
        <div v-else class="brand">
          <h1>GituDoc</h1>
          <p>Git 风格的 Docx 文件版本控制工具.</p>
        </div>
        <div class="user-profile">
          <div class="avatar">G</div>
        </div>
      </div>
    </header>

    <main>
      <ProjectSelector v-if="!store.hasActiveProject" />
      <Dashboard v-else />
    </main>
  </div>
</template>

<script setup>
import { useProjectsStore } from '@/stores/useProjectsStore';
import ProjectSelector from '@/components/ProjectSelector.vue';
import Dashboard from '@/components/Dashboard.vue';

const store = useProjectsStore();
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 20px;
}

header {
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  z-index: 10;
}

.wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.brand h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #2c3e50;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.brand p {
  margin: 0;
  font-size: 0.9rem;
  color: #555;
}

nav {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.project-name {
  font-weight: 600;
  color: #2c3e50;
  font-size: 1.1rem;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0.4rem 0.8rem;
}

.avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

main {
  flex: 1;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}
</style>
