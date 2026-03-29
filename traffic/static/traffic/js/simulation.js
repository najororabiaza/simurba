const canvas = document.getElementById('traffic-canvas');
const ctx = canvas.getContext('2d');
canvas.width = 750;
canvas.height = 650;

// ─────────────────────────────────────────────────────────────
//  Chargement des images
// ─────────────────────────────────────────────────────────────
const bgImg = new Image();
bgImg.src = '/static/traffic/img/backgroundGrass.jpg';

const carsImg = new Image();
carsImg.src = '/static/traffic/img/bk_cars1.png';

const tlRedImg = new Image();
tlRedImg.src = '/static/traffic/img/trafficLight_red.png';

const tlGreenImg = new Image();
tlGreenImg.src = '/static/traffic/img/trafficLight_green.png';

// ─────────────────────────────────────────────────────────────
//  Sprites — bk_cars1.png
// ─────────────────────────────────────────────────────────────
const carSprites = [
    { sx: 380, sy:  32, sw:  96, sh: 194 }, // Ambulance
    { sx: 494, sy:  40, sw: 104, sh: 184 }, // Rouge
    { sx: 616, sy:  40, sw: 104, sh: 184 }, // Bleu
    { sx: 734, sy:  40, sw: 104, sh: 184 }, // Jaune
    { sx: 254, sy: 240, sw: 102, sh: 199 }, // Rose
    { sx: 378, sy: 240, sw: 102, sh: 198 }, // Orange
    { sx: 494, sy: 246, sw: 104, sh: 184 }, // Blanc
    { sx: 254, sy: 692, sw:  80, sh: 172 }, // Bleu sport
];

// ─────────────────────────────────────────────────────────────
//  Réseau routier — grille 3×3 alignée sur le fond city
// ─────────────────────────────────────────────────────────────
const nodes = [
    { x: 110, y: 114 }, { x: 374, y: 114 }, { x: 659, y: 114 },
    { x: 110, y: 324 }, { x: 374, y: 324 }, { x: 659, y: 324 },
    { x: 110, y: 559 }, { x: 374, y: 559 }, { x: 659, y: 559 },
];

const stateColors = { fluide: '#4ade80', ralenti: '#fb923c', bouchon: '#ef4444' };

const roads = [
    { from: nodes[0], to: nodes[1], state: 'fluide'  },
    { from: nodes[1], to: nodes[2], state: 'ralenti' },
    { from: nodes[3], to: nodes[4], state: 'fluide'  },
    { from: nodes[4], to: nodes[5], state: 'bouchon' },
    { from: nodes[6], to: nodes[7], state: 'ralenti' },
    { from: nodes[7], to: nodes[8], state: 'fluide'  },
    { from: nodes[0], to: nodes[3], state: 'fluide'  },
    { from: nodes[1], to: nodes[4], state: 'bouchon' },
    { from: nodes[2], to: nodes[5], state: 'fluide'  },
    { from: nodes[3], to: nodes[6], state: 'ralenti' },
    { from: nodes[4], to: nodes[7], state: 'fluide'  },
    { from: nodes[5], to: nodes[8], state: 'ralenti' },
];

const vehicles = roads.map(road => ({
    road,
    progress: Math.random(),
    baseSpeed: 0.002 + Math.random() * 0.003,
    sprite: carSprites[Math.floor(Math.random() * carSprites.length)],
}));

const trafficLights = nodes.map(node => ({
    node,
    state: Math.random() > 0.5 ? 'green' : 'red',
    timer: Math.floor(Math.random() * 200),
}));

// ─────────────────────────────────────────────────────────────
//  Contrôle de vitesse
// ─────────────────────────────────────────────────────────────
let speedFactor = 1;

const speedSlider = document.getElementById('speed-slider');
const speedLabel  = document.getElementById('speed-label');

speedSlider.addEventListener('input', () => {
    speedFactor = parseFloat(speedSlider.value);
    speedLabel.textContent = '×' + speedFactor;
});

// ─────────────────────────────────────────────────────────────
//  Horloge de simulation
// ─────────────────────────────────────────────────────────────
let simSeconds = 0;
let frameAcc   = 0;
const FPS_REF  = 60;

function updateClock() {
    frameAcc += speedFactor;
    if (frameAcc >= FPS_REF) {
        simSeconds++;
        frameAcc -= FPS_REF;
    }
    const mm = String(Math.floor(simSeconds / 60)).padStart(2, '0');
    const ss = String(simSeconds % 60).padStart(2, '0');
    document.getElementById('clock').textContent = mm + ':' + ss;
}

// ─────────────────────────────────────────────────────────────
//  Références boutons
// ─────────────────────────────────────────────────────────────
const btnStart = document.getElementById('btn-start');
const btnPause = document.getElementById('btn-pause');
const btnReset = document.getElementById('btn-reset');

// ─────────────────────────────────────────────────────────────
//  Helper : état des boutons selon running/paused
//  'running' → Démarrer grisé, Pauser actif
//  'paused'  → Démarrer actif, Pauser grisé
// ─────────────────────────────────────────────────────────────
function setButtons(state) {
    btnStart.disabled = (state === 'running');
    btnPause.disabled = (state === 'paused');
    // Réinitialiser toujours disponible — jamais disabled
}

// ─────────────────────────────────────────────────────────────
//  Helper : mise à jour du statut + dot
// ─────────────────────────────────────────────────────────────
function setStatus(text, color, paused = false) {
    const statusEl = document.getElementById('status');
    const dotEl    = document.getElementById('status-dot');
    statusEl.textContent = text;
    statusEl.style.color = color;
    dotEl.className = paused ? 'status-dot paused' : 'status-dot';
}

// ─────────────────────────────────────────────────────────────
//  Dessin
// ─────────────────────────────────────────────────────────────
function drawBackground() {
    if (bgImg.complete) {
        ctx.drawImage(bgImg, 0, 0, canvas.width, canvas.height);
    } else {
        ctx.fillStyle = '#3a7d2c';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
}

function drawRoadStates() {
    roads.forEach(road => {
        ctx.beginPath();
        ctx.moveTo(road.from.x, road.from.y);
        ctx.lineTo(road.to.x, road.to.y);
        ctx.strokeStyle = stateColors[road.state];
        ctx.lineWidth = 5;
        ctx.globalAlpha = 0.80;
        ctx.stroke();
        ctx.globalAlpha = 1;
    });
}

function drawRoundabouts() {
    nodes.forEach(node => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, 24, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(70, 70, 70, 0.30)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(40, 40, 40, 0.50)';
        ctx.lineWidth = 2.5;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(node.x, node.y, 11, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(55, 130, 55, 0.65)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(30, 90, 30, 0.60)';
        ctx.lineWidth = 1.5;
        ctx.stroke();
    });
}

function drawTrafficLights() {
    trafficLights.forEach(tl => {
        const img = tl.state === 'green' ? tlGreenImg : tlRedImg;
        if (img.complete) {
            ctx.drawImage(img, tl.node.x + 18, tl.node.y - 46, 28, 52);
        }

        const cx = tl.node.x + 52;
        const cy = tl.node.y - 32;

        ctx.beginPath();
        ctx.arc(cx, cy, 11, 0, Math.PI * 2);
        ctx.fillStyle = tl.state === 'green'
            ? 'rgba(74, 222, 128, 0.25)'
            : 'rgba(239, 68, 68, 0.25)';
        ctx.fill();

        ctx.beginPath();
        ctx.arc(cx, cy, 7, 0, Math.PI * 2);
        ctx.fillStyle = tl.state === 'green' ? '#4ade80' : '#ef4444';
        ctx.fill();
    });
}

function drawVehicles() {
    const laneOffset = 12;

    vehicles.forEach(v => {
        const rawX = v.road.from.x + (v.road.to.x - v.road.from.x) * v.progress;
        const rawY = v.road.from.y + (v.road.to.y - v.road.from.y) * v.progress;
        const dx = v.road.to.x - v.road.from.x;
        const dy = v.road.to.y - v.road.from.y;
        const len = Math.sqrt(dx * dx + dy * dy);

        const perpX = (-dy / len) * laneOffset;
        const perpY = (dx / len) * laneOffset;

        const isHorizontal = Math.abs(dx) > Math.abs(dy);
        const vertCorrection = isHorizontal ? -14 : 0;

        const x = rawX + perpX;
        const y = rawY + perpY + vertCorrection;
        const angle = Math.atan2(dy, dx) + Math.PI / 2;

        const displayW = 22;
        const displayH = 38;

        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);
        if (carsImg.complete) {
            ctx.drawImage(
                carsImg,
                v.sprite.sx, v.sprite.sy, v.sprite.sw, v.sprite.sh,
                -displayW / 2, -displayH / 2, displayW, displayH
            );
        }
        ctx.restore();
    });
}

// ─────────────────────────────────────────────────────────────
//  Mises à jour logiques
// ─────────────────────────────────────────────────────────────
function updateTrafficLights() {
    trafficLights.forEach(tl => {
        tl.timer += speedFactor;
        if (tl.timer > 300) {
            tl.state = tl.state === 'green' ? 'red' : 'green';
            tl.timer = 0;
        }
    });
}

function updateVehicles() {
    vehicles.forEach(v => {
        v.progress += v.baseSpeed * speedFactor;
        if (v.progress > 1) v.progress = 0;
    });
}

function updateDashboard() {
    const counts = { fluide: 0, ralenti: 0, bouchon: 0 };
    vehicles.forEach(v => counts[v.road.state]++);

    const total = vehicles.length;

    document.getElementById('count-total').textContent   = total;
    document.getElementById('count-fluide').textContent  = counts.fluide;
    document.getElementById('count-ralenti').textContent = counts.ralenti;
    document.getElementById('count-bouchon').textContent = counts.bouchon;

    document.getElementById('bar-fluide').style.width  = (counts.fluide  / total * 100) + '%';
    document.getElementById('bar-ralenti').style.width = (counts.ralenti / total * 100) + '%';
    document.getElementById('bar-bouchon').style.width = (counts.bouchon / total * 100) + '%';
}

// ─────────────────────────────────────────────────────────────
//  Boucle principale
// ─────────────────────────────────────────────────────────────
let running = true;
let animationId;

function loop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawBackground();
    drawRoadStates();
    drawRoundabouts();
    drawTrafficLights();
    drawVehicles();
    updateVehicles();
    updateTrafficLights();
    updateDashboard();
    updateClock();
    animationId = requestAnimationFrame(loop);
}

// ─────────────────────────────────────────────────────────────
//  Événements des boutons
// ─────────────────────────────────────────────────────────────
btnStart.addEventListener('click', () => {
    if (!running) {
        running = true;
        setStatus('en cours...', '#4ade80', false);
        setButtons('running');
        loop();
    }
});

btnPause.addEventListener('click', () => {
    running = false;
    cancelAnimationFrame(animationId);
    setStatus('en pause', '#fb923c', true);
    setButtons('paused');
});

btnReset.addEventListener('click', () => {
    vehicles.forEach(v => { v.progress = 0; });
    simSeconds = 0;
    frameAcc   = 0;
    document.getElementById('clock').textContent = '00:00';
    setStatus('en cours...', '#4ade80', false);
    setButtons('running');
    if (!running) { running = true; loop(); }
});

// ─────────────────────────────────────────────────────────────
//  Lancement : cache l'overlay quand les 4 images sont prêtes
// ─────────────────────────────────────────────────────────────
let imagesLoaded = 0;
const totalImages = 4;
const loadStart = Date.now();

[bgImg, carsImg, tlRedImg, tlGreenImg].forEach(img => {
    img.onload = () => {
        imagesLoaded++;
        if (imagesLoaded === totalImages) {
            const elapsed   = Date.now() - loadStart;
            const minDelay  = 3000;
            const remaining = Math.max(0, minDelay - elapsed);

            setTimeout(() => {
                const overlay = document.getElementById('loading-overlay');
                overlay.classList.add('hidden');
                setTimeout(() => overlay.remove(), 400);
                setButtons('running'); // Démarrer grisé dès le lancement
                loop();
            }, remaining);
        }
    };
});