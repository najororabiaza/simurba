const canvas = document.getElementById('traffic-canvas');
const ctx = canvas.getContext('2d');
canvas.width = 750;
canvas.height = 650;

// Chargement des images
const bgImg = new Image();
bgImg.src = '/static/traffic/img/backgroundGrass.jpg';

const carsImg = new Image();
carsImg.src = '/static/traffic/img/bk_cars1.png';

const tlRedImg = new Image();
tlRedImg.src = '/static/traffic/img/trafficLight_red.png';

const tlGreenImg = new Image();
tlGreenImg.src = '/static/traffic/img/trafficLight_green.png';

// Sprites — bk_cars1.png
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

// Réseau routier — grille 3x3
const nodes = [
    { x: 110, y: 114 }, { x: 374, y: 114 }, { x: 659, y: 114 },
    { x: 110, y: 324 }, { x: 374, y: 324 }, { x: 659, y: 324 },
    { x: 110, y: 559 }, { x: 374, y: 559 }, { x: 659, y: 559 },
];

const stateColors = { fluide: '#4ade80', ralenti: '#fb923c', bouchon: '#ef4444' };
const stateLabels  = { fluide: 'Fluide', ralenti: 'Ralenti', bouchon: 'Bouchon' };

const roads = [
    { from: nodes[0], to: nodes[1], state: 'fluide',  name: 'Route 1 — N→E (haut)'    },
    { from: nodes[1], to: nodes[2], state: 'ralenti', name: 'Route 2 — N→E (haut)'    },
    { from: nodes[3], to: nodes[4], state: 'fluide',  name: 'Route 3 — N→E (milieu)'  },
    { from: nodes[4], to: nodes[5], state: 'bouchon', name: 'Route 4 — N→E (milieu)'  },
    { from: nodes[6], to: nodes[7], state: 'ralenti', name: 'Route 5 — N→E (bas)'     },
    { from: nodes[7], to: nodes[8], state: 'fluide',  name: 'Route 6 — N→E (bas)'     },
    { from: nodes[0], to: nodes[3], state: 'fluide',  name: 'Route 7 — N→S (gauche)'  },
    { from: nodes[1], to: nodes[4], state: 'bouchon', name: 'Route 8 — N→S (centre)'  },
    { from: nodes[2], to: nodes[5], state: 'fluide',  name: 'Route 9 — N→S (droite)'  },
    { from: nodes[3], to: nodes[6], state: 'ralenti', name: 'Route 10 — N→S (gauche)' },
    { from: nodes[4], to: nodes[7], state: 'fluide',  name: 'Route 11 — N→S (centre)' },
    { from: nodes[5], to: nodes[8], state: 'ralenti', name: 'Route 12 — N→S (droite)' },
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

// Toast — système de notifications overlay canvas
const toastContainer = document.getElementById('toast-container');
let toastTimerId = null;

function showToast(message, type = 'info', duration = 2500) {
    if (toastTimerId !== null) {
        clearTimeout(toastTimerId);
        toastTimerId = null;
    }

    const icons = { info: '●', success: '✓', warning: '⏸', danger: '⏹' };

    toastContainer.innerHTML  = '';
    toastContainer.className  = 'toast-visible toast--' + type;

    const icon = document.createElement('span');
    icon.className   = 'toast-icon';
    icon.textContent = icons[type] || '●';

    const text = document.createElement('span');
    text.className   = 'toast-text';
    text.textContent = message;

    toastContainer.appendChild(icon);
    toastContainer.appendChild(text);

    toastTimerId = setTimeout(() => {
        toastContainer.classList.remove('toast-visible');
        toastContainer.classList.add('toast-hiding');
        setTimeout(() => {
            toastContainer.className  = '';
            toastContainer.innerHTML  = '';
            toastTimerId = null;
        }, 300);
    }, duration);
}

// Contrôle de vitesse
let running = false;
let animationId = null;

let speedFactor = 1;
const speedSlider = document.getElementById('speed-slider');
const speedLabel  = document.getElementById('speed-label');
const presetBtns  = document.querySelectorAll('.speed-preset');

function setSpeed(value) {
    speedFactor = value;
    speedSlider.value = value;
    speedLabel.textContent = '×' + value;
    presetBtns.forEach(btn => {
        btn.classList.toggle('active', parseFloat(btn.dataset.speed) === value);
    });
}

speedSlider.addEventListener('input', () => setSpeed(parseFloat(speedSlider.value)));
presetBtns.forEach(btn => {
    btn.addEventListener('click', () => setSpeed(parseFloat(btn.dataset.speed)));
});

// Horloge
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

// --- BOUTONS ET CONTRÔLES D'ÉTAT ---
const btnTogglePlay = document.getElementById('btn-toggle-play');
const btnReset      = document.getElementById('btn-reset');
const btnStop       = document.getElementById('btn-stop');

function setButtons(state) {
    if (state === 'running') {
        btnTogglePlay.innerHTML = '⏸ Pauser';
        btnTogglePlay.style.background = 'var(--color-btn-pause)';
    } else { // 'paused' ou 'stopped'
        btnTogglePlay.innerHTML = '▶ Démarrer';
        btnTogglePlay.style.background = 'var(--color-btn-start)';
    }
    
    btnReset.disabled = false;
    btnStop.disabled  = (state === 'stopped');
}

function setStatus(text, color, paused = false) {
    const statusEl = document.getElementById('status');
    const dotEl    = document.getElementById('status-dot');
    statusEl.textContent = text;
    statusEl.style.color = color;
    dotEl.className = paused ? 'status-dot paused' : 'status-dot';
}

// Écran d'arrêt
function drawStopScreen() {
    const W = canvas.width, H = canvas.height;
    const grad = ctx.createRadialGradient(W / 2, H / 2, 40, W / 2, H / 2, W * 0.75);
    grad.addColorStop(0, '#1a2744');
    grad.addColorStop(1, '#0a0f1e');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    ctx.globalAlpha = 0.06;
    roads.forEach(road => {
        ctx.beginPath();
        ctx.moveTo(road.from.x, road.from.y);
        ctx.lineTo(road.to.x, road.to.y);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth   = 28;
        ctx.stroke();
    });
    ctx.globalAlpha = 1;

    const cx = W / 2, cy = H / 2 - 30, r = 42;
    ctx.beginPath();
    ctx.arc(cx, cy, r + 14, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(233, 69, 96, 0.10)';
    ctx.fill();

    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle   = 'rgba(233, 69, 96, 0.18)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(233, 69, 96, 0.70)';
    ctx.lineWidth   = 2;
    ctx.stroke();

    const ps = 20;
    ctx.beginPath();
    ctx.moveTo(cx - 10 + ps * 0.8, cy);
    ctx.lineTo(cx - 10 - ps * 0.4, cy - ps);
    ctx.lineTo(cx - 10 - ps * 0.4, cy + ps);
    ctx.closePath();
    ctx.fillStyle = '#e94560';
    ctx.fill();

    ctx.fillStyle    = '#f1f5f9';
    ctx.font         = '700 22px Inter, sans-serif';
    ctx.textAlign    = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Simulation arrêtée', cx, cy + r + 34);

    ctx.fillStyle = '#94a3b8';
    ctx.font      = '400 14px Inter, sans-serif';
    ctx.fillText('Cliquez sur  Démarrer  pour lancer une nouvelle simulation', cx, cy + r + 62);

    ctx.fillStyle = 'rgba(148, 163, 184, 0.50)';
    ctx.font      = '400 12px Inter, sans-serif';
    ctx.fillText('ou appuyez sur  Espace', cx, cy + r + 86);

    ctx.textAlign    = 'left';
    ctx.textBaseline = 'alphabetic';
}

// TOOLTIP
const tooltip     = document.getElementById('route-tooltip');
const ttTitle     = document.getElementById('tt-title');
const ttDot       = document.getElementById('tt-dot');
const ttStateText = document.getElementById('tt-state-text');

function distPointToSegment(px, py, ax, ay, bx, by) {
    const dx = bx - ax, dy = by - ay;
    const lenSq = dx * dx + dy * dy;
    if (lenSq === 0) return Math.hypot(px - ax, py - ay);
    let t = ((px - ax) * dx + (py - ay) * dy) / lenSq;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}

function screenToCanvas(screenX, screenY) {
    const rect          = canvas.getBoundingClientRect();
    const canvasAspect  = canvas.width / canvas.height;
    const displayAspect = rect.width / rect.height;
    let scale, offsetX = 0, offsetY = 0;
    if (displayAspect > canvasAspect) {
        scale   = rect.width / canvas.width;
        offsetY = (canvas.height - rect.height / scale) / 2;
    } else {
        scale   = rect.height / canvas.height;
        offsetX = (canvas.width - rect.width / scale) / 2;
    }
    return { x: (screenX - rect.left) / scale + offsetX, y: (screenY - rect.top) / scale + offsetY };
}

canvas.addEventListener('mousemove', (e) => {
    if (!running && animationId === null) { tooltip.style.display = 'none'; return; }
    const { x, y } = screenToCanvas(e.clientX, e.clientY);
    const HIT_RADIUS = 18;
    let closest = null, closestDist = Infinity;
    roads.forEach(road => {
        const d = distPointToSegment(x, y, road.from.x, road.from.y, road.to.x, road.to.y);
        if (d < HIT_RADIUS && d < closestDist) { closestDist = d; closest = road; }
    });
    if (closest) {
        ttTitle.textContent     = closest.name;
        ttDot.style.background  = stateColors[closest.state];
        ttStateText.textContent = stateLabels[closest.state];
        const zoneRect = document.getElementById('canvas-zone').getBoundingClientRect();
        let left = e.clientX - zoneRect.left + 14;
        let top  = e.clientY - zoneRect.top  - 10;
        tooltip.style.display = 'block';
        if (left + tooltip.offsetWidth > zoneRect.width - 10)
            left = e.clientX - zoneRect.left - tooltip.offsetWidth - 14;
        tooltip.style.left = left + 'px';
        tooltip.style.top  = top  + 'px';
    } else {
        tooltip.style.display = 'none';
    }
});
canvas.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });

// DONUT
const donutCanvas = document.getElementById('donut-canvas');
const dCtx        = donutCanvas.getContext('2d');

function drawDonut(counts, total) {
    const W = donutCanvas.width, H = donutCanvas.height;
    const cx = W / 2, cy = H / 2;
    const outerR = 40, innerR = 24;
    dCtx.clearRect(0, 0, W, H);
    if (total === 0) {
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
    let startAngle = -Math.PI / 2;
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
    dCtx.beginPath();
    dCtx.arc(cx, cy, innerR, 0, Math.PI * 2);
    dCtx.fillStyle = '#0f3460';
    dCtx.fill();
    dCtx.fillStyle    = '#e2e8f0';
    dCtx.font         = '700 14px Inter, sans-serif';
    dCtx.textAlign    = 'center';
    dCtx.textBaseline = 'middle';
    dCtx.fillText(total, cx, cy);
}

// Dessin canvas principal
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
        ctx.lineWidth   = 5;
        ctx.globalAlpha = 0.80;
        ctx.stroke();
        ctx.globalAlpha = 1;
    });
}

function drawRoundabouts() {
    nodes.forEach(node => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, 24, 0, Math.PI * 2);
        ctx.fillStyle   = 'rgba(70, 70, 70, 0.30)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(40, 40, 40, 0.50)';
        ctx.lineWidth   = 2.5;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(node.x, node.y, 11, 0, Math.PI * 2);
        ctx.fillStyle   = 'rgba(55, 130, 55, 0.65)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(30, 90, 30, 0.60)';
        ctx.lineWidth   = 1.5;
        ctx.stroke();
    });
}

function drawTrafficLights() {
    trafficLights.forEach(tl => {
        const img = tl.state === 'green' ? tlGreenImg : tlRedImg;
        if (img.complete) ctx.drawImage(img, tl.node.x + 18, tl.node.y - 46, 28, 52);
        const cx = tl.node.x + 52, cy = tl.node.y - 32;
        ctx.beginPath();
        ctx.arc(cx, cy, 11, 0, Math.PI * 2);
        ctx.fillStyle = tl.state === 'green' ? 'rgba(74,222,128,0.25)' : 'rgba(239,68,68,0.25)';
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
        const dx   = v.road.to.x - v.road.from.x;
        const dy   = v.road.to.y - v.road.from.y;
        const len  = Math.sqrt(dx * dx + dy * dy);
        const perpX = (-dy / len) * laneOffset;
        const perpY = ( dx / len) * laneOffset;
        const isHorizontal   = Math.abs(dx) > Math.abs(dy);
        const vertCorrection = isHorizontal ? -14 : 0;
        const x     = rawX + perpX;
        const y     = rawY + perpY + vertCorrection;
        const angle = Math.atan2(dy, dx) + Math.PI / 2;
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);
        if (carsImg.complete) {
            ctx.drawImage(carsImg,
                v.sprite.sx, v.sprite.sy, v.sprite.sw, v.sprite.sh,
                -11, -19, 22, 38
            );
        }
        ctx.restore();
    });
}

// Mises à jour logiques
function updateTrafficLights() {
    trafficLights.forEach(tl => {
        tl.timer += speedFactor;
        if (tl.timer > 300) { tl.state = tl.state === 'green' ? 'red' : 'green'; tl.timer = 0; }
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

    const bars = [
        { bar: 'bar-fluide',  tip: 'tip-fluide',  count: counts.fluide  },
        { bar: 'bar-ralenti', tip: 'tip-ralenti', count: counts.ralenti },
        { bar: 'bar-bouchon', tip: 'tip-bouchon', count: counts.bouchon },
    ];
    bars.forEach(({ bar, tip, count }) => {
        const pct   = total > 0 ? count / total * 100 : 0;
        const barEl = document.getElementById(bar);
        const tipEl = document.getElementById(tip);
        barEl.style.width = pct + '%';
        tipEl.textContent = Math.round(pct) + '%';
        barEl.classList.toggle('has-data', count > 0);
    });

    document.getElementById('pct-fluide').textContent  = Math.round(counts.fluide  / total * 100) + '%';
    document.getElementById('pct-ralenti').textContent = Math.round(counts.ralenti / total * 100) + '%';
    document.getElementById('pct-bouchon').textContent = Math.round(counts.bouchon / total * 100) + '%';

    drawDonut(counts, total);
}

// ─────────────────────────────────────────────────────────────
//  MARKOV — appel API vers Django toutes les 2 secondes
// ─────────────────────────────────────────────────────────────

//  Construit { "0": "fluide", "1": "ralenti", ... } depuis roads[]
function getEtatsActuels() {
    const etats = {};
    roads.forEach((road, index) => { etats[index] = road.state; });
    return etats;
}

//  Applique les nouveaux états Markov reçus de Django sur roads[]
function appliquerNouveauxEtats(nouveauxEtats) {
    roads.forEach((road, index) => {
        const nouvelEtat = nouveauxEtats[String(index)];
        if (nouvelEtat) road.state = nouvelEtat;
    });
}

//  Met à jour le dashboard avec les files d'attente reçues de Django
function mettreAJourFiles(files, interMax, wqMoyen) {

    // On met à jour chaque cellule de la grille 3x3
    for (let i = 0; i < 9; i++) {
        const cellNum  = document.getElementById('queue-' + i);
        const cellDiv  = cellNum ? cellNum.closest('.queue-cell') : null;
        const valeur   = files[String(i)] || 0;

        if (cellNum)  cellNum.textContent = valeur;

        // On colore la cellule selon le niveau de saturation
        if (cellDiv) {
            cellDiv.classList.remove('saturee', 'chargee');
            if (valeur >= 6)      cellDiv.classList.add('saturee');
            else if (valeur >= 3) cellDiv.classList.add('chargee');
        }
    }

    // On met à jour l'intersection max et le Wq moyen
    const interMaxEl = document.getElementById('inter-max');
    const wqMoyenEl  = document.getElementById('wq-moyen');
    if (interMaxEl) interMaxEl.textContent = 'Nœud ' + (interMax.id + 1) + ' — ' + interMax.queue + ' veh.';
    if (wqMoyenEl)  wqMoyenEl.textContent  = wqMoyen + ' s';
}

//  Met à jour la section optimisation des feux
function mettreAJourOptimisation(optim) {
    const rougeEl = document.getElementById('optim-rouge');
    const vertEl  = document.getElementById('optim-vert');
    const gainEl  = document.getElementById('optim-gain');

    if (rougeEl) rougeEl.textContent = optim.duree_rouge + ' s';
    if (vertEl)  vertEl.textContent  = optim.duree_vert  + ' s';
    if (gainEl)  gainEl.textContent  = '+' + optim.gain_pourcent + '%';
}

//  Appel POST vers /api/tick/ — cœur de la simulation côté serveur
async function appellerTick() {

    // On ne fait rien si la simulation est arrêtée
    if (!running) return;

    try {
        const reponse = await fetch('/api/tick/', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ etats: getEtatsActuels() }),
        });

        const donnees = await reponse.json();

        // Markov — on applique les nouveaux états sur les routes
        appliquerNouveauxEtats(donnees.etats);

        // Files d'attente — on met à jour la grille du dashboard
        if (donnees.files) {
            mettreAJourFiles(donnees.files, donnees.inter_max, donnees.wq_moyen);
        }

        // Optimisation — on met à jour les durées recommandées
        if (donnees.optimisation) {
            mettreAJourOptimisation(donnees.optimisation);
        }

    } catch (erreur) {
        // Erreur réseau — on continue sans planter
        console.warn('Tick API échoué :', erreur);
    }
}

//  Le tick s'exécute toutes les 2 secondes
const INTERVALLE_TICK_MS = 2000;
let tickInterval = null;

function demarrerTick() {
    if (tickInterval !== null) return;
    tickInterval = setInterval(appellerTick, INTERVALLE_TICK_MS);
}

function arreterTick() {
    if (tickInterval !== null) {
        clearInterval(tickInterval);
        tickInterval = null;
    }
}


// ─────────────────────────────────────────────────────────────
//  MONTE CARLO — sélecteur de scénario
// ─────────────────────────────────────────────────────────────

//  Appel POST vers /api/scenario/ quand l'utilisateur choisit un scénario
async function changerScenario(scenario) {

    try {
        const reponse = await fetch('/api/scenario/', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ scenario: scenario }),
        });

        const donnees = await reponse.json();

        // On applique les nouveaux états générés par Monte Carlo
        appliquerNouveauxEtats(donnees.etats);

        // On met à jour le risque de bouchon estimé
        const risqueEl = document.getElementById('risque-bouchon');
        if (risqueEl && donnees.risque_bouchon !== undefined) {
            risqueEl.textContent = Math.round(donnees.risque_bouchon * 100) + '%';
        }

        showToast('Scénario : ' + donnees.info_scenario.nom, 'info');

    } catch (erreur) {
        console.warn('Scénario API échoué :', erreur);
    }
}

//  Événements sur les boutons de scénario
document.querySelectorAll('.scenario-btn').forEach(btn => {
    btn.addEventListener('click', () => {

        // On retire la classe active de tous les boutons
        document.querySelectorAll('.scenario-btn').forEach(b => b.classList.remove('active'));

        // On active le bouton cliqué
        btn.classList.add('active');

        // On appelle l'API Monte Carlo
        changerScenario(btn.dataset.scenario);
    });
});


// ─────────────────────────────────────────────────────────────
//  Boucle principale
// ─────────────────────────────────────────────────────────────

function loop() {
    if (!running) return;

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
//  Contrôles
// ─────────────────────────────────────────────────────────────

function togglePlayPause() {
    if (running) {
        // Pause — on arrête l'animation ET le tick Markov
        running = false;
        cancelAnimationFrame(animationId);
        animationId = null;
        arreterTick();
        setStatus('en pause', '#fb923c', true);
        setButtons('paused');
        showToast('Simulation en pause', 'warning');
    } else {
        // Reprise — on redémarre l'animation ET le tick Markov
        running = true;
        setStatus('en cours...', '#4ade80', false);
        setButtons('running');
        demarrerTick();
        showToast('Simulation démarrée', 'success');
        loop();
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    switch (e.key) {
        case ' ':
            e.preventDefault();
            togglePlayPause();
            break;
        case 'r': case 'R': btnReset.click(); break;
        case 's': case 'S': btnStop.click();  break;
        case '+': case '=': setSpeed(Math.min(5, speedFactor + 0.5)); break;
        case '-':            setSpeed(Math.max(1, speedFactor - 0.5)); break;
    }
});

btnTogglePlay.addEventListener('click', togglePlayPause);

btnReset.addEventListener('click', () => {
    vehicles.forEach(v => { v.progress = 0; });
    simSeconds = 0;
    frameAcc   = 0;
    document.getElementById('clock').textContent = '00:00';
    setStatus('en cours...', '#4ade80', false);
    setButtons('running');
    showToast('Réinitialisé — ' + vehicles.length + ' véhicules remis à zéro', 'info');
    if (!running) {
        running = true;
        demarrerTick();
        loop();
    }
});

btnStop.addEventListener('click', () => {
    // On arrête tout : animation + tick Markov
    running = false;
    cancelAnimationFrame(animationId);
    animationId = null;
    arreterTick();
    vehicles.forEach(v => { v.progress = 0; });
    simSeconds = 0;
    frameAcc   = 0;
    document.getElementById('clock').textContent = '00:00';
    drawStopScreen();
    setStatus('arrêté', '#ef4444', true);
    setButtons('stopped');
    showToast('Simulation arrêtée', 'danger', 3000);
});

document.getElementById('btn-theme').addEventListener('click', () => {
    const isLight = document.body.classList.toggle('light');
    document.getElementById('btn-theme').textContent = isLight ? '☀️' : '🌙';
});


// ─────────────────────────────────────────────────────────────
//  Lancement — attend que les 4 images soient chargées
// ─────────────────────────────────────────────────────────────

let imagesLoaded = 0;
const totalImages = 4;
const loadStart   = Date.now();

[bgImg, carsImg, tlRedImg, tlGreenImg].forEach(img => {
    img.onload = () => {
        imagesLoaded++;
        if (imagesLoaded === totalImages) {
            const remaining = Math.max(0, 3000 - (Date.now() - loadStart));
            setTimeout(() => {
                const overlay = document.getElementById('loading-overlay');
                overlay.classList.add('hidden');
                setTimeout(() => overlay.remove(), 400);
                setButtons('running');

                // On démarre la simulation ET le tick Markov
                running = true;
                demarrerTick();
                loop();
            }, remaining);
        }
    };
});