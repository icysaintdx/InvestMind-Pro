// ==================== 粒子背景动画 ====================

(function() {
    const canvas = document.getElementById('particles-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const particles = [];
    const particleCount = 100;
    
    // 设置 canvas 大小
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    // 粒子类
    class Particle {
        constructor() {
            this.reset();
        }
        
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 0.5;
            this.vy = (Math.random() - 0.5) * 0.5;
            this.radius = Math.random() * 2 + 1;
            this.opacity = Math.random() * 0.5 + 0.2;
            this.color = Math.random() > 0.5 ? '59, 130, 246' : '139, 92, 246'; // 蓝色或紫色
        }
        
        update() {
            this.x += this.vx;
            this.y += this.vy;
            
            // 边界检测
            if (this.x < 0 || this.x > canvas.width) {
                this.vx *= -1;
            }
            if (this.y < 0 || this.y > canvas.height) {
                this.vy *= -1;
            }
            
            // 缓慢改变透明度
            this.opacity += (Math.random() - 0.5) * 0.01;
            this.opacity = Math.max(0.1, Math.min(0.6, this.opacity));
        }
        
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${this.color}, ${this.opacity})`;
            ctx.fill();
        }
    }
    
    // 创建粒子
    function createParticles() {
        for (let i = 0; i < particleCount; i++) {
            particles.push(new Particle());
        }
    }
    
    // 连接邻近粒子
    function connectParticles() {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 100) {
                    const opacity = (1 - distance / 100) * 0.2;
                    ctx.strokeStyle = `rgba(59, 130, 246, ${opacity})`;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
    }
    
    // 动画循环
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 更新和绘制粒子
        particles.forEach(particle => {
            particle.update();
            particle.draw();
        });
        
        // 连接粒子
        connectParticles();
        
        requestAnimationFrame(animate);
    }
    
    // 鼠标交互
    let mouse = { x: 0, y: 0 };
    
    canvas.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
        
        // 粒子受鼠标影响
        particles.forEach(particle => {
            const dx = particle.x - mouse.x;
            const dy = particle.y - mouse.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < 100) {
                const force = (100 - distance) / 100;
                particle.vx += dx * force * 0.01;
                particle.vy += dy * force * 0.01;
                
                // 限制速度
                particle.vx = Math.max(-2, Math.min(2, particle.vx));
                particle.vy = Math.max(-2, Math.min(2, particle.vy));
            }
        });
    });
    
    // 初始化
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
    createParticles();
    animate();
})();
