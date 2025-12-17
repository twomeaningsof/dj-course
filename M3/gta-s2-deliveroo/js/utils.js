// --- COLLAPSIBLE SECTIONS ---
export function toggleSection(sectionId) {
    const content = document.getElementById(sectionId + '-content');
    const icon = document.getElementById(sectionId + '-icon');

    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        icon.classList.remove('collapsed');
    } else {
        content.classList.add('collapsed');
        icon.classList.add('collapsed');
    }
}

// --- UTILS ---
export const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
export function playBonkSound() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(150, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(40, audioCtx.currentTime + 0.5);
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.6);
}

export function playCurbSound() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'square';
    osc.frequency.setValueAtTime(80, audioCtx.currentTime);
    osc.frequency.linearRampToValueAtTime(60, audioCtx.currentTime + 0.1);
    gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.2);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.2);
}

// Dźwięk piszczących opon podczas poślizgu
export let driftOscillator = null;
export let driftGain = null;

export function startDriftSound(intensity = 1.0) {
    if (audioCtx.state === 'suspended') audioCtx.resume();

    // Jeśli już gra, nie twórz nowego
    if (driftOscillator) return;

    driftOscillator = audioCtx.createOscillator();
    driftGain = audioCtx.createGain();

    driftOscillator.type = 'sawtooth';
    driftOscillator.frequency.setValueAtTime(180 + intensity * 100, audioCtx.currentTime);

    driftGain.gain.setValueAtTime(0, audioCtx.currentTime);
    driftGain.gain.linearRampToValueAtTime(0.15 * intensity, audioCtx.currentTime + 0.05);

    driftOscillator.connect(driftGain);
    driftGain.connect(audioCtx.destination);
    driftOscillator.start();
}

export function updateDriftSound(intensity = 1.0) {
    if (!driftOscillator || !driftGain) return;

    const now = audioCtx.currentTime;
    driftOscillator.frequency.setValueAtTime(180 + intensity * 100, now);
    driftGain.gain.setValueAtTime(0.15 * intensity, now);
}

export function stopDriftSound() {
    if (!driftOscillator || !driftGain) return;

    const now = audioCtx.currentTime;
    driftGain.gain.linearRampToValueAtTime(0.01, now + 0.1);

    setTimeout(() => {
        if (driftOscillator) {
            driftOscillator.stop();
            driftOscillator = null;
            driftGain = null;
        }
    }, 150);
}

// Dźwięk silnika na wysokich obrotach (revving)
export let engineRevOscillator = null;
export let engineRevGain = null;

export function startEngineRevSound(revLevel = 0.5) {
    if (audioCtx.state === 'suspended') audioCtx.resume();

    // Jeśli już gra, nie twórz nowego
    if (engineRevOscillator) return;

    engineRevOscillator = audioCtx.createOscillator();
    engineRevGain = audioCtx.createGain();

    engineRevOscillator.type = 'sawtooth';
    engineRevOscillator.frequency.setValueAtTime(80 + revLevel * 120, audioCtx.currentTime);

    engineRevGain.gain.setValueAtTime(0, audioCtx.currentTime);
    engineRevGain.gain.linearRampToValueAtTime(0.12 * revLevel, audioCtx.currentTime + 0.05);

    engineRevOscillator.connect(engineRevGain);
    engineRevGain.connect(audioCtx.destination);
    engineRevOscillator.start();
}

export function updateEngineRevSound(revLevel = 0.5) {
    if (!engineRevOscillator || !engineRevGain) return;

    const now = audioCtx.currentTime;
    engineRevOscillator.frequency.setValueAtTime(80 + revLevel * 120, now);
    engineRevGain.gain.setValueAtTime(0.12 * revLevel, now);
}

export function stopEngineRevSound() {
    if (!engineRevOscillator || !engineRevGain) return;

    const now = audioCtx.currentTime;
    engineRevGain.gain.linearRampToValueAtTime(0.01, now + 0.15);

    setTimeout(() => {
        if (engineRevOscillator) {
            engineRevOscillator.stop();
            engineRevOscillator = null;
            engineRevGain = null;
        }
    }, 200);
}


export function playLevelCompleteSound() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const gain = audioCtx.createGain();
    gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
    gain.connect(audioCtx.destination);

    const notes = [261.63, 329.63, 392.00, 523.25]; // C4, E4, G4, C5
    notes.forEach((freq, i) => {
        const osc = audioCtx.createOscillator();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime + i * 0.1);
        osc.connect(gain);
        osc.start(audioCtx.currentTime + i * 0.1);
        osc.stop(audioCtx.currentTime + i * 0.1 + 0.1);
    });
}

// Geometric Utils
export function getCorners(x, y, w, h, angle) {
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    const hw = w / 2;
    const hh = h / 2;
    return [
        { x: x + (hh * cos - hw * sin), y: y + (hh * sin + hw * cos) },
        { x: x + (hh * cos + hw * sin), y: y + (hh * sin - hw * cos) },
        { x: x + (-hh * cos + hw * sin), y: y + (-hh * sin - hw * cos) },
        { x: x + (-hh * cos - hw * sin), y: y + (-hh * sin + hw * cos) }
    ];
}

export function projectPolygon(axis, corners) {
    let min = Infinity;
    let max = -Infinity;
    for (let p of corners) {
        const proj = (p.x * axis.x + p.y * axis.y);
        if (proj < min) min = proj;
        if (proj > max) max = proj;
    }
    return { min, max };
}

export function overlap(a, b) {
    return !(a.min > b.max || b.min > a.max);
}

export function checkRectCollision(rectA, rectB) {
    const cornersA = getCorners(rectA.x, rectA.y, rectA.w, rectA.l, rectA.angle);
    const cornersB = getCorners(rectB.x, rectB.y, rectB.w, rectB.l, rectB.angle);
    const axes = [
        { x: Math.cos(rectA.angle), y: Math.sin(rectA.angle) },
        { x: -Math.sin(rectA.angle), y: Math.cos(rectA.angle) },
        { x: Math.cos(rectB.angle), y: Math.sin(rectB.angle) },
        { x: -Math.sin(rectB.angle), y: Math.cos(rectB.angle) }
    ];
    for (let axis of axes) {
        const pA = projectPolygon(axis, cornersA);
        const pB = projectPolygon(axis, cornersB);
        if (!overlap(pA, pB)) return false;
    }
    return true;
}

export function checkCircleRectCollision(circle, rect) {
    const cos = Math.cos(-rect.angle);
    const sin = Math.sin(-rect.angle);
    const dx = circle.x - rect.x;
    const dy = circle.y - rect.y;
    const localX = dx * cos - dy * sin;
    const localY = dx * sin + dy * cos;
    const closestX = Math.max(-rect.l / 2, Math.min(localX, rect.l / 2));
    const closestY = Math.max(-rect.w / 2, Math.min(localY, rect.w / 2));
    const distanceX = localX - closestX;
    const distanceY = localY - closestY;
    return (distanceX * distanceX) + (distanceY * distanceY) < (circle.r * circle.r);
}

export function isPointInRotatedRect(point, rect) {
    const cos = Math.cos(-rect.angle);
    const sin = Math.sin(-rect.angle);
    const dx = point.x - rect.x;
    const dy = point.y - rect.y;
    const localX = dx * cos - dy * sin;
    const localY = dx * sin + dy * cos;
    return Math.abs(localX) < rect.l / 2 && Math.abs(localY) < rect.w / 2;
}