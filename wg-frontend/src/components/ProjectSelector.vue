<template>
  <div class="project-selector">
    <h2>选择一个项目</h2>
    <div class="project-list">
      <div 
        v-for="proj in store.projects" 
        :key="proj" 
        class="project-item"
        @click="store.selectProject(proj)"
      >
        <span class="project-path">{{ proj }}</span>
        <button @click.stop="handleRemove(proj)" class="remove-btn" title="Remove from list">🗑️</button>
      </div>
      <div v-if="store.projects.length === 0" class="no-projects">
        No projects found. Add one below.
      </div>
    </div>

    <div class="add-project">
      <h3>添加项目</h3>
      <div class="input-group">
        <input v-model="newProjectPath" placeholder="Absolute path to project folder..." />
        <button @click="handleAdd" :disabled="!newProjectPath">Add</button>
      </div>
      <p v-if="errorMsg" class="error">{{ errorMsg }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useProjectsStore } from '@/stores/useProjectsStore';

const store = useProjectsStore();
const newProjectPath = ref('');
const errorMsg = ref('');

onMounted(() => {
  store.fetchProjects();
});

async function handleAdd() {
  errorMsg.value = '';
  try {
    await store.addProject(newProjectPath.value);
    newProjectPath.value = '';
  } catch (e) {
    errorMsg.value = 'Failed to add project. Check path and backend.';
  }
}

async function handleRemove(path) {
  if (confirm(`您确定要从列表中移除 "${path}" 吗？（文件不会被删除）`)) {
    try {
      await store.removeProject(path);
    } catch (e) {
      alert('Failed to remove project.');
    }
  }
}
</script>

<style scoped>
.project-selector {
  max-width: 600px;
  margin: 0 auto;
}

.project-list {
  margin: 1rem 0;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.project-item {
  padding: 1rem;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-path {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 1rem;
}

.remove-btn {
  background: none;
  border: none;
  padding: 0.2rem 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  opacity: 0.5;
  transition: all 0.2s;
  border-radius: 4px;
}

.remove-btn:hover {
  opacity: 1;
  background-color: rgba(255, 0, 0, 0.1);
  transform: scale(1.1);
}

.project-item:last-child {
  border-bottom: none;
}

.project-item:hover {
  background-color: #f0f0f0;
}

.no-projects {
  padding: 1rem;
  color: #888;
  text-align: center;
}

.add-project {
  margin-top: 2rem;
  padding: 1rem;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.input-group {
  display: flex;
  gap: 0.5rem;
}

input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  padding: 0.5rem 1rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background-color: #ccc;
}

.error {
  color: red;
  margin-top: 0.5rem;
  font-size: 0.9rem;
}
</style>
