import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import axios from 'axios';

// API Client
const apiClient = axios.create({ baseURL: 'http://localhost:8000/api' });

export const useProjectsStore = defineStore('projects', () => {
    // --- State ---
    const projects = ref([]); // List of project paths
    const activeProject = ref(null); // Currently selected project path

    const changedFiles = ref([]); // List of changed files in active project
    const selectedFile = ref(null); // File selected for diff view
    const stagedFiles = ref([]);   // Files selected for commit (currently we stage all or specific, let's keep it simple)

    const commits = ref([]); // Commit history

    // --- Getters ---
    const hasActiveProject = computed(() => activeProject.value !== null);

    // --- Actions ---
    async function fetchProjects() {
        try {
            const res = await apiClient.get('/projects');
            projects.value = res.data;
        } catch (error) {
            console.error("Failed to fetch projects:", error);
        }
    }

    async function addProject(path) {
        try {
            await apiClient.post('/projects', { path });
            await fetchProjects();
        } catch (error) {
            console.error("Failed to add project:", error);
            throw error;
        }
    }

    async function removeProject(path) {
        try {
            await apiClient.delete('/projects', { params: { path } });
            await fetchProjects();
        } catch (error) {
            console.error("Failed to remove project:", error);
            throw error;
        }
    }

    async function selectProject(path) {
        activeProject.value = path;
        // Reset state
        changedFiles.value = [];
        selectedFile.value = null;
        stagedFiles.value = [];
        commits.value = [];

        // Ensure project is initialized (idempotent check)
        try {
            await apiClient.post('/init', null, {
                params: { project_path: path }
            });
        } catch (e) {
            console.error("Failed to ensure project init:", e);
            // Continue anyway, maybe it's just a network glitch or permission issue
        }

        startPollingStatus();
        fetchLog(); // Fetch logs initially
    }

    function deselectProject() {
        activeProject.value = null;
        stopPollingStatus();
    }

    // --- Polling Actions ---
    let pollingInterval = null;

    async function fetchStatus() {
        if (!activeProject.value) return;
        try {
            const res = await apiClient.get('/status', {
                params: { project_path: activeProject.value }
            });
            changedFiles.value = res.data;
        } catch (error) {
            console.error("Failed to fetch status:", error);
        }
    }

    async function fetchLog() {
        if (!activeProject.value) return;
        try {
            const res = await apiClient.get('/log', {
                params: { project_path: activeProject.value }
            });
            commits.value = res.data;
        } catch (error) {
            console.error("Failed to fetch log:", error);
        }
    }

    async function resetToCommit(commitId) {
        if (!activeProject.value) return;
        await apiClient.post('/reset', { commit_id: commitId }, {
            params: { project_path: activeProject.value }
        });
        await fetchStatus();
        await fetchLog();
    }

    async function revertCommit(commitId) {
        if (!activeProject.value) return;
        await apiClient.post('/revert', { commit_id: commitId }, {
            params: { project_path: activeProject.value }
        });
        await fetchStatus();
        await fetchLog();
    }

    function startPollingStatus() {
        if (pollingInterval) clearInterval(pollingInterval);
        fetchStatus(); // Immediate fetch
        pollingInterval = setInterval(() => {
            fetchStatus();
            fetchLog(); // Also poll logs to keep history updated
        }, 2000);
    }

    function stopPollingStatus() {
        if (pollingInterval) clearInterval(pollingInterval);
    }

    return {
        projects, activeProject, changedFiles, selectedFile, stagedFiles, commits,
        hasActiveProject,
        fetchProjects, addProject, removeProject, selectProject, deselectProject, fetchStatus, fetchLog,
        resetToCommit, revertCommit
    };
});
