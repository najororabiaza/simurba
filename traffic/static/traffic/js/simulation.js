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
//  Réseau routier — grille 3×3
// ─────────────────────────────────────────────────────────────
const nodes = [
    { x: 110, y: 114 }, { x: 374, y: 114 }, { x: 659, y: 114 },
    { x: 110, y: 324 }, { x: 374, y: 324 }, { x: 659, y: 324 },
    { x: 110, y: 559 }, { x: 374, y: 559 }, { x: 659, y: 559 },
];

const stateColors = { fluide: '#4ade80', ralenti: '#fb923c', bouchon: '#ef4444' };
const stateLabels = { fluide: 'Fluide', ralenti: 'Ralenti', bouchon: 'Bouchon' };

// Noms lisibles pour le tooltip (ex: "A1 → A2")
const roads = [
    { from: nodes[0], to: nodes[1], state: 'fluide',  name: 'Route 1 — N→E (haut)'     },
    { from: nodes[1], to: nodes[2], state: 'ralenti', name: 'Route 2 — N→E (haut)'     },
    { from: nodes[3], to: nodes[4], state: 'fluide',  name: 'Route 3 — N→E (milieu)'   },
    { from: nodes[4], to: nodes[5], state: 'bouchon', name: 'Route 4 — N→E (milieu)'   },
    { from: nodes[6], to: nodes[7], state: 'ralenti', name: 'Route 5 — N→E (bas)'      },
    { from: nodes[7], to: nodes[8], state: 'fluide',  name: 'Route 6 — N→E (bas)'      },
    { from: nodes[0], to: nodes[3], state: 'fluide',  name: 'Route 7 — N→S (gauche)'   },
    { from: nodes[1], to: nodes[4], state: 'bouchon', name: 'Route 8 — N→S (centre)'   },
    { from: nodes[2], to: nodes[5], state: 'fluide',  name: 'Route 9 — N→S (droite)'   },
    { from: nodes[3], to: nodes[6], state: 'ralenti', name: 'Route 10 — N→S (gauche)'  },
    { from: nodes[4], to: nodes[7], state: 'fluide',  name: 'Route 11 — N→S (centre)'  },
    { from: nodes[5], to: nodes[8], state: 'ralenti', name: 'Route 12 — N→S (droite)'  },
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
//  Horloge
// ─────────────────────────────────────────────────────────────
let simSeconds = 0;
let frameAcc   = 0;
const FPS_REF  = 60;

function updateClock() {
    frameAcc += speedFactor;
    if (frameAcc >= FPS_REF) { simSeconds++; frameAcc -= FPS_REF; }
    const mm = String(Math.floor(simSeconds / 60)).padStart(2, '0');
    const ss = String(simSeconds % 60).padStart(2, '0');
    document.getElementById('clock').textContent = mm + ':' + ss;
}

// ─────────────────────────────────────────────────────────────
//  Boutons
// ─────────────────────────────────────────────────────────────
const btnStart = document.getElementById('btn-start');
const btnPause = document.getElementById('btn-pause');
const btnReset = document.getElementById('btn-reset');
const btnStop = document.getElementById('btn-stop');

function setButtons(state) {
    btnStart.disabled = (state === 'running');
    btnPause.disabled = (state === 'paused' || state === 'stopped');
    btnStop.disabled  = (state === 'stopped');
}

function setStatus(text, color, paused = false) {
    const statusEl = document.getElementById('status');
    const dotEl    = document.getElementById('status-dot');
    statusEl.textContent = text;
    statusEl.style.color = color;
    dotEl.className = paused ? 'status-dot paused' : 'status-dot';
}

// ─────────────────────────────────────────────────────────────
//  TOOLTIP — distance point → segment
// ─────────────────────────────────────────────────────────────
const tooltip    = document.getElementById('route-tooltip');
const ttTitle    = document.getElementById('tt-title');
const ttDot      = document.getElementById('tt-dot');
const ttStateText = document.getElementById('tt-state-text');

// Calcule la distance minimale entre un point P et le segment AB
function distPointToSegment(px, py, ax, ay, bx, by) {
    const dx = bx - ax, dy = by - ay;
    const lenSq = dx * dx + dy * dy;
    if (lenSq === 0) return Math.hypot(px - ax, py - ay);
    let t = ((px - ax) * dx + (py - ay) * dy) / lenSq;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}

// Convertit les coordonnées écran → coordonnées canvas internes
function screenToCanvas(screenX, screenY) {
    const rect = canvas.getBoundingClientRect();
    const canvasAspect  = canvas.width  / canvas.height;
    const displayAspect = rect.width    / rect.height;

    let scale, offsetX = 0, offsetY = 0;

    if (displayAspect > canvasAspect) {
        // Container plus large → scale par la largeur, haut/bas rognés
        scale   = rect.width / canvas.width;
        offsetY = (canvas.height - rect.height / scale) / 2;
    } else {
        // Container plus haut → scale par la hauteur, gauche/droite rognés
        scale   = rect.height / canvas.height;
        offsetX = (canvas.width - rect.width / scale) / 2;
    }

    return {
        x: (screenX - rect.left) / scale + offsetX,
        y: (screenY - rect.top)  / scale + offsetY,
    };
}

canvas.addEventListener('mousemove', (e) => {
    const { x, y } = screenToCanvas(e.clientX, e.clientY);

    // Cherche la route la plus proche dans un rayon de 18px (coordonnées canvas)
    const HIT_RADIUS = 18;
    let closest = null;
    let closestDist = Infinity;

    roads.forEach(road => {
        const d = distPointToSegment(
            x, y,
            road.from.x, road.from.y,
            road.to.x,   road.to.y
        );
        if (d < HIT_RADIUS && d < closestDist) {
            closestDist = d;
            closest = road;
        }
    });

    if (closest) {
        // Contenu
        ttTitle.textContent     = closest.name;
        ttDot.style.background  = stateColors[closest.state];
        ttStateText.textContent = stateLabels[closest.state];

        // Position — suit la souris avec un petit décalage
        const rect = canvas.getBoundingClientRect();
        const canvasZone = document.getElementById('canvas-zone');
        const zoneRect = canvasZone.getBoundingClientRect();

        let left = e.clientX - zoneRect.left + 14;
        let top  = e.clientY - zoneRect.top  - 10;

        // Empêche le tooltip de déborder à droite
        tooltip.style.display = 'block';
        const ttW = tooltip.offsetWidth;
        if (left + ttW > zoneRect.width - 10) left = e.clientX - zoneRect.left - ttW - 14;

        tooltip.style.left = left + 'px';
        tooltip.style.top  = top  + 'px';
    } else {
        tooltip.style.display = 'none';
    }
});

canvas.addEventListener('mouseleave', () => {
    tooltip.style.display = 'none';
});

// ─────────────────────────────────────────────────────────────
//  DONUT — dessin sur #donut-canvas
// ─────────────────────────────────────────────────────────────
const donutCanvas = document.getElementById('donut-canvas');
const dCtx        = donutCanvas.getContext('2d');

function drawDonut(counts, total) {
    const W = donutCanvas.width;
    const H = donutCanvas.height;
    const cx = W / 2, cy = H / 2;
    const outerR = 40, innerR = 24;

    dCtx.clearRect(0, 0, W, H);

    if (total === 0) {
        // Cercle gris si pas encore de données
        dCtx.beginPath();
        dCtx.arc(cx, cy, outerR, 0, Math.PI * 2);
        dCtx.arc(cx, cy, innerR, 0, Math.PI * 2, true);
        dCtx.fillStyle = '#1e293b';
        dCtx.fill();
        return;
    }

    const slices = [
        { count: counts.fluide,  color: '#4ade80' },
        { count: counts.ralenti, color: '#fb923c' },
        { count: counts.bouchon, color: '#ef4444' },
    ];

    let startAngle = -Math.PI / 2; // commence en haut

    slices.forEach(slice => {
        if (slice.count === 0) return;
        const angle = (slice.count / total) * Math.PI * 2;

        dCtx.beginPath();
        dCtx.moveTo(cx, cy);
        dCtx.arc(cx, cy, outerR, startAngle, startAngle + angle);
        dCtx.closePath();
        dCtx.fillStyle = slice.color;
        dCtx.fill();

        startAngle += angle;
    });

    // Trou central (anneau)
    dCtx.beginPath();
    dCtx.arc(cx, cy, innerR, 0, Math.PI * 2);
    dCtx.fillStyle = '#0f3460'; // même couleur que .section
    dCtx.fill();

    // Nombre total au centre
    dCtx.fillStyle = '#e2e8f0';
    dCtx.font = '700 14px Inter, sans-serif';
    dCtx.textAlign = 'center';
    dCtx.textBaseline = 'middle';
    dCtx.fillText(total, cx, cy);
}

// ─────────────────────────────────────────────────────────────
//  Dessin canvas principal
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

        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);
        if (carsImg.complete) {
            ctx.drawImage(
                carsImg,
                v.sprite.sx, v.sprite.sy, v.sprite.sw, v.sprite.sh,
                -11, -19, 22, 38
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

    // Pourcentages donut
    document.getElementById('pct-fluide').textContent  = Math.round(counts.fluide  / total * 100) + '%';
    document.getElementById('pct-ralenti').textContent = Math.round(counts.ralenti / total * 100) + '%';
    document.getElementById('pct-bouchon').textContent = Math.round(counts.bouchon / total * 100) + '%';

    // Redessine le donut
    drawDonut(counts, total);
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
//  Keyboard shortcuts
// ─────────────────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
    // Ignore si focus sur un input
    if (e.target.tagName === 'INPUT') return;

    switch (e.key) {
        case ' ': // Espace : pause/play
            e.preventDefault();
            if (running) btnPause.click();
            else         btnStart.click();
            break;
        case 'r': case 'R': // R = reset
            btnReset.click();
            break;
        case 's': case 'S': // S = stop
            btnStop.click();
            break;
        case '+': case '=': // + =  vitesse +0.5
            speedFactor = Math.min(5, speedFactor + 0.5);
            speedSlider.value = speedFactor;
            speedLabel.textContent = '×' + speedFactor;
            break;
        case '-': // - = vitesse -0.5
            speedFactor = Math.max(1, speedFactor - 0.5);
            speedSlider.value = speedFactor;
            speedLabel.textContent = '×' + speedFactor;
            break;
    }
});


// ─────────────────────────────────────────────────────────────
//  Événements boutons
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

btnStop.addEventListener('click', () => {
    running = false;
    cancelAnimationFrame(animationId);
    // Remet tout à zéro
    vehicles.forEach(v => { v.progress = 0; });
    simSeconds = 0;
    frameAcc   = 0;
    document.getElementById('clock').textContent = '00:00';
    // Efface le canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setStatus('arrêté', '#ef4444', true);
    setButtons('stopped');
});

// ── Toggle thème ──
document.getElementById('btn-theme').addEventListener('click', () => {
    const isLight = document.body.classList.toggle('light');
    document.getElementById('btn-theme').textContent = isLight ? '☀️' : '🌙';
});

// ─────────────────────────────────────────────────────────────
//  Lancement
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
                setButtons('running');
                loop();
            }, remaining);
        }
    };
});