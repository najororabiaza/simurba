const canvas = document.getElementById('traffic-canvas');
    const ctx = canvas.getContext('2d');

    const nodes = {
        topLeft:     { x: 150, y: 100 },
        topRight:    { x: 450, y: 100 },
        bottomLeft:  { x: 150, y: 400 },
        bottomRight: { x: 450, y: 400 },
    };

    const roads = [
        { from: nodes.topLeft,     to: nodes.topRight, state:'fluide'},
        { from: nodes.bottomLeft,  to: nodes.bottomRight, state:'ralenti' },
        { from: nodes.topLeft,     to: nodes.bottomLeft, state:'bouchon'  },
        { from: nodes.topRight,    to: nodes.bottomRight, state:'fluide' },
    ];

    const stateColors = {
        fluide: '#4ade80', // vert
        ralenti: '#fb923c', // orange
        bouchon: '#ef4444', // rouge
    }

    // Véhicules — un par route, progress entre 0 et 1
    const vehicles = roads.map(road => ({
        road: road,
        progress: Math.random(), // position initiale aléatoire
        speed: 0.003 + Math.random() * 0.003,
    }));

    function drawBackground() {
        ctx.fillStyle = '#1a2a1a';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = '#2a3a2a';
        ctx.lineWidth = 1;
        for (let x = 0; x < canvas.width; x += 50) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
        }
        for (let y = 0; y < canvas.height; y += 50) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
        }
    }
    
    function drawRoads() {
        roads.forEach(road => {
            // Route asphalte
            ctx.beginPath();
            ctx.moveTo(road.from.x, road.from.y);
            ctx.lineTo(road.to.x, road.to.y);
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 20;
            ctx.stroke();
    
            // Couleur état
            ctx.beginPath();
            ctx.moveTo(road.from.x, road.from.y);
            ctx.lineTo(road.to.x, road.to.y);
            ctx.strokeStyle = stateColors[road.state];
            ctx.lineWidth = 2;
            ctx.setLineDash([10, 10]);
            ctx.stroke();
            ctx.setLineDash([]);
        });
    }
    
    function drawNodes() {
        Object.values(nodes).forEach(node => {
            // Halo
            ctx.beginPath();
            ctx.arc(node.x, node.y, 20, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(233, 69, 96, 0.2)';
            ctx.fill();
            // Centre
            ctx.beginPath();
            ctx.arc(node.x, node.y, 10, 0, Math.PI * 2);
            ctx.fillStyle = '#e94560';
            ctx.fill();
        });
    }

    function drawVehicles() {
        vehicles.forEach(v => {
            const x = v.road.from.x + (v.road.to.x - v.road.from.x) * v.progress;
            const y = v.road.from.y + (v.road.to.y - v.road.from.y) * v.progress;
            ctx.beginPath();
            ctx.arc(x, y, 6, 0, Math.PI * 2);
            ctx.fillStyle = '#facc15';
            ctx.fill();
        });
    }

    function updateVehicles() {
        vehicles.forEach(v => {
            v.progress += v.speed;
            if (v.progress > 1) v.progress = 0; // repart du début
        });
    }

    function updateDashboard() {
        const counts = { fluide: 0, ralenti: 0, bouchon: 0 };
        vehicles.forEach(v => counts[v.road.state]++);
        document.getElementById('count-fluide').textContent = counts.fluide;
        document.getElementById('count-ralenti').textContent = counts.ralenti;
        document.getElementById('count-bouchon').textContent = counts.bouchon;
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
        if(!running) {
            running = true;
            document.getElementById('status').textContent= 'en cours...';
            loop();
        }
    });

    document.getElementById('btn-pause').addEventListener('click', () => {
        running = false;
        cancelAnimationFrame(animationId);
        document.getElementById('status').textContent= 'en pause'; 
    });

    document.getElementById('btn-reset').addEventListener('click', () => {
        vehicles.forEach(v => {v.progress = 0});
        document.getElementById('status').textContent = 'en cours...';
        if(!running) {running = true; loop();}
    })    ;

    loop();