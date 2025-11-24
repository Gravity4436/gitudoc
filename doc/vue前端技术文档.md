Vue.js 前端 (wg-desktop) 技术文档
1. 🎯 核心目标
解决“流畅性”问题： 创建一个“仪表盘”，用户无需离开写作流程即可被动地看到文件变更。

可视化操作： 将 wg 的命令行操作（diff, commit, log, restore）转换为直观的 UI 交互（点击、勾选、按钮）。

状态分离： “查看”（自动刷新 diff）和**“操作”**（手动点击 commit）必须是两个独立的工作流。

**项目管理**: 提供一个统一的界面来添加和选择不同的 `wg` 项目。

2. 🛠️ 技术选型
框架：Vue.js (V3)

理由： 用户首选。我们将使用 Composition API（组合式 API）来组织逻辑。

API 客户端：axios

理由： 易于使用，能方便地处理 base_url 和错误拦截。fetch 也可以，但 axios 更方便。

状态管理：Pinia

理由： 官方推荐。我们需要一个全局 Store 来管理“当前选中的文件”、“已勾选的文件”和“文件列表”，以便在组件间共享状态。

Diff 视图：vue-diff

理由： 一个现成的库，可以轻松渲染出漂亮的红绿 diff 视图。

实时更新：轮询 (Polling)

理由： 作为 V5.0 的起点，这是最简单、最可靠的实现。Vue 应用将在**选中一个项目后**，每 2 秒调用一次 `/api/status`。

（V5.1 升级路径是使用 WebSockets 替换轮询）

3. 🏗️ 构建逻辑与组件 (Components)
我们将应用拆分为**两个主视图**：`ProjectSelector.vue` 和 `Dashboard.vue` (仪表盘)。`App.vue` 将根据 Pinia store 中是否存在“当前活动项目”来决定显示哪个视图。

3.1 状态管理 (useProjectsStore.js - Pinia)
这是应用的“大脑”，现在负责管理项目列表和当前活动项目的所有状态。

JavaScript

// stores/useProjectsStore.js
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import axios from 'axios';

// API 客户端
const apiClient = axios.create({ baseURL: 'http://localhost:8000/api' });

export const useProjectsStore = defineStore('projects', () => {
  // --- State ---
  const projects = ref([]); // 所有已添加项目的路径列表
  const activeProject = ref(null); // 当前选中的项目路径, e.g., "/path/to/my-report"
  
  const changedFiles = ref([]); // 当前活动项目的变更文件
  const selectedFile = ref(null); // 用户点击用于查看 diff 的文件
  const stagedFiles = ref([]);   // 用户勾选用于提交的文件

  // --- Getters ---
  const hasActiveProject = computed(() => activeProject.value !== null);

  // --- Actions ---
  async function fetchProjects() {
    // 从 /api/projects 获取列表
    const res = await apiClient.get('/projects');
    projects.value = res.data;
  }

  async function addProject(path) {
    // 调用 POST /api/projects
    await apiClient.post('/projects', { path });
    await fetchProjects(); // 重新加载列表
  }
  
  function selectProject(path) {
    activeProject.value = path;
    // 清理旧状态并开始轮询
    changedFiles.value = [];
    selectedFile.value = null;
    stagedFiles.value = [];
    startPollingStatus();
  }
  
  function deselectProject() {
      activeProject.value = null;
      stopPollingStatus();
  }

  // --- 轮询 Actions ---
  let pollingInterval = null;

  async function fetchStatus() {
    if (!activeProject.value) return;
    try {
      const res = await apiClient.get('/status', {
        params: { project_path: activeProject.value }
      });
      changedFiles.value = res.data;
    } catch (error) {
      console.error("无法获取状态:", error);
    }
  }

  function startPollingStatus() {
    if (pollingInterval) clearInterval(pollingInterval);
    fetchStatus(); // 立即执行一次
    pollingInterval = setInterval(fetchStatus, 2000);
  }

  function stopPollingStatus() {
      if (pollingInterval) clearInterval(pollingInterval);
  }
  
  return { 
      projects, activeProject, changedFiles, selectedFile, stagedFiles,
      hasActiveProject,
      fetchProjects, addProject, selectProject, deselectProject, fetchStatus
  };
});
3.2 (新增) 项目选择器 (ProjectSelector.vue)
应用启动时的初始界面。

代码段

<template>
  <div>
    <h1>选择一个项目或添加新项目</h1>
    <div v-for="proj in store.projects" :key="proj" @click="store.selectProject(proj)">
      {{ proj }}
    </div>
    <input v-model="newProjectPath" placeholder="粘贴项目完整路径..." />
    <button @click="store.addProject(newProjectPath)">添加项目</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useProjectsStore } from '@/stores/useProjectsStore';
const store = useProjectsStore();
const newProjectPath = ref('');

onMounted(() => {
  store.fetchProjects(); // 组件加载时获取项目列表
});
</script>
3.3 (重构) 仪表盘 (Dashboard.vue)
这个组件现在是 `ChangesList`, `DiffView`, `CommitBox` 的容器。

3.4 变更列表 (ChangesList.vue)
**无重大变更**。它依赖的 `store.changedFiles`, `store.selectedFile` 和 `store.stagedFiles` 依然由 Pinia store 提供，只是这个 store 现在是 `useProjectsStore`。

3.5 差异视图 (DiffView.vue)
**逻辑微调**。`apiClient.get` 调用需要传递当前活动项目路径。

代码段

<template>
  <div class="diff-view">
    <h3 v-if="selectedFile">{{ selectedFile }}</h3>
    <h3 v-else>请从左侧选择一个文件查看差异</h3>
    
    <vue-diff 
      v-if="diffData"
      :old-string="diffData.old" 
      :new-string="diffData.new" 
      mode="split" 
    />
    </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useProjectsStore } from '@/stores/useProjectsStore';
// import { VueDiff } from 'vue-diff'; // (假设已安装)

const store = useProjectsStore();
const rawDiff = ref('');
// const diffData = ref({ old: '', new: '' });

// --- 解决“流畅性”的核心 ---
// 监视 Pinia store 中的 'selectedFile'
watch(() => store.selectedFile, async (newFile) => {
  if (newFile && store.activeProject) {
    rawDiff.value = '正在加载...';
    try {
      const res = await apiClient.get(`/diff/${newFile}`, {
          params: { project_path: store.activeProject } // <-- 关键变更
      });
      rawDiff.value = res.data.diff;
      // (如果使用 vue-diff, 在这里解析 res.data.diff)
    } catch (error) {
      rawDiff.value = `无法加载 ${newFile} 的差异。`;
    }
  }
});
</script>
3.6 提交栏 (CommitBox.vue)
**逻辑微调**。`apiClient.post` 调用需要传递当前活动项目路径。

代码段

<template>
  <div class="commit-box">
    <textarea 
      v-model="commitMessage" 
      placeholder="输入提交信息..."
    ></textarea>
    <button 
      @click="handleCommit"
      :disabled="!canCommit"
    >
      提交 ({{ store.stagedFiles.length }} 个文件)
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useProjectsStore } from '@/stores/useProjectsStore';
const store = useProjectsStore();

const commitMessage = ref('');

// 计算属性：是否可以提交
const canCommit = computed(() => {
  return store.stagedFiles.length > 0 && commitMessage.value.trim() !== '';
});

async function handleCommit() {
  if (!canCommit.value) return;

  try {
    await apiClient.post('/commit', {
      message: commitMessage.value,
      files: store.stagedFiles
    }, {
      params: { project_path: store.activeProject } // <-- 关键变更
    });
    
    // 提交成功！
    commitMessage.value = '';
    store.stagedFiles = [];
    store.fetchStatus(); // 立即刷新状态
    
  } catch (error) {
    console.error("提交失败:", error);
    // (在这里向用户显示一个错误提示)
  }
}
</script>