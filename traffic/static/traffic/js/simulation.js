const canvas = document.getElementById('traffic-canvas');
const ctx = canvas.getContext('2d');
canvas.width = 750;
canvas.height = 650;

// Chargement des images
const bgImg = new Image();
bgImg.src = '/static/traffic/img/backgroundGrass.jpg';

const roadImgWith = new Image();
roadImgWith.src = '/static/traffic/img/road2lanesCropWith.png';

const roadImgWithout = new Image();
roadImgWithout.src = '/static/traffic/img/road2lanesCropWithout.png';

const carsImg = new Image();
carsImg.src = '/static/traffic/img/bk_cars1.png';

const tlRedImg = new Image();
tlRedImg.src = '/static/traffic/img/trafficLight_red.png';

const tlGreenImg = new Image();
tlGreenImg.src = '/static/traffic/img/trafficLight_green.png';

// Sprites des voitures dans le spritesheet (sx, sy, sw, sh)
const carSprites = [
    { sx: 188, sy: 16,  sw: 59, sh: 100 }, // Ambulance
    { sx: 248, sy: 16,  sw: 48, sh: 100 }, // Rouge
    { sx: 311, sy: 16,  sw: 46, sh: 100 }, // Bleu
    { sx: 369, sy: 16,  sw: 48, sh: 100 }, // Jaune
    { sx: 125, sy: 116, sw: 60, sh: 100 }, // Rose
    { sx: 188, sy: 116, sw: 59, sh: 100 }, // Orange
    { sx: 248, sy: 116, sw: 48, sh: 100 }, // Blanc
    { sx: 125, sy: 347, sw: 40, sh: 84 }, // Rouge sport
    { sx: 188, sy: 446, sw: 59, sh: 89  }, // Bleu sport
];

// Grille 3x3
const nodes = [
    { x: 180, y: 150 }, { x: 375, y: 150 }, { x: 570, y: 150 },
    { x: 180, y: 325 }, { x: 375, y: 325 }, { x: 570, y: 325 },
    { x: 180, y: 500 }, { x: 375, y: 500 }, { x: 570, y: 500 },
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

function drawRoads() {
    roads.forEach(road => {
        const dx = road.to.x - road.from.x;
        const dy = road.to.y - road.from.y;
        const len = Math.sqrt(dx * dx + dy * dy);
        const angle = Math.atan2(dy, dx);
        const roadWidth = 36;
        const nSegments = Math.ceil(len / 15);

        for (let i = 0; i < nSegments; i++) {
            const t = (i + 0.5) / nSegments;
            const cx = road.from.x + dx * t;
            const cy = road.from.y + dy * t;
            const segLen = len / nSegments * 1.05;

            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(angle);
            const img = (i % 2 === 0) ? roadImgWith : roadImgWithout;
            if (img.complete) {
                ctx.drawImage(img, -segLen / 2, -roadWidth / 2, segLen, roadWidth);
            }
            ctx.restore();
        }

        // Indicateur état coloré
        ctx.beginPath();
        ctx.moveTo(road.from.x, road.from.y);
        ctx.lineTo(road.to.x, road.to.y);
        ctx.strokeStyle = stateColors[road.state];
        ctx.lineWidth = 2;
        ctx.globalAlpha = 0.4;
        ctx.stroke();
        ctx.globalAlpha = 1;
    });
}

function drawNodes() {
    nodes.forEach(node => {
        ctx.fillStyle = '#555';
        ctx.fillRect(node.x - 18, node.y - 18, 36, 36);
    });
}

function drawTrafficLights() {
    trafficLights.forEach(tl => {
        const img = tl.state === 'green' ? tlGreenImg : tlRedImg;
        if (img.complete) {
            ctx.drawImage(img, tl.node.x + 14, tl.node.y - 30, 16, 30);
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
    vehicles.forEach(v => {
        const x = v.road.from.x + (v.road.to.x - v.road.from.x) * v.progress;
        const y = v.road.from.y + (v.road.to.y - v.road.from.y) * v.progress;
        const dx = v.road.to.x - v.road.from.x;
        const dy = v.road.to.y - v.road.from.y;
        const angle = Math.atan2(dy, dx) + Math.PI / 2;

        const displayW = 16;
        const displayH = 24;

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
    drawRoads();
    drawNodes();
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

let imagesLoaded = 0;
const totalImages = 6;
[bgImg, roadImgWith, roadImgWithout, carsImg, tlRedImg, tlGreenImg].forEach(img => {
    img.onload = () => {
        imagesLoaded++;
        if (imagesLoaded === totalImages) loop();
    };
});