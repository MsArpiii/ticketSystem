// ==========================================
// 🎵 WEB AUDIO API SYNTHESIZER
// ==========================================
let audioCtx = null;
let soundEnabled = false;

function initAudio() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
}

document.addEventListener('click', () => {
    if (!audioCtx) initAudio();
}, { once: true });

function playSound(type) {
    if (!soundEnabled) return;
    if (!audioCtx) initAudio();
    if (audioCtx.state === 'suspended') {
        audioCtx.resume().catch(() => {});
    }
    if (!audioCtx) return;

    const osc = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    
    osc.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    const now = audioCtx.currentTime;

    if (type === 'pop') {
        // Fun bouncy tick
        osc.type = 'sine';
        osc.frequency.setValueAtTime(400, now);
        osc.frequency.linearRampToValueAtTime(1000, now + 0.05);
        gainNode.gain.setValueAtTime(0, now);
        gainNode.gain.linearRampToValueAtTime(0.5, now + 0.01);
        gainNode.gain.linearRampToValueAtTime(0, now + 0.1);
        osc.start(now);
        osc.stop(now + 0.1);
    } 
    else if (type === 'create') {
        // Ascending triangle whoosh
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(200, now);
        osc.frequency.linearRampToValueAtTime(800, now + 0.3);
        gainNode.gain.setValueAtTime(0, now);
        gainNode.gain.linearRampToValueAtTime(0.3, now + 0.1);
        gainNode.gain.linearRampToValueAtTime(0, now + 0.3);
        osc.start(now);
        osc.stop(now + 0.3);
    }
    else if (type === 'resolve') {
        // Polyphonic chime arpeggio
        const freqs = [523.25, 659.25, 783.99, 1046.50]; // C Major chord
        freqs.forEach((freq, i) => {
            const o = audioCtx.createOscillator();
            const g = audioCtx.createGain();
            o.type = 'sine';
            o.frequency.value = freq;
            o.connect(g);
            g.connect(audioCtx.destination);
            
            const start = now + (i * 0.1);
            g.gain.setValueAtTime(0, start);
            g.gain.linearRampToValueAtTime(0.2, start + 0.05);
            g.gain.linearRampToValueAtTime(0, start + 0.5);
            
            o.start(start);
            o.stop(start + 0.5);
        });
    }
}

// Sound Toggle Logic
const soundToggleBtn = document.getElementById('soundToggle');
if (soundToggleBtn) {
    soundEnabled = localStorage.getItem('soundEnabled') === 'true';
    soundToggleBtn.textContent = soundEnabled ? '🔊 Sound: On' : '🔇 Sound: Off';

    soundToggleBtn.addEventListener('click', () => {
        initAudio();
        soundEnabled = !soundEnabled;
        localStorage.setItem('soundEnabled', soundEnabled);
        soundToggleBtn.textContent = soundEnabled ? '🔊 Sound: On' : '🔇 Sound: Off';
        if (soundEnabled) playSound('pop');
    });
}

// ==========================================
// 🫧 INTERACTIVE PHYSICS CANVAS (Bubbles)
// ==========================================
const canvas = document.getElementById('bubbleCanvas');
let ctx = null;
let bubbles = [];
let mouse = { x: -1000, y: -1000 };

// Pop Score Tracking
let popScore = parseInt(localStorage.getItem('popScore')) || 0;
const scoreDisplay = document.getElementById('popScoreDisplay');
if (scoreDisplay) scoreDisplay.textContent = popScore;

function incrementPopScore() {
    popScore++;
    localStorage.setItem('popScore', popScore);
    if (scoreDisplay) {
        scoreDisplay.textContent = popScore;
        scoreDisplay.style.transform = 'scale(1.5)';
        setTimeout(() => scoreDisplay.style.transform = 'scale(1)', 150);
    }
    playSound('pop');
}

if (canvas) {
    ctx = canvas.getContext('2d');
    
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    document.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });
    
    document.addEventListener('click', (e) => {
        // Pop any bubble clicked
        for (let i = bubbles.length - 1; i >= 0; i--) {
            const b = bubbles[i];
            const dx = e.clientX - b.x;
            const dy = e.clientY - b.y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            if (dist < b.radius) {
                bubbles.splice(i, 1);
                incrementPopScore();
                createParticles(b.x, b.y, b.color);
            }
        }
    });

    class Bubble {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = canvas.height + Math.random() * 100;
            this.radius = Math.random() * 30 + 10;
            this.speedY = Math.random() * -1 - 0.5;
            this.speedX = (Math.random() - 0.5) * 0.5;
            
            const colors = [
                'rgba(255, 182, 193, 0.4)', // Pink
                'rgba(173, 216, 230, 0.4)', // Light blue
                'rgba(221, 160, 221, 0.4)', // Plum
                'rgba(152, 251, 152, 0.4)'  // Pale green
            ];
            this.color = colors[Math.floor(Math.random() * colors.length)];
        }

        update() {
            // Mouse Displacement Force
            const dx = this.x - mouse.x;
            const dy = this.y - mouse.y;
            const forceDist = 150;

            // Fast AABB check before expensive Math.sqrt
            if (Math.abs(dx) < forceDist && Math.abs(dy) < forceDist) {
                const dist = Math.sqrt(dx*dx + dy*dy);

                if (dist < forceDist) {
                    const force = (forceDist - dist) / forceDist;
                    this.x += (dx / dist) * force * 5;
                    this.y += (dy / dist) * force * 5;
                    
                    // If cursor is super close and moving fast, pop it!
                    if (dist < this.radius + 10) {
                        return true; // flag for pop
                    }
                }
            }

            this.y += this.speedY;
            this.x += this.speedX;

            // Wobble
            this.x += Math.sin(this.y * 0.05) * 0.5;

            return this.y + this.radius < 0; // flag if off screen
        }

        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.fill();
            ctx.strokeStyle = 'rgba(255,255,255,0.6)';
            ctx.lineWidth = 1;
            ctx.stroke();
            
            // Highlight
            ctx.beginPath();
            ctx.arc(this.x - this.radius*0.3, this.y - this.radius*0.3, this.radius*0.2, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(255,255,255,0.8)';
            ctx.fill();
        }
    }

    let particles = [];
    function createParticles(x, y, color) {
        for (let i=0; i<8; i++) {
            particles.push({
                x: x, y: y,
                vx: (Math.random()-0.5)*5, vy: (Math.random()-0.5)*5,
                life: 1.0, color: color
            });
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Add new bubbles randomly
        if (bubbles.length < 30 && Math.random() < 0.02) {
            bubbles.push(new Bubble());
        }

        // Update and draw bubbles
        for (let i = bubbles.length - 1; i >= 0; i--) {
            const popped = bubbles[i].update();
            bubbles[i].draw();

            if (popped) {
                // Only increment score if popped by mouse (near mouse)
                const dx = bubbles[i].x - mouse.x;
                const dy = bubbles[i].y - mouse.y;
                if (Math.abs(dx) < 150 && Math.abs(dy) < 150) {
                    if (Math.sqrt(dx*dx + dy*dy) < 150) {
                        incrementPopScore();
                        createParticles(bubbles[i].x, bubbles[i].y, bubbles[i].color);
                    }
                }
                bubbles.splice(i, 1);
            }
        }

        // Draw particles
        for (let i = particles.length - 1; i >= 0; i--) {
            const p = particles[i];
            p.x += p.vx; p.y += p.vy; p.life -= 0.05;
            if (p.life <= 0) {
                particles.splice(i, 1);
                continue;
            }
            ctx.globalAlpha = p.life;
            ctx.fillStyle = '#fff';
            ctx.beginPath();
            ctx.arc(p.x, p.y, 2, 0, Math.PI*2);
            ctx.fill();
            ctx.globalAlpha = 1.0;
        }

        requestAnimationFrame(animate);
    }
    animate();
}

// ==========================================
// 🖱️ BIND SOUNDS TO UI ELEMENTS
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    // Form Submissions
    const forms = document.querySelectorAll("form");
    forms.forEach(f => {
        f.addEventListener("submit", (e) => {
            if (soundEnabled && audioCtx) {
                e.preventDefault();
                playSound('create');
                setTimeout(() => {
                    f.submit();
                }, 300);
            }
        });
    });

    // Resolve Button
    const resolveBtns = document.querySelectorAll('a[href*="/resolve/"]');
    resolveBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (soundEnabled && audioCtx) {
                e.preventDefault();
                playSound('resolve');
                setTimeout(() => {
                    window.location.href = btn.href;
                }, 500);
            }
        });
    });
});