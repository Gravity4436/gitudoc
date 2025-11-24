import './style.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import VueDiff from 'vue-diff'
import 'vue-diff/dist/index.css'

import App from './App.vue'

const app = createApp(App)

app.use(createPinia())
app.use(VueDiff)

app.mount('#app')
