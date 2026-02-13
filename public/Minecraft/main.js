/* global THREE */

// =====================================================
// BlockCraft — Mountains + Trees + Building + Collision
// =====================================================

// ---------- Scene / Camera / Renderer ----------
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87ceeb);

const camera = new THREE.PerspectiveCamera(
  75,
  window.innerWidth / window.innerHeight,
  0.1,
  4000
);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
document.body.appendChild(renderer.domElement);

// Lights
const sun = new THREE.DirectionalLight(0xffffff, 1.0);
sun.position.set(60, 140, 40);
scene.add(sun);
scene.add(new THREE.AmbientLight(0xffffff, 0.45));

// Soft fog (nice vibe)
scene.fog = new THREE.Fog(0x87ceeb, 60, 900);

// ---------- Materials ----------
let selectedBlock = "grass";

const blockMaterials = {
  grass: new THREE.MeshStandardMaterial({ color: 0x55aa55 }),
  stone: new THREE.MeshStandardMaterial({ color: 0x888888 }),
  dirt:  new THREE.MeshStandardMaterial({ color: 0x8b5a2b }),
  water: new THREE.MeshStandardMaterial({ color: 0x2f7fe0, transparent: true, opacity: 0.85 }),
  wood:  new THREE.MeshStandardMaterial({ color: 0x6b4f2a }),
  leaf:  new THREE.MeshStandardMaterial({ color: 0x2f8a3a })
};

const blockGeo = new THREE.BoxGeometry(1, 1, 1);

// ---------- Placed Blocks ----------
const blocks = []; // only player-placed blocks (removeable)
function createBlock(x, y, z, type = selectedBlock) {
  const mat = blockMaterials[type] || blockMaterials.grass;
  const mesh = new THREE.Mesh(blockGeo, mat.clone());
  mesh.position.set(x, y, z);
  scene.add(mesh);
  blocks.push(mesh);
  return mesh;
}
function removeBlock(mesh) {
  const idx = blocks.indexOf(mesh);
  if (idx !== -1) blocks.splice(idx, 1);
  scene.remove(mesh);
  mesh.geometry.dispose?.();
  mesh.material.dispose?.();
}

// ---------- Simple 2D Noise (fast, no libs) ----------
function hash2(x, z) {
  // deterministic pseudo-random 0..1
  const s = Math.sin(x * 127.1 + z * 311.7) * 43758.5453123;
  return s - Math.floor(s);
}
function smoothstep(t) { return t * t * (3 - 2 * t); }
function lerp(a, b, t) { return a + (b - a) * t; }

function valueNoise(x, z) {
  const xi = Math.floor(x);
  const zi = Math.floor(z);
  const xf = x - xi;
  const zf = z - zi;

  const a = hash2(xi, zi);
  const b = hash2(xi + 1, zi);
  const c = hash2(xi, zi + 1);
  const d = hash2(xi + 1, zi + 1);

  const u = smoothstep(xf);
  const v = smoothstep(zf);

  return lerp(lerp(a, b, u), lerp(c, d, u), v);
}

function fbm(x, z) {
  // fractal noise
  let total = 0;
  let amp = 1;
  let freq = 0.02;
  let max = 0;

  for (let i = 0; i < 5; i++) {
    total += valueNoise(x * freq, z * freq) * amp;
    max += amp;
    amp *= 0.5;
    freq *= 2;
  }
  return total / max;
}

// ---------- Terrain (mountains) ----------
const TERRAIN_SIZE = 700;
const SEGMENTS = 260; // detail
const terrainGeo = new THREE.PlaneGeometry(TERRAIN_SIZE, TERRAIN_SIZE, SEGMENTS, SEGMENTS);
terrainGeo.rotateX(-Math.PI / 2);

const pos = terrainGeo.attributes.position;

function terrainHeight(x, z) {
  // Mountains + rolling hills
  const n = fbm(x, z);
  const m = fbm(x + 999, z - 222); // extra layer
  const hills = n * 12;
  const mountains = Math.pow(m, 2.1) * 55;
  const base = 0;
  return base + hills + mountains;
}

// Displace vertices
for (let i = 0; i < pos.count; i++) {
  const x = pos.getX(i);
  const z = pos.getZ(i);
  const y = terrainHeight(x, z);
  pos.setY(i, y);
}
terrainGeo.computeVertexNormals();

const terrainMat = new THREE.MeshStandardMaterial({
  color: 0x3f8f3f,
  roughness: 1,
  metalness: 0
});

const terrain = new THREE.Mesh(terrainGeo, terrainMat);
terrain.receiveShadow = true;
scene.add(terrain);

// Water plane (low areas)
const waterY = 6;
const waterGeo = new THREE.PlaneGeometry(TERRAIN_SIZE, TERRAIN_SIZE, 1, 1);
waterGeo.rotateX(-Math.PI / 2);
const waterMat = blockMaterials.water.clone();
const water = new THREE.Mesh(waterGeo, waterMat);
water.position.y = waterY;
scene.add(water);

// ---------- Trees (simple voxel trees) ----------
function addTree(x, z) {
  const baseY = terrainHeight(x, z);
  if (baseY < waterY + 1) return; // avoid water

  // trunk height
  const h = 4 + Math.floor(hash2(x, z) * 3);

  // trunk
  for (let i = 0; i < h; i++) {
    const t = new THREE.Mesh(blockGeo, blockMaterials.wood.clone());
    t.position.set(Math.round(x), Math.floor(baseY) + 1 + i, Math.round(z));
    scene.add(t);
  }

  // leaves blob
  const topY = Math.floor(baseY) + 1 + h;
  const radius = 2;

  for (let lx = -radius; lx <= radius; lx++) {
    for (let lz = -radius; lz <= radius; lz++) {
      for (let ly = -1; ly <= 2; ly++) {
        const dist = Math.abs(lx) + Math.abs(lz) + Math.abs(ly);
        if (dist > 4) continue;

        const leaf = new THREE.Mesh(blockGeo, blockMaterials.leaf.clone());
        leaf.position.set(
          Math.round(x) + lx,
          topY + ly,
          Math.round(z) + lz
        );
        scene.add(leaf);
      }
    }
  }
}

// Scatter trees (not too many)
const TREE_COUNT = 70;
for (let t = 0; t < TREE_COUNT; t++) {
  const x = (hash2(t * 10, t * 33) - 0.5) * (TERRAIN_SIZE * 0.85);
  const z = (hash2(t * 90, t * 17) - 0.5) * (TERRAIN_SIZE * 0.85);

  // Only place some (noise gate)
  const gate = fbm(x + 200, z - 500);
  if (gate > 0.55) addTree(x, z);
}

// ---------- Player / Camera movement ----------
let yaw = 0;
let pitch = 0;
let isLocked = false;

// Player body
const player = {
  pos: new THREE.Vector3(0, 30, 20), // feet position
  velY: 0,
  onGround: false,
  radius: 0.35,      // xz
  height: 1.75,      // player height
  eye: 1.6,          // camera height above feet
  speed: 0.09,       // walking speed (not too fast)
  gravity: 0.012,
  jump: 0.28
};

camera.position.set(player.pos.x, player.pos.y + player.eye, player.pos.z);

// Controls
const keys = {};
document.addEventListener("keydown", (e) => (keys[e.code] = true));
document.addEventListener("keyup", (e) => (keys[e.code] = false));

// Pointer lock
document.body.addEventListener("click", () => {
  document.body.requestPointerLock();
});
document.addEventListener("pointerlockchange", () => {
  isLocked = document.pointerLockElement === document.body;
});
document.addEventListener("mousemove", (e) => {
  if (!isLocked) return;
  const sens = 0.002;
  yaw -= e.movementX * sens;
  pitch -= e.movementY * sens;
  pitch = Math.max(-1.45, Math.min(1.45, pitch));
});

// Collision helpers (placed blocks only)
const playerBox = new THREE.Box3();
const blockBox = new THREE.Box3();

function collidesAt(testPos) {
  // Build AABB from feet pos
  const center = new THREE.Vector3(testPos.x, testPos.y + player.height / 2, testPos.z);
  const size = new THREE.Vector3(player.radius * 2, player.height, player.radius * 2);
  playerBox.setFromCenterAndSize(center, size);

  for (const b of blocks) {
    blockBox.setFromObject(b);
    if (playerBox.intersectsBox(blockBox)) return true;
  }
  return false;
}

function updatePlayer() {
  // Build directions from yaw
  const forward = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)).normalize();
  const right = new THREE.Vector3(Math.sin(yaw - Math.PI / 2), 0, Math.cos(yaw - Math.PI / 2)).normalize();

  const move = new THREE.Vector3();
  if (keys["KeyW"]) move.addScaledVector(forward, -1);
  if (keys["KeyS"]) move.addScaledVector(forward, 1);
  if (keys["KeyA"]) move.addScaledVector(right, 1);
  if (keys["KeyD"]) move.addScaledVector(right, -1);

  if (move.lengthSq() > 0) move.normalize().multiplyScalar(player.speed);

  // Axis-separated collision (prevents sticky walls)
  const next = player.pos.clone();

  // X
  next.x += move.x;
  if (!collidesAt(next)) player.pos.x = next.x;

  // Z
  next.copy(player.pos);
  next.z += move.z;
  if (!collidesAt(next)) player.pos.z = next.z;

  // Gravity
  player.velY -= player.gravity;
  next.copy(player.pos);
  next.y += player.velY;

  // Ground from terrain
  const groundY = terrainHeight(player.pos.x, player.pos.z);
  const minFeet = Math.max(groundY, waterY) + 0.0;

  // Block collision vertical
  if (!collidesAt(next)) {
    player.pos.y = next.y;
    player.onGround = false;
  } else {
    // If we hit a block while falling
    player.velY = 0;
    player.onGround = true;
  }

  // Terrain floor clamp
  if (player.pos.y < minFeet) {
    player.pos.y = minFeet;
    player.velY = 0;
    player.onGround = true;
  }

  // Jump
  if (keys["Space"] && player.onGround) {
    player.velY = player.jump;
    player.onGround = false;
  }

  // Update camera transform
  camera.rotation.order = "YXZ";
  camera.rotation.y = yaw;
  camera.rotation.x = pitch;

  camera.position.set(player.pos.x, player.pos.y + player.eye, player.pos.z);
}

// ---------- Raycasting for building/mining ----------
const raycaster = new THREE.Raycaster();
raycaster.far = 12;

function getAimRay() {
  // Crosshair center
  raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
}

function snap(n) { return Math.round(n); }

// place/remove
document.addEventListener("mousedown", (e) => {
  // 0 left, 2 right
  getAimRay();

  // Hit placed blocks first
  const hits = raycaster.intersectObjects(blocks, false);

  if (hits.length > 0) {
    const hit = hits[0];

    if (e.button === 2) {
      removeBlock(hit.object);
      return;
    }

    // Place adjacent to face normal
    const normal = hit.face.normal.clone();
    const p = hit.object.position.clone().add(normal);
    createBlock(snap(p.x), snap(p.y), snap(p.z), selectedBlock);
    return;
  }

  // Otherwise hit terrain
  const terrainHits = raycaster.intersectObject(terrain, false);
  if (!terrainHits.length) return;

  const p = terrainHits[0].point;

  if (e.button === 2) {
    // Can't remove terrain in this demo (keeps it fast)
    return;
  }

  // Place on top of terrain at snapped grid
  const x = snap(p.x);
  const z = snap(p.z);
  const y = Math.floor(terrainHeight(x, z)) + 1;
  createBlock(x, y, z, selectedBlock);
});

// Disable right-click menu
document.addEventListener("contextmenu", (e) => e.preventDefault());

// ---------- Hotbar ----------
const slots = document.querySelectorAll(".slot");
function setSelected(blockName) {
  selectedBlock = blockName;
  slots.forEach(s => s.classList.toggle("selected", s.dataset.block === blockName));
}
slots.forEach(slot => {
  slot.addEventListener("click", () => setSelected(slot.dataset.block));
});
document.addEventListener("keydown", (e) => {
  const n = Number(e.key);
  if (n >= 1 && n <= 5) {
    const slot = slots[n - 1];
    if (slot) setSelected(slot.dataset.block);
  }
});

// ---------- Resize ----------
window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// ---------- Start position (above terrain) ----------
(function spawn() {
  const y = terrainHeight(0, 20);
  player.pos.set(0, y + 2, 20);
  camera.position.set(player.pos.x, player.pos.y + player.eye, player.pos.z);
})();

// ---------- Main Loop ----------
function animate() {
  requestAnimationFrame(animate);
  updatePlayer();
  renderer.render(scene, camera);
}
animate();
