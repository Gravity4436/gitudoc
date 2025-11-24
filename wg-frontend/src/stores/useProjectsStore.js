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
    const allFiles = ref([]); // List of all .docx files
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

    async function selectFile(path) {
        selectedFile.value = path;
        await fetchLog();
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

    async function fetchFiles() {
        if (!activeProject.value) return;
        try {
            const res = await apiClient.get('/files', {
                params: { project_path: activeProject.value }
            });
            allFiles.value = res.data;
        } catch (error) {
            console.error("Failed to fetch files:", error);
        }
    }

    async function fetchLog() {
        if (!activeProject.value) return;
        try {
            const params = { project_path: activeProject.value };
            // If a file is selected, filter logs for that file
            if (selectedFile.value) {
                params.files = [selectedFile.value];
            }

            // Note: We need to pass 'files' as a list in query params
            // axios handles array params by default as files[]=a&files[]=b
            // FastAPI expects ?files=a&files=b
            // We might need to use URLSearchParams or custom serializer if axios default doesn't match
            // But let's try simple object first, axios usually does a good job.
            // Actually, for GET with array, axios default is 'files[]'. FastAPI wants 'files'.
            // Let's use URLSearchParams to be safe.

            const queryParams = new URLSearchParams();
            queryParams.append('project_path', activeProject.value);
            if (selectedFile.value) {
                queryParams.append('files', selectedFile.value);
            }

            const res = await apiClient.get('/log', { params: queryParams });
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

    async function restoreFile(commitId, fileName) {
        if (!activeProject.value) return;
        await apiClient.post('/restore', {
            commit_id: commitId,
            file_name: fileName
        }, {
            params: { project_path: activeProject.value }
        });
        // No need to fetch status immediately as it creates a new file, 
        // but good practice to refresh
        await fetchStatus();
    }

    function startPollingStatus() {
        if (pollingInterval) clearInterval(pollingInterval);
        fetchStatus(); // Immediate fetch
        fetchFiles(); // Fetch all files
        pollingInterval = setInterval(() => {
            fetchStatus();
            fetchFiles(); // Keep file list updated (in case new files are added)
            fetchLog(); // Also poll logs to keep history updated
        }, 2000);
    }

    function stopPollingStatus() {
        if (pollingInterval) clearInterval(pollingInterval);
    }

    return {
        projects, activeProject, changedFiles, allFiles, selectedFile, stagedFiles, commits,
        hasActiveProject,
        fetchProjects, addProject, removeProject, selectProject, deselectProject, fetchStatus, fetchFiles, fetchLog, selectFile,
        resetToCommit, revertCommit, restoreFile
    };
});
