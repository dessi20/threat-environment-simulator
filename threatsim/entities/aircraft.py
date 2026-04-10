import math
from collections import deque
from threatsim.entities.base import BaseEntity

_TRACK_MAX = 500


def _angle_diff(target: float, current: float) -> float:
    """Signed angular difference in degrees, normalised to [-180, 180]."""
    return (target - current + 180.0) % 360.0 - 180.0


class Aircraft(BaseEntity):
    def __init__(
        self,
        id: str,
        name: str,
        start_position: tuple[float, float],
        speed: float,
        heading: float,
        turn_rate: float,
        waypoints: list[tuple[float, float]],
        hold_radius: float = 30.0,
        arrival_threshold: float = 10.0,
    ) -> None:
        super().__init__(id=id, position=start_position)
        self.name = name
        self.speed = speed
        self.heading = heading
        self.turn_rate = turn_rate
        self.waypoints = waypoints
        if not self.waypoints:
            raise ValueError("waypoints must contain at least one point")
        self.hold_radius = hold_radius
        self.arrival_threshold = arrival_threshold
        self.current_waypoint_index: int = 0
        self.track_history: deque[tuple[float, float]] = deque(maxlen=_TRACK_MAX)
        self._in_hold: bool = False
        self._hold_center: tuple[float, float] | None = None
        self._hold_angle: float = 0.0  # radians

    def _bearing_to(self, target: tuple[float, float]) -> float:
        """Bearing in degrees from current position to target (clockwise from +x)."""
        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]
        return math.degrees(math.atan2(dy, dx)) % 360.0

    def _move(self, dt: float) -> None:
        rad = math.radians(self.heading)
        x, y = self.position
        self.position = (x + math.cos(rad) * self.speed * dt,
                         y + math.sin(rad) * self.speed * dt)

    def _enter_hold(self) -> None:
        self._in_hold = True
        self._hold_center = self.waypoints[-1]
        dx = self.position[0] - self._hold_center[0]
        dy = self.position[1] - self._hold_center[1]
        self._hold_angle = math.atan2(dy, dx)

    def _update_hold(self, dt: float) -> None:
        omega = self.speed / self.hold_radius  # rad/s
        self._hold_angle += omega * dt
        cx, cy = self._hold_center  # type: ignore[misc]
        self.position = (
            cx + self.hold_radius * math.cos(self._hold_angle),
            cy + self.hold_radius * math.sin(self._hold_angle),
        )
        self.heading = math.degrees(self._hold_angle + math.pi / 2) % 360.0

    def update(self, dt: float) -> None:
        """Advance aircraft state by dt seconds."""
        if self._in_hold:
            self._update_hold(dt)
        else:
            target = self.waypoints[self.current_waypoint_index]
            bearing = self._bearing_to(target)
            error = _angle_diff(bearing, self.heading)
            max_turn = self.turn_rate * dt
            self.heading = (self.heading + max(-max_turn, min(max_turn, error))) % 360.0
            self._move(dt)
            dist = math.hypot(target[0] - self.position[0], target[1] - self.position[1])
            if dist < self.arrival_threshold:
                if self.current_waypoint_index < len(self.waypoints) - 1:
                    self.current_waypoint_index += 1
                else:
                    self._enter_hold()

        self.track_history.append(self.position)
