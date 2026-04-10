from threatsim.entities.sam import SAMSite
from threatsim.entities.threat_state import ThreatState


def _make_sam(pos=(400, 400), detection=200, engagement=100):
    return SAMSite(
        id="s1", name="SA-6", position=pos,
        detection_radius=detection, engagement_radius=engagement,
    )


def test_sam_initial_state():
    s = _make_sam()
    assert s.state == ThreatState.SEARCHING


def test_sam_tracking():
    s = _make_sam(pos=(400, 400), detection=200, engagement=100)
    s.update_state((400 + 150, 400))
    assert s.state == ThreatState.TRACKING


def test_sam_engaging():
    s = _make_sam(pos=(400, 400), detection=200, engagement=100)
    s.update_state((400 + 80, 400))
    assert s.state == ThreatState.ENGAGING


def test_sam_is_distinct_type_from_radar():
    from threatsim.entities.radar import RadarEmitter
    s = _make_sam()
    assert not isinstance(s, RadarEmitter)
    assert isinstance(s, SAMSite)
