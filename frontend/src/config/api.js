// API 配置
const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? `http://${window.location.hostname}:8000` // 生产环境使用当前IP+后端端口
  : 'http://localhost:8000' // 开发环境使用完整路径

// WebSocket 配置
const getWsBaseUrl = () => {
  if (process.env.NODE_ENV === 'production') {
    // 生产环境：根据当前页面协议和主机动态生成
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}`
  }
  return 'ws://' + window.location.hostname + ':8000'
}

export const WS_BASE_URL = getWsBaseUrl()
export default API_BASE_URL
