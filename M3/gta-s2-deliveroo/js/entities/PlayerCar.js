import { CONFIG, VEHICLE_STATS } from '../constants.js';

export default class PlayerCar {
    constructor(x, y, angleDeg, carType = 'standard') {
        this.carType = carType;
        this.reset(x, y, angleDeg, carType);
    }

    reset(x, y, angleDeg, carType = 'standard') {
        console.log('b', carType)
        this.carType = carType;
        this.x = x;
        this.y = y;
        this.angle = angleDeg * (Math.PI / 180);
        this.speed = 0;

        // Wektor prędkości dla zaawansowanej fizyki
        this.velocityX = 0;
        this.velocityY = 0;
        this.angularVelocity = 0; // Prędkość rotacji

        this.steeringAngle = 0;

        this.w = VEHICLE_STATS[carType].width || VEHICLE_STATS['standard'].width;
        this.l = VEHICLE_STATS[carType].length || VEHICLE_STATS['standard'].length;
        this.engineOn = true;
        this.enterKeyProcessed = false;
        this.steeringMode = 'DRIVING';

        // Tryb zimowy - domyślnie wyłączony (bezpieczna jazda)
        if (this.winterMode === undefined) {
            this.winterMode = false;
        }

        // Stan poślizgu
        this.isDrifting = false;
        this.driftAngle = 0; // Kąt poślizgu
        this.skidMarks = []; // Ślady opon

        // Hamulec ręczny - startowanie
        this.handbrakeBoost = 0; // Zgromadzona moc (0-1)
        this.previousSpaceKey = false; // Czy w poprzedniej klatce trzymał SPACE
    }

    toggleSteeringMode() {
        if (this.steeringMode === 'DRIVING') {
            this.steeringMode = 'PARKING';
            document.getElementById('toggle-steering-mode').innerText = 'Asystent Kierownicy: WYŁ';
        } else {
            this.steeringMode = 'DRIVING';
            document.getElementById('toggle-steering-mode').innerText = 'Asystent Kierownicy: WŁ';
        }
    }

    toggleWinterMode() {
        this.winterMode = !this.winterMode;
        const btn = document.getElementById('toggle-winter-mode');
        if (this.winterMode) {
            btn.innerText = 'Poślizgi Zimowe: WŁ';
        } else {
            btn.innerText = 'Poślizgi Zimowe: WYŁ';
            // Wyczyść ślady opon przy wyłączeniu trybu zimowego
            this.skidMarks = [];
            this.isDrifting = false;
            // Zatrzymaj dźwięk poślizgu
            if (driftOscillator) {
                stopDriftSound();
            }
        }
    }

    update(input, deltaTime) {
        // Engine toggle
        if (input.keys.Enter) {
            if (!this.enterKeyProcessed) {
                this.engineOn = !this.engineOn;
                this.enterKeyProcessed = true;
            }
        } else {
            this.enterKeyProcessed = false;
        }

        // Wybierz fizykę w zależności od trybu
        if (this.winterMode) {
            this.updateWinterPhysics(input, deltaTime);
        } else {
            this.updateSimplePhysics(input, deltaTime);
        }
    }

    // === PROSTA FIZYKA (bezpieczna, przewidywalna) ===
    updateSimplePhysics(input, deltaTime) {
        // Normalize deltaTime to 60 FPS (deltaTime * 60 gives us a frame multiplier)
        const dt = deltaTime * 60;

        // === HAMULEC RĘCZNY - STARTOWANIE ===
        const isHandbraking = input.keys.Space;
        const isThrottling = input.keys.ArrowUp || input.keys.ArrowDown;

        // Budowanie boost gdy trzyma hamulec + gaz
        if (isHandbraking && isThrottling && this.engineOn) {
            this.handbrakeBoost = Math.min(CONFIG.handbrakeBoostMax, this.handbrakeBoost + CONFIG.handbrakeBoostRate * dt);

            // Hamuj auto podczas budowania boost
            this.speed *= Math.pow(0.8, dt); // Mocne hamowanie
            if (Math.abs(this.speed) < 0.5) this.speed = 0;

            // Dźwięk silnika na wysokich obrotach
            if (!engineRevOscillator) {
                startEngineRevSound(this.handbrakeBoost);
            } else {
                updateEngineRevSound(this.handbrakeBoost);
            }
        }
        // Jeśli puścił hamulec (ale dalej trzyma gaz) - LAUNCH!
        else if (!isHandbraking && this.previousSpaceKey && isThrottling && this.handbrakeBoost > 0.1) {
            // MOCNY START!
            const boostDirection = input.keys.ArrowUp ? 1 : -1;
            this.speed += boostDirection * this.handbrakeBoost * CONFIG.handbrakeBoostMultiplier;
            this.handbrakeBoost = 0; // Zużyte!

            // Zatrzymaj dźwięk silnika
            if (engineRevOscillator) {
                stopEngineRevSound();
            }
        }
        // Normalne zmniejszanie boost gdy nie używany
        else if (this.handbrakeBoost > 0) {
            this.handbrakeBoost = Math.max(0, this.handbrakeBoost - CONFIG.handbrakeBoostDecay * dt);

            // Zatrzymaj dźwięk gdy boost spada
            if (this.handbrakeBoost < 0.1 && engineRevOscillator) {
                stopEngineRevSound();
            }
        }

        this.previousSpaceKey = isHandbraking;

        // === NORMALNA FIZYKA ===
        if (this.engineOn) {
            // 1. Acceleration (tylko jeśli NIE buduje boost)
            if (!(isHandbraking && isThrottling)) {
                if (input.keys.ArrowUp) this.speed += CONFIG.acceleration * dt;
                else if (input.keys.ArrowDown) this.speed -= CONFIG.acceleration * dt;
            }

            // 2. Braking (tylko jeśli NIE trzyma gazu równocześnie)
            if (input.keys.Space && !isThrottling) {
                if (this.speed > 0) this.speed -= CONFIG.brakingForce * dt;
                else if (this.speed < 0) this.speed += CONFIG.brakingForce * dt;
                if (Math.abs(this.speed) < 0.5) this.speed = 0;
            }
        }

        // 3. Friction
        if (!input.keys.ArrowUp && !input.keys.ArrowDown && !input.keys.Space) {
            this.speed *= Math.pow(1 - CONFIG.friction, dt);
            if (Math.abs(this.speed) < 0.05) this.speed = 0;
        }
        if (!this.engineOn) {
            this.speed *= Math.pow(1 - CONFIG.friction, dt);
            if (Math.abs(this.speed) < 0.05) this.speed = 0;
        }

        // Limits
        if (this.speed > CONFIG.maxSpeed) this.speed = CONFIG.maxSpeed;
        if (this.speed < CONFIG.maxReverseSpeed) this.speed = CONFIG.maxReverseSpeed;

        // 4. Steering
        if (this.engineOn) {
            if (input.keys.ArrowLeft) {
                this.steeringAngle -= CONFIG.steerSpeed * dt;
            } else if (input.keys.ArrowRight) {
                this.steeringAngle += CONFIG.steerSpeed * dt;
            } else {
                if (this.steeringMode === 'DRIVING') {
                    // Auto-straighten in Driving Mode
                    if (this.steeringAngle > 0) {
                        this.steeringAngle -= CONFIG.steerRestoringDriving * dt;
                        if (this.steeringAngle < 0) this.steeringAngle = 0;
                    } else if (this.steeringAngle < 0) {
                        this.steeringAngle += CONFIG.steerRestoringDriving * dt;
                        if (this.steeringAngle > 0) this.steeringAngle = 0;
                    }
                }
            }
        }

        // Clamp steer
        if (this.steeringAngle > CONFIG.maxSteerAngle) this.steeringAngle = CONFIG.maxSteerAngle;
        if (this.steeringAngle < -CONFIG.maxSteerAngle) this.steeringAngle = -CONFIG.maxSteerAngle;

        // 5. Movement - prosty model kinematyczny
        if (Math.abs(this.speed) > 0.05) {
            const L = CONFIG.wheelBase;
            const oldAngle = this.angle;

            this.angle += (this.speed / L) * Math.tan(this.steeringAngle) * dt;

            const rearAxleX = this.x - (L / 2) * Math.cos(oldAngle);
            const rearAxleY = this.y - (L / 2) * Math.sin(oldAngle);

            const newRearAxleX = rearAxleX + this.speed * Math.cos(oldAngle) * dt;
            const newRearAxleY = rearAxleY + this.speed * Math.sin(oldAngle) * dt;

            this.x = newRearAxleX + (L / 2) * Math.cos(this.angle);
            this.y = newRearAxleY + (L / 2) * Math.sin(this.angle);
        } else {
            this.x += Math.cos(this.angle) * this.speed * dt;
            this.y += Math.sin(this.angle) * this.speed * dt;
        }

        // Synchronizuj velocityX/Y dla kompatybilności
        this.velocityX = Math.cos(this.angle) * this.speed;
        this.velocityY = Math.sin(this.angle) * this.speed;
        this.angularVelocity = 0;
        this.isDrifting = false;
        this.driftAngle = 0;
    }

    // === ZAAWANSOWANA FIZYKA Z POŚLIZGAMI (tryb zimowy) ===
    updateWinterPhysics(input, deltaTime) {
        // Normalize deltaTime to 60 FPS (deltaTime * 60 gives us a frame multiplier)
        const dt = deltaTime * 60;

        // === HAMULEC RĘCZNY - STARTOWANIE ===
        const isHandbraking = input.keys.Space;
        const isThrottling = input.keys.ArrowUp || input.keys.ArrowDown;

        // Budowanie boost gdy trzyma hamulec + gaz
        if (isHandbraking && isThrottling && this.engineOn) {
            this.handbrakeBoost = Math.min(CONFIG.handbrakeBoostMax, this.handbrakeBoost + CONFIG.handbrakeBoostRate * dt);

            // Hamuj auto podczas budowania boost
            this.velocityX *= Math.pow(0.75, dt);
            this.velocityY *= Math.pow(0.75, dt);
            const currentSpeed = Math.sqrt(this.velocityX * this.velocityX + this.velocityY * this.velocityY);
            if (currentSpeed < 0.5) {
                this.velocityX = 0;
                this.velocityY = 0;
            }

            // Dźwięk silnika na wysokich obrotach
            if (!engineRevOscillator) {
                startEngineRevSound(this.handbrakeBoost);
            } else {
                updateEngineRevSound(this.handbrakeBoost);
            }
        }
        // Jeśli puścił hamulec (ale dalej trzyma gaz) - LAUNCH!
        else if (!isHandbraking && this.previousSpaceKey && isThrottling && this.handbrakeBoost > 0.1) {
            // MOCNY START!
            const boostDirection = input.keys.ArrowUp ? 1 : -1;
            const boostPower = boostDirection * this.handbrakeBoost * CONFIG.handbrakeBoostMultiplier;

            // Dodaj boost w kierunku samochodu
            this.velocityX += Math.cos(this.angle) * boostPower;
            this.velocityY += Math.sin(this.angle) * boostPower;

            this.handbrakeBoost = 0; // Zużyte!

            // Zatrzymaj dźwięk silnika
            if (engineRevOscillator) {
                stopEngineRevSound();
            }
        }
        // Normalne zmniejszanie boost gdy nie używany
        else if (this.handbrakeBoost > 0) {
            this.handbrakeBoost = Math.max(0, this.handbrakeBoost - CONFIG.handbrakeBoostDecay * dt);

            // Zatrzymaj dźwięk gdy boost spada
            if (this.handbrakeBoost < 0.1 && engineRevOscillator) {
                stopEngineRevSound();
            }
        }

        this.previousSpaceKey = isHandbraking;

        // 1. Sterowanie - kąt skrętu
        if (this.engineOn) {
            if (input.keys.ArrowLeft) {
                this.steeringAngle -= CONFIG.steerSpeed * dt;
            } else if (input.keys.ArrowRight) {
                this.steeringAngle += CONFIG.steerSpeed * dt;
            } else {
                if (this.steeringMode === 'DRIVING') {
                    // Auto-prostowanie w trybie jazdy
                    if (this.steeringAngle > 0) {
                        this.steeringAngle -= CONFIG.steerRestoringDriving * dt;
                        if (this.steeringAngle < 0) this.steeringAngle = 0;
                    } else if (this.steeringAngle < 0) {
                        this.steeringAngle += CONFIG.steerRestoringDriving * dt;
                        if (this.steeringAngle > 0) this.steeringAngle = 0;
                    }
                }
            }
        }

        // Ogranicz kąt skrętu - zawsze maksymalny, niezależnie od prędkości
        // Fizyka zadba o poślizg przy dużych prędkościach!
        this.steeringAngle = Math.max(-CONFIG.maxSteerAngle, Math.min(CONFIG.maxSteerAngle, this.steeringAngle));

        // 2. Akceleracja i hamowanie
        const isBraking = input.keys.Space && !isThrottling; // Hamowanie tylko bez gazu
        let throttle = 0;

        // Akceleracja tylko jeśli NIE buduje boost (hamulec + gaz)
        if (this.engineOn && !(isHandbraking && isThrottling)) {
            if (input.keys.ArrowUp) throttle = CONFIG.acceleration * dt;
            else if (input.keys.ArrowDown) throttle = -CONFIG.acceleration * dt;
        }

        // 3. Oblicz prędkość w lokalnym układzie samochodu (forward/lateral)
        const cos = Math.cos(this.angle);
        const sin = Math.sin(this.angle);

        // Prędkość w kierunku "do przodu" i "na boki" względem auta
        const forwardVelocity = this.velocityX * cos + this.velocityY * sin;
        const lateralVelocity = -this.velocityX * sin + this.velocityY * cos;

        // 4. Zastosuj akcelerację do przodu
        let newForwardVelocity = forwardVelocity + throttle;

        // 5. Oblicz siłę boczną z powodu skrętu kół
        // FIZYKA: Siła odśrodkowa F = m*v²/r, więc rośnie KWADRATOWO z prędkością!
        const baseLateralVelocity = newForwardVelocity * Math.tan(this.steeringAngle);

        // Dodatkowy mnożnik dla dużych prędkości (symuluje v² efekt)
        const speedMagnitude = Math.sqrt(this.velocityX * this.velocityX + this.velocityY * this.velocityY);
        const speedSquaredFactor = 1.0 + (speedMagnitude / CONFIG.maxSpeed) * CONFIG.lateralForceMultiplier;

        const desiredLateralVelocity = baseLateralVelocity * speedSquaredFactor;

        // 6. Określ przyczepność opon (grip)
        let currentGrip = isBraking ? CONFIG.tireGripBraking : CONFIG.tireGrip;

        // 7. Sprawdź warunek poślizgu
        const lateralChange = desiredLateralVelocity - lateralVelocity;

        // Jeśli zmiana prędkości bocznej jest zbyt duża = poślizg!
        const lateralAcceleration = Math.abs(lateralChange);

        // Przyczepność rośnie tylko liniowo z prędkością (nie kwadratowo!)
        // To sprawia że przy dużych prędkościach łatwo przekroczyć limit
        const maxGrip = currentGrip * Math.abs(newForwardVelocity);

        if (lateralAcceleration > maxGrip && speedMagnitude > CONFIG.driftThreshold) {
            // POŚLIZG!
            this.isDrifting = true;

            // Ograniczona zmiana prędkości bocznej - opony nie nadążają
            const actualLateralChange = Math.sign(lateralChange) * maxGrip;
            const newLateralVelocity = lateralVelocity + actualLateralChange;

            // Kąt poślizgu
            this.driftAngle = Math.atan2(newLateralVelocity, newForwardVelocity);

            // Podczas poślizgu - wolniejsza rotacja
            this.angularVelocity = (newForwardVelocity / CONFIG.wheelBase) * Math.tan(this.steeringAngle) * currentGrip * dt;

            // Zastosuj tarcie podczas poślizgu
            newForwardVelocity *= Math.pow(CONFIG.driftFriction, dt);

            // Konwersja z powrotem do współrzędnych globalnych
            this.velocityX = newForwardVelocity * cos - newLateralVelocity * sin;
            this.velocityY = newForwardVelocity * sin + newLateralVelocity * cos;

            // Dodaj ślad opon podczas poślizgu
            if (Math.abs(this.driftAngle) > 0.15) { // Minimum kąt dla śladów
                this.addSkidMark();
            }

            // Dźwięk piszczących opon - intensywność zależy od kąta poślizgu
            const driftIntensity = Math.min(1.0, Math.abs(this.driftAngle) / 0.5);
            if (!driftOscillator) {
                startDriftSound(driftIntensity);
            } else {
                updateDriftSound(driftIntensity);
            }
        } else {
            // Normalna jazda - pełna przyczepność
            this.isDrifting = false;
            this.driftAngle = 0;

            const newLateralVelocity = desiredLateralVelocity;

            // Normalna rotacja
            this.angularVelocity = (newForwardVelocity / CONFIG.wheelBase) * Math.tan(this.steeringAngle) * dt;

            // Konwersja z powrotem do współrzędnych globalnych
            this.velocityX = newForwardVelocity * cos - newLateralVelocity * sin;
            this.velocityY = newForwardVelocity * sin + newLateralVelocity * cos;

            // Zatrzymaj dźwięk poślizgu
            if (driftOscillator) {
                stopDriftSound();
            }
        }

        // 8. Hamowanie
        if (isBraking) {
            const brakingDeceleration = CONFIG.brakingForce * dt;
            const currentSpeed = Math.sqrt(this.velocityX * this.velocityX + this.velocityY * this.velocityY);

            if (currentSpeed > 0.1) {
                const brakeMultiplier = Math.max(0, (currentSpeed - brakingDeceleration) / currentSpeed);
                this.velocityX *= brakeMultiplier;
                this.velocityY *= brakeMultiplier;
            } else {
                this.velocityX = 0;
                this.velocityY = 0;
            }
        }

        // 9. Tarcie naturalne
        if (!input.keys.ArrowUp && !input.keys.ArrowDown && !isBraking) {
            this.velocityX *= Math.pow(1 - CONFIG.friction, dt);
            this.velocityY *= Math.pow(1 - CONFIG.friction, dt);
        }

        if (!this.engineOn) {
            this.velocityX *= Math.pow(1 - CONFIG.friction, dt);
            this.velocityY *= Math.pow(1 - CONFIG.friction, dt);
        }

        // Zatrzymaj jeśli bardzo wolno
        const finalSpeed = Math.sqrt(this.velocityX * this.velocityX + this.velocityY * this.velocityY);
        if (finalSpeed < 0.05) {
            this.velocityX = 0;
            this.velocityY = 0;
            this.angularVelocity = 0;
        }

        // 10. Ogranicz maksymalną prędkość
        if (finalSpeed > CONFIG.maxSpeed) {
            const ratio = CONFIG.maxSpeed / finalSpeed;
            this.velocityX *= ratio;
            this.velocityY *= ratio;
        }

        // 11. Aktualizuj rotację
        this.angle += this.angularVelocity;
        this.angularVelocity *= Math.pow(CONFIG.angularDamping, dt);

        // 12. Aktualizuj pozycję
        this.x += this.velocityX * dt;
        this.y += this.velocityY * dt;

        // 13. Aktualizuj zmienną speed dla kompatybilności
        this.speed = Math.sqrt(this.velocityX * this.velocityX + this.velocityY * this.velocityY) *
            Math.sign(Math.cos(this.angle) * this.velocityX + Math.sin(this.angle) * this.velocityY);

        // 14. Zarządzaj śladami opon (max 200 punktów)
        if (this.skidMarks.length > 200) {
            this.skidMarks.shift();
        }
    }

    addSkidMark() {
        // Dodaj ślad pod tylnymi kołami
        const rearAxleOffset = -CONFIG.wheelBase / 2;
        const wheelOffset = CONFIG.carWidth / 3;

        const cos = Math.cos(this.angle);
        const sin = Math.sin(this.angle);

        // Lewe tylne koło
        const leftX = this.x + (rearAxleOffset * cos - wheelOffset * sin);
        const leftY = this.y + (rearAxleOffset * sin + wheelOffset * cos);

        // Prawe tylne koło
        const rightX = this.x + (rearAxleOffset * cos + wheelOffset * sin);
        const rightY = this.y + (rearAxleOffset * sin - wheelOffset * cos);

        this.skidMarks.push({ x: leftX, y: leftY, angle: this.angle, alpha: 1.0 });
        this.skidMarks.push({ x: rightX, y: rightY, angle: this.angle, alpha: 1.0 });
    }

    drawSkidMarks(ctx) {
        // Rysuj ślady opon
        ctx.save();
        ctx.strokeStyle = 'rgba(30, 30, 30, 0.7)';
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';

        for (let i = 1; i < this.skidMarks.length; i++) {
            const prev = this.skidMarks[i - 1];
            const curr = this.skidMarks[i];

            // Zanikaj starsze ślady
            const fadeIndex = Math.max(0, this.skidMarks.length - 150);
            const alpha = i < fadeIndex ? 0.3 : 0.7;

            ctx.globalAlpha = alpha;
            ctx.beginPath();
            ctx.moveTo(prev.x, prev.y);
            ctx.lineTo(curr.x, curr.y);
            ctx.stroke();
        }

        ctx.restore();
    }

    draw(ctx) {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate(this.angle);

        // Wybierz odpowiednie renderowanie
        if (this.carType === 'truck') {
            this.drawTruck(ctx);
        } else {
            this.drawStandardCar(ctx);
        }

        ctx.restore();
    }

    drawStandardCar(ctx) {
        // Symmetrical positions
        const wheelCenterY = 15;
        const wheelTopY_L = -wheelCenterY - this.wheelWidth / 2;
        const wheelTopY_R = wheelCenterY - this.wheelWidth / 2;

        const headlightCenterY = 12;
        const headlightHeight = 10;
        const headlightTopY_L = -headlightCenterY - headlightHeight / 2;
        const headlightTopY_R = headlightCenterY - headlightHeight / 2;

        // Trajectory
        if (this.engineOn && Math.abs(this.steeringAngle) > 0.05) {
            ctx.save();
            ctx.strokeStyle = 'rgba(255, 255, 0, 0.4)';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            const steer = this.steeringAngle;
            const wx = this.wheelBase / 2;
            let wy_L = -wheelCenterY;
            ctx.moveTo(wx, wy_L);
            ctx.lineTo(wx + Math.cos(steer) * 100, wy_L + Math.sin(steer) * 100);
            let wy_R = wheelCenterY;
            ctx.moveTo(wx, wy_R);
            ctx.lineTo(wx + Math.cos(steer) * 100, wy_R + Math.sin(steer) * 100);
            ctx.stroke();
            ctx.restore();
        }

        // Wheels
        ctx.fillStyle = '#222';
        this.drawWheel(ctx, -this.wheelBase / 2, wheelTopY_L, 0);
        this.drawWheel(ctx, -this.wheelBase / 2, wheelTopY_R, 0);
        this.drawWheel(ctx, this.wheelBase / 2, wheelTopY_L, this.steeringAngle);
        this.drawWheel(ctx, this.wheelBase / 2, wheelTopY_R, this.steeringAngle);

        // Body
        ctx.fillStyle = '#3498db';
        ctx.beginPath();
        ctx.roundRect(-this.l / 2, -this.w / 2, this.l, this.w, 6);
        ctx.fill();
        ctx.strokeStyle = '#2980b9';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Roof
        ctx.fillStyle = '#85c1e9';
        ctx.beginPath();
        ctx.roundRect(-this.l / 4, -this.w / 2 + 6, this.l / 2, this.w - 12, 3);
        ctx.fill();

        // Windshield
        ctx.fillStyle = 'rgba(255,255,255,0.3)';
        ctx.fillRect(this.l / 4, -this.w / 2 + 7, 5, this.w - 14);

        if (this.engineOn) {
            // Lights logic (same as before)
            const isReversing = this.speed < -0.1;
            const isBraking = this.speed > 0 ? (this.speed > 0 && this.speed < this.speed - 0.1) : isReversing; // Simplified check or bind input

            // Note: Since I don't have input in draw, I assume brake lights might flicker or use speed diff
            // For full accuracy, store isBraking in 'update' to 'this.isBrakingForDraw'

            // Simple generic red lights for now
            ctx.fillStyle = '#8b0000';
            ctx.beginPath();
            ctx.rect(-this.l / 2, headlightTopY_L, 3, headlightHeight);
            ctx.rect(-this.l / 2, headlightTopY_R, 3, headlightHeight);
            ctx.fill();

            // Headlights
            ctx.fillStyle = '#f1c40f';
            ctx.save();
            ctx.globalCompositeOperation = 'screen';
            ctx.fillStyle = 'rgba(255, 255, 200, 0.2)';
            ctx.beginPath();
            ctx.moveTo(this.l / 2, headlightTopY_L + headlightHeight / 2);
            ctx.lineTo(this.l / 2 + 150, (headlightTopY_L + headlightHeight / 2) - 60);
            ctx.lineTo(this.l / 2 + 150, (headlightTopY_R + headlightHeight / 2) + 60);
            ctx.lineTo(this.l / 2, headlightTopY_R + headlightHeight / 2);
            ctx.fill();
            ctx.restore();

            ctx.fillStyle = '#fff';
            ctx.beginPath();
            ctx.rect(this.l / 2 - 2, headlightTopY_L, 2, headlightHeight);
            ctx.rect(this.l / 2 - 2, headlightTopY_R, 2, headlightHeight);
            ctx.fill();
        }

        // Text
        ctx.save();
        ctx.fillStyle = '#000000';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('DELIVEROO', 0, 0);
        ctx.restore();
    }

    drawTruck(ctx) {
        // Truck Logic - Cabin + Trailer
        const frontAxleX = this.wheelBase / 2;
        const rearAxleX = -this.wheelBase / 2;
        const rearAxle2X = rearAxleX - 24; // Druga oś tylna

        // Koła (6 sztuk)
        ctx.fillStyle = '#222';
        // Przód
        this.drawWheel(ctx, frontAxleX, -this.w / 2 + 6, this.steeringAngle);
        this.drawWheel(ctx, frontAxleX, this.w / 2 - 6, this.steeringAngle);
        // Tył (Podwójna oś)
        this.drawWheel(ctx, rearAxleX, -this.w / 2 + 6, 0);
        this.drawWheel(ctx, rearAxleX, this.w / 2 - 6, 0);
        this.drawWheel(ctx, rearAxle2X, -this.w / 2 + 6, 0);
        this.drawWheel(ctx, rearAxle2X, this.w / 2 - 6, 0);

        // Łącznik (Rama)
        ctx.fillStyle = '#333';
        ctx.fillRect(-this.l / 2 + 10, -10, this.l - 20, 20);

        // Kabina (Przód)
        ctx.fillStyle = '#e67e22'; // Pomarańczowa kabina
        ctx.strokeStyle = '#d35400';
        ctx.lineWidth = 2;
        ctx.beginPath();
        // Kabina jest krótka i z przodu
        const cabinLen = 50;
        const cabinX = this.l / 2 - cabinLen;
        ctx.roundRect(cabinX, -this.w / 2, cabinLen, this.w, 4);
        ctx.fill();
        ctx.stroke();

        // Szyba kabiny
        ctx.fillStyle = '#85c1e9';
        ctx.fillRect(cabinX + 30, -this.w / 2 + 4, 15, this.w - 8);

        // Naczepa (Tył)
        ctx.fillStyle = '#ecf0f1'; // Biała naczepa
        ctx.strokeStyle = '#bdc3c7';
        ctx.beginPath();
        const trailerLen = 100;
        const trailerX = -this.l / 2;
        ctx.roundRect(trailerX, -this.w / 2 - 2, trailerLen, this.w + 4, 2);
        ctx.fill();
        ctx.stroke();

        // Detal naczepy
        ctx.fillStyle = '#bdc3c7';
        ctx.fillRect(trailerX + 5, -this.w / 2 + 5, trailerLen - 10, this.w - 10);

        // Światła ciężarówki (jeśli włączone)
        if (this.engineOn) {
            // Reflektory
            ctx.fillStyle = 'rgba(255, 255, 200, 0.3)';
            ctx.beginPath();
            ctx.moveTo(this.l / 2, -15);
            ctx.lineTo(this.l / 2 + 120, -60);
            ctx.lineTo(this.l / 2 + 120, 60);
            ctx.lineTo(this.l / 2, 15);
            ctx.fill();
        }
    }

    drawWheel(ctx, x, y, angle) {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);
        // Tire tread
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(-CONFIG.wheelLength / 2, 0, CONFIG.wheelLength, CONFIG.wheelWidth);
        // Rim highlight
        ctx.fillStyle = '#555';
        ctx.fillRect(-2, 2, 4, 6);
        ctx.restore();
    }
}

