const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  chainWebpack: config => {
    config
      .plugin('html')
      .tap(args => {
        args[0].title = 'InvestMind Pro - 智投顾问团'
        return args
      })
  },
  devServer: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
        secure: false,
        logLevel: 'debug',
        onError(err) {
          console.error('Proxy error:', err);
        },
        onProxyReq(proxyReq, req) {
          console.log('Proxying:', req.method, req.url);
        }
      }
    }
  }
})
