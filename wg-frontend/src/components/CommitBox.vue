<template>
  <div class="commit-box">
    <textarea 
      v-model="commitMessage" 
      placeholder="Commit message..."
      rows="3"
    ></textarea>
    <button 
      @click="handleCommit"
      :disabled="!canCommit"
      class="commit-btn"
    >
      Commit ({{ store.stagedFiles.length }})
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useProjectsStore } from '@/stores/useProjectsStore';
import axios from 'axios';

const store = useProjectsStore();
const commitMessage = ref('');

const canCommit = computed(() => {
  return store.stagedFiles.length > 0 && commitMessage.value.trim() !== '';
});

async function handleCommit() {
  if (!canCommit.value) return;

  try {
    await axios.post('http://localhost:8000/api/commit', {
      message: commitMessage.value,
      files: store.stagedFiles
    }, {
      params: { project_path: store.activeProject }
    });
    
    // Success
    commitMessage.value = '';
    store.stagedFiles = [];
    store.fetchStatus(); // Refresh
    
  } catch (error) {
    alert("Commit failed: " + error.message);
  }
}
</script>

<style scoped>
.commit-box {
  border-top: 1px solid rgba(255,255,255,0.3);
  padding-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

textarea {
  width: 100%;
  box-sizing: border-box; /* Ensure padding doesn't add to width */
  resize: vertical;
  padding: 0.8rem;
  border: 1px solid rgba(255,255,255,0.4);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.4);
  font-family: inherit;
  font-size: 0.9rem;
  color: #2c3e50;
  transition: all 0.2s;
  outline: none;
}

textarea:focus {
  background: rgba(255, 255, 255, 0.6);
  border-color: #a18cd1;
  box-shadow: 0 0 0 3px rgba(161, 140, 209, 0.2);
}

textarea::placeholder {
  color: #888;
}

.commit-btn {
  width: 100%; /* Match textarea width */
  box-sizing: border-box;
  background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%);
  color: white;
  border: none;
  padding: 0.8rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 0.9rem;
  box-shadow: 0 4px 6px rgba(161, 140, 209, 0.3);
  transition: all 0.2s;
}

.commit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(161, 140, 209, 0.4);
  filter: brightness(1.05);
}

.commit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.commit-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  box-shadow: none;
  opacity: 0.7;
}
</style>
