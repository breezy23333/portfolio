import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js";

// ================= SCENE =================
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000010);
scene.fog = new THREE.Fog(0x000010, 30, 260);

// ================= CAMERA =================
const camera = new THREE.PerspectiveCamera(70, innerWidth / innerHeight, 0.1, 1000);
camera.position.set(0, 12, 18);

// ================= RENDERER =================
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
document.body.appendChild(renderer.domElement);

// ================= LIGHTS =================
scene.add(new THREE.AmbientLight(0xffffff, 0.22));
const sunLight = new THREE.DirectionalLight(0xffffff, 1.4);
sunLight.position.set(0, 50, -120);
scene.add(sunLight);

// ================= PLAYER =================
const shipGeo = new THREE.ConeGeometry(0.6, 2, 8);
const shipMat = new THREE.MeshStandardMaterial({ color: 0x00ffff, roughness: 0.2, metalness: 0.6 });
const ship = new THREE.Mesh(shipGeo, shipMat);
ship.rotation.x = Math.PI / 2;
ship.position.set(0, 0.5, 0);
scene.add(ship);

// ================= HORIZON SUN =================
const sunGeo = new THREE.SphereGeometry(20, 32, 32);
const sunMat = new THREE.MeshBasicMaterial({ color: 0xff6600 });
const horizonSun = new THREE.Mesh(sunGeo, sunMat);
scene.add(horizonSun);

// glow halo
const haloGeo = new THREE.SphereGeometry(28, 32, 32);
const haloMat = new THREE.MeshBasicMaterial({ color: 0xff3300, transparent: true, opacity: 0.14 });
const sunHalo = new THREE.Mesh(haloGeo, haloMat);
scene.add(sunHalo);

// ================= INFINITE GROUND =================
const groundW = 24;
const groundL = 220;
const groundGeo = new THREE.PlaneGeometry(groundW, groundL);
const groundMat = new THREE.MeshStandardMaterial({
  color: 0x050510,
  roughness: 0.85,
  metalness: 0.15
});

const ground1 = new THREE.Mesh(groundGeo, groundMat);
const ground2 = new THREE.Mesh(groundGeo, groundMat);

ground1.rotation.x = -Math.PI / 2.05;
ground2.rotation.x = -Math.PI / 2.05;

ground1.position.set(0, 0, -groundL / 2);
ground2.position.set(0, 0, -groundL - groundL / 2);

scene.add(ground1, ground2);

// ================= LANE LINES =================
const laneGeo = new THREE.BoxGeometry(0.18, 0.01, 6);
const laneMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });

const lanes = [];
for (let i = 0; i < 26; i++) {
  const left = new THREE.Mesh(laneGeo, laneMat);
  left.position.set(-5, 0.03, -i * 14);
  scene.add(left);
  lanes.push(left);

  const right = new THREE.Mesh(laneGeo, laneMat);
  right.position.set(5, 0.03, -i * 14);
  scene.add(right);
  lanes.push(right);
}

// ================= STARFIELD (subtle) =================
const starsGeo = new THREE.PlaneGeometry(120, 520);
const starsMat = new THREE.MeshBasicMaterial({ color: 0x05050f });
const stars1 = new THREE.Mesh(starsGeo, starsMat);
const stars2 = new THREE.Mesh(starsGeo, starsMat);

stars1.rotation.x = -Math.PI / 2;
stars2.rotation.x = -Math.PI / 2;
stars1.position.z = -260;
stars2.position.z = -780;
stars1.position.y = -0.1;
stars2.position.y = -0.1;
scene.add(stars1, stars2);

// ================= OBJECTS =================
const asteroids = [];
const asteroidGeo = new THREE.DodecahedronGeometry(1);
const asteroidMat = new THREE.MeshStandardMaterial({ color: 0x666666, roughness: 1, metalness: 0 });

const boosts = [];
const boostGeo = new THREE.BoxGeometry(3, 0.12, 3);
const boostMat = new THREE.MeshBasicMaterial({ color: 0xff00ff });

// ================= GAME STATE =================
let score = 0;
let speed = 0.45;
let timeLeft = 60;
let gameRunning = true;

const scoreUI = document.getElementById("score");
const timerUI = document.getElementById("timer");
const gameOverScreen = document.getElementById("gameOverScreen");
const finalScore = document.getElementById("finalScore");

// ================= INPUT =================
const keys = {};
addEventListener("keydown", e => keys[e.code] = true);
addEventListener("keyup", e => keys[e.code] = false);

// ================= SPAWN =================
function spawnAsteroidWave() {
  if (!gameRunning) return;

  const lanesX = [-5, 0, 5];

  lanesX.forEach(x => {
    if (Math.random() > 0.42) {
      const rock = new THREE.Mesh(asteroidGeo, asteroidMat);
      rock.position.set(x, 0.7, ship.position.z - 140);
      rock.rotation.set(Math.random(), Math.random(), Math.random());
      rock.scale.setScalar(1.2 + Math.random() * 1.6);
      scene.add(rock);
      asteroids.push(rock);
    }
  });
}
setInterval(spawnAsteroidWave, 1100);

function spawnBoost() {
  if (!gameRunning) return;

  const pad = new THREE.Mesh(boostGeo, boostMat);
  const lane = [-5, 0, 5][Math.floor(Math.random() * 3)];
  pad.position.set(lane, 0.06, ship.position.z - 190);
  scene.add(pad);
  boosts.push(pad);
}
setInterval(spawnBoost, 4200);

// ================= GAME OVER =================
function endGame() {
  gameRunning = false;
  finalScore.innerText = "Final Score: " + score;
  gameOverScreen.classList.remove("hidden");
}
window.restartGame = function () { location.reload(); };

// ================= TIMER + DAY CYCLE =================
setInterval(() => {
  if (!gameRunning) return;

  timeLeft--;
  timerUI.innerText = "Time: " + timeLeft;

  const progress = Math.max(0, timeLeft) / 60; // 1 -> 0
  // sky darker over time
  scene.background = new THREE.Color().setHSL(
    0.65 * progress,   // hue
    0.55,
    0.08 + 0.18 * progress
  );

  // sun shifts color slightly
  horizonSun.material.color.setHSL(0.08 + 0.08 * progress, 1, 0.5);

  if (timeLeft <= 0) endGame();
}, 1000);

// ================= LOOP =================
function animate() {
  requestAnimationFrame(animate);

  if (!gameRunning) {
    renderer.render(scene, camera);
    return;
  }

  // controls
  if (keys["KeyA"]) ship.position.x -= 0.28;
  if (keys["KeyD"]) ship.position.x += 0.28;
  ship.position.x = Math.max(-8, Math.min(8, ship.position.x));

  // move forward
  ship.position.z -= speed;
  speed += 0.0006;

  // speed fov feel
  camera.fov = 70 + Math.min(18, speed * 22);
  camera.updateProjectionMatrix();

  // camera follow
  camera.position.x = ship.position.x;
  camera.position.z = ship.position.z + 18;
  camera.lookAt(ship.position.x, 0, ship.position.z - 40);

  // sun follow
  horizonSun.position.set(0, 30, ship.position.z - 420);
  sunHalo.position.copy(horizonSun.position);

  // ground loop
  ground1.position.z += speed;
  ground2.position.z += speed;

  const resetZ = ship.position.z - (groundL * 1.5);
  if (ground1.position.z > ship.position.z + 40) ground1.position.z = resetZ;
  if (ground2.position.z > ship.position.z + 40) ground2.position.z = resetZ;

  // stars loop
  stars1.position.z += speed;
  stars2.position.z += speed;
  if (stars1.position.z > ship.position.z + 40) stars1.position.z = ship.position.z - 820;
  if (stars2.position.z > ship.position.z + 40) stars2.position.z = ship.position.z - 820;

  // lane lines loop
  for (const l of lanes) {
    l.position.z += speed * 2;
    if (l.position.z > ship.position.z + 10) {
      l.position.z = ship.position.z - 360;
    }
  }

  // asteroids
  for (let i = asteroids.length - 1; i >= 0; i--) {
    const a = asteroids[i];
    a.position.z += speed * 2.2;
    a.rotation.x += 0.01;
    a.rotation.y += 0.013;

    if (a.position.distanceTo(ship.position) < 1.7) endGame();

    if (a.position.z > ship.position.z + 14) {
      scene.remove(a);
      asteroids.splice(i, 1);
      score++;
      scoreUI.innerText = "Score: " + score;

      if (score % 20 === 0) timeLeft += 5;
    }
  }

  // boosts
  for (let i = boosts.length - 1; i >= 0; i--) {
    const b = boosts[i];
    b.position.z += speed * 1.6;

    if (b.position.distanceTo(ship.position) < 2.2) {
      speed += 0.35;
      scene.remove(b);
      boosts.splice(i, 1);
    }

    if (b.position.z > ship.position.z + 14) {
      scene.remove(b);
      boosts.splice(i, 1);
    }
  }

  renderer.render(scene, camera);
}

animate();

// ================= RESIZE =================
addEventListener("resize", () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});
