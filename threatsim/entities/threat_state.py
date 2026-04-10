from enum import IntEnum


class ThreatState(IntEnum):
    """Operational mode of a threat entity, ordered by engagement severity."""
    SEARCHING = 0
    TRACKING = 1
    ENGAGING = 2
