import InputHandler from './InputHandler.js';
import Game from './Game.js';

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

export const input = new InputHandler();
export let game;

function loadNextLevel() {
    const nextLevel = game.currentLevelIdx + 1;
    if (nextLevel < game.levels.length) {
        game.loadLevel(nextLevel);
    } else {
        alert('Gratulacje! Ukończyłeś wszystkie poziomy!');
        game.loadLevel(0);
    }
}

function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    if (game && game.state !== 'TITLE_SCREEN' && game.state !== 'LEVEL_COMPLETE') {
        game.loadLevel(game.currentLevelIdx);
    }
}

let lastTime = 0;
function loop(timestamp = 0) {
    if (!game) return;

    // Calculate delta time in seconds
    const deltaTime = lastTime ? Math.min((timestamp - lastTime) / 1000, 0.1) : 0.016;
    lastTime = timestamp;

    game.update(deltaTime);
    game.draw();
    requestAnimationFrame(loop);
}

// Mouse handling for title screen and level complete screen
canvas.addEventListener('mousemove', (e) => {
    if (!game) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Title screen button
    if (game.state === 'TITLE_SCREEN' && game.titleButtonBounds) {
        const btn = game.titleButtonBounds;
        game.titleButtonHover = (
            mouseX >= btn.x && mouseX <= btn.x + btn.width &&
            mouseY >= btn.y && mouseY <= btn.y + btn.height
        );
        canvas.style.cursor = game.titleButtonHover ? 'pointer' : 'default';
    }
    // Level complete button
    else if (game.state === 'LEVEL_COMPLETE' && game.levelCompleteButtonBounds) {
        const btn = game.levelCompleteButtonBounds;
        game.levelCompleteButtonHover = (
            mouseX >= btn.x && mouseX <= btn.x + btn.width &&
            mouseY >= btn.y && mouseY <= btn.y + btn.height
        );
        canvas.style.cursor = game.levelCompleteButtonHover ? 'pointer' : 'default';
    }
    // Reset cursor when not on special screens
    else {
        canvas.style.cursor = 'default';
    }
});

canvas.addEventListener('click', (e) => {
    if (!game) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Title screen button
    if (game.state === 'TITLE_SCREEN' && game.titleButtonBounds) {
        const btn = game.titleButtonBounds;
        const isInButton = (
            mouseX >= btn.x && mouseX <= btn.x + btn.width &&
            mouseY >= btn.y && mouseY <= btn.y + btn.height
        );

        if (isInButton) {
            canvas.style.cursor = 'default';
            game.startGame();
        }
    }

    // Level complete button
    if (game.state === 'LEVEL_COMPLETE' && game.levelCompleteButtonBounds) {
        const btn = game.levelCompleteButtonBounds;
        const isInButton = (
            mouseX >= btn.x && mouseX <= btn.x + btn.width &&
            mouseY >= btn.y && mouseY <= btn.y + btn.height
        );

        if (isInButton) {
            canvas.style.cursor = 'default';
            loadNextLevel();
        }
    }
});

window.onload = function () {
    game = new Game();
    window.addEventListener('resize', resize);
    resize(); // Initial resize and level load
    loop();
};