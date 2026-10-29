"""Independent rotating-frame two-body calibration for a future-commutation gate.

This is a standalone numerical model, NOT the ANISE or Nyx native implementation.
It uses a constant Earth-spin approximation and does not authenticate source code.
"""

import math


MU = 398600.435436096  # km^3/s^2, report's public Earth gravitational parameter
SPIN = 7.2921159e-5    # radians/second, idealized constant Earth spin
R0 = 7000.0            # km
V0 = 7.5               # km/s


def norm_difference(a, b):
    return math.hypot(*(x - y for x, y in zip(a, b)))


def _rhs(kind, state):
    x, y, vx, vy = state
    r3 = math.hypot(x, y)**3
    ax, ay = -MU*x/r3, -MU*y/r3
    if kind == 'correct_rotating':
        ax += 2*SPIN*vy + SPIN**2*x
        ay += -2*SPIN*vx + SPIN**2*y
    return (vx, vy, ax, ay)


def _step(kind, state, h):
    def shifted(s, k, factor):
        return tuple(si + h*factor*ki for si, ki in zip(s, k))
    k1 = _rhs(kind, state)
    k2 = _rhs(kind, shifted(state, k1, 0.5))
    k3 = _rhs(kind, shifted(state, k2, 0.5))
    k4 = _rhs(kind, shifted(state, k3, 1.0))
    return tuple(si + h*(a+2*b+2*c+d)/6
                 for si, a, b, c, d in zip(state, k1, k2, k3, k4))


def simulate(kind, *, duration=600.0, step=1.0):
    if kind not in ('inertial', 'naive_rotating', 'correct_rotating'):
        raise ValueError(kind)
    if duration < 0 or step <= 0:
        raise ValueError('invalid interval')
    state = (R0, 0.0, 0.0, V0 if kind == 'inertial' else V0 - SPIN*R0)
    steps = max(1, math.ceil(duration/step))
    h = duration/steps
    for _ in range(steps):
        state = _step(kind, state, h)
    x, y, vx, vy = state
    if kind == 'inertial':
        return (x, y), (vx, vy)
    # R(t) maps rotating coordinates to inertial coordinates. Velocity must
    # include basis-motion transport, not merely an ordinary vector rotation.
    c, s = math.cos(SPIN*duration), math.sin(SPIN*duration)
    return ((c*x-s*y, s*x+c*y),
            (c*(vx-SPIN*y)-s*(vy+SPIN*x),
             s*(vx-SPIN*y)+c*(vy+SPIN*x)))


def kepler_truth(duration):
    """Independent closed-form two-body solution (no RK4 or frame transform)."""
    energy = V0**2/2 - MU/R0
    a = -MU/(2*energy)
    e = R0/a - 1
    n = math.sqrt(MU/a**3)
    mean = math.pi + n*duration
    anomaly = mean
    for _ in range(15):
        anomaly -= (anomaly - e*math.sin(anomaly)-mean)/(1-e*math.cos(anomaly))
    q = 1-e*math.cos(anomaly)
    x = -a*(math.cos(anomaly)-e)
    y = -a*math.sqrt(1-e*e)*math.sin(anomaly)
    vx = +a*n*math.sin(anomaly)/q
    vy = -a*n*math.sqrt(1-e*e)*math.cos(anomaly)/q
    return (x, y), (vx, vy)
