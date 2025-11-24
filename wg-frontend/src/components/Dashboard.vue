<template>
  <div class="dashboard">
    <div class="sidebar glass-panel">
      <ChangesList />
      <CommitBox />
    </div>
    <div class="main-content glass-panel">
      <DiffView />
    </div>
    <div class="history-panel glass-panel">
      <CommitHistory />
    </div>
  </div>
</template>

<script setup>
import ChangesList from './ChangesList.vue';
import CommitBox from './CommitBox.vue';
import DiffView from './DiffView.vue';
import CommitHistory from './CommitHistory.vue';
</script>

<style scoped>
.dashboard {
  display: grid;
  grid-template-columns: 300px 1fr 320px;
  grid-template-rows: minmax(0, 1fr); /* Force row to fit container */
  gap: 20px;
  height: 100%;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  overflow: hidden;
  /* Apply subtle liquid filter to borders if desired, but keep it clean for layout */
}

.main-content {
  overflow: hidden;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  min-height: 0; /* Critical for flex scrolling */
  height: 100%; /* Ensure it fills the grid cell */
}

.history-panel {
  padding: 1.5rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
