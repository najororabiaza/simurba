// ============================================================================
// SIMURBA — simulation.js
// JavaScript : affichage, interface, interactions UNIQUEMENT
// Python (Django) : tous les calculs, mathématiques, algorithmes, pathfinding
// ============================================================================

// ── SECTION 1 : Canvas & images ──────────────────────────────────────────────

const canvas = document.getElementById('traffic-canvas');
const ctx    = canvas.getContext('2d');
canvas.width  = 750;
canvas.height = 650;

const bgImg    = new Image(); bgImg.src    = '/static/traffic/img/backgroundGrass.jpg';
const carsImg  = new Image(); carsImg.src  = '/static/traffic/img/bk_cars1.png';
const tlRedImg = new Image(); tlRedImg.src = '/static/traffic/img/trafficLight_red.png';
const tlGrnImg = new Image(); tlGrnImg.src = '/static/traffic/img/trafficLight_green.png';

// Sprites bk_cars1.png
const carSprites = [
    { sx: 380, sy:  32, sw:  96, sh: 194 },  // Ambulance
    { sx: 494, sy:  40, sw: 104, sh: 184 },  // Rouge
    { sx: 616, sy:  40, sw: 104, sh: 184 },  // Bleu
    { sx: 734, sy:  40, sw: 104, sh: 184 },  // Jaune
    { sx: 254, sy: 240, sw: 102, sh: 199 },  // Rose
    { sx: 378, sy: 240, sw: 102, sh: 198 },  // Orange
    { sx: 494, sy: 246, sw: 104, sh: 184 },  // Blanc
    { sx: 254, sy: 692, sw:  80, sh: 172 },  // Bleu sport
];

// ── SECTION 2 : Réseau routier 3×3 ──────────────────────────────────────────

const nodes = [
    { x: 110, y: 114 }, { x: 374, y: 114 }, { x: 659, y: 114 },
    { x: 110, y: 324 }, { x: 374, y: 324 }, { x: 659, y: 324 },
    { x: 110, y: 559 }, { x: 374, y: 559 }, { x: 659, y: 559 },
];

// ROADS_DEF côté JS — identique à ROUTES_DEF côté Python
// Indice = road_idx envoyé par Python dans les chemins
const ROADS_DEF_JS = [
    [0, 1], [1, 2],          // 0-1
    [3, 4], [4, 5],          // 2-3
    [6, 7], [7, 8],          // 4-5
    [0, 3], [1, 4], [2, 5], // 6-8
    [3, 6], [4, 7], [5, 8], // 9-11
];

const stateColors = { fluide: '#4ade80', ralenti: '#fb923c', bouchon: '#ef4444' };
const stateLabels = { fluide: 'Fluide', ralenti: 'Ralenti', bouchon: 'Bouchon' };

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

// ── SECTION 3 : Véhicules ────────────────────────────────────────────────────

const vehicles = roads.map((road, i) => ({
    // --- Champs standard (mode normal) ---
    road,
    progress:  Math.random(),
    baseSpeed: 0.002 + Math.random() * 0.003,
    sprite:    carSprites[i % carSprites.length],

    // --- Champs pathfinding (inactifs par défaut) ---
    pfEnabled:     false,   // pathfinding activé pour ce véhicule ?
    pfPath:        [],      // chemin calculé par Python
    pfStep:        0,       // étape courante dans pfPath
    pfOriginNode:  -1,      // nœud d'origine — jamais revisité
    pfCurrentNode: -1,      // nœud de fin du tronçon courant
    pfVisited:     [],      // nœuds récemment visités (pour extension)
    pfFetchPending:false,   // requête d'extension en cours

    // --- Animation de virage (bezier) ---
    pfTurning: false,
    pfTurnT:   0,           // 0 → 1 : progression dans l'arc bezier
    pfTurnP0:  null,        // {x,y} départ de l'arc
    pfTurnP1:  null,        // {x,y} point de contrôle (intersection)
    pfTurnP2:  null,        // {x,y} fin de l'arc
}));

// ── SECTION 4 : Feux tricolores ──────────────────────────────────────────────

const trafficLights = nodes.map(node => ({
    node,
    state: Math.random() > 0.5 ? 'green' : 'red',
    timer: Math.floor(Math.random() * 200),
}));

// ── SECTION 5 : Toasts ───────────────────────────────────────────────────────

const toastContainer = document.getElementById('toast-container');
let toastTimerId = null;

function showToast(message, type = 'info', duration = 2500) {
    if (toastTimerId !== null) { clearTimeout(toastTimerId); toastTimerId = null; }
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
        setTimeout(() => { toastContainer.className = ''; toastContainer.innerHTML = ''; toastTimerId = null; }, 300);
    }, duration);
}

// ── SECTION 6 : Vitesse & horloge ───────────────────────────────────────────

let running     = false;
let animationId = null;
let speedFactor = 1;
let dureeVertFrames  = 30 * 60;
let dureeRougeFrames = 30 * 60;

const speedSlider = document.getElementById('speed-slider');
const speedLabel  = document.getElementById('speed-label');
const presetBtns  = document.querySelectorAll('.speed-preset');

function setSpeed(value) {
    speedFactor = value;
    speedSlider.value    = value;
    speedLabel.textContent = '×' + value;
    presetBtns.forEach(btn => {
        btn.classList.toggle('active', parseFloat(btn.dataset.speed) === value);
    });
}

speedSlider.addEventListener('input', () => setSpeed(parseFloat(speedSlider.value)));
presetBtns.forEach(btn => btn.addEventListener('click', () => setSpeed(parseFloat(btn.dataset.speed))));

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

// ── SECTION 7 : Contrôles ────────────────────────────────────────────────────

const btnTogglePlay = document.getElementById('btn-toggle-play');
const btnReset      = document.getElementById('btn-reset');
const btnStop       = document.getElementById('btn-stop');

function setButtons(state) {
    if (state === 'running') {
        btnTogglePlay.innerHTML = '⏸ Pauser';
        btnTogglePlay.style.background = 'var(--color-btn-pause)';
    } else {
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

// ── SECTION 8 : Écran d'arrêt ────────────────────────────────────────────────

function drawStopScreen() {
    const W = canvas.width, H = canvas.height;
    const grad = ctx.createRadialGradient(W/2, H/2, 40, W/2, H/2, W * 0.75);
    grad.addColorStop(0, '#1a2744');
    grad.addColorStop(1, '#0a0f1e');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);
    ctx.globalAlpha = 0.06;
    roads.forEach(road => {
        ctx.beginPath(); ctx.moveTo(road.from.x, road.from.y); ctx.lineTo(road.to.x, road.to.y);
        ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 28; ctx.stroke();
    });
    ctx.globalAlpha = 1;
    const cx = W/2, cy = H/2 - 30, r = 42;
    ctx.beginPath(); ctx.arc(cx, cy, r+14, 0, Math.PI*2);
    ctx.fillStyle = 'rgba(233,69,96,0.10)'; ctx.fill();
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI*2);
    ctx.fillStyle = 'rgba(233,69,96,0.18)'; ctx.fill();
    ctx.strokeStyle = 'rgba(233,69,96,0.70)'; ctx.lineWidth = 2; ctx.stroke();
    const ps = 20;
    ctx.beginPath();
    ctx.moveTo(cx - 10 + ps*0.8, cy);
    ctx.lineTo(cx - 10 - ps*0.4, cy - ps);
    ctx.lineTo(cx - 10 - ps*0.4, cy + ps);
    ctx.closePath(); ctx.fillStyle = '#e94560'; ctx.fill();
    ctx.fillStyle = '#f1f5f9'; ctx.font = '700 22px Inter, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('Simulation arrêtée', cx, cy + r + 34);
    ctx.fillStyle = '#94a3b8'; ctx.font = '400 14px Inter, sans-serif';
    ctx.fillText('Cliquez sur  Démarrer  pour lancer une nouvelle simulation', cx, cy + r + 62);
    ctx.fillStyle = 'rgba(148,163,184,0.50)'; ctx.font = '400 12px Inter, sans-serif';
    ctx.fillText('ou appuyez sur  Espace', cx, cy + r + 86);
    ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
}

// ── SECTION 9 : Tooltip ──────────────────────────────────────────────────────

const tooltip     = document.getElementById('route-tooltip');
const ttTitle     = document.getElementById('tt-title');
const ttDot       = document.getElementById('tt-dot');
const ttStateText = document.getElementById('tt-state-text');

function distPointToSegment(px, py, ax, ay, bx, by) {
    const dx = bx-ax, dy = by-ay, lenSq = dx*dx + dy*dy;
    if (lenSq === 0) return Math.hypot(px-ax, py-ay);
    let t = ((px-ax)*dx + (py-ay)*dy) / lenSq;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(px - (ax + t*dx), py - (ay + t*dy));
}

function screenToCanvas(screenX, screenY) {
    const rect = canvas.getBoundingClientRect();
    const canvasAspect = canvas.width / canvas.height;
    const displayAspect = rect.width / rect.height;
    let scale, offsetX = 0, offsetY = 0;
    if (displayAspect > canvasAspect) {
        scale = rect.width / canvas.width;
        offsetY = (canvas.height - rect.height/scale) / 2;
    } else {
        scale = rect.height / canvas.height;
        offsetX = (canvas.width - rect.width/scale) / 2;
    }
    return { x: (screenX - rect.left)/scale + offsetX, y: (screenY - rect.top)/scale + offsetY };
}

canvas.addEventListener('mousemove', (e) => {
    if (!running && animationId === null) { tooltip.style.display = 'none'; return; }
    const { x, y } = screenToCanvas(e.clientX, e.clientY);
    const HIT = 18;
    let closest = null, closestDist = Infinity;
    roads.forEach(road => {
        const d = distPointToSegment(x, y, road.from.x, road.from.y, road.to.x, road.to.y);
        if (d < HIT && d < closestDist) { closestDist = d; closest = road; }
    });
    if (closest) {
        ttTitle.textContent    = closest.name;
        ttDot.style.background = stateColors[closest.state];
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

// ── SECTION 10 : Donut ───────────────────────────────────────────────────────

const donutCanvas = document.getElementById('donut-canvas');
const dCtx        = donutCanvas.getContext('2d');

function drawDonut(counts, total) {
    const W = donutCanvas.width, H = donutCanvas.height;
    const cx = W/2, cy = H/2, outerR = 40, innerR = 24;
    dCtx.clearRect(0, 0, W, H);
    if (total === 0) {
        dCtx.beginPath(); dCtx.arc(cx, cy, outerR, 0, Math.PI*2);
        dCtx.fillStyle = '#1e293b'; dCtx.fill(); return;
    }
    const slices = [
        { count: counts.fluide,  color: '#4ade80' },
        { count: counts.ralenti, color: '#fb923c' },
        { count: counts.bouchon, color: '#ef4444' },
    ];
    let startAngle = -Math.PI / 2;
    slices.forEach(s => {
        if (s.count === 0) return;
        const angle = (s.count / total) * Math.PI * 2;
        dCtx.beginPath(); dCtx.moveTo(cx, cy);
        dCtx.arc(cx, cy, outerR, startAngle, startAngle + angle);
        dCtx.closePath(); dCtx.fillStyle = s.color; dCtx.fill();
        startAngle += angle;
    });
    dCtx.beginPath(); dCtx.arc(cx, cy, innerR, 0, Math.PI*2);
    dCtx.fillStyle = '#0f3460'; dCtx.fill();
    dCtx.fillStyle = '#e2e8f0'; dCtx.font = '700 14px Inter, sans-serif';
    dCtx.textAlign = 'center'; dCtx.textBaseline = 'middle';
    dCtx.fillText(total, cx, cy);
}

// ── SECTION 11 : Dessin fond / routes / ronds-points / feux ─────────────────

function drawBackground() {
    if (bgImg.complete) ctx.drawImage(bgImg, 0, 0, canvas.width, canvas.height);
    else { ctx.fillStyle = '#3a7d2c'; ctx.fillRect(0, 0, canvas.width, canvas.height); }
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
        ctx.beginPath(); ctx.arc(node.x, node.y, 24, 0, Math.PI*2);
        ctx.fillStyle = 'rgba(70,70,70,0.30)'; ctx.fill();
        ctx.strokeStyle = 'rgba(40,40,40,0.50)'; ctx.lineWidth = 2.5; ctx.stroke();
        ctx.beginPath(); ctx.arc(node.x, node.y, 11, 0, Math.PI*2);
        ctx.fillStyle = 'rgba(55,130,55,0.65)'; ctx.fill();
        ctx.strokeStyle = 'rgba(30,90,30,0.60)'; ctx.lineWidth = 1.5; ctx.stroke();
    });
}

function drawTrafficLights() {
    trafficLights.forEach(tl => {
        const img = tl.state === 'green' ? tlGrnImg : tlRedImg;
        if (img.complete) ctx.drawImage(img, tl.node.x+18, tl.node.y-46, 28, 52);
        const cx = tl.node.x+52, cy = tl.node.y-32;
        ctx.beginPath(); ctx.arc(cx, cy, 11, 0, Math.PI*2);
        ctx.fillStyle = tl.state === 'green' ? 'rgba(74,222,128,0.25)' : 'rgba(239,68,68,0.25)';
        ctx.fill();
        ctx.beginPath(); ctx.arc(cx, cy, 7, 0, Math.PI*2);
        ctx.fillStyle = tl.state === 'green' ? '#4ade80' : '#ef4444';
        ctx.fill();
    });
}

// ── SECTION 12 : Géométrie pathfinding ──────────────────────────────────────
//   Ces fonctions ne font QUE des calculs géométriques pour l'affichage.
//   Le pathfinding lui-même vient de Python via API.

const LANE_OFFSET    = 12;   // décalage latéral (voie droite)
const PF_EXIT_PROG   = 0.86; // le véhicule quitte le tronçon à ce point
const PF_ENTRY_PROG  = 0.14; // il repart sur le suivant à ce point
const PF_TURN_SPEED  = 0.038;// avancement par frame dans l'arc bezier (vitesse×1)

/**
 * Position d'un véhicule sur un tronçon droit (avec décalage de voie).
 * @param {object} fromPos  {x,y}
 * @param {object} toPos    {x,y}
 * @param {number} progress 0..1
 * @returns {object} {x, y, angle}
 */
function getSegmentPos(fromPos, toPos, progress) {
    const dx  = toPos.x - fromPos.x;
    const dy  = toPos.y - fromPos.y;
    const len = Math.hypot(dx, dy) || 1;
    const nx  = dx / len;
    const ny  = dy / len;
    // Perpendiculaire à droite du sens de marche
    const px  = -ny;
    const py  =  nx;
    const rawX = fromPos.x + dx * progress;
    const rawY = fromPos.y + dy * progress;
    const isHoriz = Math.abs(dx) > Math.abs(dy);
    return {
        x:     rawX + px * LANE_OFFSET,
        y:     rawY + py * LANE_OFFSET + (isHoriz ? -14 : 0),
        angle: Math.atan2(dy, dx) + Math.PI / 2,
    };
}

/** Point sur un arc bezier quadratique. */
function bezierPos(P0, P1, P2, t) {
    const mt = 1 - t;
    return {
        x: mt*mt*P0.x + 2*mt*t*P1.x + t*t*P2.x,
        y: mt*mt*P0.y + 2*mt*t*P1.y + t*t*P2.y,
    };
}

/** Angle tangent à l'arc bezier (pour l'orientation du véhicule). */
function bezierAngle(P0, P1, P2, t) {
    const mt = 1 - t;
    const dx = 2*mt*(P1.x - P0.x) + 2*t*(P2.x - P1.x);
    const dy = 2*mt*(P1.y - P0.y) + 2*t*(P2.y - P1.y);
    return Math.atan2(dy, dx) + Math.PI / 2;
}

/** Retourne {fromPos, toPos} d'un tronçon selon qu'il est inversé ou non. */
function stepPositions(step) {
    const [a, b] = ROADS_DEF_JS[step.road_idx];
    return step.reversed
        ? { fromPos: nodes[b], toPos: nodes[a] }
        : { fromPos: nodes[a], toPos: nodes[b] };
}

// ── SECTION 13 : État global pathfinding ─────────────────────────────────────

let pathfindingMode = false;   // pathfinding globalement activé ?
let pfModeContinu   = true;    // true=continuer position, false=nouveau départ

const btnPathfinding   = document.getElementById('btn-pathfinding');
const pfPanel          = document.getElementById('pf-panel');
const btnPfContinue    = document.getElementById('btn-pf-continue');
const btnPfRestart     = document.getElementById('btn-pf-restart');

// Effets visuels — intersections qui "brillent" lors d'un virage
let intersectionFlashes = [];  // [{nodeIdx, alpha, frame}]

// ── SECTION 14 : API pathfinding (appels vers Python) ────────────────────────

/**
 * Initialise le pathfinding pour tous les véhicules.
 * Python calcule les chemins; JS applique et affiche.
 * @param {boolean} keepProgress true=garder position, false=nouveau départ
 */
async function initPathfinding(keepProgress) {
    try {
        const reponse = await fetch('/api/pathfinding/init/', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                num_vehicles: vehicles.length,
                etats:        getEtatsActuels(),
                path_length:  32,
            }),
        });
        const data = await reponse.json();

        // Appliquer les chemins Python à chaque véhicule (JS = affichage uniquement)
        data.paths.forEach((pData, i) => {
            const v   = vehicles[i];
            if (!pData.path || pData.path.length === 0) return;

            v.pfEnabled      = true;
            v.pfPath         = pData.path;
            v.pfStep         = 0;
            v.pfOriginNode   = pData.origin_node;
            v.pfCurrentNode  = pData.origin_node;
            v.pfVisited      = [pData.origin_node];
            v.pfFetchPending = false;
            v.pfTurning      = false;
            v.pfTurnT        = 0;

            const firstStep = pData.path[0];

            if (!keepProgress) {
                // Nouveau départ : placer le véhicule au début du premier tronçon
                const { fromPos, toPos } = stepPositions(firstStep);
                v.progress = PF_ENTRY_PROG;
                v.road     = roads[firstStep.road_idx] || roads[0];
            } else {
                // Continuer : garder progress actuel, switcher à la nouvelle route
                v.road = roads[firstStep.road_idx] || v.road;
                if (v.progress > PF_EXIT_PROG) v.progress = PF_ENTRY_PROG;
            }
        });

        pathfindingMode = true;
        btnPathfinding.classList.add('active');
        btnPathfinding.textContent = '🗺 Pathfinding actif';
        pfPanel.style.display = 'block';
        showToast('🗺 Pathfinding activé — routes dynamiques', 'success', 3000);

    } catch (err) {
        console.warn('Pathfinding init échoué :', err);
        showToast('Erreur pathfinding', 'danger');
    }
}

/** Désactive le pathfinding (retour au mode normal). */
function disablePathfinding() {
    pathfindingMode = false;
    vehicles.forEach(v => {
        v.pfEnabled  = false;
        v.pfTurning  = false;
        v.pfPath     = [];
        v.pfStep     = 0;
    });
    btnPathfinding.classList.remove('active');
    btnPathfinding.textContent = '🗺 Activer Pathfinding';
    pfPanel.style.display = 'none';
    showToast('Pathfinding désactivé', 'info');
}

/**
 * Étend le chemin d'un véhicule (appelé par JS quand < 6 étapes restantes).
 * Python calcule l'extension; JS l'ajoute à pfPath.
 */
async function extendVehiclePath(v) {
    if (v.pfFetchPending) return;
    v.pfFetchPending = true;

    // Le nœud courant = destination du tronçon actif
    const step = v.pfPath[v.pfStep] || v.pfPath[v.pfPath.length - 1];
    if (!step) { v.pfFetchPending = false; return; }
    const currentNode = step.reversed
        ? ROADS_DEF_JS[step.road_idx][0]
        : ROADS_DEF_JS[step.road_idx][1];

    try {
        const reponse = await fetch('/api/pathfinding/extend/', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                current_node:  currentNode,
                origin_node:   v.pfOriginNode,
                visited_nodes: v.pfVisited.slice(-6),
                etats:         getEtatsActuels(),
            }),
        });
        const data = await reponse.json();
        if (data.path && data.path.length > 0) {
            v.pfPath = v.pfPath.concat(data.path);
        }
    } catch (err) {
        console.warn('Extension chemin échouée :', err);
    } finally {
        v.pfFetchPending = false;
    }
}

// ── SECTION 15 : Mise à jour véhicules — mode pathfinding ────────────────────

function updateVehiclePF(v) {
    if (!v.pfEnabled || !v.pfPath || v.pfPath.length === 0) return;

    // ── PHASE VIRAGE (bezier arc) ────────────────────────────────────────────
    if (v.pfTurning) {
        v.pfTurnT += PF_TURN_SPEED * speedFactor;
        if (v.pfTurnT >= 1.0) {
            v.pfTurnT  = 1.0;
            v.pfTurning = false;
            v.progress  = PF_ENTRY_PROG;
        }
        return;
    }

    // ── PHASE DÉPLACEMENT ────────────────────────────────────────────────────
    const step = v.pfPath[v.pfStep];
    if (!step) return;

    // Vitesse selon état Markov de la route courante
    let mult = 1.0;
    if (v.road.state === 'ralenti') mult = 0.4;
    else if (v.road.state === 'bouchon') mult = 0.1;

    v.progress += v.baseSpeed * speedFactor * mult;

    // ── FIN DU TRONÇON → VIRAGE ──────────────────────────────────────────────
    if (v.progress >= PF_EXIT_PROG) {

        const nextStepIdx = v.pfStep + 1;

        // Si plus de tronçons, rester en attente et demander une extension
        if (nextStepIdx >= v.pfPath.length) {
            v.progress = PF_EXIT_PROG;
            if (!v.pfFetchPending) extendVehiclePath(v);
            return;
        }

        // Tronçon courant : point de sortie (P0)
        const currFrom = stepPositions(step).fromPos;
        const currTo   = stepPositions(step).toPos;
        const P0       = getSegmentPos(currFrom, currTo, PF_EXIT_PROG);

        // Tronçon suivant : point d'entrée (P2)
        const nextStep   = v.pfPath[nextStepIdx];
        const nextFrom   = stepPositions(nextStep).fromPos;
        const nextTo     = stepPositions(nextStep).toPos;
        const P2         = getSegmentPos(nextFrom, nextTo, PF_ENTRY_PROG);

        // Point de contrôle = intersection (nœud de jonction des deux tronçons)
        // On choisit le nœud commun entre fin du tronçon courant et début du suivant
        const intersectionPos = currTo;  // fin du tronçon courant = l'intersection
        const P1 = {
            x: intersectionPos.x,
            y: intersectionPos.y,
        };

        // Enregistrer le flash de l'intersection
        const nodeIdx = step.reversed
            ? ROADS_DEF_JS[step.road_idx][0]
            : ROADS_DEF_JS[step.road_idx][1];
        intersectionFlashes.push({ nodeIdx, alpha: 1.0 });

        // Mémoriser le nœud visité
        v.pfVisited.push(nodeIdx);
        if (v.pfVisited.length > 8) v.pfVisited.shift();
        v.pfCurrentNode = nodeIdx;

        // Avancer dans le chemin
        v.pfStep = nextStepIdx;
        v.road   = roads[nextStep.road_idx] || v.road;

        // Lancer le virage bezier
        v.pfTurning = true;
        v.pfTurnT   = 0;
        v.pfTurnP0  = P0;
        v.pfTurnP1  = P1;
        v.pfTurnP2  = P2;

        // Demander une extension si proche de la fin du chemin
        if (v.pfStep >= v.pfPath.length - 6 && !v.pfFetchPending) {
            extendVehiclePath(v);
        }
    }
}

// ── SECTION 16 : Dessin véhicules — mode pathfinding ─────────────────────────

function drawVehiclePF(v) {
    if (!v.pfEnabled) return;

    let x, y, angle;

    if (v.pfTurning && v.pfTurnP0 && v.pfTurnP1 && v.pfTurnP2) {
        // ── VIRAGE : position sur l'arc bezier ──────────────────────────────
        const pos = bezierPos(v.pfTurnP0, v.pfTurnP1, v.pfTurnP2, v.pfTurnT);
        x     = pos.x;
        y     = pos.y;
        angle = bezierAngle(v.pfTurnP0, v.pfTurnP1, v.pfTurnP2, v.pfTurnT);

        // Petit halo de virage pour rendre le changement de route bien visible
        ctx.save();
        ctx.beginPath();
        ctx.arc(x, y, 14, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(250, 220, 50, ${0.25 * (1 - v.pfTurnT)})`;
        ctx.fill();
        ctx.restore();

    } else {
        // ── DÉPLACEMENT DROIT ────────────────────────────────────────────────
        const step = v.pfPath[v.pfStep];
        if (!step) return;
        const { fromPos, toPos } = stepPositions(step);
        const pos = getSegmentPos(fromPos, toPos, v.progress);
        x     = pos.x;
        y     = pos.y;
        angle = pos.angle;
    }

    // Dessiner le sprite du véhicule
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
}

/**
 * Dessine les indicateurs de chemin (ligne pointillée vers la prochaine destination).
 * Rend le changement de route CLAIREMENT VISIBLE avant que le véhicule arrive.
 */
function drawPathIndicators() {
    if (!pathfindingMode) return;

    vehicles.forEach(v => {
        if (!v.pfEnabled || !v.pfPath || v.pfPath.length === 0) return;

        // Tronçon suivant (si disponible) → flèche directionnelle
        const nextStepIdx = v.pfStep + 1;
        if (nextStepIdx >= v.pfPath.length) return;

        const nextStep = v.pfPath[nextStepIdx];
        const { fromPos, toPos } = stepPositions(nextStep);

        // Ligne pointillée légère vers la prochaine destination
        const midFrom = stepPositions(v.pfPath[v.pfStep] || nextStep);
        ctx.save();
        ctx.setLineDash([3, 7]);
        ctx.lineWidth    = 1.5;
        ctx.strokeStyle  = 'rgba(250, 200, 50, 0.35)';
        ctx.globalAlpha  = 0.7;
        ctx.beginPath();
        ctx.moveTo(fromPos.x, fromPos.y);
        ctx.lineTo(toPos.x,   toPos.y);
        ctx.stroke();

        // Petite flèche à mi-chemin du tronçon suivant
        const mx = (fromPos.x + toPos.x) / 2;
        const my = (fromPos.y + toPos.y) / 2;
        const ang = Math.atan2(toPos.y - fromPos.y, toPos.x - fromPos.x);
        const al  = 8, aw = 4;

        ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(250, 200, 50, 0.55)';
        ctx.beginPath();
        ctx.moveTo(mx + Math.cos(ang) * al,       my + Math.sin(ang) * al);
        ctx.lineTo(mx + Math.cos(ang+2.4) * aw,   my + Math.sin(ang+2.4) * aw);
        ctx.lineTo(mx + Math.cos(ang-2.4) * aw,   my + Math.sin(ang-2.4) * aw);
        ctx.closePath();
        ctx.fill();

        ctx.restore();
    });
}

/** Anime les flashs d'intersection lors des virages. */
function drawIntersectionFlashes() {
    intersectionFlashes = intersectionFlashes.filter(f => f.alpha > 0);
    intersectionFlashes.forEach(f => {
        const node = nodes[f.nodeIdx];
        if (!node) return;
        ctx.save();
        ctx.beginPath();
        ctx.arc(node.x, node.y, 22, 0, Math.PI * 2);
        ctx.fillStyle   = `rgba(250, 220, 80, ${f.alpha * 0.45})`;
        ctx.fill();
        ctx.strokeStyle = `rgba(250, 220, 80, ${f.alpha * 0.7})`;
        ctx.lineWidth   = 2;
        ctx.stroke();
        ctx.restore();
        f.alpha -= 0.04 * speedFactor;
    });
}

// ── SECTION 17 : Mise à jour & dessin — mode normal ─────────────────────────

function drawVehicles() {
    const laneOffset = LANE_OFFSET;
    vehicles.forEach(v => {
        if (v.pfEnabled) { drawVehiclePF(v); return; }

        // Mode normal (boucle sur la même route)
        const rawX = v.road.from.x + (v.road.to.x - v.road.from.x) * v.progress;
        const rawY = v.road.from.y + (v.road.to.y - v.road.from.y) * v.progress;
        const dx   = v.road.to.x - v.road.from.x;
        const dy   = v.road.to.y - v.road.from.y;
        const len  = Math.sqrt(dx*dx + dy*dy);
        const perpX = (-dy/len) * laneOffset;
        const perpY = ( dx/len) * laneOffset;
        const isHoriz = Math.abs(dx) > Math.abs(dy);
        const x     = rawX + perpX;
        const y     = rawY + perpY + (isHoriz ? -14 : 0);
        const angle = Math.atan2(dy, dx) + Math.PI / 2;
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);
        if (carsImg.complete) {
            ctx.drawImage(carsImg, v.sprite.sx, v.sprite.sy, v.sprite.sw, v.sprite.sh, -11, -19, 22, 38);
        }
        ctx.restore();
    });
}

function updateTrafficLights() {
    trafficLights.forEach(tl => {
        tl.timer += speedFactor;
        const dureeActuelle = tl.state === 'green' ? dureeVertFrames : dureeRougeFrames;
        if (tl.timer > dureeActuelle) {
            tl.state = tl.state === 'green' ? 'red' : 'green';
            tl.timer = 0;
        }
    });
}

function updateVehicles() {
    vehicles.forEach(v => {
        if (v.pfEnabled) {
            updateVehiclePF(v);
            return;
        }
        // Mode normal : boucle
        let mult = 1.0;
        if (v.road.state === 'ralenti') mult = 0.4;
        else if (v.road.state === 'bouchon') mult = 0.1;
        v.progress += v.baseSpeed * speedFactor * mult;
        if (v.progress > 1) v.progress = 0;
    });
}

// ── SECTION 18 : Dashboard ───────────────────────────────────────────────────

function updateDashboard() {
    const counts = { fluide: 0, ralenti: 0, bouchon: 0 };
    vehicles.forEach(v => counts[v.road.state]++);
    const total = vehicles.length;

    document.getElementById('count-total').textContent   = total;
    document.getElementById('count-fluide').textContent  = counts.fluide;
    document.getElementById('count-ralenti').textContent = counts.ralenti;
    document.getElementById('count-bouchon').textContent = counts.bouchon;

    [
        { bar: 'bar-fluide',  tip: 'tip-fluide',  count: counts.fluide  },
        { bar: 'bar-ralenti', tip: 'tip-ralenti', count: counts.ralenti },
        { bar: 'bar-bouchon', tip: 'tip-bouchon', count: counts.bouchon },
    ].forEach(({ bar, tip, count }) => {
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

// ── SECTION 19 : API Markov ──────────────────────────────────────────────────

function getEtatsActuels() {
    const etats = {};
    roads.forEach((road, index) => { etats[index] = road.state; });
    return etats;
}

function appliquerNouveauxEtats(nouveauxEtats) {
    roads.forEach((road, index) => {
        const nouvelEtat = nouveauxEtats[String(index)];
        if (nouvelEtat) road.state = nouvelEtat;
    });
}

function mettreAJourFiles(files, interMax, wqMoyen) {
    for (let i = 0; i < 9; i++) {
        const cellNum = document.getElementById('queue-' + i);
        const cellDiv = cellNum ? cellNum.closest('.queue-cell') : null;
        const valeur  = files[String(i)] || 0;
        if (cellNum) cellNum.textContent = valeur;
        if (cellDiv) {
            cellDiv.classList.remove('saturee', 'chargee');
            if (valeur >= 6)      cellDiv.classList.add('saturee');
            else if (valeur >= 3) cellDiv.classList.add('chargee');
        }
    }
    const interMaxEl = document.getElementById('inter-max');
    const wqMoyenEl  = document.getElementById('wq-moyen');
    if (interMaxEl) interMaxEl.textContent = 'Nœud ' + (interMax.id + 1) + ' — ' + interMax.queue + ' veh.';
    if (wqMoyenEl)  wqMoyenEl.textContent  = wqMoyen + ' s';
}

function mettreAJourOptimisation(optim) {
    const rougeEl = document.getElementById('optim-rouge');
    const vertEl  = document.getElementById('optim-vert');
    const gainEl  = document.getElementById('optim-gain');
    if (rougeEl) rougeEl.textContent = optim.duree_rouge + ' s';
    if (vertEl)  vertEl.textContent  = optim.duree_vert  + ' s';
    if (gainEl)  gainEl.textContent  = '+' + optim.gain_pourcent + '%';
    dureeVertFrames  = optim.duree_vert  * 60;
    dureeRougeFrames = optim.duree_rouge * 60;
}

const INTERVALLE_TICK_MS = 2000;
let tickInterval = null;

function demarrerTick() {
    if (tickInterval !== null) return;
    tickInterval = setInterval(appellerTick, INTERVALLE_TICK_MS);
}

function arreterTick() {
    if (tickInterval !== null) { clearInterval(tickInterval); tickInterval = null; }
}

async function appellerTick() {
    if (!running) return;
    try {
        const reponse = await fetch('/api/tick/', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ etats: getEtatsActuels() }),
        });
        const donnees = await reponse.json();
        appliquerNouveauxEtats(donnees.etats);
        if (donnees.files) mettreAJourFiles(donnees.files, donnees.inter_max, donnees.wq_moyen);
        if (donnees.optimisation) { mettreAJourOptimisation(donnees.optimisation); appellerStats(); }
    } catch (erreur) {
        console.warn('Tick API échoué :', erreur);
    }
}

async function appellerStats() {
    if (!running) return;
    try {
        const reponse = await fetch('/api/stats/');
        const donnees = await reponse.json();
        const metriques = Object.values(donnees.metriques_par_route);
        const nb        = metriques.length;
        const lq_moyen  = (metriques.reduce((s, m) => s + m.Lq,  0) / nb).toFixed(3);
        const rho_moyen = (metriques.reduce((s, m) => s + m.rho, 0) / nb).toFixed(3);
        const lqEl  = document.getElementById('lq-moyen');
        const rhoEl = document.getElementById('rho-moyen');
        if (lqEl)  lqEl.textContent  = lq_moyen  + ' veh.';
        if (rhoEl) rhoEl.textContent = rho_moyen;
    } catch (erreur) {
        console.warn('Stats API échoué :', erreur);
    }
}

// ── SECTION 20 : Monte Carlo ─────────────────────────────────────────────────

async function changerScenario(scenario) {
    try {
        const reponse = await fetch('/api/scenario/', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ scenario }),
        });
        const donnees = await reponse.json();
        appliquerNouveauxEtats(donnees.etats);
        const risqueEl = document.getElementById('risque-bouchon');
        if (risqueEl && donnees.risque_bouchon !== undefined)
            risqueEl.textContent = Math.round(donnees.risque_bouchon * 100) + '%';
        showToast('Scénario : ' + donnees.info_scenario.nom, 'info');
    } catch (erreur) {
        console.warn('Scénario API échoué :', erreur);
    }
}

document.querySelectorAll('.scenario-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.scenario-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        changerScenario(btn.dataset.scenario);
    });
});

// ── SECTION 21 : Boucle principale ───────────────────────────────────────────

function loop() {
    if (!running) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawBackground();
    drawRoadStates();
    drawRoundabouts();

    // Indicateurs de chemin (avant les feux pour rester derrière)
    if (pathfindingMode) {
        drawPathIndicators();
        drawIntersectionFlashes();
    }

    drawTrafficLights();
    drawVehicles();      // gère normal ET pathfinding
    updateVehicles();
    updateTrafficLights();
    updateDashboard();
    updateClock();

    // Mise à jour des stats pathfinding (affichage uniquement)
    if (pathfindingMode) {
        const pfActive   = vehicles.filter(v => v.pfEnabled).length;
        const pfTurning  = vehicles.filter(v => v.pfTurning).length;
        const pfFetching = vehicles.filter(v => v.pfFetchPending).length;
        const elA = document.getElementById('pf-stat-active');
        const elT = document.getElementById('pf-stat-turning');
        const elF = document.getElementById('pf-stat-fetching');
        if (elA) elA.textContent = pfActive + ' / ' + vehicles.length;
        if (elT) elT.textContent = pfTurning;
        if (elF) elF.textContent = pfFetching;
    }

    animationId = requestAnimationFrame(loop);
}

// ── SECTION 22 : Événements & initialisation ─────────────────────────────────

function togglePlayPause() {
    if (running) {
        running = false;
        cancelAnimationFrame(animationId);
        animationId = null;
        arreterTick();
        setStatus('en pause', '#fb923c', true);
        setButtons('paused');
        showToast('Simulation en pause', 'warning');
    } else {
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
        case 'p': case 'P':
            e.preventDefault();
            revelerPathfinding();
            break;
    }
});

btnTogglePlay.addEventListener('click', togglePlayPause);

btnReset.addEventListener('click', () => {
    vehicles.forEach(v => {
        v.progress   = 0;
        v.pfTurning  = false;
        v.pfStep     = 0;
        v.pfVisited  = [];
    });
    simSeconds = 0; frameAcc = 0;
    document.getElementById('clock').textContent = '00:00';
    setStatus('en cours...', '#4ade80', false);
    setButtons('running');
    showToast('Réinitialisé — ' + vehicles.length + ' véhicules remis à zéro', 'info');
    if (!running) { running = true; demarrerTick(); loop(); }
});

btnStop.addEventListener('click', () => {
    running = false;
    cancelAnimationFrame(animationId); animationId = null;
    arreterTick();
    vehicles.forEach(v => { v.progress = 0; v.pfTurning = false; });
    simSeconds = 0; frameAcc = 0;
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

// ── Révélation de la section Pathfinding (raccourci P) ───────────────────────

let pfSectionVisible = false;

function revelerPathfinding() {
    const section = document.getElementById('section-pathfinding');
    if (!section) return;

    if (!pfSectionVisible) {
        // Apparition avec animation
        section.style.display   = 'block';
        section.style.opacity   = '0';
        section.style.transform = 'translateY(-8px)';
        section.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        // Forcer reflow pour que la transition parte de 0
        section.getBoundingClientRect();
        section.style.opacity   = '1';
        section.style.transform = 'translateY(0)';
        // Scroll doux vers la section
        setTimeout(() => section.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 80);
        pfSectionVisible = true;
        showToast('🗺 Pathfinding déverrouillé !', 'success', 3000);
    } else {
        // Disparition
        section.style.opacity   = '0';
        section.style.transform = 'translateY(-8px)';
        setTimeout(() => {
            section.style.display = 'none';
            section.style.transition = '';
        }, 400);
        pfSectionVisible = false;
        // Si le pathfinding était actif, on le désactive proprement
        if (pathfindingMode) disablePathfinding();
    }
}

// ── Contrôles Pathfinding ────────────────────────────────────────────────────

// Sélection du mode (continuer / nouveau départ)
btnPfContinue.addEventListener('click', () => {
    pfModeContinu = true;
    btnPfContinue.classList.add('active');
    btnPfRestart.classList.remove('active');
});

btnPfRestart.addEventListener('click', () => {
    pfModeContinu = false;
    btnPfRestart.classList.add('active');
    btnPfContinue.classList.remove('active');
});

// Bouton principal Pathfinding
btnPathfinding.addEventListener('click', () => {
    if (pathfindingMode) {
        // Désactiver
        disablePathfinding();
    } else {
        // Activer : si simulation pas démarrée, la lancer
        if (!running) {
            running = true;
            setStatus('en cours...', '#4ade80', false);
            setButtons('running');
            demarrerTick();
            loop();
        }
        initPathfinding(pfModeContinu);
    }
});

// Raccourci clavier D = panneau latéral
document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'd' || e.key === 'D') {
        const sidebar = document.getElementById('sidebar');
        const sideToggle = document.getElementById('sidebar-toggle');
        if (sidebar) sidebar.classList.toggle('collapsed');
        if (sideToggle) sideToggle.classList.toggle('collapsed');
    }
});

// ── Lancement — attend que les 4 images soient chargées ──────────────────────

let imagesLoaded = 0;
const totalImages = 4;
const loadStart   = Date.now();

[bgImg, carsImg, tlRedImg, tlGrnImg].forEach(img => {
    img.onload = () => {
        imagesLoaded++;
        if (imagesLoaded === totalImages) {
            const remaining = Math.max(0, 3000 - (Date.now() - loadStart));
            setTimeout(() => {
                const overlay = document.getElementById('loading-overlay');
                overlay.classList.add('hidden');
                setTimeout(() => overlay.remove(), 400);
                setButtons('running');
                running = true;
                demarrerTick();
                loop();
            }, remaining);
        }
    };
    img.onerror = () => { imagesLoaded++; };
});
