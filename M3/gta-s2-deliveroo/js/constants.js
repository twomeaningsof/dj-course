// --- CONFIGURATION ---
export const CONFIG = {
    // Car dimensions (approx 1px = 2cm scale)
    carWidth: 44,
    carLength: 90,
    wheelBase: 60,
    wheelWidth: 10,
    wheelLength: 20,

    // Physics - adjusted for "High Speed" potential
    // We map internal speed 1.0 to approx 15 km/h
    kmhFactor: 8,
    maxSpeed: 18.0, // ~216 km/h theoretical max
    maxReverseSpeed: -5.0, // ~60 km/h

    // Car mode: 'normal' (city car) or 'sport' (performance car)
    carMode: 'normal', // Default: normal city car
    accelerationNormal: 0.05, // ~10 seconds to 100 km/h (city car)
    accelerationSport: 0.15,   // ~1.4 seconds to 100 km/h (sport car)
    get acceleration() {
        return this.carMode === 'sport' ? this.accelerationSport : this.accelerationNormal;
    },

    friction: 0.06,
    brakingForce: 0.5,

    // Steering
    maxSteerAngle: 0.65, // ~37 degrees
    steerSpeed: 0.03, // Slower steering change for weight feeling
    steerRestoringDriving: 0.02, // Auto-center speed for Driving Mode

    // Handbrake Start (Launch Control)
    handbrakeBoostRate: 0.018, // Jak szybko buduje się boost (obroty silnika)
    handbrakeBoostMax: 1.0, // Maksymalny poziom boost
    handbrakeBoostMultiplier: 6.0, // Mnożnik przyspieszenia przy starcie - MEGA BOOST!
    handbrakeBoostDecay: 0.05, // Jak szybko spada boost gdy nie używany

    // Drift Physics (New!)
    tireGrip: 0.85, // Przyczepność opon (0.0 = brak, 1.0 = perfekcyjna) - ZMNIEJSZONE dla łatwiejszego poślizgu
    tireGripBraking: 0.65, // Zmniejszona przyczepność podczas hamowania - BARDZIEJ zmniejszone
    driftThreshold: 2.0, // Minimalna prędkość dla poślizgu - OBNIŻONE
    driftFriction: 0.98, // Tarcie podczas poślizgu (wyższe = wolniejsze hamowanie)
    angularDamping: 0.94, // Tłumienie rotacji podczas poślizgu - więcej rotacji
    lateralForceMultiplier: 2.0, // Mnożnik siły bocznej (symuluje v² zamiast v) - ZWIĘKSZONE!

    // Interaction
    curbSafeSpeed: 1.5 // ~18 km/h. Below this, curbs bounce. Above, crash.
};

export const VEHICLE_STATS = {
    standard: {
        // Dimensions
        width: 44, length: 90, wheelBase: 60,
        wheelWidth: 10, wheelLength: 20,
        // Physics
        maxSpeed: 18.0, maxReverseSpeed: -5.0,
        acceleration: 0.05, // Averaged 'normal' acceleration
        brakingForce: 0.5,
        friction: 0.06,
        // Steering
        maxSteerAngle: 0.65, // ~37 degrees
        steerSpeed: 0.03,
        // Drift
        tireGrip: 0.85,
        lateralForceMultiplier: 2.0
    },
    suv: {
        // Dimensions
        width: 50, length: 115, wheelBase: 60,
        wheelWidth: 10, wheelLength: 20,
        // Physics
        maxSpeed: 18.0, maxReverseSpeed: -5.0,
        acceleration: 0.05, // Averaged 'normal' acceleration
        brakingForce: 0.5,
        friction: 0.06,
        // Steering
        maxSteerAngle: 0.65, // ~37 degrees
        steerSpeed: 0.03,
        // Drift
        tireGrip: 0.85,
        lateralForceMultiplier: 2.0
    },
    truck: {
        // Dimensions (Significantly larger)
        width: 55, length: 150, wheelBase: 110,
        wheelWidth: 12, wheelLength: 24,
        // Physics (Heavier, slower)
        maxSpeed: 12.0, maxReverseSpeed: -3.0,
        acceleration: 0.015, // Very slow acceleration
        brakingForce: 0.3,   // Harder to stop
        friction: 0.04,      // More momentum (lower friction)
        // Steering
        maxSteerAngle: 0.45, // Trucks have limited turning radius
        steerSpeed: 0.015,   // Heavy steering wheel
        // Drift (Scary, heavy drift)
        tireGrip: 0.75,      // Less grip due to weight shifting
        lateralForceMultiplier: 2.5 // Slide easier at speed
    }
};