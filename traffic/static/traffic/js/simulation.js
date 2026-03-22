const canvas = document.getElementById('traffic-canvas');
const ctx = canvas.getContext('2d');

canvas.width = 700;
canvas.height = 600;

// Grille 3x3 — 9 intersections
const nodes = [
    { x: 150, y: 120 }, { x: 350, y: 120 }, { x: 550, y: 120 },
    { x: 150, y: 300 }, { x: 350, y: 300 }, { x: 550, y: 300 },
    { x: 150, y: 480 }, { x: 350, y: 480 }, { x: 550, y: 480 },
];

const stateColors = {
    fluide:  '#4ade80',
    ralenti: '#fb923c',
    bouchon: '#ef4444',
};

const states = ['fluide', 'ralenti', 'bouchon'];

const roads = [
    // Horizontales
    { from: nodes[0], to: nodes[1], state: 'fluide'  },
    { from: nodes[1], to: nodes[2], state: 'ralenti' },
    { from: nodes[3], to: nodes[4], state: 'fluide'  },
    { from: nodes[4], to: nodes[5], state: 'bouchon' },
    { from: nodes[6], to: nodes[7], state: 'ralenti' },
    { from: nodes[7], to: nodes[8], state: 'fluide'  },
    // Verticales
    { from: nodes[0], to: nodes[3], state: 'fluide'  },
    { from: nodes[1], to: nodes[4], state: 'bouchon' },
    { from: nodes[2], to: nodes[5], state: 'fluide'  },
    { from: nodes[3], to: nodes[6], state: 'ralenti' },
    { from: nodes[4], to: nodes[7], state: 'fluide'  },
    { from: nodes[5], to: nodes[8], state: 'ralenti' },
];

const vehicleEmojis = ['🚗', '🚕', '🚙', '🚌', '🚑', '🚓'];

const vehicles = roads.map(road => ({
    road,
    progress: Math.random(),
    speed: 0.002 + Math.random() * 0.003,
    emoji: vehicleEmojis[Math.floor(Math.random() * vehicleEmojis.length)],
}));

function drawBackground() {
    // Fond herbe
    ctx.fillStyle = '#2d5a1b';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Texture herbe quadrillée
    ctx.strokeStyle = '#336b20';
    ctx.lineWidth = 1;
    for (let x = 0; x < canvas.width; x += 40) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 40) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
    }
}

function drawRoads() {
    roads.forEach(road => {
        // Asphalte
        ctx.beginPath();
        ctx.moveTo(road.from.x, road.from.y);
        ctx.lineTo(road.to.x, road.to.y);
        ctx.strokeStyle = '#555';
        ctx.lineWidth = 28;
        ctx.lineJoin = 'round';
        ctx.stroke();

        // Bord route
        ctx.beginPath();
        ctx.moveTo(road.from.x, road.from.y);
        ctx.lineTo(road.to.x, road.to.y);
        ctx.strokeStyle = '#777';
        ctx.lineWidth = 30;
        ctx.stroke();

        // Asphalte centre
        ctx.beginPath();
        ctx.moveTo(road.from.x, road.from.y);
        ctx.lineTo(road.to.x, road.to.y);
        ctx.strokeStyle = '#444';
        ctx.lineWidth = 26;
        ctx.stroke();

        // Marquage central coloré selon état
        ctx.beginPath();
        ctx.moveTo(road.from.x, road.from.y);
        ctx.lineTo(road.to.x, road.to.y);
        ctx.strokeStyle = stateColors[road.state];
        ctx.lineWidth = 2;
        ctx.setLineDash([12, 10]);
        ctx.stroke();
        ctx.setLineDash([]);
    });
}

function drawNodes() {
    nodes.forEach(node => {
        // Intersection asphalte
        ctx.beginPath();
        ctx.arc(node.x, node.y, 18, 0, Math.PI * 2);
        ctx.fillStyle = '#444';
        ctx.fill();

        // Halo
        ctx.beginPath();
        ctx.arc(node.x, node.y, 22, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255,255,255,0.15)';
        ctx.lineWidth = 2;
        ctx.stroke();
    });
}

function drawVehicles() {
    vehicles.forEach(v => {
        const x = v.road.from.x + (v.road.to.x - v.road.from.x) * v.progress;
        const y = v.road.from.y + (v.road.to.y - v.road.from.y) * v.progress;
        ctx.font = '14px serif';
        ctx.fillText(v.emoji, x - 8, y + 6);
    });
}

function updateVehicles() {
    vehicles.forEach(v => {
        v.progress += v.speed;
        if (v.progress > 1) v.progress = 0;
    });
}

function updateDashboard() {
    const counts = { fluide: 0, ralenti: 0, bouchon: 0 };
    vehicles.forEach(v => counts[v.road.state]++);
    document.getElementById('count-fluide').textContent = counts.fluide;
    document.getElementById('count-ralenti').textContent = counts.ralenti;
    document.getElementById('count-bouchon').textContent = counts.bouchon;
    const total = vehicles.length;
    document.getElementById('bar-fluide').style.width = (counts.fluide / total * 100) + '%';
    document.getElementById('bar-ralenti').style.width = (counts.ralenti / total * 100) + '%';
    document.getElementById('bar-bouchon').style.width = (counts.bouchon / total * 100) + '%';
}

let running = true;
let animationId;

function loop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawBackground();
    drawRoads();
    drawNodes();
    drawVehicles();
    updateVehicles();
    updateDashboard();
    animationId = requestAnimationFrame(loop);
}

document.getElementById('btn-start').addEventListener('click', () => {
    if (!running) {
        running = true;
        document.getElementById('status').textContent = 'en cours...';
        loop();
    }
});

document.getElementById('btn-pause').addEventListener('click', () => {
    running = false;
    cancelAnimationFrame(animationId);
    document.getElementById('status').textContent = 'en pause';
});

document.getElementById('btn-reset').addEventListener('click', () => {
    vehicles.forEach(v => { v.progress = 0; });
    document.getElementById('status').textContent = 'en cours...';
    if (!running) { running = true; loop(); }
});

loop();