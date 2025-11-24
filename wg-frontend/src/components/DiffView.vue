<template>
  <div class="diff-view">
    <div v-if="!store.selectedFile" class="placeholder">
      请选择一个文件来查看变化。
    </div>
    <div v-else class="diff-inner">
      <div class="header">
        <h3>{{ store.selectedFile }}</h3>
        <div class="toolbar">
          <label class="auto-refresh">
            <input type="checkbox" v-model="autoRefresh"> 
            Auto Refresh
          </label>
          <button @click="fetchDiff" class="refresh-btn" :disabled="loading" title="Refresh Diff">
            <span v-if="loading">...</span>
            <span v-else>↻</span>
          </button>
        </div>
      </div>
      <div v-if="loading && !diffData" class="loading-state">Loading diff...</div>
      <div v-else-if="error">{{ error }}</div>
      <div v-else class="diff-container" ref="containerRef">
        <div v-if="parsedDiff.length === 0" class="no-diff-message">
          <span class="check-icon">✓</span>
          <p>当前文件没有检测到更改 (Clean)</p>
        </div>
        <div v-else class="diff-content">
          <div 
            v-for="(line, index) in parsedDiff" 
            :key="index"
            class="diff-line"
            :class="line.type"
          >
            <span class="line-number" v-if="line.type !== 'meta'"></span>
            <span class="line-content">{{ line.content }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onUnmounted } from 'vue';
import { useProjectsStore } from '@/stores/useProjectsStore';
import axios from 'axios';

const store = useProjectsStore();
const diffData = ref('');
const loading = ref(false);
const error = ref('');
const autoRefresh = ref(false);
let refreshInterval = null;
const containerRef = ref(null);

async function fetchDiff() {
  if (!store.selectedFile || !store.activeProject) return;
  
  // Don't set loading to true if we already have data (for smoother auto-refresh)
  if (!diffData.value) loading.value = true;
  error.value = '';
  
  try {
    const res = await axios.get('http://localhost:8000/api/diff/' + store.selectedFile, {
        params: { project_path: store.activeProject }
    });
    diffData.value = res.data.diff;
  } catch (e) {
    // Only show error if we don't have data, or if it's a manual refresh
    if (!diffData.value) error.value = 'Failed to load diff.';
    console.error(e);
  } finally {
    loading.value = false;
  }
}

// Watch for file selection changes
watch(() => store.selectedFile, (newFile) => {
  diffData.value = ''; // Clear old diff immediately
  if (newFile) {
    fetchDiff();
  }
});

// Watch for auto-refresh toggle
watch(autoRefresh, (enabled) => {
  if (enabled) {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(fetchDiff, 3000); // Poll every 3 seconds
  } else {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = null;
  }
});

// Cleanup
onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval);
});

const parsedDiff = computed(() => {
  if (!diffData.value) return [];
  
  return diffData.value.split('\n').map(line => {
    let type = 'normal';
    if (line.startsWith('diff --git') || line.startsWith('index ') || line.startsWith('--- ') || line.startsWith('+++ ')) {
      type = 'header';
    } else if (line.startsWith('@@')) {
      type = 'meta';
    } else if (line.startsWith('+')) {
      type = 'add';
    } else if (line.startsWith('-')) {
      type = 'del';
    }
    
    return { content: line, type };
  });
});
</script>

<style scoped>
.diff-view {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0; /* Critical for nested flex scrolling */
}

.diff-inner {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.header {
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

/* ... existing styles ... */

.diff-container {
  flex: 1;
  overflow: auto;
  border-radius: 12px;
  background-color: rgba(255, 255, 255, 0.5);
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
  border: 1px solid rgba(255,255,255,0.3);
  min-height: 0; /* Critical for nested flex scrolling */
}

/* ... existing styles ... */

.diff-container {
  flex: 1;
  overflow: auto;
  border-radius: 12px;
  background-color: rgba(255, 255, 255, 0.5);
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
  border: 1px solid rgba(255,255,255,0.3);
  min-height: 0; /* Critical for nested flex scrolling */
  border: 2px solid purple; /* DEBUG: Layer 5 */
}

h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #2c3e50;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: 1rem;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.auto-refresh {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #555;
  cursor: pointer;
  user-select: none;
}

.refresh-btn {
  background: rgba(255,255,255,0.5);
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 4px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1.1rem;
  line-height: 1;
  padding: 0;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(255,255,255,0.8);
  transform: rotate(180deg);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: wait;
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  font-size: 1.2rem;
  background: rgba(255,255,255,0.2);
  border-radius: 12px;
  border: 1px dashed rgba(255,255,255,0.4);
}

.diff-container {
  flex: 1;
  overflow: auto;
  border-radius: 12px;
  background-color: rgba(255, 255, 255, 0.5);
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
  border: 1px solid rgba(255,255,255,0.3);
  min-height: 0; /* Critical for nested flex scrolling */
}

.diff-content {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  padding: 1rem;
}

.diff-line {
  white-space: pre-wrap;
  padding: 0 4px;
  border-radius: 4px;
}

.diff-line.header {
  color: #555;
  font-weight: bold;
  background-color: rgba(0,0,0,0.03);
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  border-radius: 6px;
}

.diff-line.meta {
  color: #800080;
  opacity: 0.8;
}

.diff-line.add {
  background-color: rgba(16, 185, 129, 0.15); /* Green */
  color: #064e3b;
}

.diff-line.del {
  background-color: rgba(239, 68, 68, 0.15); /* Red */
  color: #7f1d1d;
}

.diff-line.normal {
  color: #374151;
}

.loading-state {
  padding: 1rem;
  color: #666;
  font-style: italic;
}

.no-diff-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  padding: 2rem;
}

.check-icon {
  font-size: 3rem;
  color: #10b981;
  margin-bottom: 0.5rem;
  filter: drop-shadow(0 4px 6px rgba(16, 185, 129, 0.2));
}
</style>
