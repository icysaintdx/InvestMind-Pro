// API 配置
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '' // 生产环境使用相对路径
  : 'http://localhost:8000' // 开发环境使用完整路径

export default API_BASE_URL
