import math
from threatsim.entities.radar import ThreatEntity, _radial_state
from threatsim.entities.threat_state import ThreatState


class SAMSite(ThreatEntity):
    """Surface-to-Air Missile site. Same state machine as RadarEmitter; different visual.

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
