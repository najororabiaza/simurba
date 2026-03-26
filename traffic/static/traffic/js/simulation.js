const canvas = document.getElementById('traffic-canvas');
const ctx = canvas.getContext('2d');
canvas.width = 750;
canvas.height = 650;

// Chargement des images (road2lanesCropWith/Without supprimés)
const bgImg = new Image();
bgImg.src = '/static/traffic/img/backgroundGrass.jpg';

const carsImg = new Image();
carsImg.src = '/static/traffic/img/bk_cars1.png';

const tlRedImg = new Image();
tlRedImg.src = '/static/traffic/img/trafficLight_red.png';

const tlGreenImg = new Image();
tlGreenImg.src = '/static/traffic/img/trafficLight_green.png';

// Sprites des voitures dans le spritesheet (sx, sy, sw, sh)
const carSprites = [
    { sx: 380, sy:  32, sw:  96, sh: 194 }, // Ambulance  (Row1 Col4)
    { sx: 494, sy:  40, sw: 104, sh: 184 }, // Rouge      (Row1 Col5)
    { sx: 616, sy:  40, sw: 104, sh: 184 }, // Bleu       (Row1 Col6)
    { sx: 734, sy:  40, sw: 104, sh: 184 }, // Jaune      (Row1 Col7)
    { sx: 254, sy: 240, sw: 102, sh: 199 }, // Rose       (Row2 Col3)
    { sx: 378, sy: 240, sw: 102, sh: 198 }, // Orange     (Row2 Col4)
    { sx: 494, sy: 246, sw: 104, sh: 184 }, // Blanc      (Row2 Col5)
    { sx: 254, sy: 692, sw:  80, sh: 172 }, // Bleu sport (Row4 Col3)
];

// Grille 3x3 — positions recalculées pour s'aligner sur les routes
// du fond (backgroundGrass.jpg 1024×1024 → canvas 750×650)
// Routes verticales bg: x≈150, 510, 900  → canvas x: 110, 374, 659
// Routes horizontales bg: y≈180, 510, 880 → canvas y: 114, 324, 559
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
    speed: 0.002 + Math.random() * 0.003,
    sprite: carSprites[Math.floor(Math.random() * carSprites.length)],
}));

const trafficLights = nodes.map(node => ({
    node,
    state: Math.random() > 0.5 ? 'green' : 'red',
    timer: Math.floor(Math.random() * 200),
}));

function drawBackground() {
    if (bgImg.complete) {
        ctx.drawImage(bgImg, 0, 0, canvas.width, canvas.height);
    } else {
        ctx.fillStyle = '#3a7d2c';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
}

// Indicateurs d'état colorés sur les routes du fond (sans images de route)
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

// Ronds-points semi-transparents sur les 9 intersections
function drawRoundabouts() {
    nodes.forEach(node => {
        // Anneau extérieur
        ctx.beginPath();
        ctx.arc(node.x, node.y, 24, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(70, 70, 70, 0.30)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(40, 40, 40, 0.50)';
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Îlot central vert
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
            // Positionné légèrement au-dessus/à droite de chaque rond-point
            ctx.drawImage(img, tl.node.x + 18, tl.node.y - 46, 28, 52);
        }
    });
}

function updateTrafficLights() {
    trafficLights.forEach(tl => {
        tl.timer++;
        if (tl.timer > 300) {
            tl.state = tl.state === 'green' ? 'red' : 'green';
            tl.timer = 0;
        }
    });
}

function drawVehicles() {
    // Décalage de voie : les voitures roulent sur la voie droite
    const laneOffset = 12;

    vehicles.forEach(v => {
        const rawX = v.road.from.x + (v.road.to.x - v.road.from.x) * v.progress;
        const rawY = v.road.from.y + (v.road.to.y - v.road.from.y) * v.progress;
        const dx = v.road.to.x - v.road.from.x;
        const dy = v.road.to.y - v.road.from.y;
        const len = Math.sqrt(dx * dx + dy * dy);

        // Vecteur perpendiculaire droit (sens de la route)
        const perpX = (-dy / len) * laneOffset;
        const perpY = (dx / len) * laneOffset;

        // Correction verticale pour les routes horizontales :
        // sur une route horizontale (|dx| >> |dy|), les voitures remontent de 14px
        const isHorizontal = Math.abs(dx) > Math.abs(dy);
        const vertCorrection = isHorizontal ? -14 : 0;

        const x = rawX + perpX;
        const y = rawY + perpY + vertCorrection;
        const angle = Math.atan2(dy, dx) + Math.PI / 2;

        // Taille légèrement augmentée pour correspondre aux routes du fond
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
    document.getElementById('bar-fluide').style.width  = (counts.fluide  / total * 100) + '%';
    document.getElementById('bar-ralenti').style.width = (counts.ralenti / total * 100) + '%';
    document.getElementById('bar-bouchon').style.width = (counts.bouchon / total * 100) + '%';
}

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

// 4 images uniquement (road2lanesCropWith/Without supprimés)
let imagesLoaded = 0;
const totalImages = 4;
[bgImg, carsImg, tlRedImg, tlGreenImg].forEach(img => {
    img.onload = () => {
        imagesLoaded++;
        if (imagesLoaded === totalImages) loop();
    };
});