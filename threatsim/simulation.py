from threatsim.entities.aircraft import Aircraft
from threatsim.entities import ThreatEntity


class Simulation:
    FIXED_DT: float = 1.0 / 60.0
    MAX_STEPS_PER_FRAME: int = 10  # prevent spiral-of-death on slow frames

    def __init__(self, aircraft: Aircraft, threats: list[ThreatEntity]) -> None:
        self.aircraft = aircraft
        self.threats = threats
        self._accumulator: float = 0.0
        self.tick_count: int = 0

    def step(self, dt: float) -> None:
        """Advance simulation by exactly one fixed step."""
        self.aircraft.update(dt)
        for threat in self.threats:
            threat.update_state(self.aircraft.position)
        self.tick_count += 1

    def update(self, wall_dt: float) -> None:
        """Consume wall-clock delta using fixed-timestep accumulator."""
        self._accumulator += wall_dt
        steps = 0
        while self._accumulator >= self.FIXED_DT and steps < self.MAX_STEPS_PER_FRAME:
            self.step(self.FIXED_DT)
            self._accumulator -= self.FIXED_DT
            steps += 1
