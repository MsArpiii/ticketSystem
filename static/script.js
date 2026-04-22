// THEME TOGGLE
const toggleBtn = document.getElementById("themeToggle");

toggleBtn.addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
});


// BUBBLES
const bubbleContainer = document.querySelector(".bubbles");

for (let i = 0; i < 30; i++) {
    let bubble = document.createElement("span");

    let size = Math.random() * 20 + 10;

    bubble.style.width = size + "px";
    bubble.style.height = size + "px";
    bubble.style.left = Math.random() * 100 + "%";
    bubble.style.animationDuration = (Math.random() * 5 + 5) + "s";

    bubbleContainer.appendChild(bubble);
}


// SAND EFFECT
const canvas = document.getElementById("sandCanvas");
const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let particles = [];

document.addEventListener("mousemove", (e) => {
    for (let i = 0; i < 4; i++) {
        particles.push({
            x: e.clientX,
            y: e.clientY,
            size: Math.random() * 4,
            speedX: (Math.random() - 0.5) * 2,
            speedY: (Math.random() - 0.5) * 2
        });
    }
});

function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach((p, i) => {
        p.x += p.speedX;
        p.y += p.speedY;
        p.size *= 0.96;

        ctx.fillStyle = "rgba(255,255,255,0.5)";
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();

        if (p.size < 0.5) particles.splice(i, 1);
    });

    requestAnimationFrame(animate);
}

animate();

// FORM ELEMENTS
const form = document.getElementById("ticketForm");
const title = document.getElementById("title");
const desc = document.getElementById("desc");
const submitBtn = document.getElementById("submitBtn");
const charCount = document.getElementById("charCount");
const toast = document.getElementById("toast");

// CHARACTER COUNT
desc.addEventListener("input", () => {
    let len = desc.value.length;
    charCount.textContent = `${len} / 200`;

    if (len > 200) {
        charCount.style.color = "red";
    } else {
        charCount.style.color = "rgba(255,255,255,0.6)";
    }
});

// LIVE VALIDATION
title.addEventListener("input", () => {
    if (title.value.length < 3) {
        document.getElementById("titleError").textContent = "Min 3 characters";
    } else {
        document.getElementById("titleError").textContent = "";
    }
});

// LOADING BUTTON + TOAST
form.addEventListener("submit", (e) => {
    submitBtn.innerHTML = "⏳ Creating...";
    submitBtn.disabled = true;

    setTimeout(() => {
        toast.classList.add("show");
    }, 300);
});