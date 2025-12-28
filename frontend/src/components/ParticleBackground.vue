<template>
  <canvas ref="canvas" class="particle-canvas"></canvas>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'

export default {
  name: 'ParticleBackground',
  props: {
    enabled: {
      type: Boolean,
      default: true
    },
    particleCount: {
      type: Number,
      default: 80
    },
    particleColor: {
      type: String,
      default: '#3b82f6'
    },
    speed: {
      type: Number,
      default: 1
    }
  },
  setup(props) {
    const canvas = ref(null)
    let animationId = null
    let particles = []
    
    class Particle {
      constructor(canvas) {
        this.canvas = canvas
        this.x = Math.random() * canvas.width
        this.y = Math.random() * canvas.height
        this.vx = (Math.random() - 0.5) * props.speed
        this.vy = (Math.random() - 0.5) * props.speed
        this.radius = Math.random() * 2 + 1
        this.opacity = Math.random() * 0.5 + 0.2
      }
      
      update() {
        this.x += this.vx
        this.y += this.vy
        
        if (this.x < 0 || this.x > this.canvas.width) {
          this.vx = -this.vx
        }
        if (this.y < 0 || this.y > this.canvas.height) {
          this.vy = -this.vy
        }
      }
      
      draw(ctx) {
        ctx.save()
        ctx.globalAlpha = this.opacity
        ctx.fillStyle = props.particleColor
        ctx.beginPath()
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2)
        ctx.fill()
        ctx.restore()
      }
    }
    
    const initCanvas = () => {
      if (!canvas.value) return
      
      canvas.value.width = window.innerWidth
      canvas.value.height = window.innerHeight
      
      // 创建粒子
      particles = []
      for (let i = 0; i < props.particleCount; i++) {
        particles.push(new Particle(canvas.value))
      }
    }
    
    const animate = () => {
      if (!canvas.value || !props.enabled) return
      
      const ctx = canvas.value.getContext('2d')
      ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
      
      // 更新和绘制粒子
      particles.forEach(particle => {
        particle.update()
        particle.draw(ctx)
      })
      
      // 绘制连线
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const distance = Math.sqrt(dx * dx + dy * dy)
          
          if (distance < 120) {
            ctx.save()
            ctx.globalAlpha = (1 - distance / 120) * 0.3
            ctx.strokeStyle = props.particleColor
            ctx.lineWidth = 0.5
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.stroke()
            ctx.restore()
          }
        }
      }
      
      animationId = requestAnimationFrame(animate)
    }
    
    const handleResize = () => {
      initCanvas()
    }
    
    onMounted(() => {
      initCanvas()
      if (props.enabled) {
        animate()
      }
      window.addEventListener('resize', handleResize)
    })
    
    onUnmounted(() => {
      if (animationId) {
        cancelAnimationFrame(animationId)
      }
      window.removeEventListener('resize', handleResize)
    })
    
    return {
      canvas
    }
  }
}
</script>

<style scoped>
.particle-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  opacity: 0.6;
}
</style>
