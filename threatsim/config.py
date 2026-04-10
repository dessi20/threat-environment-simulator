import json
import pathlib
from threatsim.entities.aircraft import Aircraft
from threatsim.entities.radar import RadarEmitter
from threatsim.entities.sam import SAMSite
from threatsim.entities.noflyzone import NoFlyZone


class ConfigError(Exception):
    pass


_AIRCRAFT_REQUIRED = ["id", "start_position", "speed", "heading", "turn_rate", "waypoints"]
_RADAR_SAM_REQUIRED = ["id", "name", "position", "detection_radius", "engagement_radius"]
_NFZ_REQUIRED = ["id", "name", "polygon", "approach_radius"]
_THREAT_REQUIRED: dict[str, list[str]] = {
    "radar": _RADAR_SAM_REQUIRED,
    "sam": _RADAR_SAM_REQUIRED,
    "noflyzone": _NFZ_REQUIRED,
}
_THREAT_CLASSES = {"radar": RadarEmitter, "sam": SAMSite}


def _require(data: dict, fields: list[str], context: str) -> None:
    for f in fields:
        if f not in data:
            raise ConfigError(f"{context}: missing required field '{f}'")


def _build_aircraft(data: dict) -> Aircraft:
    _require(data, _AIRCRAFT_REQUIRED, "aircraft")
    return Aircraft(
        id=data["id"],
        name=data.get("name", data["id"]),
        start_position=tuple(data["start_position"]),
        speed=data["speed"],
        heading=data["heading"],
        turn_rate=data["turn_rate"],
        waypoints=[tuple(w) for w in data["waypoints"]],
        hold_radius=data.get("hold_radius", 30.0),
        arrival_threshold=data.get("arrival_threshold", 10.0),
    )


def _build_threat(data: dict):
    t_type = data.get("type")
    if t_type not in _THREAT_REQUIRED:
        raise ConfigError(f"Unknown threat type: '{t_type}'")
    _require(data, _THREAT_REQUIRED[t_type], f"threat '{data.get('id', '?')}'")

    if t_type in _THREAT_CLASSES:
        cls = _THREAT_CLASSES[t_type]
        return cls(
            id=data["id"],
            name=data["name"],
            position=tuple(data["position"]),
            detection_radius=data["detection_radius"],
            engagement_radius=data["engagement_radius"],
        )
    # noflyzone
    return NoFlyZone(
        id=data["id"],
        name=data["name"],
        polygon=[tuple(p) for p in data["polygon"]],
        approach_radius=data["approach_radius"],
    )


def load_scenario(path: str | pathlib.Path) -> dict:
    try:
        with open(path) as f:
            raw = json.load(f)
    except FileNotFoundError:
        raise ConfigError(f"Scenario file not found: '{path}'")

    aircraft_data = raw.get("aircraft")
    if not aircraft_data:
        raise ConfigError("Missing required section 'aircraft'")

    aircraft = _build_aircraft(aircraft_data)
    threats = [_build_threat(t) for t in raw.get("threats", [])]
    window = raw.get("window", {"width": 1200, "height": 800})

    return {"aircraft": aircraft, "threats": threats, "window": window}
