import math
from threatsim.entities.radar import ThreatEntity
from threatsim.entities.threat_state import ThreatState


def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    """Ray-casting algorithm. Returns True if point is inside polygon."""
    x, y = point
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _dist_to_segment(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    """Minimum distance from point p to line segment ab."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _min_dist_to_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> float:
    """Minimum distance from point to any edge of polygon."""
    n = len(polygon)
    return min(
        _dist_to_segment(point, polygon[i], polygon[(i + 1) % n])
        for i in range(n)
    )


def _centroid(polygon: list[tuple[float, float]]) -> tuple[float, float]:
    """Arithmetic mean of polygon vertices. Correct for regular/convex polygons."""
    n = len(polygon)
    cx = sum(p[0] for p in polygon) / n
    cy = sum(p[1] for p in polygon) / n
    return (cx, cy)


class NoFlyZone(ThreatEntity):
    """No-fly zone defined by a polygon. State machine uses polygon geometry instead of radii.

    approach_radius: distance to polygon boundary at which TRACKING is triggered.
    ENGAGING is triggered when aircraft is inside the polygon (point-in-polygon test).
    position is set to the polygon centroid for HUD distance display.
    """

    def __init__(
        self,
        id: str,
        name: str,
        polygon: list[tuple[float, float]],
        approach_radius: float,
    ) -> None:
        super().__init__(id=id, name=name, position=_centroid(polygon))
        if len(polygon) < 3:
            raise ValueError(f"polygon must have at least 3 vertices, got {len(polygon)}")
        self.polygon = polygon
        self.approach_radius = approach_radius

    def update_state(self, aircraft_pos: tuple[float, float]) -> None:
        if _point_in_polygon(aircraft_pos, self.polygon):
            self.state = ThreatState.ENGAGING
        elif _min_dist_to_polygon(aircraft_pos, self.polygon) <= self.approach_radius:
            self.state = ThreatState.TRACKING
        else:
            self.state = ThreatState.SEARCHING
