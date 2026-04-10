import math
from threatsim.entities.base import BaseEntity
from threatsim.entities.threat_state import ThreatState


def _radial_state(dist: float, engagement_radius: float, detection_radius: float) -> ThreatState:
    """Compute ThreatState for a radial (circular) threat based on distance."""
    if dist <= engagement_radius:
        return ThreatState.ENGAGING
    elif dist <= detection_radius:
        return ThreatState.TRACKING
    return ThreatState.SEARCHING


class ThreatEntity(BaseEntity):
    """Base for all stationary threat entities."""

    def __init__(self, id: str, name: str, position: tuple[float, float]) -> None:
        super().__init__(id=id, position=position)
        self.name = name
        self.state: ThreatState = ThreatState.SEARCHING

    def update_state(self, aircraft_pos: tuple[float, float]) -> None:
        """Recompute threat state based on aircraft position. Override for non-radial threats."""
        raise NotImplementedError

    def update(self, dt: float) -> None:
        """Stationary — no position update needed."""
        pass


class RadarEmitter(ThreatEntity):
    """Radar emitter threat. Transitions state based on aircraft distance.

    detection_radius: distance at which aircraft enters TRACKING state.
    engagement_radius: distance at which aircraft enters ENGAGING state.
    Both radii are in world units (pixels). engagement_radius must be <= detection_radius.
    """

    def __init__(
        self,
        id: str,
        name: str,
        position: tuple[float, float],
        detection_radius: float,
        engagement_radius: float,
    ) -> None:
        super().__init__(id=id, name=name, position=position)
        if engagement_radius > detection_radius:
            raise ValueError(
                f"engagement_radius ({engagement_radius}) must not exceed "
                f"detection_radius ({detection_radius})"
            )
        self.detection_radius = detection_radius
        self.engagement_radius = engagement_radius

    def update_state(self, aircraft_pos: tuple[float, float]) -> None:
        dist = math.hypot(
            aircraft_pos[0] - self.position[0],
            aircraft_pos[1] - self.position[1],
        )
        self.state = _radial_state(dist, self.engagement_radius, self.detection_radius)
