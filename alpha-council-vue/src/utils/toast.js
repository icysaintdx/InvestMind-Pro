import { createApp } from 'vue'
import Toast from '@/components/Toast.vue'

let toastInstance = null
let toastApp = null

const initToast = () => {
  if (!toastInstance) {
    // 创建一个挂载点
    const mountNode = document.createElement('div')
    document.body.appendChild(mountNode)
    
    // 创建 Toast 实例
    toastApp = createApp(Toast)
    toastInstance = toastApp.mount(mountNode)
  }
  return toastInstance
}

const toast = {
  show(options) {
    const instance = initToast()
    instance.show(options)
  },
  
  success(message, duration) {
    const instance = initToast()
    instance.success(message, duration)
  },
  
  error(message, duration) {
    const instance = initToast()
    instance.error(message, duration)
  },
  
  warning(message, duration) {
    const instance = initToast()
    instance.warning(message, duration)
  },
  
  info(message, duration) {
    const instance = initToast()
    instance.info(message, duration)
  },
  
  hide() {
    if (toastInstance) {
      toastInstance.hide()
    }
  }
}

// 创建一个 confirm 的替代方案
toast.confirm = (message, onConfirm, onCancel) => {
  // 暂时使用原生 confirm，后续可以实现自定义确认框
  const result = window.confirm(message)
  if (result && onConfirm) {
    onConfirm()
  } else if (!result && onCancel) {
    onCancel()
  }
  return result
}

// 提供一个全局安装方法
export const installToast = (app) => {
  app.config.globalProperties.$toast = toast
  window.$toast = toast
}

export default toast
