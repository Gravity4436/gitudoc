<template>
  <div class="commit-history">
    <h3>提交历史（Commits）</h3>
    <div v-if="store.commits.length === 0" class="no-commits">
      No commits yet.
    </div>
    <ul v-else class="timeline">
      <li v-for="commit in store.commits" :key="commit.id" class="commit-item">
        <div class="timeline-marker"></div>
        <div class="commit-card">
          <div class="commit-header">
            <span class="commit-message">{{ commit.message }}</span>
            <span class="commit-date">{{ commit.date }}</span>
          </div>
          
          <!-- Modified Files Hint -->
          <div v-if="commit.files && commit.files.length > 0" class="commit-files">
            <span class="file-label">Modified:</span>
            <span v-for="(file, index) in commit.files" :key="index" class="file-tag">
              {{ file }}
            </span>
          </div>

          <div class="commit-meta">
            <span class="commit-author">👤 {{ commit.author }}</span>
            <span class="commit-id">#{{ commit.id.substring(0, 7) }}</span>
          </div>
          
          <div class="commit-actions">
            <button 
              v-if="store.selectedFile" 
              @click="handleRestore(commit.id)" 
              class="action-btn restore" 
              title="Save this version as a new file"
            >
              📄 Restore Copy
            </button>
            <button @click="handleRevert(commit.id)" class="action-btn revert" title="Revert (Advanced)">↩ Revert (Dev)</button>
            <button @click="handleReset(commit.id)" class="action-btn reset" title="Reset">⏮ Reset</button>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { useProjectsStore } from '@/stores/useProjectsStore';

const store = useProjectsStore();

async function handleRestore(id) {
  if (!store.selectedFile) return;
  if (confirm(`Create a copy of '${store.selectedFile}' from this version?`)) {
    try {
      await store.restoreFile(id, store.selectedFile);
      alert('Success! A copy has been created.');
    } catch (e) {
      alert('Restore failed: ' + e.message);
    }
  }
}

async function handleRevert(id) {
  if (confirm('Advanced: Revert creates a new commit that undoes changes. For .docx files, this often fails due to conflicts. Are you sure?')) {
    try {
      await store.revertCommit(id);
    } catch (e) {
      alert('Revert failed: ' + e.message);
    }
  }
}

async function handleReset(id) {
  if (confirm('WARNING: Are you sure you want to RESET to this commit? All changes after this commit will be LOST!')) {
    try {
      await store.resetToCommit(id);
    } catch (e) {
      alert('Reset failed: ' + e.message);
    }
  }
}
</script>

<style scoped>
.commit-history {
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

.timeline {
  list-style: none;
  padding: 0;
  margin: 0;
  position: relative;
  padding-left: 10px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 14px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: rgba(255, 255, 255, 0.3);
}

.commit-item {
  position: relative;
  padding-left: 30px;
  margin-bottom: 1.5rem;
}

.timeline-marker {
  position: absolute;
  left: 0;
  top: 5px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #a18cd1;
  border: 2px solid rgba(255,255,255,0.8);
  box-shadow: 0 0 0 4px rgba(161, 140, 209, 0.2);
  z-index: 1;
}

.commit-card {
  background: rgba(255, 255, 255, 0.4);
  border-radius: 12px;
  padding: 1rem;
  transition: all 0.2s;
  border: 1px solid rgba(255,255,255,0.2);
}

.commit-card:hover {
  background: rgba(255, 255, 255, 0.6);
  transform: translateX(2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.commit-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.commit-message {
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.95rem;
}

.commit-date {
  font-size: 0.75rem;
  color: #666;
  white-space: nowrap;
  margin-left: 0.5rem;
}

.commit-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #555;
  margin-bottom: 0.8rem;
}

.commit-files {
  font-size: 0.75rem;
  color: #666;
  margin-bottom: 0.8rem;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.file-label {
  font-weight: 600;
  margin-right: 4px;
}

.file-tag {
  background: rgba(0, 0, 0, 0.05);
  padding: 1px 4px;
  border-radius: 4px;
  font-family: monospace;
}

.commit-id {
  font-family: monospace;
  background: rgba(255,255,255,0.5);
  padding: 1px 4px;
  border-radius: 4px;
}

.commit-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.action-btn {
  padding: 0.3rem 0.6rem;
  font-size: 0.75rem;
  border-radius: 6px;
  border: none;
  background: rgba(255,255,255,0.6);
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.action-btn.restore {
  color: #fff;
  background: #52c41a; /* Green */
}

.action-btn.restore:hover {
  background: #73d13d;
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(82, 196, 26, 0.3);
}

.action-btn.revert:hover {
  color: #1890ff;
  background: #e6f7ff;
}

.action-btn.reset:hover {
  color: #ff4d4f;
  background: #fff1f0;
}

.no-commits {
  text-align: center;
  color: #666;
  padding: 2rem;
}
</style>
