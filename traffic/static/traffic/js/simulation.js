const canvas = document.getElementById('traffic-canvas');
    const ctx = canvas.getContext('2d');

    const nodes = {
        topLeft:     { x: 150, y: 100 },
        topRight:    { x: 450, y: 100 },
        bottomLeft:  { x: 150, y: 400 },
        bottomRight: { x: 450, y: 400 },
    };

    const roads = [
        { from: nodes.topLeft,     to: nodes.topRight    },
        { from: nodes.bottomLeft,  to: nodes.bottomRight },
        { from: nodes.topLeft,     to: nodes.bottomLeft  },
        { from: nodes.topRight,    to: nodes.bottomRight },
    ];

    // Véhicules — un par route, progress entre 0 et 1
    const vehicles = roads.map(road => ({
        road: road,
        progress: Math.random(), // position initiale aléatoire
        speed: 0.003 + Math.random() * 0.003,
    }));

    function drawRoads() {
        roads.forEach(road => {
            ctx.beginPath();
            ctx.moveTo(road.from.x, road.from.y);
            ctx.lineTo(road.to.x, road.to.y);
            ctx.strokeStyle = '#4ade80';
            ctx.lineWidth = 4;
            ctx.stroke();
        });
    }

    function drawNodes() {
        Object.values(nodes).forEach(node => {
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

    let running = true;
    let animationId;

    function loop() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawRoads();
        drawNodes();
        drawVehicles();
        updateVehicles();
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