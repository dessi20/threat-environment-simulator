import math
from threatsim.entities.threat_state import ThreatState
from threatsim.entities.radar import RadarEmitter


def test_threat_state_members():
    assert ThreatState.SEARCHING is not None
    assert ThreatState.TRACKING is not None
    assert ThreatState.ENGAGING is not None


def test_threat_state_ordering():
    states = [ThreatState.SEARCHING, ThreatState.TRACKING, ThreatState.ENGAGING]
    assert states[0].value < states[1].value < states[2].value


def _make_radar(pos=(500, 500), detection=150, engagement=75):
    return RadarEmitter(
        id="r1", name="TEST RADAR", position=pos,
        detection_radius=detection, engagement_radius=engagement,
    )


def test_radar_initial_state_is_searching():
    r = _make_radar()
    assert r.state == ThreatState.SEARCHING


def test_radar_transitions_to_tracking():
    r = _make_radar(pos=(500, 500), detection=150, engagement=75)
    # Place aircraft just inside detection radius
    aircraft_pos = (500 + 140, 500)
    r.update_state(aircraft_pos)
    assert r.state == ThreatState.TRACKING


def test_radar_transitions_to_engaging():
    r = _make_radar(pos=(500, 500), detection=150, engagement=75)
    aircraft_pos = (500 + 50, 500)
    r.update_state(aircraft_pos)
    assert r.state == ThreatState.ENGAGING


def test_radar_reverts_to_searching():
    r = _make_radar(pos=(500, 500), detection=150, engagement=75)
    r.update_state((500 + 50, 500))   # ENGAGING
    assert r.state == ThreatState.ENGAGING
    r.update_state((500 + 200, 500))  # outside detection — back to SEARCHING
    assert r.state == ThreatState.SEARCHING


def test_radar_boundary_exactly_at_detection_radius():
    r = _make_radar(pos=(0, 0), detection=100, engagement=50)
    # Exactly at boundary: dist == detection_radius → TRACKING
    r.update_state((100.0, 0.0))
    assert r.state == ThreatState.TRACKING


def test_radar_update_does_not_move():
    r = _make_radar(pos=(500, 500))
    r.update(dt=1.0)
    assert r.position == (500, 500)
