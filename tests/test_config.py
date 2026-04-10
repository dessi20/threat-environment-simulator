import json
import pathlib
import tempfile
import pytest
from threatsim.config import load_scenario, ConfigError
from threatsim.entities.aircraft import Aircraft
from threatsim.entities.radar import RadarEmitter
from threatsim.entities.sam import SAMSite
from threatsim.entities.noflyzone import NoFlyZone

VALID_SCENARIO = {
    "window": {"width": 1200, "height": 800},
    "aircraft": {
        "id": "ac1",
        "name": "VIPER 01",
        "start_position": [100, 400],
        "speed": 120,
        "heading": 0,
        "turn_rate": 45,
        "hold_radius": 30,
        "arrival_threshold": 10,
        "waypoints": [[300, 200], [600, 350]],
    },
    "threats": [
        {"type": "radar", "id": "r1", "name": "EW RADAR",
         "position": [400, 300], "detection_radius": 150, "engagement_radius": 75},
        {"type": "sam", "id": "s1", "name": "SA-6",
         "position": [700, 250], "detection_radius": 200, "engagement_radius": 100},
        {"type": "noflyzone", "id": "nfz1", "name": "NFZ ALPHA",
         "polygon": [[500, 100], [650, 100], [650, 220], [500, 220]],
         "approach_radius": 50},
    ],
}


def _write_temp(data: dict) -> pathlib.Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    return pathlib.Path(f.name)


def test_load_valid_scenario():
    path = _write_temp(VALID_SCENARIO)
    result = load_scenario(path)
    assert isinstance(result["aircraft"], Aircraft)
    assert len(result["threats"]) == 3
    assert result["window"] == {"width": 1200, "height": 800}


def test_threat_types_are_correct():
    path = _write_temp(VALID_SCENARIO)
    result = load_scenario(path)
    threats = result["threats"]
    assert isinstance(threats[0], RadarEmitter)
    assert isinstance(threats[1], SAMSite)
    assert isinstance(threats[2], NoFlyZone)


def test_aircraft_fields_loaded_correctly():
    path = _write_temp(VALID_SCENARIO)
    ac = load_scenario(path)["aircraft"]
    assert ac.id == "ac1"
    assert ac.speed == 120
    assert ac.turn_rate == 45
    assert ac.waypoints == [(300, 200), (600, 350)]


def test_missing_aircraft_raises_config_error():
    data = json.loads(json.dumps(VALID_SCENARIO))
    del data["aircraft"]
    path = _write_temp(data)
    with pytest.raises(ConfigError, match="aircraft"):
        load_scenario(path)


def test_missing_aircraft_field_raises_config_error():
    data = json.loads(json.dumps(VALID_SCENARIO))
    del data["aircraft"]["speed"]
    path = _write_temp(data)
    with pytest.raises(ConfigError, match="speed"):
        load_scenario(path)


def test_unknown_threat_type_raises_config_error():
    data = json.loads(json.dumps(VALID_SCENARIO))
    data["threats"][0]["type"] = "missile"
    path = _write_temp(data)
    with pytest.raises(ConfigError, match="missile"):
        load_scenario(path)


def test_missing_threat_required_field_raises_config_error():
    data = json.loads(json.dumps(VALID_SCENARIO))
    del data["threats"][0]["detection_radius"]
    path = _write_temp(data)
    with pytest.raises(ConfigError, match="detection_radius"):
        load_scenario(path)
