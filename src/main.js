import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import './styles/theme-dark.css'
import App from './App.vue'
import router from './router.js'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.mount('#app')

