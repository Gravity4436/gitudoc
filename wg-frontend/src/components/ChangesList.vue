<template>
  <div class="changes-list">
    <h3>文件树（Tree）</h3>
    <div v-if="store.changedFiles.length === 0" class="no-changes">
      <span class="check-icon">✓</span>
      <p>所有文件都是干净的</p>
    </div>
    <ul v-else>
      <li 
        v-for="file in store.changedFiles" 
        :key="file.path"
        :class="{ active: store.selectedFile === file.path }"
        @click="store.selectedFile = file.path"
      >
        <span class="file-icon">📄</span>
        <span class="filename">{{ file.path }}</span>
        
        <div class="status-badges">
           <span class="status" :class="file.status">{{ file.status }}</span>
           <input 
            type="checkbox" 
            :value="file.path" 
            v-model="store.stagedFiles"
            @click.stop
            class="stage-checkbox"
          />
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { useProjectsStore } from '@/stores/useProjectsStore';
const store = useProjectsStore();
</script>

<style scoped>
.changes-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.1rem;
  color: #2c3e50;
  font-weight: 600;
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

li {
  display: flex;
  align-items: center;
  padding: 0.8rem;
  cursor: pointer;
  border-radius: 12px;
  transition: all 0.2s;
  margin-bottom: 0.5rem;
  border: 1px solid transparent;
}

li:hover {
  background-color: rgba(255, 255, 255, 0.3);
  transform: translateX(2px);
}

li.active {
  background-color: rgba(255, 255, 255, 0.5);
  border-color: rgba(255, 255, 255, 0.6);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.file-icon {
  margin-right: 0.5rem;
  font-size: 1.1rem;
  opacity: 0.7;
}

.filename {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
  color: #333;
}

.status-badges {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status {
  font-family: monospace;
  font-weight: bold;
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: 6px;
}

.status.M { color: #d97706; background: rgba(254, 243, 199, 0.8); }
.status.A { color: #059669; background: rgba(209, 250, 229, 0.8); }
.status.\?\? { color: #dc2626; background: rgba(254, 226, 226, 0.8); }

.stage-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #667eea;
}

.no-changes {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
}

.check-icon {
  font-size: 3rem;
  color: #10b981;
  margin-bottom: 0.5rem;
  filter: drop-shadow(0 4px 6px rgba(16, 185, 129, 0.2));
}
</style>
