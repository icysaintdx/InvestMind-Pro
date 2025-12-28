import { createApp } from 'vue'
import App from './App.vue'
import { installToast } from './utils/toast'

const app = createApp(App)

// 安装全局 Toast
installToast(app)

app.mount('#app')
